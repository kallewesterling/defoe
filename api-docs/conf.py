import sphinx_rtd_theme

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------

project = "Defoe"
copyright = "2022, Rosa Filgueira, Kalle Westerling"
author = "Rosa Filgueira, Kalle Westerling"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.autodoc",
    "sphinx_copybutton",
    "sphinx.ext.intersphinx",
    "hoverxref.extension",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"

html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "lxml": ("https://lxml.de/apidoc", None),
    # TODO: Can we link to SpaCy's docs?
    # "spacy": ("https://spacy.io/", None),
}

# List of zero or more Sphinx-specific warning categories to be squelched (i.e.,
# suppressed, ignored).
suppress_warnings = [
    # FIXME: *THIS IS TERRIBLE.* Generally speaking, we do want Sphinx to
    # inform us about cross-referencing failures. Remove this hack entirely
    # after Sphinx resolves this open issue:
    #    https://github.com/sphinx-doc/sphinx/issues/4961
    # Squelch mostly ignorable warnings resembling:
    #     WARNING: more than one target found for cross-reference 'Archive':
    #     defoe.books.archive.Archive, defoe.fmp.archive.Archive,
    #     defoe.nls.archive.Archive, defoe.nlsArticles.archive.Archive
    #
    # Sphinx currently emits many of these warnings against our documentation.
    # All of these warnings appear to be ignorable. Although we could
    # explicitly squelch *SOME* of these warnings by canonicalizing relative
    # to absolute references in docstrings, Sphinx emits still others of these
    # warnings when parsing PEP-compliant type hints via static analysis.
    # Since those hints are actual hints that *CANNOT* by definition be
    # canonicalized, our only recourse is to squelch warnings altogether.
    "ref.python",
]
