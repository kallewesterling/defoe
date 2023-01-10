.. _fmp-api:

FMP API
========

Getting started
---------------

Setting up an ALTO object from data from Find My Past can be done by opening an ``Archive``:

.. autoclass:: defoe.fmp.archive.Archive
  :noindex:

To iterate through the elements of the ``Archive``:

.. code-block:: python

    archive = Archive("./path/to/directory/or/zip_file.zip")

    for document in archive:
        for page in document:
            for tb in page.textblocks:
                tb
            for area in page.areas:
                area

FMP API Contents
----------------

.. toctree::
   :maxdepth: 3
   
   archive
   document
   page
   area
   textblock
   alto_archive