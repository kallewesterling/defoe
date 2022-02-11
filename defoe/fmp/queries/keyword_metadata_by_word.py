"""
Gets concordance for keywords and groups by word.
"""

from defoe import query_utils
from defoe.fmp.query_utils import get_article_matches

import yaml
import os


def do_query(archives, config_file=None, logger=None, context=None):
    """
    Gets concordance for keywords and groups by word.

    config_file must be the path to a configuration file with a list
    of the keywords to search for, one per line.

    Both keywords and words in documents are normalized, by removing
    all non-'a-z|A-Z' characters.

    Returns result of form:

        {
          <WORD>:
          [
            { "article_id": <ARTICLE ID>,
              "issue_filename": <ISSUE.ZIP>, 
              "coord": <COORDENATES>, 
              "page_area": <PAGE AREA>,
              "page_filename": < PAGE FILENAME>,
              "place": <PLACE>,
              "textblock_id": <TEXTBLOCK ID>,
              "title": <TITLER>,
              "words": <WORDS>
              "year": <YEAR>,
            },
            ...
          ],
          <WORD>:
          ...
        }

    :param archives: RDD of defoe.fmp.archive.Archive
    :type archives: pyspark.rdd.PipelinedRDD
    :param config_file: query configuration file
    :type config_file: str or unicode
    :param logger: logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: information on documents in which keywords occur grouped
    by word
    :rtype: dict
    """
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    preprocess_type = query_utils.extract_preprocess_word_type(config)
    data_file = query_utils.extract_data_file(config, os.path.dirname(config_file))

    keywords = []
    with open(data_file, "r") as f:
        keywords = [
            query_utils.preprocess_word(word, preprocess_type) for word in list(f)
        ]

    # [document, ...]
    documents = archives.flatMap(
        lambda archive: [document for document in list(archive)]
    )

    filtered_words = documents.flatMap(
        lambda document: get_article_matches(document, keywords, preprocess_type)
    )
    # [(year, document, article, textblock_id, textblock_coords, textblock_page_area, words, page_name, keyword), ....]
    # =>
    # [(word, {"article_id": article_id, ...}), ...]
    matching_docs = filtered_words.map(
        lambda document_article_word: (
            document_article_word[8],
            {
                "title": document_article_word[1].title,
                "place": document_article_word[1].place,
                "article_id": document_article_word[2],
                "textblock_id": document_article_word[3],
                "coord": document_article_word[4],
                "page_area": document_article_word[5],
                "year": document_article_word[0],
                "words": document_article_word[6],
                "page_filename": document_article_word[7],
                "issue_filename": document_article_word[1].archive.filename,
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
