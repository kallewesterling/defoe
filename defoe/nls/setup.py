"""
Given a filename create a defoe.books.archive.Archive.
"""
from __future__ import annotations

from defoe.nls.archive import Archive
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Union, Optional


def filename_to_object(
    filename: str,
) -> tuple[Union[Archive, str], Optional[str]]:
    """
    Given a filename create a defoe.books.archive.Archive.  If an error
    arises during its creation this is caught and returned as a
    string.

    :param filename: Filename
    :type filename: str
    :return: Tuple of form (Archive, None) or (filename, error message),
        if there was an error creating Archive
    :rtype: tuple[Union[Archive, str], Optional[str]]
    """
    try:
        result = (Archive(filename), None)
    except Exception as exception:
        result = (filename, str(exception))

    return result
