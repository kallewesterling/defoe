"""
Run Spark text query job.

    usage: run_query.py [-h]
                        [-n [NUM_CORES]]
                        [-r [RESULTS_FILE]]
                        [-e [ERRORS_FILE]]
                        data_file
                        model_name
                        query_name
                        [query_config_file]

    positional arguments:
        data_file           Data file listing data files to query
        model_name          Data model to which data files conform:
                            ['books', 'papers', 'fmp','nzpp', 'generic_xml', 'nls', 'hdfs', 'psql', 'es', 'nlsArticles']
        query_name          Query module name
        query_config_file   Query-specific configuration file

    optional arguments:
        -h, --help          Show this help message and exit
        -n [NUM_CORES], --num_cores [NUM_CORES]
                            Number of cores
        -r [RESULTS_FILE], --results_file [RESULTS_FILE]
                            Query results file
        -e [ERRORS_FILE], --errors_file [ERRORS_FILE]
                            Errors file

    * data_file: lists either URLs or paths to files on the file system.
    * model_name: text model to be used. The model determines the modules
        loaded. Given a "model_name" value of "<MODEL_NAME>" then a module
        "defoe.<MODEL_NAME>.setup" must exist and support a function:

        tuple(Object | str or unicode, str or unicode)
        filename_to_object(str or unicode: filename)

        - tuple(Object, None) is returned where Object is an instance of the
        - object model representing the data, if the file was successfully
        - read and parsed into an object
        - tuple(str or unicode, filename) is returned with the filename and
        - an error message, if the file was not successfully read and parsed
        - into an object
    * query_name: name of Python module implementing the query to run
        e.g. "defoe.alto.queries.find_words_group_by_word" or
        "defoe.papers.queries.articles_containing_words". The query must be
        compatible with the chosen model in "model_name". The module
        must support a function

            list do_query(pyspark.rdd.PipelinedRDD rdd,
                        str|unicode config_file,
                        py4j.java_gateway.JavaObject logger)

    * "query_config_file": query-specific configuration file. This is
        optional and depends on the chosen query module above.
    * results_file": name of file to hold query results in YAML
        format. Default: "results.yml".
"""


from defoe.spark_utils import files_to_rdd, ROOT_MODULE, SETUP_MODULE, MODELS

from argparse import ArgumentParser

try:
    from pyspark import SparkContext, SparkConf
except ImportError:
    raise ImportError(
        "Unable to load Spark. Did you install it on your machine?"
    )

import importlib
import json
import os
import yaml


def get_args():
    """
    :meta private:
    """

    parser = ArgumentParser(description="Run Spark text analysis job")
    parser.add_argument(
        "data_file", help="Data file listing data files to query"
    )
    parser.add_argument(
        "model_name",
        help=f"Data model to which data files conform: {MODELS}",
    )
    parser.add_argument("query_name", help="Query module name")
    parser.add_argument(
        "query_config_file",
        nargs="?",
        default=None,
        help="Query-specific configuration file",
    )
    parser.add_argument(
        "-n", "--num_cores", nargs="?", default=1, help="Number of cores"
    )
    parser.add_argument(
        "-r",
        "--results_file",
        nargs="?",
        default="results.yml",
        help="Query results file",
    )
    parser.add_argument(
        "-e",
        "--errors_file",
        nargs="?",
        default="errors.yml",
        help="Errors file",
    )

    return parser.parse_args()


def _test_args(args) -> bool:
    """
    Tests whether all the arguments passed from the command line are correctly
    formatted and adheres to the script's standards.

    :param args: Arguments passed from ``ArgumentParser.parse_args``
    :raises SyntaxError: Raises SyntaxError if there are any problems with the
        arguments passed.
    :return: True
    :rtype: bool
    """
    if args.model_name not in MODELS:
        raise SyntaxError(f"'model' must be one of {MODELS}")

    return True


def main():
    """
    Run Spark text analysis job.
    """

    args = get_args()
    _test_args(args)

    # Set up errors and results files
    yaml_errors_file = any(
        [args.errors_file.endswith(".yml"), args.errors_file.endswith(".yaml")]
    )
    json_errors_file = any([args.errors_file.endswith(".json")])

    if not json_errors_file or yaml_errors_file:
        raise SyntaxError("Errors file ending must be .yaml or .json.")

    yaml_results_file = any(
        [
            args.results_file.endswith(".yml"),
            args.results_file.endswith(".yaml"),
        ]
    )
    json_results_file = any([args.results_file.endswith(".json")])

    if not json_results_file or yaml_results_file:
        raise SyntaxError("Results file ending must be .yaml or .json.")

    for f in [args.results_file, args.errors_file]:
        if os.path.exists(f):
            # TODO: issue warning here?
            os.remove(f)

    # Dynamically load model and query modules
    setup = importlib.import_module(
        ROOT_MODULE + "." + args.model_name + "." + SETUP_MODULE
    )
    query = importlib.import_module(args.query_name)

    filename_to_object = setup.filename_to_object
    do_query = query.do_query

    # Configure Spark
    conf = SparkConf()
    conf.setAppName(args.model_name)
    conf.set("spark.cores.max", args.num_cores)

    # Submit job
    context = SparkContext(conf=conf)
    log = context._jvm.org.apache.log4j.LogManager.getLogger(__name__)

    if args.model_name in ["hdfs", "psql", "es"]:
        # We just need to execute the query because the data has been already
        # preprocessed and saved into HDFS | db
        ok_data = filename_to_object(args.data_file, context)
    else:
        # Collect and record problematic files before attempting query

        # [filename,...]
        rdd_filenames = files_to_rdd(
            context, args.num_cores, data_file=args.data_file
        )

        # [(object, None)|(filename, error_message), ...]
        data = rdd_filenames.map(lambda filename: filename_to_object(filename))

        # [object, ...]
        ok_data = data.filter(
            lambda obj_file_err: obj_file_err[1] is None
        ).map(lambda obj_file_err: obj_file_err[0])

        # [(filename, error_message), ...]
        error_data = data.filter(
            lambda obj_file_err: obj_file_err[1] is not None
        ).map(lambda obj_file_err: (obj_file_err[0], obj_file_err[1]))

        # Collect and write the errors to errors_file
        errors = error_data.collect()
        errors = list(errors)
        if errors:
            with open(args.errors_file, "w") as f:
                if yaml_errors_file:
                    f.write(yaml.safe_dump(list(errors)))
                elif json_errors_file:
                    f.write(json.dumps(list(errors)))

    results = do_query(ok_data, args.query_config_file, log, context)

    if results == "0":
        # TODO: We might want some kind of output in case the results are "0"
        # as well?
        return

    with open(args.results_file, "w") as f:
        if yaml_results_file:
            f.write(json.dumps(dict(results)))
        elif json_results_file:
            f.write(yaml.safe_dump(dict(results)))


if __name__ == "__main__":
    main()
