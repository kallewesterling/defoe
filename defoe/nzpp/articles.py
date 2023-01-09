"""
Object model representation of a collection of articles from New Zealand
Papers Past represented as an XML document.
"""

from lxml import etree

from .article import Article
from defoe.spark_utils import open_stream
from typing import Iterator, Optional


class Articles(object):
    """
    Object model representation of a collaction of articles from New Zealand
    Papers Past represented as an XML document.

    :param filename: XML filename
    :type: filename: str
    """

    def __init__(self, filename: str):
        """
        Constructor method.
        """
        self.filename = filename
        stream = open_stream(self.filename)
        parser = etree.XMLParser(recover=True)
        self.xml_tree = etree.parse(stream, parser)
        self.articles = [
            Article(article, self.filename)
            for article in self.query(".//result")
        ]
        self.document_type = "newspaper"
        self.model = "nzpp"

    def query(self, query: etree.XPath) -> list:
        """
        Run XPath query.

        :param query: XPath query
        :type query: lxml.etree.XPath
        :return: List of query results or an empty list if the object
            represents an empty document or any errors arose
        :rtype: list(lxml.etree.<MODULE>) (depends on query)
        """
        if not self.xml_tree:
            return []
        try:
            return self.xml_tree.xpath(query)
        except AssertionError:
            return []

    def single_query(self, query: etree.XPath) -> Optional[str]:
        """
        Run XPath query and return first result.

        :param query: XPath query
        :type query: lxml.etree.XPath
        :return: Query results or None if the object represents an
            empty document
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
        :rtype: defoe.nzpp.article.Article
        """
        return self.articles[index]

    def __iter__(self) -> Iterator[Article]:
        """
        Iterate over articles.

        :return: Article object
        :rtype: defoe.nzpp.article.Article
        """
        for article in self.articles:
            yield article
