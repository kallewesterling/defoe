"""
Helper functions for accessing files within Python modules.
"""

import os
from types import ModuleType
from typing import TextIO


def get_path(module: ModuleType, *name: str) -> str:
    """
    Gets path to file in module, given module and relative path.

    Usage:

    .. code-block:: python

        import spacy
        get_path(spacy, "__init__.py")

    :param module: Any given module
    :type module: module
    :param name: File name components, can be provided as positional arguments
    :type name: str
    :return: Path to file
    :rtype: str
    """
    return os.path.join(os.path.dirname(module.__file__), *name)


def open_file(module: ModuleType, *name: str) -> TextIO:
    """
    Gets path to file in module, given module and relative path,
    and returns open file.

    Usage:

    .. code-block:: python

        import spacy
        open_file(spacy, "__init__.py")

    :param module: Any given module
    :type module: module
    :param name: File name components, can be provided as positional arguments
    :type name: str
    :return: Stream
    :rtype: TextIO
    """
    return open(get_path(module, *name))


def load_content(module: ModuleType, *name: str) -> str:
    """
    Gets path to file in module, given module and relative path, and returns
    the file contents.

    Usage:

    .. code-block:: python

        import spacy
        load_content(spacy, "__init__.py")

    :param module: Any given module
    :type module: module
    :param name: File name components, can be provided as positional arguments
    :type name: str
    :return: file content
    :rtype: str
    """
    with open_file(module, *name) as f:
        result = f.read()

    return result
