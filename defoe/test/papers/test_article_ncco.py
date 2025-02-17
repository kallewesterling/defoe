"""
defoe.papers.article.Article tests for newspapers conforming to
nccoissue.dtd.
"""

from defoe.papers.issue import Issue
from defoe.file_utils import get_path
from defoe.test.papers import fixtures
from defoe.test.papers.test_article import TestArticle


class TestArticleNcco(TestArticle):
    """
    defoe.papers.article.Article tests for newspapers conforming to
    nccoissue.dtd.
    """

    __test__ = True

    def setUp(self):
        """
        Creates Issue from test file fixtures/1912_11_10_ncco.xml then
        retrieves first Article.
        """
        self.filename = get_path(fixtures, "1912_11_10_ncco.xml")
        issue = Issue(self.filename)
        self.article = issue.articles[0]
        self.article_id = "NID123-1912-NOV10-001-001"
        self.page_id = "001"
