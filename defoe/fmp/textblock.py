"""
Object model representation of a textblock represented as an XML file in
METS/MODS format.
"""

from pathlib import Path
import mimetypes

mimetypes.init()


class TextBlock(object):
    """
    Object model representation of a textblock represented as an XML file
    in METS/MODS format.
    """

    # XPath Queries
    STRINGS_XPATH = "TextLine/String"  # String elements
    WC_XPATH = "TextLine/String/@WC"  # Word confidence content
    CC_XPATH = "TextLine/String/@CC"  # Character confidence content
    WORDS_XPATH = "TextLine/String/@CONTENT"  # Word content

    def __init__(self, textblock_tree, document_code, page_code):
        """
        Constructor.
        """
        self.textblock_tree = textblock_tree
        self.textblock_words = None
        self.textblock_strings = None
        self.textblock_images = None
        self.textblock_wc = None
        self.textblock_cc = None
        self.textblock_shape = None
        # Note that the attribute `textblock_coords` is only set when
        # iterating through a Document.articles.
        # TODO: The attribute `textblock_coords` should be set on the object
        # instead.
        self.textblock_coords = None
        self.textblock_page_area = None
        self.textblock_id = self.textblock_tree.get("ID")
        self.page_name = document_code + "_" + page_code + ".xml"
        self.image_name = self.get_image_name(document_code, page_code)

    def get_image_name(self, document_code, page_code):
        image_types = [
            x for x, y in mimetypes.types_map.items() if y.split("/")[0] == "image"
        ]
        test = {
            f"xxx{ext}": Path(f"xxx{ext}").exists()
            for ext in image_types
            if Path(f"xxx{ext}").exists()
        }
        if len(test) == 1:
            key = list(test.keys())[0]
            return key
        elif len(test) > 1:
            raise RuntimeError(
                "Multiple possible images found: " + ", ".join(list(test.keys()))
            )
        else:
            return None

    @property
    def words(self):
        """
        Gets all words in textblock. These are then saved in an attribute,
        so the words are only retrieved once.

        :return: words
        :rtype: list(str)
        """
        if not self.textblock_words:
            self.textblock_words = list(
                map(str, self.textblock_tree.xpath(TextBlock.WORDS_XPATH))
            )
        return self.textblock_words

    @property
    def wc(self):
        """
        Gets all word confidences (wc)  in textblock. These are then saved in
        an attribute, so the wc are only retrieved once.

        :return: wc
        :rtype: list(str)
        """
        if not self.textblock_wc:
            self.textblock_wc = list(self.textblock_tree.xpath(TextBlock.WC_XPATH))
        return self.textblock_wc

    @property
    def cc(self):
        """
        Gets all character confidences (cc)  in textblock. These are then
        saved in an attribute, so the cc are only retrieved once.

        :return: cc
        :rtype: list(str)
        """
        if not self.textblock_cc:
            self.textblock_cc = list(self.textblock_tree.xpath(TextBlock.CC_XPATH))

        return self.textblock_cc

    @property
    def strings(self):
        """
        Gets all strings in textblock. These are then saved in an attribute,
        so the strings are only retrieved once.

        :return: strings
        :rtype: list(lxml.etree._ElementStringResult)
        """
        if not self.textblock_strings:
            self.textblock_strings = self.textblock_tree.xpath(TextBlock.STRINGS_XPATH)
        return self.textblock_strings

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
