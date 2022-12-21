"""
Object model representation of a textblock represented as an XML file in METS/
MODS format.
"""

from PIL import ImageOps
from defoe.query_utils import (
    normalize,
    normalize_including_numbers,
    lemmatize,
    stem as stem_word,
)
from thefuzz import fuzz
from typing import Union

import re

from .constants import FUZZ_METHOD, MIN_RATIO


class TextBlock(object):
    """
    Object model representation of a textblock represented as an XML file in
    METS/MODS format.
    """

    # XPath Queries
    STRINGS_XPATH = "TextLine/String"  # String elements
    WC_XPATH = "TextLine/String/@WC"  # Word confidence content
    CC_XPATH = "TextLine/String/@CC"  # Character confidence content
    WORDS_XPATH = "TextLine/String/@CONTENT"  # Word content

    def __init__(self, textblock_tree, page):
        """
        Constructor.
        """
        self.tree = textblock_tree
        self.document_code = page.document.code
        self.page_code = page.code
        self.document = page.document
        self.page = page
        self.page_name = self.document_code + "_" + self.page_code + ".xml"

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

    def get_tokens_bbox(self):
        """
        Returns the "real" bounding box for the tokens' x and y values.
        """
        xs = [x[0] for x in self.tokens] + [x[0] + x[2] for x in self.tokens]
        ys = [x[1] for x in self.tokens] + [x[1] + x[3] for x in self.tokens]

        if not xs or not ys:
            # fallback: return the full page. TODO: Print warning?
            return [0, 0, self.page.width, self.page.height]

        return min(xs), min(ys), max(xs), max(ys)

    @property
    def tokens_bbox(self):
        if not self._tokens_bbox:
            self._tokens_bbox = self.get_tokens_bbox()
        return self._tokens_bbox

    @property
    def image(self):
        """
        Gets the image for the text block. This is then saved in an attribute,
        so the image is only retrieved once.

        :return: page image
        :rtype: PIL.Image.Image
        """
        if not self._image:
            self._image = self.page.image.copy()
            self._image = self._image.crop(self.tokens_bbox)

        return self._image

    @property
    def words(self):
        """
        Gets all words in textblock. These are then saved in an attribute,
        so the words are only retrieved once.

        :return: words
        :rtype: list(str)
        """
        if not self._words:
            self._words = list(
                map(str, self.tree.xpath(TextBlock.WORDS_XPATH))
            )
        return self._words

    @property
    def word_confidences(self):
        """
        Gets all word confidences (wc)  in textblock. These are then saved in
        an attribute, so the wc are only retrieved once.

        :return: wc
        :rtype: list(str)
        """
        if not self._word_confidences:
            self._word_confidences = list(self.tree.xpath(TextBlock.WC_XPATH))

        # Attempt to set word confidence to floating point
        try:
            self._word_confidences = [float(x) for x in self._word_confidences]
        except ValueError:
            pass

        return self._word_confidences

    @property
    def character_confidences(self):
        """
        Gets all character confidences (cc)  in textblock. These are then
        saved in an attribute, so the cc are only retrieved once.

        :return: cc
        :rtype: list(str)
        """
        if not self._character_confidences:
            self._character_confidences = list(
                self.tree.xpath(TextBlock.CC_XPATH)
            )

        # Attempt to set word confidence to floating point
        try:
            self._character_confidences = [
                float(x) for x in self._character_confidences
            ]
        except ValueError:
            pass

        return self._character_confidences

    @property
    def strings(self):
        """
        Gets all strings in textblock. These are then saved in an attribute,
        so the strings are only retrieved once.

        :return: strings
        :rtype: list(lxml.etree._ElementStringResult)
        """
        try:
            self._strings
        except AttributeError:
            self._strings = None

        if not self._strings:
            self._strings = self.tree.xpath(TextBlock.STRINGS_XPATH)
        return self._strings

    @property
    def content(self):
        """
        Gets all words in textblock and concatenates together using ' ' as
        delimiter.

        :return: content
        :rtype: str
        """
        return " ".join(self.words)

    @property
    def tokens(self):
        """
        Gets all strings in textblock and returns them as a list of tuples:
            [
                (x, y, width, height, content)
            ]
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

    def highlight(self, highlight=[], max_width=0, max_height=0):
        """
        Shortcut function to add highlight to a TextBlock
        # TODO: Add functionality to just pass a token index list?
        """
        image = self.page.highlight(image=self.page.image, highlight=highlight)

        cropped = image.crop(self.tokens_bbox)

        if max_width and max_height:
            return self.get_resized_image(
                max_width=max_width, max_height=max_height, image=cropped
            )

        return cropped

    def get_resized_image(
        self, max_width: int = 500, max_height: int = 500, image=None
    ):
        """
        Shortcut function that returns a resized image constrained by a
        maximum width and a maximum height.
        """
        if not image:
            image = self.image

        return ImageOps.contain(image, (max_width, max_height))

    def get_article_id(self):
        """Attempts to get article ID in parent document for the TextBlock"""
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

    def process_tokens(
        self, normalise=True, include_numbers=True, lemmatise=True, stem=True
    ):
        tokens = self.tokens.copy()

        if normalise and include_numbers:
            tokens = [
                (x, y, w, h, normalize(token)) for x, y, w, h, token in tokens
            ]
        elif normalise and not include_numbers:
            tokens = [
                (x, y, w, h, normalize_including_numbers(token))
                for x, y, w, h, token in tokens
            ]

        if lemmatise:
            tokens = [
                (x, y, w, h, lemmatize(token)) for x, y, w, h, token in tokens
            ]

        if stem:
            tokens = [
                (x, y, w, h, stem_word(token)) for x, y, w, h, token in tokens
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
    ):
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

        tokens = self.process_tokens(
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
