"""
Run Spark several text queries jobs.

    usage: run_queries.py [-h] [-n [NUM_CORES]]  [-e [ERRORS_FILE]]
                        data_file model_name -l query_list [query_config_file]

    Run Spark text analysis job

    positional arguments:
        data_file             Data file listing data files to query
        model_name            Data model to which data files conform:
        ['books', 'papers', 'fmp','nzpp', 'generic_xml', 'nls', 'hdfs', 'psql', 'es']
        query_list            A file with the queries to run. For each query
                                we have to indicate: query_module [query_configuration_file] [-r results_file]
        Example:
            defoe.nls.queries.normalize -r results.txt
            defoe.nls.queries.keysearch_by_year queries/sport.yml -r results_sc_sports


    optional arguments:
        -h, --help            show this help message and exit
        -n [NUM_CORES], --num_cores [NUM_CORES]
                                Number of cores
        -e [ERRORS_FILE], --errors_file [ERRORS_FILE]
                                Errors file

    * data_file: lists either URLs or paths to files on the file system.
    * model_name: text model to be used. The model determines the modules
                    loaded. Given a "model_name" value of "<MODEL_NAME>" then a module
                    "defoe.<MODEL_NAME>.setup" must exist and support a function:
    tuple(Object | str, str)
    filename_to_object(str: filename)

        - tuple(Object, None) is returned where Object is an instance of the
        - object model representing the data, if the file was successfully
        - read and parsed into an object
        - tuple(str, filename) is returned with the filename and
        - an error message, if the file was not successfully read and parsed
        - into an object
    * query_name: name of Python module implementing the query to run
        e.g. "defoe.alto.queries.find_words_group_by_word" or
        "defoe.papers.queries.articles_containing_words". The query must be
        compatible with the chosen model in "model_name". The module
        must support a function

        list do_query(pyspark.rdd.PipelinedRDD rdd,
                    str config_file,
                    py4j.java_gateway.JavaObject logger)

    * "query_config_file": query-specific configuration file. This is
        optional and depends on the chosen query module above.
    * results_file": name of file to hold query results in YAML
        format. Default: "results_NUM_QUERY.yml".
"""

try:
    from pyspark import SparkContext, SparkConf
except ImportError:
    raise ImportError(
        "Unable to load Spark. Did you install it on your machine?"
    )

from defoe.spark_utils import files_to_rdd, ROOT_MODULE, SETUP_MODULE, MODELS

from argparse import ArgumentParser
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
        help="Data model to which data files conform: " + str(MODELS),
    )
    parser.add_argument(
        "-l", "--queries_list", nargs="?", help="Queries list file"
    )
    parser.add_argument(
        "-n", "--num_cores", nargs="?", default=1, help="Number of cores"
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
    :return: True
    :rtype: bool
    :raises SyntaxError: if there are any problems with the arguments passed
    """
    if args.model_name not in MODELS:
        raise SyntaxError(f"'model' must be one of {MODELS}")

    return True


def main() -> True:
    """
    Run Spark text analysis job.

    :return: True if job is successful.
    :rtype: True
    :raises SyntaxError: if "errors_file" argument does not end with ".yaml"
        or ".json"
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

    # Dynamically load model and query modules.
    setup = importlib.import_module(
        ROOT_MODULE + "." + args.model_name + "." + SETUP_MODULE
    )

    filename_to_object = setup.filename_to_object

    # Configure Spark.
    conf = SparkConf()
    conf.setAppName(args.model_name)
    conf.set("spark.cores.max", args.num_cores)

    # Submit job.
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
        # Collect and record problematic files before attempting query.
        errors = error_data.collect()
        errors = list(errors)
        if errors:
            with open(args.errors_file, "w") as f:
                if yaml_errors_file:
                    f.write(yaml.safe_dump(list(errors)))
                elif json_errors_file:
                    f.write(json.dumps(list(errors)))

    # Lets open the queries list and run each of them:
    with open(args.queries_list, "r") as f:
        queries = f.readlines()

    for num_query, query in enumerate(queries):
        query_l = query.rstrip()
        arguments = query_l.split(" ")
        query_name = arguments[0]

        # Default values for results and config_file:
        query_config_file = None
        results_file = f"results_{num_query}.yml"

        if arguments[1]:
            if arguments[1] != "-r":
                query_config_file = arguments[1]
                if arguments[2]:
                    results_file = arguments[3]
            else:
                results_file = arguments[2]

        # Remove old results file if it exists
        if os.path.exists(results_file):
            # TODO: issue warning here?
            os.remove(results_file)

        query = importlib.import_module(query_name)
        do_query = query.do_query
        results = do_query(ok_data, query_config_file, log, context)

        if results != "0":
            with open(results_file, "w") as f:
                f.write(yaml.safe_dump(dict(results)))

    return True


if __name__ == "__main__":
    main()
