"""
This query filters articles' textblocks by selecting the ones that have one of
the target word(s) AND any the keywords. Later it produces the segmentation/
crop or the filtered textblocks.
"""

from pyspark.rdd import PipelinedRDD

from defoe import query_utils
from defoe.fmp import Document
from defoe.fmp.query_utils import (
    segment_image,
    preprocess_word,
    PreprocessWordType,
    MatchedWords,
    WordLocation,
)

from collections import defaultdict
import os


# compute_distance provides the absolute distance between `position` attributes of two WordLocation objects
compute_distance = lambda k_loc, t_loc: abs(k_loc.position - t_loc.position)


def get_min_distance_to_target(keyword_locations: list, target_locations: list):
    """
    # TODO #3: add missing docstring
    """

    # TODO: I have a feeling this could be refactored with `functools.reduce`
    min_distance, target_loc, keyword_loc = None, None, None
    for k_loc in keyword_locations:
        for t_loc in target_locations:
            word_distance = compute_distance(k_loc, t_loc)

            if not min_distance or word_distance < min_distance:
                min_distance = word_distance
                target_loc = t_loc
                keyword_loc = k_loc

    return min_distance, target_loc, keyword_loc


get_highlight_coords = lambda target_loc, keyword_loc: [
    (target_loc.x, target_loc.y, target_loc.w, target_loc.h),
    (keyword_loc.x, keyword_loc.y, keyword_loc.w, keyword_loc.h),
]


def find_words_in_document(
    document: Document,
    target_words: list,
    keywords: list,
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
):
    """
    If a keyword occurs more than once on a page, there will be only
    one tuple for the page for that keyword.

    If more than one keyword occurs on a page, there will be one tuple
    per keyword.

    The distance between keyword and target word is recorded in the output tuple.

    :param document: document
    :type document: defoe.fmp.document.Document
    :param target_words: # TODO #3
    :type target_words: # TODO #3
    :param keywords: keywords
    :type keywords: list(str)
    :param preprocess_type: how words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: list of tuples
    :rtype: list(tuple)
    """

    matches = []
    for article_id, article in document.articles.items():
        for tb in article:
            preprocessed_data = [
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

            keywords_matched = defaultdict(lambda: [])
            targetwords_matched = []
            for x, y, w, h, word, position in preprocessed_data:
                loc = WordLocation(
                    word=word,
                    position=position,
                    year=document.year,
                    document=document,
                    article=article_id,
                    textblock_id=tb.textblock_id,
                    textblock_coords=tb.textblock_coords,
                    textblock_page_area=tb.textblock_page_area,
                    textblock_page_name=tb.page_name,
                    x=x,
                    y=y,
                    w=w,
                    h=h,
                )

                # TODO: Only absolute match. We may want to consider fuzzy matching here as well
                if word != "" and word in keywords:
                    keywords_matched[word].append(loc)

                if word != "" and word in target_words:
                    targetwords_matched.append(loc)

            for locations in keywords_matched.values():
                min_distance, target_loc, keyword_loc = get_min_distance_to_target(
                    locations, targetwords_matched
                )

                if min_distance:
                    matches.append(
                        MatchedWords(
                            target_word=target_loc.word,
                            keyword=keyword_loc.word,
                            textblock=target_loc,
                            distance=min_distance,
                            words=tb.words,
                            preprocessed=preprocessed_data,
                            highlight=get_highlight_coords(target_loc, keyword_loc),
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
    :param logger: logger (unused)
    :type logger: py4j.java_gateway.JavaObject
    :return: information on documents in which keywords occur grouped
    by word
    :rtype: dict
    """

    def parse(input_words):
        if not "targets" in input_words.keys() or not "keywords" in input_words.keys():
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
            [preprocess_word(word, preprocess_type) for word in input_words["targets"]]
        )

        keywords = set(
            [preprocess_word(word, preprocess_type) for word in input_words["keywords"]]
        )

        if logger:
            target_list = ",".join(target_words)
            kw_list = ",".join(keywords)
            logger.info(f"Query uses target words (after preprocessing): {target_list}")
            logger.info(f"Query uses keywords (after preprocessing): {kw_list}")

        return target_words, keywords

    # Setup settings
    config = query_utils.get_config(config_file)
    preprocess_type = query_utils.extract_preprocess_word_type(config)
    data_file = query_utils.extract_data_file(config, os.path.dirname(config_file))
    year_min, year_max = query_utils.extract_years_filter(config)
    output_path = query_utils.extract_output_path(config)
    target_words, keywords = parse(query_utils.get_config(data_file))

    if output_path == ".":
        if logger:
            logger.warn("Output path is set to `.` -- no images will be generated.")
        get_highlight = lambda _: []
    else:
        highlight_results = config["highlight"]
        get_highlight = lambda match: match.highlight if highlight_results else []

    optional_crop = (
        lambda match: segment_image(
            coords=match.textblock.textblock_coords,
            page_name=match.textblock.textblock_page_name,
            issue_path=match.textblock.document.archive.filename,
            keyword=match.keyword,
            output_path=output_path,
            target=match.target_word,
            highlight=get_highlight(match),
        )
        if output_path != "."
        else None
    )

    # Retrieve documents from each archive
    documents = archives.flatMap(
        lambda arch: [doc for doc in arch if int(year_min) <= doc.year <= int(year_max)]
    )

    # find textblocks that contain pairs of (target word, keyword) and record their distance
    filtered_words = documents.flatMap(
        lambda doc: find_words_in_document(doc, target_words, keywords, preprocess_type)
    )

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
