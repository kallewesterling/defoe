"""
Query-related utility functions.
"""
from __future__ import annotations

from defoe.query_utils import PreprocessWordType, preprocess_word

from collections import namedtuple
from math import floor
from nltk.corpus import words
from pathlib import Path
from PIL import Image, ImageDraw, ImageColor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .document import Document
    from .page import Page
    from logging import Logger
    from typing import Optional

import os


WordLocation = namedtuple(
    "WordLocation",
    (
        "word "
        "position "
        "year "
        "document "
        "article "
        "textblock_id "
        "textblock_coords "
        "textblock_page_area "
        "textblock_page_name "
        "x "
        "y "
        "w "
        "h"
    ),
)

MatchedWords = namedtuple(
    "MatchedWords",
    "target_word keyword textblock distance words preprocessed highlight",
)


def convert_coords(
    x: int, y: int, w: int, h: int
) -> list[tuple[int, int], tuple[int, int]]:
    """
    Takes starting x, y coordinates (upper-left corner) and a width and height,
    and returns the correct format for PIL to draw a rectangle.

    :param x: X value in pixels for left side of rectangle
    :type x: int
    :param y: Y value in pixels for left side of rectangle
    :type y: int
    :param w: Rectangle's width in pixels
    :type w: int
    :param h: Rectangle's height in pixels
    :type h: int
    :return: List of two tuples with coordinates of the rectangle's two
        opposite corners: (1) upper-left, (2) lower-right
    :rtype: list[tuple[int, int], tuple[int, int]]
    """
    x0 = x
    y0 = y
    x1 = x + w
    y1 = y + h

    return [(x0, y0), (x1, y1)]


