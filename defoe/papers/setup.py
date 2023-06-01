"""
Given a filename create a defoe.papers.issue.Issue.
"""
from __future__ import annotations

from defoe.papers.issue import Issue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Union, Optional


def filename_to_object(filename) -> tuple[Union[Issue, str], Optional[str]]:
    """
    Given a filename create a defoe.papers.issue.Issue.  If an error
    arises during its creation this is caught and returned as a
    string.

    :param filename: Filename
    :type filename: str
    :return: Tuple of form (Issue, None) or (filename, error message),
    if there was an error creating Issue
    :rtype: tuple[Union[Issue, str], Optional[str]]
    """
    try:
        result = (Issue(filename), None)
    except Exception as exception:
        result = (filename, str(exception))

    return result
