from defoe.books.archive import Archive
from typing import Union, Optional


def filename_to_object(
    filename: str,
) -> tuple[Union[Archive, str], Optional[str]]:
    """
    Given a filename, creates a defoe.books.archive.Archive.  If an error
    arises during its creation this is caught and returned as a string.

    :param filename: filename
    :type filename: str
    :return: tuple of form (Archive, None) or (filename, error message),
        if there was an error creating Archive
    :rtype: tuple(defoe.books.archive.Archive | str, str)
    """
    try:
        return (Archive(filename), None)
    except Exception as exception:
        return (filename, str(exception))
