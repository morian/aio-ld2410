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

# -- Path setup --------------------------------------------------------------

# This seems somehow necessary to have linkcode work properly on ReadTheDocs.
# See https://github.com/readthedocs/readthedocs.org/issues/2139#issuecomment-352188629
sys.path.insert(0, os.path.abspath('..'))


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
author = 'Romain Bezut'
project = 'aio-ld2410'
copyright = f'2024, {author}'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.linkcode',
    'sphinx.ext.napoleon',
    'sphinx_copybutton',
    'sphinx_inline_tabs',
    'sphinx_autodoc_typehints',
    'sphinxext.opengraph',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Extensions configuration ------------------------------------------------
# Nitpick configuration
nitpicky = True
nitpick_ignore = [
    # construct does not document `Container` which is an `OrderedDict`.
    ('py:class', 'construct.lib.containers.Container'),
]

# Napoleon settings
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
typehints_use_rtype = False

# InterSphinx
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'construct': ('https://construct.readthedocs.io/en/latest', None),
}

# OpenGraph
ogp_site_url = os.environ.get(
    'READTHEDOCS_CANONICAL_URL',
    'https://aio-ld2410.readthedocs.io/en/stable/',
)
ogp_image = '_static/aio-ld2410.png'


## ReadTheDocs compatibility as we're using rtd-addons.
## See https://about.readthedocs.com/blog/2024/07/addons-by-default/

# Define the canonical URL if you are using a custom domain on Read the Docs
html_baseurl = os.environ.get('READTHEDOCS_CANONICAL_URL', '')

# Tell Jinja2 templates the build is running on Read the Docs
if os.environ.get('READTHEDOCS') == 'True':
    if 'html_context' not in globals():
        html_context = {}

    # This is required by furo to display a link to the github repository.
    # When furo will be updated everything should come to order.
    html_context.update(
        {
            'github_user': 'morian',
            'github_repo': 'aio-ld2410',
            'display_github': True,
            'slug': 'aio-ld2410',
            'READTHEDOCS': True,
        }
    )


def get_current_commit() -> str:
    """Try to find out which commit we're building for."""
    # READTHEDOCS_GIT_IDENTIFIER does not seem to contain the tag name.
    ver_type = os.environ.get('READTHEDOCS_VERSION_TYPE', '')
    ver_name = os.environ.get('READTHEDOCS_VERSION_NAME', '')
    if ver_type == 'tag' and ver_name.startswith('v'):
        commit = ver_name
    else:
        commit = os.environ.get('READTHEDOCS_GIT_COMMIT_HASH', 'master')

    return commit


commit = get_current_commit()
repo_url = 'https://github.com/morian/aio-ld2410/'


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
    if not file.startswith('aio_ld2410'):
        # e.g. object is a typing.NewType
        return None

    start, end = lines[1], lines[1] + len(lines[0]) - 1
    return f'{repo_url}/blob/{commit}/{file}#L{start}-L{end}'


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'

html_theme_options = {
    'source_repository': repo_url,
    'source_branch': commit,
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
    'top_of_page_buttons': ['view'],
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
