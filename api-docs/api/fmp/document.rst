Document
=============

Setting up
-------------

A ``Document`` is most often accessed as part of an :doc:`archive`, i.e. by indexing, slicing or iterating as was documented in the ``Archive`` :ref:`example <archive-setup>`.

If you want to build a ``Document`` object, you need to do something like this:

.. code-block:: python

    archive = Archive("./path/to/directory/or/zip_file.zip")

    # Use a document code (see below *)
    code = "0002247_18621004"

    document = Document(archive=archive, code=code)

\* In the ``code`` variable you will want to save a metadata code from your ``Archive`` :ref:`setup directory <metadata-code>`.

Usage
-------------

While the full documentation of methods and properties on the ``Document`` class is available :ref:`below <document-api-reference>`, in this section, we will cover some common uses of methods and properties in the ``Document`` object.

Searching across a ``Document``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If we want to search across all the text in the ``Document``'s all ``Page`` elements, we could iterate through each ``Page`` and then in the nested ``TextBlock`` to match. But we have a shortcut method on the ``Document`` that can help us do that in one fell swoop:

.. code-block:: python

    archive = Archive("./path/to/directory/or/zip_file.zip")

    # Use a document code (see below *)
    code = "0002247_18621004"

    document = Document(archive=archive, code=code)

    matches = document.match(token="accident")

    print(matches)

This short code block matches the token accident across all the tokens in the ``Document`` and returns a list of matches in descending order for the match ratio. See :func:`~defoe.fmp.document.Document.match` for more information about the method, its available parameters and how it works more broadly.

Second section
^^^^^^^^^^^^^^

TODO

.. _document-api-reference:

API Reference
-------------

.. automodule:: defoe.fmp.document
    :members: