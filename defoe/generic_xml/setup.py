from defoe.generic_xml.document import Document
from typing import Union, Optional


def filename_to_object(
    filename: str,
) -> tuple[Union[Document, str], Optional[str]]:
    """
    Given a filename create a defoe.generic_xml.document.Document. If
    an error arises during its creation this is caught and returned as
    a string.

    :param filename: Filename
    :type filename: str
    :return: Tuple of form (Document, None) or (filename, error message),
        if there was an error creating Document
    :rtype: tuple(defoe.generic_xml.document.Document | str, str)
    """
    try:
        return (Document(filename), None)
    except Exception as exception:
        return (filename, str(exception))
