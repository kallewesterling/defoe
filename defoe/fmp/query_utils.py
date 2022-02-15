"""
Query-related utility functions.
"""

from defoe.query_utils import PreprocessWordType, preprocess_word
from defoe.fmp.document import Document
from defoe.fmp.page import Page

from nltk.corpus import words
from PIL import Image

from pathlib import Path
import os


def get_page_matches(
    document: Document, keywords, preprocess_type=PreprocessWordType.NORMALIZE
):
    """
    Get pages within a document that include one or more keywords.
    For each page that includes a specific keyword, add a tuple of
    form:
        (<YEAR>, <DOCUMENT>, <PAGE>, <KEYWORD>)
    If a keyword occurs more than once on a page, there will be only
    one tuple for the page for that keyword.
    If more than one keyword occurs on a page, there will be one tuple
    per keyword.
    :param document: document
    :type document: defoe.fmp.document.Document
    :param keywords: keywords
    :type keywords: list(str or unicode:
    :param preprocess_type: how words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: list of tuples
    :rtype: list(tuple)
    """

    matches = []
    for keyword in keywords:
        for page in document:
            match = None

            for word in page.words:
                preprocessed_word = preprocess_word(word, preprocess_type)

                if preprocessed_word == keyword:
                    match = (document.year, document, page, keyword)
                    break

            if match:
                matches.append(match)
                continue  # move to next page

    return matches


def get_tb_matches(target_match, keywords):
    """
    TODO #3: Incomplete docstring

    (target_match=><YEAR>, <DOCUMENT>, <ARTICLE>, <BLOCK_ID>, <COORDINATES>, <PAGE_AREA>, <ORIGINAL_WORDS>,<PREPROCESSED_WORDS>, <PAGE_NAME>, <TARGETWORD>)

    :param document: target_match
    :type document: list
    :param keywords: keywords
    :type keywords: list(str or unicode:
    :return: list of tuples
    :rtype: list(tuple)
    """

    (
        year,
        document,
        article,
        textblock_id,
        textblock_coords,
        textblock_page_area,
        words,
        tb_preprocessed_words,
        page_name,
        target,
    ) = target_match

    matches = []
    for keyword in keywords:
        match = None

        for preprocessed_word in tb_preprocessed_words:
            if preprocessed_word == keyword:
                match = (
                    year,
                    document,
                    article,
                    textblock_id,
                    textblock_coords,
                    textblock_page_area,
                    words,
                    tb_preprocessed_words,
                    page_name,
                    keyword,
                    target,
                )
                break

        if match:
            # move to next article
            matches.append(match)
            continue

    return matches


def get_article_matches(
    document: Document,
    keywords: list,
    preprocess_type=PreprocessWordType.LEMMATIZE,
    fuzzy=False,
):
    """
    Takes a document and a list of keywords and a type of preprocessing,
    loops through each keyword and looks in each textblock inside each
    article for the first occurring match of the keyword in the textblock.

    If a keyword occurs more than once on a page, there will be only
    one tuple for the page for that keyword.

    If more than one keyword occurs on a page, there will be one tuple
    per keyword.

    Returns a list of tuples of the following format:

        (
            <YEAR>,
            <DOCUMENT>,
            <ARTICLE>,
            <BLOCK_ID>,
            <COORDINATES>,
            <PAGE_AREA>,
            <ORIGINAL_WORDS>,
            <PREPROCESSED_DATA>,
            <PAGE_NAME>,
            <MATCHED_KEYWORD>
        )

    :param document: document
    :type document: defoe.fmp.document.Document
    :param keywords: keywords
    :type keywords: list(str)
    :param preprocess_type: how words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: list of tuples
    :rtype: list(tuple)
    """

    matches = []
    for keyword in keywords:
        processed_keyword = preprocess_word(keyword, preprocess_type)

        for article_id, article in document.articles.items():
            for tb in article:
                preprocessed_data = [
                    (x[0], x[1], x[2], x[3], preprocess_word(x[4], preprocess_type))
                    for x in tb.locations
                ]

                match, highlight = None, None
                for *_, word in preprocessed_data:
                    if fuzzy:
                        matching = (
                            word == keyword
                            or word == processed_keyword
                            or processed_keyword in word
                        )
                    else:
                        matching = word == keyword or word == processed_keyword

                    if matching:
                        if fuzzy:
                            highlight = [
                                (x, y, w, h, word)
                                for x, y, w, h, word in preprocessed_data
                                if word and processed_keyword in word or keyword in word
                            ]
                        else:
                            highlight = [
                                (x, y, w, h, word)
                                for x, y, w, h, word in preprocessed_data
                                if word and processed_keyword == word or keyword == word
                            ]

                        match = (
                            document.year,
                            document,
                            article_id,
                            tb.textblock_id,
                            tb.textblock_coords,
                            tb.textblock_page_area,
                            tb.words,
                            preprocessed_data,
                            tb.page_name,
                            keyword,
                            highlight,
                        )
                        break

                if match:
                    # append and move to next article
                    matches.append(match)
                    continue

    return matches


# TODO #7: This function will accept x, y, width, and height for highlighting
def segment_image(
    coords: str,
    page_name: str,
    issue_path: str,
    keyword: str,
    output_path: str,
    target="",
    highlight=[],
) -> list:
    """
    Segments textblock articles given coordinates and page path

    :param coords: coordinates of an image
    :type coords: string
    :param page_name: name of the page XML which the textblock has been extracted from.
    :type page_name: string
    :param issue_path: path of the ZIPPED archive or the issue
    :type issue_path: string
    :param year: year of the publication
    :type year: integer
    :param keyword: word for which the textblock has been selected/filtered
    :type keyword: string
    :param output_path: path to store the cropped image
    :type output_path: string
    :param target # TODO
    :type target # TODO
    :return: list of images cropped/segmented
    """

    # Get image_in (the image we want to crop)
    if ".zip" in issue_path:
        image_in = os.path.split(issue_path)[0]
    else:
        image_in = issue_path

    image_name = Path(page_name).stem
    image_in = Path(image_in, image_name + ".jp2")

    coords_list = coords.split(",")
    c_set = tuple([int(s) for s in coords_list])

    # Setup image_out (the image we want to save)
    filename = f"crop_{Path(image_in).stem}_"
    coords_name = coords.replace(",", "_")
    if target:
        filename += f"{target}_{keyword}"
    else:
        filename += f"{keyword}"
    filename += f"_{coords_name}.jpg"

    image_out = os.path.join(output_path, filename)

    # Open image (using PIL)
    im = Image.open(image_in)

    # TODO #7: From `improcess`/`crop_images.py`, we get:
    # draw = ImageDraw.Draw(im)
    # for coords in draw_coords:
    #    draw.rectangle(coords, fill=None, outline=colour, width=3)
    print(highlight)

    # Crop image (using PIL)
    crop = im.crop(c_set)

    # TODO #7: This is also where we should adopt the resizing from `improcess`/`crop_images.py`
    # Resize image if >1200px tall:
    # width, height = crop.size
    # if height > max_height:
    #   Calculate aspect ratio
    #   ratio = max_height / height
    #   new_width = int(floor(ratio * width))
    #   new_height = int(floor(ratio * height))
    #   crop = crop.resize((new_width, new_height))

    # Save image (using PIL)
    crop.save(image_out, quality=80, optimize=True)

    return image_out


def get_document_keywords(
    document, keywords, preprocess_type=PreprocessWordType.NORMALIZE
):
    """
    Gets list of keywords occuring within an document.

    :param article: Article
    :type article: defoe.papers.article.Article
    :param keywords: keywords
    :type keywords: list(str or unicode)
    :param preprocess_type: how words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: sorted list of keywords that occur within article
    :rtype: list(str or unicode)
    """

    matches = set()

    for page in document:
        for word in page.words:
            preprocessed_word = preprocess_word(word, preprocess_type)

            if preprocessed_word in keywords:
                matches.add(preprocessed_word)

    return sorted(list(matches))


def document_contains_word(
    document, keyword, preprocess_type=PreprocessWordType.NORMALIZE
):
    """
    Checks if a keyword occurs within an article.

    :param article: Article
    :type article: defoe.papers.article.Article
    :param keywords: keyword
    :type keywords: str or unicode
    :param preprocess_type: how words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: True if the article contains the word, false otherwise
    :rtype: bool
    """

    for page in document:
        for word in page.words:
            preprocessed_word = preprocess_word(word, preprocess_type)

            if keyword == preprocessed_word:
                return True

    return False


def calculate_words_within_dictionary(
    page, preprocess_type=PreprocessWordType.NORMALIZE
):
    """
    Calculates the % of page words within a dictionary and also returns the page quality (pc)
    Page words are normalized.
    :param page: Page
    :type page: defoe.fmp.page.Page
    :param preprocess_type: how words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :return: matches
    :rtype: list(str or unicode)
    """

    dictionary = words.words()

    counter = 0
    total_words = 0

    for word in page.words:
        preprocessed_word = preprocess_word(word, preprocess_type)

        if preprocessed_word != "":
            total_words += 1

            if preprocessed_word in dictionary:
                counter += 1

    try:
        calculate_pc = str(counter * 100 / total_words)
    except:
        calculate_pc = "0"

    return calculate_pc


def calculate_words_confidence_average(page):
    """
    Calculates the average of "words confidence (wc)" within a page.
    Page words are normalized.

    :param page: Page
    :type page: defoe.fmp.page.Page
    :param preprocess_type: how words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :return: matches
    :rtype: list(str or unicode)
    """

    total_wc = 0
    for wc in page.wc:
        total_wc += float(wc)

    try:
        calculate_wc = str(total_wc / len(page.wc))
    except:
        calculate_wc = "0"

    return calculate_wc

