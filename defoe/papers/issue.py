"""
Object model representation of an issue of a newspaper represented as
an XML document.

The XML document can conform to the following schemas:

* British Library Newspapers
* Times Digital Archive

Or newspapers conforming to the following DTDs:

* bl_ncnp_issue_apex.dtd
* GALENP.dtd
* nccoissue.dtd
* LTO_issue.md
"""

from __future__ import annotations

from datetime import datetime
from lxml import etree
from defoe.papers.article import Article
from defoe.spark_utils import open_stream
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator, Optional


class Issue(object):
    """
    Object model representation of an issue of a newspaper represented
    as an XML document.

    :param filename: XML filename. If the filename cannot be parsed into valid
        XML an empty document is created.
    :type: filename: str
    :raises Exception: Raises an Exception if the XML does not have an
        ``issue`` element.
    """

    def __init__(self, filename):
        """
        Constructor method.
        """
        self.filename = filename
        stream = open_stream(self.filename)

        self.issue_tree = None
        self.issue = ""
        self.newspaper_id = ""
        self.articles = []
        self.date = datetime.now()
        self.page_count = 0
        self.day_of_week = ""
        self.document_type = "newspaper"
        self.model = "papers"
        # Attempt to parse the file, even if its XML is invalid e.g:
        # <wd ...>.../wd>
        parser = etree.XMLParser(recover=True)
        self.issue_tree = etree.parse(stream, parser)

        has_issue = len(self.query("..//issue")) > 0
        if not has_issue:
            raise Exception("Missing 'issue' element")

        self.issue = self.single_query(".//issue")

        # bl_ncnp_issue_apex.dtd, GALENP.dtd, nccoissue.dtd
        newspaper_id = self.single_query("//issue/id/text()")
        if newspaper_id is None:
            # LTO_issue.md
            newspaper_id = self.single_query(
                "//issue/metadatainfo/PSMID/text()"
            )
        if newspaper_id is not None:
            self.newspaper_id = newspaper_id

        self.articles = [
            Article(article, self.filename)
            for article in self.query(".//article")
        ]

        # bl_ncnp_issue_apex.dtd, GALENP.dtd, LTO_issue.dtd
        raw_date = self.single_query("//pf/text()")
        if raw_date is None:
            # nccoissue.dtd
            raw_date = self.single_query("//da/searchableDateStart/text()")
        if raw_date:
            self.date = datetime.strptime(raw_date, "%Y%m%d")
        else:
            self.date = None

        try:
            self.page_count = int(self.single_query("//ip/text()"))
        except Exception:
            pass

    def query(self, query: etree.XPath) -> list:
        """
        Run XPath query.

        :param query: XPath query
        :type query: lxml.etree.XPath
        :return: list of query results or an empty list if the object
            represents an empty document
        :rtype: list(lxml.etree.<MODULE>) (depends on query)
        """
        if not self.issue_tree:
            return []
        try:
            return self.issue_tree.xpath(query)
        except AssertionError:
            return []

    def single_query(self, query: etree.XPath) -> Optional[str]:
        """
        Run XPath query and return first result.

        :param query: XPath query
        :type query: lxml.etree.XPath
        :return: Query results or None if the object represents an empty
            document
        :rtype: str
        """
        result = self.query(query)
        if not result:
            return None
        return str(result[0])

    def __getitem__(self, index: int) -> Article:
        """
        Given an article index, return the requested article.

        :param index: Article index
        :type index: int
        :return: Article object
        :rtype: defoe.papers.article.Article
        """
        return self.articles[index]

    def __iter__(self) -> Iterator[Article]:
        """
        Iterate over articles.

        :return: Article object
        :rtype: Iterator[defoe.papers.article.Article]
        """
        for article in self.articles:
            yield article
