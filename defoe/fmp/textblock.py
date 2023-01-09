"""
Object model representation of a textblock represented as an XML file in
METS/MODS format.
"""

from __future__ import annotations

from .constants import FUZZ_METHOD, MIN_RATIO

from defoe import query_utils
from PIL import ImageOps, Image
from spellchecker import SpellChecker
from thefuzz import fuzz
from typing import TYPE_CHECKING

import re

if TYPE_CHECKING:
    from .page import Page
    from lxml import etree
    from typing import Optional, Union


class TextBlock(object):
    """
    Object model representation of a textblock represented as an XML file in
    METS/MODS format.

    Usage:

    .. code-block:: python

        from defoe.fmp.archive import Archive

        archive = Archive("path/to/xml-files/")

        # See documentation for defoe.fmp.document.Document here:
        document = archive[0]

        # See documentation for defoe.fmp.page.Page here:
        page = document[0]

        # Iterate through an archive's document's page's textblocks
        for textblock in page.textblocks:
            # Access the properties and methods from the TextBlock
            print(textblock.tokens)

    :param textblock_tree: The XML element that contains the
        ``defoe.fmp.textblock.TextBlock``
    :type textblock_tree: lxml.etree._Element
    :param page: The parent ``defoe.fmp.page.Page`` which contains the
        ``defoe.fmp.textblock.TextBlock``
    :type page: defoe.fmp.page.Page
    """

    # XPath Queries
    STRINGS_XPATH = "TextLine/String"  # String elements
    WC_XPATH = "TextLine/String/@WC"  # Word confidence content
    CC_XPATH = "TextLine/String/@CC"  # Character confidence content
    WORDS_XPATH = "TextLine/String/@CONTENT"  # Word content

    def __init__(self, textblock_tree, page: Page):
        """
        Constructor method.
        """

        self.tree = textblock_tree
        self.document_code = page.document.code
        self.page_code = page.code
        self.document = page.document
        self.page = page
        self.page_name = f"{self.document_code}_{self.page_code}.xml"

        self.id = self.tree.get("ID")

        self.shape = None
        self.coords = None
        self.page_area = None

        # Try to set `self.shape`, `self.coords`, `self.page_area`
        area = [area for area in self.page.areas if area.id == self.id]
        if len(area) > 1:
            raise RuntimeError(
                f"TextBlock {self.id} looks like it belongs to multiple areas:\n \
                ({','.join([x.id for x in area])})"  # noqa
            )
        if len(area) == 1:
            area = area[0]
            self.shape = area.type
            self.coords = area.coords
            self.page_area = area.page_part

        self._tokens_bbox = self.get_tokens_bbox()
        self.x, self.y, x1, y1 = self._tokens_bbox
        self.width = x1 - self.x
        self.height = y1 - self.y

        # See property accessors below
        self._words = None
        self._strings = None
        self.textblock_images = None
        self._word_confidences = None
        self._character_confidences = None
        self._image = None

        # Adding backward compatibility
        self.textblock_id = self.id
        self.textblock_words = self.words
        self.textblock_strings = self.strings
        self.textblock_wc = self.word_confidences
        self.textblock_cc = self.character_confidences
        self.textblock_shape = self.shape
        self.textblock_coords = self.coords
        self.textblock_page_area = self.page_area
        self.image_name = self.page.get_image_name()
        self.locations = self.tokens
        self.get_locations_bbox = self.get_tokens_bbox
        self.locations_bbox = self.tokens_bbox
        self.cc = self.character_confidences
        self.wc = self.word_confidences
        self._cc = self._character_confidences
        self._wc = self._word_confidences

    def get_tokens_bbox(self) -> tuple[int, int, int, int]:
        """
        Returns the "real" bounding box for the tokens' x and y values.

        :return: The "real" bounding box for the tokens' x and y values.
        :rtype: tuple
        """
        xs = [x[0] for x in self.tokens] + [x[0] + x[2] for x in self.tokens]
        ys = [x[1] for x in self.tokens] + [x[1] + x[3] for x in self.tokens]

        if not xs or not ys:
            # fallback: return the full page.
            # TODO: Print warning?
            return [0, 0, self.page.width, self.page.height]

        return min(xs), min(ys), max(xs), max(ys)

    @property
    def tokens_bbox(self) -> tuple[int, int, int, int]:
        """
        Property that returns the value of ``get_tokens_bbox``. This value is
        saved in an attribute, so the image is only retrieved once.

        :return: The "real" bounding box for the tokens' x and y values.
        :rtype: tuple
        """
        if not self._tokens_bbox:
            self._tokens_bbox = self.get_tokens_bbox()
        return self._tokens_bbox

    @property
    def image(self) -> Image.Image:
        """
        Returns the image for the TextBlock. This is saved in an attribute,
        so the image is only retrieved once.

        :return: The ``defoe.fmp.page.Page``'s image, cropped to the
            coordinates of the ``defoe.fmp.textblock.TextBlock``
        :rtype: PIL.Image.Image
        """
        if not self._image:
            self._image = self.page.image.copy()
            self._image = self._image.crop(self.tokens_bbox)

        return self._image

    @property
    def words(self) -> list[str]:
        """
        Returns all the words in the TextBlock. These are saved in an
        attribute, so the words are only retrieved once.

        :return: The ``defoe.fmp.textblock.TextBlock``'s words
        :rtype: list[str]
        """
        if not self._words:
            self._words = list(
                map(str, self.tree.xpath(TextBlock.WORDS_XPATH))
            )
        return self._words

    @property
    def word_confidences(self) -> list[Optional[Union[float, str]]]:
        """
        Returns all word confidences in the TextBlock. These are saved in
        an attribute, so the word confidences are only retrieved once.

        The function will try to make all the list's elements into floating
        point values but if it fails, the list will contain the original,
        unconvertable, string values.

        :return: A list containing the ``defoe.fmp.textblock.TextBlock``'s
            word confidences, or an empty list if there are no word
            confidences in the ``defoe.fmp.textblock.TextBlock``.
        :rtype: list[Optional[Union[float, str]]]
        """
        if not self._word_confidences:
            self._word_confidences = list(self.tree.xpath(TextBlock.WC_XPATH))

        # Attempt to set word confidence to floating point
        try:
            self._word_confidences = [
                float(x) for x in self._word_confidences if x
            ]
        except ValueError:
            pass

        return self._word_confidences

    @property
    def character_confidences(self) -> list[Optional[Union[float, str]]]:
        """
        Returns all character confidences in the the TextBlock. These are
        saved in an attribute, so the character confidences are only retrieved
        once.

        The function will try to make all the list's elements into floating
        point values but if it fails, the list will contain the original,
        unconvertable, string values.

        :return: A list containing the ``defoe.fmp.textblock.TextBlock``'s
            character confidences, or an empty list if there are no character
            confidences in the ``defoe.fmp.textblock.TextBlock``.
        :rtype: list[Optional[Union[float, str]]]
        """
        if not self._character_confidences:
            self._character_confidences = list(
                self.tree.xpath(TextBlock.CC_XPATH)
            )

        # Attempt to set word confidence to floating point
        try:
            self._character_confidences = [
                float(x) for x in self._character_confidences if x
            ]
        except ValueError:
            pass

        return self._character_confidences

    @property
    def strings(self) -> list[etree._ElementStringResult]:
        """
        Returns all strings in the TextBlock. These are then saved in an
        attribute, so the strings are only retrieved once.

        :return: The ``defoe.fmp.textblock.TextBlock``'s strings
        :rtype: list[lxml.etree._ElementStringResult]
        """
        try:
            self._strings
        except AttributeError:
            self._strings = None

        if not self._strings:
            self._strings = self.tree.xpath(TextBlock.STRINGS_XPATH)
        return self._strings

    @property
    def content(self) -> str:
        """
        Returns all words in the TextBlock, concatenated using ' ' as
        delimiter.

        :return: The ``defoe.fmp.textblock.TextBlock``'s content
        :rtype: str
        """
        return " ".join(self.words)

    @property
    def spellchecked_content(self) -> str:
        """
        Returns all words in the TextBlock, concatenated using ' ' as
        delimiter, followed by a spell checker using a Levenshtein Distance
        algorithm to find permutations within an edit distance of 2 from the
        original word.

        :return: The ``defoe.fmp.textblock.TextBlock``'s content, spellchecked
        :rtype: str
        """

        spell = SpellChecker()

        words = [(ix, spell[word]) for ix, word in enumerate(self.words)]
        suggestion = [
            (word[0], spell.correction(self.words[word[0]]))
            for word in words
            if word[1] == 0
        ]
        suggestion = [x for x in suggestion if x[1]]

        words = []
        for ix, word in enumerate(self.words):
            yes_suggestion = [x for x in suggestion if x[0] == ix]
            if len(yes_suggestion) == 1:
                words.append(yes_suggestion[0][1])
            else:
                words.append(word)

        return " ".join(words)

    @property
    def tokens(self) -> list[tuple[int, int, int, int, str]]:
        """
        Returns all tokens in the TextBlock and returns them as a list of
        tuples: ``[(x, y, width, height, content)]``.

        :return: The ``defoe.fmp.textblock.TextBlock``'s tokens as list of
            tuples
        :rtype: list[tuple[int, int, int, int, str]]
        """
        attribs = [string.attrib for string in self.strings]
        return [
            (
                int(x["HPOS"]),
                int(x["VPOS"]),
                int(x["WIDTH"]),
                int(x["HEIGHT"]),
                x["CONTENT"],
            )
            for x in attribs
        ]

    def highlight(
        self, highlight=[], max_width=500, max_height=500
    ) -> Image.Image:
        """
        Shortcut function to add highlight to a TextBlock

        :param highlight: A list of all the rectangles in need of highlight.
            The list should contain 4-, 5-, or 6-tuples with
            ``[(x0, y0, x1, y1)]`` as the minimum required tuple information.
            The remaining two positions can include an RGB value for the fill
            colour, and a floating point value between 0 and 1 for opacity:
            ``[(x0, y0, x1, y1, (255, 255, 255))]`` or
            ``[(x0, y0, x1, y1, (255, 255, 255), 0.4)]``
        :type highlight: list[tuple]
        :param max_width: Maximum pixel width for resulting image, defaults to
            500
        :type max_width: int, optional
        :param max_height: Maximum pixel height for resulting image, defaults
            to 500
        :type max_height: int, optional
        :return: Resized and highlighted image constrained by a maximum width
            and a maximum height
        :rtype: PIL.Image.Image
        """

        # TODO: Add functionality to just pass a token index list?

        image = self.page.highlight(image=self.page.image, highlight=highlight)

        cropped = image.crop(self.tokens_bbox)

        if max_width and max_height:
            return self.get_resized_image(
                max_width=max_width, max_height=max_height, image=cropped
            )

        return cropped

    def get_resized_image(
        self, max_width: int = 500, max_height: int = 500, image=None
    ) -> Image.Image:
        """
        Shortcut function that returns a resized image constrained by a
        maximum width and a maximum height.

        :param max_width: Maximum pixel width for resulting image, defaults to
            500
        :type max_width: int, optional
        :param max_height: Maximum pixel height for resulting image, defaults
            to 500
        :type max_height: int, optional
        :return: Resized image constrained by a maximum number of pixels wide
            and high.
        :rtype: PIL.Image.Image
        """
        if not image:
            image = self.image

        return ImageOps.contain(image, (max_width, max_height))

    def get_article_id(self) -> str:
        """
        Returns the article ID from the ``defoe.fmp.textblock.TextBlock``'s
        parent ``defoe.fmp.document.Document``.

        :raises RuntimeError: If the article ID cannot be reconstructed, a
            RuntimeError will be raised.
        :return: The ``defoe.fmp.textblock.TextBlock``'s article ID
        :rtype: str
        """
        test = [
            id
            for id, textblock_ids in self.document.articlesParts.items()
            if self.id in textblock_ids
        ]

        if len(test) == 1:
            return test[0]

        raise RuntimeError(
            "Article ID for TextBlock could not be reconstructed:\n- "
            + "\n- ".join(test)
        )

    def _process_tokens(
        self, normalise=True, include_numbers=True, lemmatise=True, stem=True
    ) -> list[int, int, int, int, str]:
        tokens = self.tokens.copy()

        if normalise and include_numbers:
            tokens = [
                (x, y, w, h, query_utils.normalize(token))
                for x, y, w, h, token in tokens
            ]
        elif normalise and not include_numbers:
            tokens = [
                (x, y, w, h, query_utils.normalize_including_numbers(token))
                for x, y, w, h, token in tokens
            ]

        if lemmatise:
            tokens = [
                (x, y, w, h, query_utils.lemmatize(token))
                for x, y, w, h, token in tokens
            ]

        if stem:
            tokens = [
                (x, y, w, h, query_utils.stem(token))
                for x, y, w, h, token in tokens
            ]

        return tokens

    def match(
        self,
        token: Union[str, list] = [],
        normalise: bool = True,
        include_numbers: bool = True,
        lemmatise: bool = True,
        stem: bool = True,
        fuzz_method: str = FUZZ_METHOD,
        min_ratio: float = MIN_RATIO,
        all_results: bool = False,
        sort_results: bool = True,
        sort_reverse: bool = True,
        add_textblock: bool = False,
        regex: bool = False,
    ) -> list[tuple, int, int, int, int, str, int]:
        """
        Matches any given token(s) in the TextBlock.

        :param token: Either a string representation of a token to match or a
            list of string representation of tokens to match
        :type token: Union[str, list]
        :param normalise: Boolean determining whether to match tokens on
            lowercase and no numbers (unless ``include_numbers`` is set to
            ``True``)
        :type normalise: bool, optional
        :param include_numbers: Boolean determining whether to match tokens on
            numbers included (only affects the outcome if ``normalise`` is set
            to ``True``)
        :type include_numbers: bool, optional
        :param lemmatise: Boolean determining whether tokens should be
            lemmatised before matching
        :type lemmatise: bool, optional
        :param stem: Boolean determining whether tokens should be stemmed
            before matching
        :type stem: bool, optional
        :param fuzz_method: String determining which fuzzy matching method
            should be used; can be set to ``partial_ratio``, ``ratio``,
            ``token_sort_ratio`` or ``token_set_ratio``
        :type fuzz_method: str, optional
        :param min_ratio: Minimum ratio required to return a match
        :type min_ratio: float, optional
        :param all_results: Boolean determining whether the returning value
            should include all the matches, regardless of ``min_ratio``
        :type all_results: bool, optional
        :param sort_results: Boolean determining whether the returned values
            should be sorted by the match's ratio (ascending)
        :type sort_results: bool, optional
        :param sort_reverse: Boolean determining whether the sorting done by
            ``sort_results`` above should be in descending order instead of
            ascending. Thus, only affects the result if ``sort_results`` is
            set to ``True``
        :type sort_reverse: bool, optional
        :param add_textblock: Boolean determining whether the TextBlock itself
            should be returned in the resulting list
        :type add_textblock: bool, optional
        :param regex: Boolean determining wheter the token string(s) provided
            should be interpreted as regular expressions or not
        :type regex: bool, optional

        :return: A list of tuples including where to find the matched token,
            its index in the list of tokens in the TextBlock, its x, y, width,
            and height values, the token itself, and the match ratio as a
            value between 0 and 100
        :rtype: list[tuple]
        """

        if isinstance(token, str):
            match_words = [token]
        elif isinstance(token, list) and all(
            [isinstance(x, str) for x in token]
        ):
            match_words = list(set(token))
        else:
            raise SyntaxError("Token must be a string or list of strings.")

        nav = (
            self.page.document.archive.filename,
            self.page.document.code,
            self.page.code,
            self.id,
        )

        if add_textblock:
            nav += (self,)

        tokens = self._process_tokens(
            normalise=normalise,
            include_numbers=include_numbers,
            lemmatise=lemmatise,
            stem=stem,
        )

        tokens = [
            (nav, ix, x[0], x[1], x[2], x[3], x[4])
            for ix, x in enumerate(tokens)
        ]

        if regex:
            matches = []

            for match_word in match_words:
                g = re.compile(match_word, flags=re.IGNORECASE)
                matches += [
                    (
                        nav,
                        ix,
                        x,
                        y,
                        w,
                        h,
                        token,
                        100 if g.search(token) else 0
                        # g.match(token, match_word)
                    )
                    for nav, ix, x, y, w, h, token in tokens
                ]
        else:
            if fuzz_method == "partial_ratio":
                fuzz_func = fuzz.partial_ratio
            elif fuzz_method == "ratio":
                fuzz_func = fuzz.ratio
            elif fuzz_method == "token_sort_ratio":
                fuzz_func = fuzz.token_sort_ratio
            elif fuzz_method == "token_set_ratio":
                fuzz_func = fuzz.token_set_ratio
            else:
                raise SyntaxError(
                    f"Unknown fuzz method provided: {fuzz_method}"
                )

            matches = []

            for match_word in match_words:
                matches += [
                    (
                        nav,
                        ix,
                        x,
                        y,
                        w,
                        h,
                        token,
                        fuzz_func(token, match_word),
                    )
                    for nav, ix, x, y, w, h, token in tokens
                ]

        if all_results:
            if not sort_results:
                # we want all results, unsorted
                return matches
            # we want all results, sorted
            if regex:
                return sorted(matches)

            return sorted(matches, key=lambda x: x[7], reverse=sort_reverse)

        # let's match at a certain ratio
        if regex:
            matches = [x for x in matches if x[7]]
        else:
            matches = [x for x in matches if x[7] >= min_ratio]

        if not sort_results:
            return matches

        # we want sorted matches
        if regex:
            return sorted(matches)

        return sorted(matches, key=lambda x: x[7], reverse=sort_reverse)
