"""
Object model representation of a page represented as an XML file in
METS/MODS format.
"""
from __future__ import annotations

from lxml import etree

from typing import BinaryIO, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .document import Document


class Page(object):
    """
    Object model representation of a page represented as an XML file in
    METS/MODS format.

    :param document: ``Document`` object corresponding to the ``Document``
        to which this ``Page`` belongs
    :type document: defoe.alto.document.Document
    :param code: Identifier for this page within an archive
    :type code: str
    :param source: Stream. If None then an attempt is made to
        open the file holding the page via the given ``Document``
    :type source: zipfile.ZipExt or another file-like object
    """

    def __init__(self, document: Document, code: str, source: BinaryIO = None):
        """
        Constructor method.
        """

        if not source:
            source = document.archive.open_page(document.code, code)
        self.code = code
        self.tree, self.namespaces = self.alto_parse(source)
        self.page_tree = self.alto_page()
        self.width = self.alto_page_width()
        self.height = self.alto_page_height()
        self.pc = self.alto_page_pc()
        self.page_id = self.alto_page_id()
        self.image_nr = self.alto_image_nr()
        self.page_words = None
        self.page_header_left_words = None
        self.page_header_right_words = None
        self.page_hpos_vpos_font_words = None

        self.page_strings = None
        self.page_images = None
        self.page_wc = None
        self.page_cc = None

    def alto_parse(self, source):
        xml = etree.parse(source)
        xmlns = xml.getroot().tag.split("}")[0].strip("{")
        return xml, xmlns

    def alto_page(self) -> Union[int, str]:
        try:
            return self.tree.find("//{%s}Page" % self.namespaces)
        except:  # TODO: Change bare excepts to explicit
            return 0

    def alto_page_width(self) -> Union[int, str]:
        try:
            return int(self.page_tree.attrib.get("WIDTH"))
        except:  # TODO: Change bare excepts to explicit
            return 0

    def alto_page_id(self) -> str:
        try:
            return self.page_tree.attrib.get("ID")
        except:  # TODO: Change bare excepts to explicit
            return "0"

    def alto_image_nr(self) -> str:
        try:
            return self.page_tree.attrib.get("PHYSICAL_IMG_NR")
        except:  # TODO: Change bare excepts to explicit
            return "0"

    def alto_page_height(self) -> Union[int, str]:
        try:
            return int(self.page_tree.attrib.get("HEIGHT"))
        except:  # TODO: Change bare excepts to explicit
            return 0

    def alto_page_pc(self) -> Union[int, str]:
        try:
            return self.page_tree.attrib.get("PC")
        except:  # TODO: Change bare excepts to explicit
            return "0"

    @property
    def words(self) -> list[Optional[str]]:
        if not self.page_words:
            page_words = []
            lines = list(
                self.tree.iterfind(".//{%s}TextLine" % self.namespaces)
            )
            num_lines = len(lines)
            f_line = self.tree.find(".//{%s}TextLine" % self.namespaces)
            if f_line is not None:
                vpos = int(f_line.attrib.get("VPOS"))
                ln = 1
                flag = 1
                while (flag == 1) and (ln < num_lines):
                    current_vpos = int(lines[ln].attrib.get("VPOS"))
                    if current_vpos == vpos:
                        ln += 1
                    else:
                        flag = 0
                if flag == 0:
                    while ln < num_lines:
                        for line in lines[ln].findall(
                            "{%s}String" % self.namespaces
                        ):
                            text = line.attrib.get("CONTENT")
                            page_words.append(text)
                        ln += 1
                    self.page_words = list(map(str, page_words))
                else:
                    self.page_words = []
            else:
                self.page_words = []
        return self.page_words

    @property
    def hpos_vpos_font_words(self) -> list[tuple[str, str, str, str]]:
        if not self.page_hpos_vpos_font_words:
            page_hpos_vpos_font_words = []
            lines = list(
                self.tree.iterfind(".//{%s}TextLine" % self.namespaces)
            )
            num_lines = len(lines)
            f_line = self.tree.find(".//{%s}TextLine" % self.namespaces)
            if f_line is not None:
                vpos = int(f_line.attrib.get("VPOS"))
                ln = 1
                flag = 1
                while (flag == 1) and (ln < num_lines):
                    current_vpos = int(lines[ln].attrib.get("VPOS"))
                    if current_vpos == vpos:
                        ln += 1
                    else:
                        flag = 0
                if flag == 0:
                    while ln < num_lines:
                        line_data = []
                        for ln_word in lines[ln].findall(
                            "{%s}String" % self.namespaces
                        ):
                            vpos = ln_word.attrib.get("VPOS")
                            hpos = ln_word.attrib.get("HPOS")
                            font = ln_word.attrib.get("STYLEREFS")
                            text = ln_word.attrib.get("CONTENT")
                            word_data = [hpos, vpos, font, text]
                            line_data.append(word_data)
                        page_hpos_vpos_font_words.append(line_data)
                        ln += 1
                    self.page_hpos_vpos_font_words = page_hpos_vpos_font_words
                else:
                    self.page_hpos_vpos_font_words = []
            else:
                self.page_hpos_vpos_font_words = []
        return self.page_hpos_vpos_font_words

    @property
    def header_left_words(self) -> list[str]:
        if not self.page_header_left_words:
            page_header_left_words = []
            lines = list(
                self.tree.iterfind(".//{%s}TextLine" % self.namespaces)
            )
            f_line = self.tree.find(".//{%s}TextLine" % self.namespaces)
            if f_line is not None:
                vpos = int(f_line.attrib.get("VPOS"))
                for line in f_line.findall("{%s}String" % self.namespaces):
                    text = line.attrib.get("CONTENT")
                    page_header_left_words.append(text)
                ln = 1
                flag = 1
                num_lines = len(lines)
                while (flag == 1) and (ln < num_lines):
                    current_vpos = int(lines[ln].attrib.get("VPOS"))
                    if (current_vpos == vpos) or (current_vpos < vpos + 5):
                        for line in lines[ln].findall(
                            "{%s}String" % self.namespaces
                        ):
                            text = line.attrib.get("CONTENT")
                            page_header_left_words.append(text)
                        ln += 1
                    else:
                        flag = 0
                self.page_header_left_words = list(
                    map(str, page_header_left_words)
                )
            else:
                self.page_header_left_words = []
        return self.page_header_left_words

    @property
    def header_right_words(self) -> list[str]:
        if not self.page_header_right_words:
            page_header_right_words = []
            lines = list(
                self.tree.iterfind(".//{%s}TextLine" % self.namespaces)
            )
            f_line = self.tree.find(".//{%s}TextLine" % self.namespaces)
            if f_line is not None:
                vpos = int(f_line.attrib.get("VPOS"))
                ln = 1
                flag = 1
                num_lines = len(lines)
                while (flag == 1) and (ln < num_lines):
                    current_vpos = int(lines[ln].attrib.get("VPOS"))
                    if (current_vpos + 5) >= vpos:
                        vpos = current_vpos
                        ln += 1
                    else:
                        flag = 0
                if flag == 0:
                    for line in lines[ln].findall(
                        "{%s}String" % self.namespaces
                    ):
                        text = line.attrib.get("CONTENT")
                        page_header_right_words.append(text)
                    vpos = current_vpos
                    flag = 1
                    ln += 1
                    while (flag == 1) and (ln < num_lines):
                        current_vpos = int(lines[ln].attrib.get("VPOS"))
                        if (current_vpos == vpos) or (current_vpos < vpos + 5):
                            for line in lines[ln].findall(
                                "{%s}String" % self.namespaces
                            ):
                                text = line.attrib.get("CONTENT")
                                page_header_right_words.append(text)
                            ln += 1
                        else:
                            flag = 0
                    self.page_header_right_words = list(
                        map(str, page_header_right_words)
                    )
                else:
                    self.page_header_right_words = []
            else:
                self.page_header_right_words = []
        return self.page_header_right_words

    @property
    def wc(self) -> list[str]:
        if not self.page_wc:
            try:
                for lines in self.tree.iterfind(
                    ".//{%s}TextLine" % self.namespaces
                ):
                    for line in lines.findall("{%s}String" % self.namespaces):
                        text = line.attrib.get("WC")
                        self.page_wc.append(text)
            except:  # TODO: Change bare excepts to explicit
                pass
        return self.page_wc

    @property
    def cc(self) -> list[str]:
        if not self.page_cc:
            try:
                for lines in self.tree.iterfind(
                    ".//{%s}TextLine" % self.namespaces
                ):
                    for line in lines.findall("{%s}String" % self.namespaces):
                        text = line.attrib.get("CC")
                        self.page_cc.append(text)
            except:  # TODO: Change bare excepts to explicit
                pass
        return self.page_cc

    @property
    def strings(self) -> list[str]:
        if not self.page_strings:
            try:
                for lines in self.tree.iterfind(
                    ".//{%s}TextLine" % self.namespaces
                ):
                    for line in lines.findall("{%s}String" % self.namespaces):
                        self.page_strings.append(line)
            except:  # TODO: Change bare excepts to explicit
                pass
        return self.page_strings

    @property
    def images(self) -> list[str]:
        if not self.page_images:
            try:
                for graphical in self.tree.iterfind(
                    ".//{%s}GraphicalElement" % self.namespaces
                ):
                    graphical_id = graphical.attrib.get("ID")
                    graphical_coords = (
                        graphical.attrib.get("HEIGHT")
                        + ","
                        + graphical.attrib.get("WIDTH")
                        + ","
                        + graphical.attrib.get("VPOS")
                        + ","
                        + graphical.attrib.get("HPOS")
                    )
                    graphical_elements = graphical_id + "=" + graphical_coords
                    self.page_images.append(graphical_elements)
            except:  # TODO: Change bare excepts to explicit
                pass
        return self.page_images

    @property
    def content(self) -> str:
        """
        Gets all words in page and contatenates together using ' ' as
        delimiter.
        :return: content
        :rtype: str
        """
        return " ".join(self.words)
