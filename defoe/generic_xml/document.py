"""
Object model representation of an XML document.
"""

from defoe.spark_utils import open_stream

from lxml import etree
from typing import Optional
import os


XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = etree.QName(XSI_NS, "schemaLocation")
NO_NS_SCHEMA_LOCATION = etree.QName(XSI_NS, "noNamespaceSchemaLocation")


class Document(object):
    """
    Object model representation of an XML document.

    :param filename: XML filename
    :type: filename: str
    """

    def __init__(self, filename: str):
        """
        Constructor method.
        """
        self.filename = filename
        self.filesize = os.path.getsize(filename)

        stream = open_stream(self.filename)
        self.document_tree = None
        parser = etree.XMLParser()
        self.document_tree = etree.parse(stream, parser)
        self.root_element = self.document_tree.getroot()
        self.root_element_tag = str(self.root_element.tag)
        self.doc_type = str(self.document_tree.docinfo.doctype)
        self.namespaces = self.root_element.nsmap
        self.schema_locations = self.root_element.get(SCHEMA_LOCATION.text)
        if self.schema_locations is not None:
            self.schema_locations = self.schema_locations.split(" ")
        else:
            self.schema_locations = []
        self.no_ns_schema_location = self.root_element.get(
            NO_NS_SCHEMA_LOCATION.text
        )

    def query(self, query: str) -> list:
        """
        Run XPath query.

        :param query: XPath query
        :type query: str
        :return: List of query results or an empty list if the object
            represents an empty document or any errors arose
        :rtype: list(lxml.etree.<MODULE>) (depends on query)
        """
        if not self.document_tree:
            return []
        try:
            return self.document_tree.xpath(query)
        except AssertionError:
            return []

    def single_query(self, query: str) -> Optional[str]:
        """
        Run XPath query and return first result.

        :param query: XPath query
        :type query: str
        :return: query result or None if the object represents an
            empty document or any errors arose
        :rtype: Optional[str]
        """
        result = self.query(query)
        if not result:
            return None
        return str(result[0])
