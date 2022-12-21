"""
This query filters articles' textblocks by selecting the ones that have one of
the target word(s) AND any the keywords. Later it produces the segmentation/
crop or the filtered textblocks.
"""

from pyspark.rdd import PipelinedRDD

from defoe import query_utils
from defoe.fmp import Document
from defoe.fmp.textblock import TextBlock

from defoe.fmp.query_utils import (
    segment_image,
    preprocess_word,
    PreprocessWordType,
    MatchedWords,
    WordLocation,
)

# from collections import defaultdict
from itertools import product
import os


def get_highlight_coords(
    target_loc: WordLocation, keyword_loc: WordLocation
) -> list:
    """
    Parses out the coordinates for highlights around target words and keywords.
    """

    return [
        (target_loc.x, target_loc.y, target_loc.w, target_loc.h),
        (keyword_loc.x, keyword_loc.y, keyword_loc.w, keyword_loc.h),
    ]


def check_word(word, lst, fuzzy=False) -> bool:
    """
    Fuzzy/non-fuzzy check of word against a list.

    :return: boolean determining whether a word exists in a list
    :rtype: bool
    """

    if not word:
        return False

    if not fuzzy:
        return word in lst

    # TODO: Consider DeezyMatch?
    for target_or_keyword in lst:
        if target_or_keyword in word:
            return True


def get_word_data(
    loc: TextBlock.locations,
    document: Document,
    article_id: str,
    textblock: TextBlock,
) -> WordLocation:
    """
    Combines data from a tb.location object, a Document, its article, and TextBlock.

    :return: a WordLocation object that describes the word's data in-depth.
    :rtype: defoe.fmp.query_utils.WordLocation
    """

    return WordLocation(
        word=loc[4],
        position=loc[5],
        document=document,
        year=document.year,
        article=article_id,
        textblock_id=textblock.id,
        textblock_coords=textblock.coords,
        textblock_page_area=textblock.page_area,
        textblock_page_name=textblock.page_name,
        x=loc[0],
        y=loc[1],
        w=loc[2],
        h=loc[3],
    )


def find_closest(
    document: Document,
    target_words: list,
    keywords: list,
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
    fuzzy_target: bool = False,
    fuzzy_keyword: bool = False,
) -> list:
    """
    Updated query structure (replaces the earlier one, above). This structure allows for
    fuzzy searching, and is faster (?).

    TODO: More docstring needed.
    """

    matches = []

    for article_id, article in document.articles.items():
        for tb in article:
            # Preprocess all words in textblock
            # Result is list of tuples:
            # [
            #   (x, y, w, h, word, position in textblock),
            #   ...
            # ]
            preprocessed_locations = [
                (
                    x[0],
                    x[1],
                    x[2],
                    x[3],
                    preprocess_word(x[4], preprocess_type),
                    position,
                )
                for position, x in enumerate(tb.locations)
            ]

            # Find targets in preprocessed_locations
            found_targets = [
                get_word_data(x, document, article_id, tb)
                for x in preprocessed_locations
                if check_word(x[4], target_words, fuzzy_target)
            ]

            # Find keywords in preprocessed_locations
            found_keywords = [
                get_word_data(x, document, article_id, tb)
                for x in preprocessed_locations
                if check_word(x[4], keywords, fuzzy_keyword)
            ]

            # Pair targets and keywords and add a final count of their difference in position
            found = [
                (x[0], x[1], abs(x[0].position - x[1].position))
                for x in list(product(found_targets, found_keywords))
            ]

            # Sort by the difference in position
            found.sort(key=lambda x: x[2])

            if found:
                # extract from found[0]:
                # target:WordLocation, keyword:WordLocation, distance:int
                target_loc, keyword_loc, distance = found[0]

                # append the closest distance word between target and keyword
                # to matches list
                matches.append(
                    MatchedWords(
                        target_word=target_loc.word,
                        keyword=keyword_loc.word,
                        textblock=target_loc,
                        distance=distance,
                        words=tb.words,
                        preprocessed=preprocessed_locations,
                        highlight=get_highlight_coords(
                            target_loc, keyword_loc
                        ),
                    )
                )

    return matches


