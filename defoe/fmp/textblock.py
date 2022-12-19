"""
Object model representation of a textblock represented as an XML file in METS/
MODS format.
"""

from PIL import ImageOps


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

    def __init__(
        self, textblock_tree, document_code, page_code, document, page
    ):
        """
        Constructor.
        """
        self.tree = textblock_tree
        self.document_code = document_code
        self.page_code = page_code
        self.document = document
        self.page = page

        self.textblock_shape = None  # this is set by defoe.fmp.document
        # Note that the attribute `textblock_coords` is only set when
        # iterating through a Document.articles.
        # TODO: The attribute `textblock_coords` should be set on the object
        # instead.
        self.textblock_coords = None  # this is set by defoe.fmp.document
        self.textblock_page_area = None
        self.id = self.tree.get("ID")
        self.page_name = document_code + "_" + page_code + ".xml"

        self._locations_bbox = self.get_locations_bbox()
        self.x = self._locations_bbox[0]
        self.y = self._locations_bbox[1]
        self.width = self._locations_bbox[2] - self._locations_bbox[0]
        self.height = self._locations_bbox[3] - self._locations_bbox[1]

        # See property accessors below
        self._words = None
        self._strings = None
        self.textblock_images = None
        self._wc = None
        self._cc = None
        self._image = None

        # Adding backward compatibility
        self.textblock_id = self.id
        self.textblock_words = self.words
        self.textblock_strings = self.strings
        self.textblock_wc = self.wc
        self.textblock_cc = self.cc
        self.image_name = self.page.get_image_name()

    def get_locations_bbox(self):
        xs = [x[0] for x in self.locations] + [
            x[0] + x[2] for x in self.locations
        ]
        ys = [x[1] for x in self.locations] + [
            x[1] + x[3] for x in self.locations
        ]

        if not xs or not ys:
            # fallback: return the full page. TODO: Print warning?
            return [0, 0, self.page.width, self.page.height]

        return min(xs), min(ys), max(xs), max(ys)

    @property
    def locations_bbox(self):
        if not self._locations_bbox:
            self._locations_bbox = self.get_locations_bbox()
        return self._locations_bbox

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
            self._image = self._image.crop(self.locations_bbox)

        return self._image

    def highlight(self, highlight=[], max_width=0, max_height=0):
        image = self.page.highlight(image=self.page.image, highlight=highlight)

        cropped = image.crop(self.locations_bbox)

        if max_width and max_height:
            return self.get_resized_image(
                max_width=max_width, max_height=max_height, image=cropped
            )

        return cropped

    def get_resized_image(
        self, max_width: int = 500, max_height: int = 500, image=None
    ):
        if not image:
            image = self.image

        return ImageOps.contain(image, (max_width, max_height))

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
    def wc(self):
        """
        Gets all word confidences (wc)  in textblock. These are then saved in
        an attribute, so the wc are only retrieved once.

        :return: wc
        :rtype: list(str)
        """
        if not self._wc:
            self._wc = list(self.tree.xpath(TextBlock.WC_XPATH))
        return self._wc

    @property
    def cc(self):
        """
        Gets all character confidences (cc)  in textblock. These are then
        saved in an attribute, so the cc are only retrieved once.

        :return: cc
        :rtype: list(str)
        """
        if not self._cc:
            self._cc = list(self.tree.xpath(TextBlock.CC_XPATH))

        return self._cc

    @property
    def strings(self):
        """
        Gets all strings in textblock. These are then saved in an attribute,
        so the strings are only retrieved once.

        :return: strings
        :rtype: list(lxml.etree._ElementStringResult)
        """
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
    def locations(self):
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
