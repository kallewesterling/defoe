"""
Segementation of images for keywords and groups by word.
"""

from pyspark.rdd import PipelinedRDD

from defoe import query_utils
from defoe.fmp.query_utils import get_article_matches, segment_image

import os


def do_query(archives: PipelinedRDD, config_file=None, logger=None, context=None):
    """
    Crops articles' images for keywords and groups by word.

    config_file must be a yml file that has the following values:
        * preprocess: Treatment to use for preprocessing the words. Options: [normalize|stem|lemmatize|none]
        * data: TXT file with a list of the keywords to search for, one per line.
                This should be in the same path at the configuration file.
        * years_filter: Min and Max years to filter the data. Years are inclusive,
                which means that a max year of 1882 will include papers from that year.
                The two years should be separated using a dash (-).
        * output_path: The path to store the cropped images.

    Returns result of form:

        {
            <WORD>:
                [
                    {
                        "article_id": <ARTICLE ID>,
                        "issue_filename": <ISSUE.ZIP>,
                        "issue_id": <ISSUE ID>
                        "coord": <COORDINATES>,
                        "cropped_image": <IMAGE.JPG>
                        "page_area": <PAGE AREA>,
                        "page_filename": < PAGE FILENAME>,
                        "place": <PLACE>,
                        "textblock_id": <TEXTBLOCK ID>,
                        "title": <TITLER>,
                        "words": <WORDS>,
                        "preprocessed_DATA": <PREPROCESSED DATA>,
                        "year": <YEAR>,
                        "date": <DATE>
                    },
                    ...
                ],
            <WORD>:
                ...
        }

    :param archives: RDD of defoe.fmp.archive.Archive
    :type archives: pyspark.rdd.PipelinedRDD
    :param config_file: query configuration file
    :type config_file: str
    :param logger: logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: information on documents in which keywords occur grouped
    by word
    :rtype: dict
    """

    # Get configuration
    config = query_utils.get_config(config_file)

    # Process configuration
    preprocess_type = query_utils.extract_preprocess_word_type(config)
    data_file = query_utils.extract_data_file(config, os.path.dirname(config_file))
    year_min, year_max = query_utils.extract_years_filter(config)
    output_path = query_utils.extract_output_path(config)
    keywords = query_utils.get_normalized_keywords(data_file, preprocess_type)

    optional_crop = (
        lambda document_article_word: segment_image(
            coords=document_article_word[4],
            page_name=document_article_word[8],
            issue_path=document_article_word[1].archive.filename,
            keyword=document_article_word[9],
            highlight=document_article_word[10],
            logger=logger,
        )
        if output_path != "."
        else None
    )

    # Spark: List all documents in archive, filtered by (year_min, year_max)
    # documents = [document, ...]
    documents = archives.flatMap(
        lambda archive: [
            document
            for document in list(archive)
            if document.year >= int(year_min) and document.year <= int(year_max)
        ]
    )

    # Spark: apply get_article_matches to each document
    # article_matches = [
    #    (year, document, article, textblock_id, textblock_coords, textblock_page_area, words, preprocessed_data, page_name, keyword),
    #       ...
    # ]
    article_matches = documents.flatMap(
        lambda document: get_article_matches(document, keywords, preprocess_type)
    )

    # Spark: re-organize article_matches into matching_docs
    # matching_docs = [
    #   (word, {"article_id": article_id, ...}),
    # ...]
    matching_docs = article_matches.map(
        lambda document_article_word: (
            document_article_word[9],
            {
                "title": document_article_word[1].title,
                "place": document_article_word[1].place,
                "article_id": document_article_word[2],
                "textblock_id": document_article_word[3],
                "coord": document_article_word[4],
                "page_area": document_article_word[5],
                "year": document_article_word[0],
                "words": document_article_word[6],
                "date": document_article_word[1].date,
                "preprocessed_data": document_article_word[7],
                "page_filename": document_article_word[8],
                "issue_id": document_article_word[1].documentId,
                "issue_dirname": document_article_word[1].archive.filename,
                "cropped_image": optional_crop(document_article_word),
            },
        )
    )

    # [(word, {"article_id": article_id, ...}), ...]
    # =>
    # [(word, [{"article_id": article_id, ...], {...}), ...)]
    result = (
        matching_docs.groupByKey()
        .map(lambda word_context: (word_context[0], list(word_context[1])))
        .collect()
    )

    return result