def do_query(
    archives: PipelinedRDD, config_file: str = None, logger=None, context=None
):
    """
    Crops articles' images for keywords and groups by word.

    config_file must be a yml file that has the following values:
        * preprocess: Treatment to use for preprocessing the words. Options: [normalize|stem|lemmatize|none]
        * data: YAML file with a list of the target words and a list of keywords to search for.
                This should be in the same path at the configuration file.
        * years_filter: Min and Max years to filter the data. Separated by "-"
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
                        "cropped_image": <IMAGE.JPG>,
                        "page_area": <PAGE AREA>,
                        "page_filename": <PAGE FILENAME>,
                        "place": <PLACE>,
                        "textblock_id": <TEXTBLOCK ID>,
                        "title": <TITLER>,
                        "words": <WORDS>,
                        "preprocessed_words": <PREPROCESSED WORDS>,
                        "year": <YEAR>,
                        "date": <DATE>,
                        "distance": <DISTANCE BETWEEN TARGET AND KEYWORD>,
                        "total_words": <NUMBER OF WORDS IN TEXTBLOCK>
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
    :param logger: logger
    :type logger: py4j.java_gateway.JavaObject
    :return: information on documents in which keywords occur grouped
    by word
    :rtype: dict
    """

    '''
    def log(msg, level):
        """ Wrapper function for logging. """

        if not logger:
            return False

        if level == "info":
            logger.info(msg)

        if level == "warn":
            logger.warn(msg)
    '''

    def parse(input_words):
        if (
            not "targets" in input_words.keys()
            or not "keywords" in input_words.keys()
        ):
            raise RuntimeError(
                f"Your data file ({data_file}) must contain two lists: targets and keywords."
            )
        if (
            not type(input_words.get("targets")) == list
            or not type(input_words.get("keywords")) == list
        ):
            raise RuntimeError(
                f"Your data file ({data_file}) must contain two lists: targets and keywords. At least one of them is currently not a valid YAML list."
            )

        target_words = set(
            [
                preprocess_word(word, preprocess_type)
                for word in input_words["targets"]
            ]
        )

        keywords = set(
            [
                preprocess_word(word, preprocess_type)
                for word in input_words["keywords"]
            ]
        )

        # target_list = ",".join(target_words)
        # kw_list = ",".join(keywords)
        # log(f"Query uses target words (after preprocessing): {target_list}", "info")
        # log(f"Query uses keywords (after preprocessing): {kw_list}", "info")

        return target_words, keywords

    # Setup settings
    config = query_utils.get_config(config_file)
    preprocess_type = query_utils.extract_preprocess_word_type(config)
    data_file = query_utils.extract_data_file(
        config, os.path.dirname(config_file)
    )
    year_min, year_max = query_utils.extract_years_filter(config)
    output_path = query_utils.extract_output_path(config)
    fuzzy_keyword = query_utils.extract_fuzzy(config, "keyword")
    fuzzy_target = query_utils.extract_fuzzy(config, "target")
    target_words, keywords = parse(query_utils.get_config(data_file))

    if output_path == ".":
        # log("Output path is set to `.` -- no images will be generated.", "warn")
        get_highlight = lambda _: []
    else:
        highlight_results = config["highlight"]
        get_highlight = (
            lambda match: match.highlight if highlight_results else []
        )

    optional_crop = (
        lambda match: segment_image(
            coords=match.textblock.textblock_coords,
            page_name=match.textblock.textblock_page_name,
            issue_path=match.textblock.document.archive.filename,
            keyword=match.keyword,
            output_path=output_path,
            target=match.target_word,
            highlight=get_highlight(match),
            logger=logger,
        )
        if output_path != "."
        else None
    )

    # Retrieve documents from each archive
    documents = archives.flatMap(
        lambda arch: [
            doc for doc in arch if int(year_min) <= doc.year <= int(year_max)
        ]
    )

    # log("1/3 Documents retrieved from archive.", "info")

    # find textblocks that contain the closest pair of any given tuple (target word,
    # keyword) and record their distance
    filtered_words = documents.flatMap(
        lambda doc: find_closest(
            doc,
            target_words,
            keywords,
            preprocess_type,
            fuzzy_target,
            fuzzy_keyword,
        )
    )

    # log("2/3 Search query ran.", "info")

    # create the output dictionary
    # mapping from
    #   [MatchedWords(target_word, keyword, textblock_location, distance, words, preprocessed)]
    # to
    #   [(word, {"article_id": article_id, ...}), ...]
    matching_docs = filtered_words.map(
        lambda match: (
            match.keyword,
            {
                "title": match.textblock.document.title,
                "place": match.textblock.document.place,
                "article_id": match.textblock.article,
                "textblock_id": match.textblock.textblock_id,
                "coord": match.textblock.textblock_coords,
                "page_area": match.textblock.textblock_page_area,
                "year": match.textblock.year,
                "date": match.textblock.document.date,
                "page_filename": match.textblock.textblock_page_name,
                "issue_id": match.textblock.document.documentId,
                "issue_dirname": match.textblock.document.archive.filename,
                "target_word": match.target_word,
                "distance": match.distance,
                "cropped_image": optional_crop(match),
            },
        )
    )

    # log("3/3 Output dictionary created.", "info")

    # group by the matched keywords and collect all the articles by keyword
    # [(word, {"article_id": article_id, ...}), ...]
    # =>
    # [(word, [{"article_id": article_id, ...], {...}), ...)]
    # sorted by distance between target and keyword
    result = (
        matching_docs.groupByKey()
        .map(
            lambda word_context: (
                word_context[0],
                sorted(list(word_context[1]), key=lambda d: d["distance"]),
            )
        )
        .collect()
    )

    return result
