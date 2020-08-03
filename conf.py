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
sys.path.append(os.path.abspath("./_ext"))


# -- Project information -----------------------------------------------------

project = 'Test'
copyright = '2020, John Doe'
author = 'John Doe'

numfig = True

# Debug
keep_warnings = True
nitpicky = True

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'exercices',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

latex_engine = "xelatex"
latex_use_xindy = False
pygments_style = "colorful"
latex_elements = {
    'inputenc': '',
    'utf8extra': '',
    'preamble': r'''

\usepackage{fontspec}
\setmonofont{DejaVu Sans Mono}

\usepackage{colortbl}
\usepackage{etoolbox}
\usepackage{xcolor,graphicx}
\usepackage[xparse,skins,breakable]{tcolorbox}

\newtcolorbox{hint}{breakable,enhanced,arc=0mm,colback=lightgray!5,colframe=lightgray,leftrule=11mm,%
height from=1.3cm to 16cm,%
overlay={\node[anchor=north west,outer sep=1mm] at (frame.north west) {
    \includegraphics[width=2em]{../../icons/hint.pdf}}; }}

\newtcolorbox{code}{breakable,enhanced,arc=0mm,colback=lightgray!5,colframe=lightgray}

\renewenvironment{sphinxnote}[1]
    {\begin{hint}{#1}}
    {\end{hint}}
''',
}

