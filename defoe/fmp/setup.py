"""
Given a filename create a defoe.fmp.archive.Archive.
"""

from defoe.fmp.archive import Archive


def filename_to_object(filename):
    """
    Given a filename create a defoe.fmp.archive.Archive.  If an error
    arises during its creation this is caught and returned as a
    string.

    :param filename: Filename
    :type filename: str
    :return: tuple of form (Archive, None) or (filename, error message),
    if there was an error creating Archive
    :rtype: tuple(defoe.fmp.archive.Archive | str, str)
    """
    try:
        result = (Archive(filename), None)
    except Exception as exception:
        result = (filename, str(exception))

    return result
