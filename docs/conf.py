# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from __future__ import annotations

import importlib
import inspect
import os
import sys

from aio_ld2410 import version as release

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
project = 'aio-ld2410'
copyright = '2024, Romain Bezut'
author = 'Romain Bezut'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.linkcode',
    'sphinx.ext.napoleon',
    'sphinx_copybutton',
    'sphinx_inline_tabs',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Extensions configuration ------------------------------------------------
# Nitpick configuration
nitpicky = True
nitpick_ignore = [
    # See https://github.com/sphinx-doc/sphinx/issues/12867
    ('py:class', '_io.BytesIO'),
    ('py:class', 'construct.lib.containers.Container'),
]

# Napoleon settings
napoleon_google_docstring = True
napoleon_use_admonition_for_notes = True

# Autodoc
autodoc_default_options = {
    'show-inheritance': True,
    'member-order': 'bysource',
    'exclude-members': '__new__,__init__',
}
autodoc_class_signature = 'separated'
autoclass_content = 'class'

# Sphinx autodoc typehints
always_use_bars_union = True
typehints_defaults = 'comma'
typehints_use_signature = True
typehints_use_signature_return = True

# InterSphinx
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'construct': ('https://construct.readthedocs.io/en/latest', None),
}

code_url = f'https://github.com/morian/aio-ld2410/blob/v{release}'


def linkcode_resolve(domain, info):
    """Create a link to the mentioned source code."""
    if domain != 'py':
        return None

    mod = importlib.import_module(info['module'])
    if '.' in info['fullname']:
        objname, attrname = info['fullname'].split('.')
        obj = getattr(mod, objname)
        try:
            # object is a method of a class
            obj = getattr(obj, attrname)
        except AttributeError:
            # object is an attribute of a class
            return None
    else:
        obj = getattr(mod, info['fullname'])

    try:
        file = inspect.getsourcefile(obj)
        lines = inspect.getsourcelines(obj)
    except TypeError:
        # e.g. object is a typing.Union
        return None

    file = os.path.relpath(file, os.path.abspath('..'))
    if not file.startswith('aio_ld2410/'):
        # e.g. object is a typing.NewType
        return None
    start, end = lines[1], lines[1] + len(lines[0]) - 1

    return f'{code_url}/{file}#L{start}-L{end}'


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'

html_theme_options = {
    'source_repository': 'https://github.com/morian/aio-ld2410/',
    'source_branch': 'master',
    'source_directory': 'docs/',
    'light_css_variables': {
        'color-brand-primary': '#306998',  # blue from logo
        'color-brand-content': '#0b487a',  # blue more saturated and less dark
    },
    'dark_css_variables': {
        'color-brand-primary': '#ffd43bcc',  # yellow from logo, more muted than content
        'color-brand-content': '#ffd43bd9',  # yellow from logo, transparent like text
    },
    'sidebar_hide_name': True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_css_files = [
    'css/custom.css',
]

html_copy_source = False
html_show_sourcelink = True
html_show_sphinx = False
html_logo = '_static/aio-ld2410.png'
html_favicon = '_static/favicon.png'
