"""
Given a filename create a defoe.nzpp.articles.Articles.
"""
from __future__ import annotations

from defoe.nzpp.articles import Articles
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Union, Optional


def filename_to_object(filename) -> tuple[Union[Articles, str], Optional[str]]:
    """
    Given a filename create a defoe.nzpp.articles.Articles. If an
    error arises during its creation this is caught and returned as a
    string.

    :param filename: Filename
    :type filename: str
    :return: Tuple of form (Articles, None) or (filename, error message),
    if there was an error creating Articles
    :rtype: tuple[Union[Articles, str], Optional[str]]
    """
    try:
        result = (Articles(filename), None)
    except Exception as exception:
        result = (filename, str(exception))

    return result
