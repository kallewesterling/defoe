FMP ``Archive``
===============

Setting up FMP ``Archive``
--------------------------

.. _metadata-code:

Setting up an FMP archive presumes the presence of a ZIP file or a directory of files in METS/ALTO format compliant with Find My Past's newspapers. The ZIP file or the directory should contain any ALTO files (following the naming convention ``<METADATA_CODE>_<FILE_CODE>.xml`` where ``<METADATA_CODE>`` is ``[0-9]*?_[0-9]*?`` and ``<FILE_CODE>`` is ``[0-9_]*``) and any METS files that address those ALTO files (following the naming convention ``<METADATA_CODE>_mets.xml`` with ``METADATA_CODE`` following the same regular expression as previously mentioned).

Once you have the directory or ZIP file set up, you can initialise an ``Archive`` object like this:

.. code-block:: python

    archive = Archive("./path/to/directory/or/zip_file.zip")

An ``Archive`` can contain one or multiple ``Document`` objects, depending on how many METS files are present in the directory or ZIP file that you pass as an argument to the constructor.

The ``Archive`` object (which inherits from the abstract class :class:`defoe.fmp.archive_combine.AltoArchive`) can be interated and sliced, in order to access the ``Document`` objects nested in the ``Archive``:

.. _archive-setup:

.. code-block:: python

    archive = Archive("./path/to/directory/or/zip_file.zip")

    first_document = archive[0]

    # Note that this will raise an ``IndexError`` if there are not two documents present in the ``Archive``
    second_document = archive[1]

    # Iterate throught the documents
    for document in archive:
        print(document.code)

To read more about available properties and methods for the ``Document``, see :class:`defoe.fmp.document.Document`.

FMP ``Archive`` API Reference
-----------------------------
.. automodule:: defoe.fmp.archive
    :members:
