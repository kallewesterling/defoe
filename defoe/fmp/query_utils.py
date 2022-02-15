"""
Query-related utility functions.
"""

from defoe.query_utils import PreprocessWordType, preprocess_word
from defoe.fmp.document import Document
from defoe.fmp import Page

from nltk.corpus import words
from PIL import Image, ImageDraw, ImageColor

from pathlib import Path
from math import floor
import os


def convert_coords(x, y, w, h):
    """
    Takes starting x, y coordinates (upper-left corner) and a width and height,
    and returns the correct format for PIL to draw a rectangle.

    :param x: x value in pixels for left side of rectangle
    :type x: int
    :param y: y value in pixels for left side of rectangle
    :type y: int
    :param w: rectangle's width in pixels
    :type w: int
    :param h: rectangle's height in pixels
    :type h: int
    :return: list of two tuples with coordinates of the rectangle's two
    opposite corners: (1) upper-left, (2) lower-right
    :rtype: list(tuple)
    """
    x0 = x
    y0 = y
    x1 = x + w
    y1 = y + h

    return [(x0, y0), (x1, y1)]


def get_page_matches(
    document: Document, keywords: list, preprocess_type=PreprocessWordType.NORMALIZE
):
    """
    Get pages within a document that include one or more keywords.
    For each page that includes a specific keyword, add a tuple of form:
        (<YEAR>, <DOCUMENT>, <PAGE>, <KEYWORD>)

    If a keyword occurs more than once on a page, there will be only
    one tuple for the page for that keyword.

    If more than one keyword occurs on a page, there will be one tuple
    per keyword.

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


def segment_image(
    coords: str,
    page_name: str,
    issue_path: str,
    keyword: str,
    output_path: str,
    target: str = "",
    highlight: list = [],
    highlight_frame: str = "#C02F1D",  # highlight box frame's tint (hex)
    highlight_frame_width: int = 2,  # highlight box frame's width (pixels)
    highlight_tint: str = "#FFFF00",  # highlight box's tint (hex)
    highlight_tint_transparency: float = 0.25,  # Degree of transparency, 0-1 (percent)
    max_height: int = 1200,  # max height of resulting image (pixels)
    limit_size: int = 950000,  # File size limit (bytes)
    overwrite_existing: bool = False,
) -> str:
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
    :param target: # TODO #3
    :type target: # TODO #3
    :param highlight: # TODO #3
    :type highlight: # TODO #3
    :param highlight_frame: # TODO #3
    :type highlight_frame: # TODO #3
    :param highlight_frame_width: # TODO #3
    :type highlight_frame_width: # TODO #3
    :param highlight_tint: # TODO #3
    :type highlight_tint: # TODO #3
    :param highlight_tint_transparency: # TODO #3
    :type highlight_tint_transparency: # TODO #3
    :param max_height: # TODO #3
    :type max_height: # TODO #3
    :param limit_size: # TODO #3
    :type limit_size: # TODO #3
    :return: the path of the cropped/segmented image
    """

    def get_image_name(issue_path, page_name):
        """Get image_in (the image we want to crop)"""
        if ".zip" in issue_path:
            image_in = os.path.split(issue_path)[0]
        else:
            image_in = issue_path

        image_name = Path(page_name).stem
        image_in = Path(image_in, image_name + ".jp2")

        return image_in

    def get_image_out(image_in, coords, target, keyword):
        """Setup image_out (the image we want to save)"""
        filename = f"crop_{Path(image_in).stem}_"
        coords_name = coords.replace(",", "_")
        if target:
            filename += f"{target}_{keyword}"
        else:
            filename += f"{keyword}"
        filename += f"_{coords_name}.jpg"

        return os.path.join(output_path, filename)

    image_in = get_image_name(issue_path, page_name)
    image_out = get_image_out(image_in, coords, target, keyword)

    if os.path.exists(image_out) and overwrite_existing:
        # Exit early, without any file operations - to save time
        return image_out

    # Open image (using PIL)
    im = Image.open(image_in)
    im = im.convert("RGBA")

    # Set up our drawing
    highlight_frame = ImageColor.getrgb(highlight_frame)
    TINT_COLOR = ImageColor.getrgb(highlight_tint)
    OPACITY = int(255 * highlight_tint_transparency)
    overlay = Image.new("RGBA", im.size, TINT_COLOR + (0,))
    draw = ImageDraw.Draw(overlay)

    for points in highlight:
        x, y, w, h, _ = points
        draw.rectangle(
            convert_coords(x, y, w, h),
            fill=TINT_COLOR + (OPACITY,),
            outline=highlight_frame,
            width=highlight_frame_width,
        )

    im = Image.alpha_composite(im, overlay)
    im = im.convert("RGB")  # Remove alpha for saving in jpg format.

    # Set up our cropping
    coords_list = coords.split(",")
    c_set = tuple([int(s) for s in coords_list])

    # Crop image (using PIL)
    crop = im.crop(c_set)

    # Resize image if >1200px tall:
    if max_height:
        width, height = crop.size
        if height > max_height:
            # Calculate aspect ratio
            ratio = max_height / height
            new_width = int(floor(ratio * width))
            new_height = int(floor(ratio * height))
            crop = crop.resize((new_width, new_height))

    # Save image (using PIL)
    crop.save(image_out, quality=80, optimize=True)

    # Limit file size to 1MB
    check_size = lambda path: os.stat(path).st_size

    if check_size(image_out) > limit_size:
        crop.save(image_out, quality=50, optimize=True)

    # TODO: This should be a while loop (with a lower limit) attempting to save
    if check_size(image_out) > limit_size:
        print(f"Warning: File {image_out} still too large.")

    return image_out


def get_document_keywords(
    document: Document, keywords: list, preprocess_type=PreprocessWordType.NORMALIZE
):
    """
    Gets list of keywords occuring within an document.

    :param document: Document
    :type document: defoe.fmp.document.Document
    :param keywords: keywords
    :type keywords: list(str)
    :param preprocess_type: how words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: sorted list of keywords that occur within document
    :rtype: list(str)
    """

    matches = set()

    for page in document:
        for word in page.words:
            preprocessed_word = preprocess_word(word, preprocess_type)

            if preprocessed_word in keywords:
                matches.add(preprocessed_word)

    return sorted(list(matches))


def document_contains_word(
    document: Document, keyword: str, preprocess_type=PreprocessWordType.NORMALIZE
):
    """
    Checks if a keyword occurs within an document.

    :param document: Document
    :type document: defoe.fmp.document.Document
    :param keyword: keyword
    :type keyword: str
    :param preprocess_type: how words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: True if the document contains the word, false otherwise
    :rtype: bool
    """

    for page in document:
        for word in page.words:
            preprocessed_word = preprocess_word(word, preprocess_type)

            if keyword == preprocessed_word:
                return True

    return False


def calculate_words_within_dictionary(
    page: Page, preprocess_type=PreprocessWordType.NORMALIZE
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


def calculate_words_confidence_average(page: Page):
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