def get_page_matches(
    document: Document,
    keywords: list[str],
    preprocess_type: PreprocessWordType = PreprocessWordType.NORMALIZE,
) -> list[tuple[int, Document, Page, str]]:
    """
    Get pages within a document that include one or more keywords.

    For each page that includes a specific keyword, add a tuple of form:
    ``(<YEAR>, <DOCUMENT>, <PAGE>, <KEYWORD>)``

    If a keyword occurs more than once on a page, there will be only
    one tuple for the page for that keyword.

    If more than one keyword occurs on a page, there will be one tuple
    per keyword.

    :param document: Document
    :type document: defoe.fmp.document.Document
    :param keywords: Keywords
    :type keywords: list[str]
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: List of tuples
    :rtype: list[tuple[int, Document, Page, str]]
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


def get_tb_matches(
    target_match: tuple[
        int,
        Document,
        str,
        str,
        Optional[list[int, int, int, int]],
        str,
        list,
        list,
        str,
        str,
    ],
    keywords: list[str],
) -> list[
    tuple[
        int,
        Document,
        str,
        str,
        Optional[list[int, int, int, int]],
        str,
        list,
        list,
        str,
        str,
    ]
]:
    """
    Takes a complex target_match and filters its preprocessed words according
    to whether they appear in a provided list of keywords.

    :param target_match: A given target match
    :type target_match: tuple[int, Document, str, str, Optional[list[int, int,
        int, int]], str, list, list, str, str]
    :param keywords: Keywords
    :type keywords: list[str]
    :return: List of tuples
    :rtype: list[tuple[int, Document, str, str, Optional[list[int, int, int,
        int]], str, list, list, str, str]]
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
    keywords: list[str],
    preprocess_type: PreprocessWordType = PreprocessWordType.LEMMATIZE,
    fuzzy: bool = False,
) -> list[
    tuple[
        int,
        Document,
        str,
        str,
        Optional[list[int, int, int, int]],
        str,
        list,
        list,
        str,
        str,
        Optional[list[int, int, int, int, str]],
    ]
]:
    """
    Takes a document and a list of keywords and a type of preprocessing, loops
    through each keyword and looks in each textblock inside each article for
    the first occurring match of the keyword in the textblock.

    If a keyword occurs more than once on a page, there will be only one tuple
    for the page for that keyword.

    If more than one keyword occurs on a page, there will be one tuple per
    keyword.

    Returns a list of tuples of the following format: (``<YEAR>``,
    ``<DOCUMENT>``, ``<ARTICLE>``, ``<BLOCK_ID>``, ``<COORDINATES>``,
    ``<PAGE_AREA>``, ``<ORIGINAL_WORDS>``, ``<PREPROCESSED_DATA>``,
    ``<PAGE_NAME>``, ``<MATCHED_KEYWORD>``)

    :param document: Document
    :type document: defoe.fmp.document.Document
    :param keywords: Keywords
    :type keywords: list[str]
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: List of tuples of the following format: (``<YEAR>``,
        ``<DOCUMENT>``, ``<ARTICLE>``, ``<BLOCK_ID>``, ``<COORDINATES>``,
        ``<PAGE_AREA>``, ``<ORIGINAL_WORDS>``, ``<PREPROCESSED_DATA>``,
        ``<PAGE_NAME>``, ``<MATCHED_KEYWORD>``)
    :rtype: list[tuple[int, Document, str, str, Optional[list[int, int, int,
        int]], str, list, list, str, str, Optional[list[int, int, int, int,
        str]]]]
    """

    matches = []
    for keyword in keywords:
        processed_keyword = preprocess_word(keyword, preprocess_type)

        for article_id, textblocks in document.articles.items():
            for tb in textblocks:
                preprocessed_data = [
                    (
                        x[0],
                        x[1],
                        x[2],
                        x[3],
                        preprocess_word(x[4], preprocess_type),
                    )
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
                                if word
                                and processed_keyword in word
                                or keyword in word
                            ]
                        else:
                            highlight = [
                                (x, y, w, h, word)
                                for x, y, w, h, word in preprocessed_data
                                if word
                                and processed_keyword == word
                                or keyword == word
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
    target: Optional[str] = "",
    highlight: Optional[list[Optional[tuple[int, int, int, int]]]] = [],
    highlight_frame: str = "#C02F1D",
    highlight_frame_width: int = 2,
    highlight_tint: str = "#FFFF00",
    highlight_tint_transparency: float = 0.25,
    max_height: Optional[int] = 0,
    limit_size: int = 950000,
    overwrite_existing: bool = False,
    logger: Logger = None,
) -> str:
    """
    Segments textblock articles given coordinates and page path

    :param coords: Coordinates of an image
    :type coords: str
    :param page_name: Name of the page XML which the textblock has been
        extracted from.
    :type page_name: str
    :param issue_path: Path of the ZIPPED archive or the issue
    :type issue_path: str
    :param year: Year of the publication
    :type year: integer
    :param keyword: Word for which the textblock has been selected/filtered
    :type keyword: str
    :param output_path: Path to store the cropped image
    :type output_path: str
    :param target: Target keyword, will be added to final result file
    :type target: str, optional
    :param highlight: List of tuples, consisting of x-axis pixel value, y-axis
        pixel value, width in pixels, height in pixels, i.e. ``(x, y, w, h)``,
        optional
    :type highlight: Optional[list[Optional[tuple[int, int, int, int]]]]
    :param highlight_frame: Highlight box frame's tint (hex), defaults to
        ``"#C02F1D"``
    :type highlight_frame: str
    :param highlight_frame_width: Highlight box frame's width (pixels),
        defaults to ``2``
    :type highlight_frame_width: int
    :param highlight_tint: Highlight box's tint (hex), defaults to
        ``"#FFFF00"``
    :type highlight_tint: str
    :param highlight_tint_transparency: Degree of transparency, percent as
        floating point value between 0.0 and 1.0, defaults to ``0.25``
    :type highlight_tint_transparency: float
    :param max_height: Max height of resulting image (pixels)
    :type max_height: int, optional
    :param limit_size: File size limit (bytes), defaults to ``950000``
    :type limit_size: int
    :param logger: Optional logger
    :type: logging.Logger
    :return: The path of the cropped/segmented image
    :rtype: str
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

    def check_size(path):
        """Return the size of a file in a given path"""
        return os.stat(path).st_size

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
        x, y, w, h, *_ = points
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

    # Resize image if max_height is set up:
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
    if check_size(image_out) > limit_size:
        crop.save(image_out, quality=50, optimize=True)

    if check_size(image_out) > limit_size:
        # Temporary solution to #11 (TODO: refactor this whole part of file size check + resizing)
        width, height = crop.size
        if height > 2000:
            # Calculate aspect ratio
            ratio = 2000 / height
            new_width = int(floor(ratio * width))
            new_height = int(floor(ratio * height))
            crop = crop.resize((new_width, new_height))
        crop.save(image_out, quality=40, optimize=True)

    if check_size(image_out) > limit_size:
        crop.save(image_out, quality=30, optimize=True)

    if check_size(image_out) > limit_size:
        crop.save(image_out, quality=20, optimize=True)

    # TODO: This should be a while loop (with a lower limit) attempting to save
    if check_size(image_out) > limit_size:
        # TODO: This should probably be a logging thing also
        print(f"Warning: File {image_out} still too large.")

    if logger:
        logger.info(f"File saved: {image_out}")

    return image_out


def get_document_keywords(
    document: Document,
    keywords: list[str],
    preprocess_type: PreprocessWordType = PreprocessWordType.NORMALIZE,
) -> list[str]:
    """
    Gets list of keywords occuring within an document.

    :param document: Document
    :type document: defoe.fmp.document.Document
    :param keywords: Keywords
    :type keywords: list[str]
    :param preprocess_type: How words should be preprocessed
    (normalize, normalize and stem, normalize and lemmatize, none)
    :type preprocess_type: defoe.query_utils.PreprocessWordType
    :return: Sorted list of keywords that occur within document
    :rtype: list[str]
    """

    matches = set()

    for page in document:
        for word in page.words:
            preprocessed_word = preprocess_word(word, preprocess_type)

            if preprocessed_word in keywords:
                matches.add(preprocessed_word)

    return sorted(list(matches))


def document_contains_word(
    document: Document,
    keyword: str,
    preprocess_type: PreprocessWordType = PreprocessWordType.NORMALIZE,
) -> bool:
    """
    Checks if a keyword occurs within an document.

    :param document: Document
    :type document: defoe.fmp.document.Document
    :param keyword: Keyword
    :type keyword: str
    :param preprocess_type: How words should be preprocessed
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
    page: Page,
    preprocess_type: PreprocessWordType = PreprocessWordType.NORMALIZE,
) -> str:
    """
    Calculates the % of a given page's words within a dictionary (see
    ``nltk.corpus.words``). Page words are normalized.

    :param page: Page
    :type page: defoe.fmp.page.Page
    :param preprocess_type: How words should be preprocessed
        (normalize, normalize and stem, normalize and lemmatize, none)
    :return: Percent of a given page's words that appear within a dictionary
    :rtype: str
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
    except TypeError:
        calculate_pc = "0"

    return calculate_pc


def calculate_words_confidence_average(page: Page) -> str:
    """
    Calculates the average of a given ``defoe.fmp.page.Page``'s word
    confidence.

    :param page: Page
    :type page: defoe.fmp.page.Page
    :return: The word confidence average of a given ``defoe.fmp.page.Page`` as
        string
    :rtype: str
    """

    total_wc = 0
    for wc in page.wc:
        total_wc += float(wc)

    try:
        calculate_wc = str(total_wc / len(page.wc))
    except TypeError:
        calculate_wc = "0"

    return calculate_wc
