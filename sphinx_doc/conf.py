# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Eqasim'
copyright = '2024, Eqasim contributors'
author = 'Eqasim contributors'
release = 'v1.2.0'  # TODO: fetch from version.txt
version = release[1:]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['myst_parser']

source_suffix = ['.rst', '.md']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_baseurl = "https://eqasim.readthedocs.io/stable/"
html_theme_options = {
    "collapse_navigation": True,
    "navigation_depth": 2,
    "show_prev_next": False,
    "icon_links": [
        {"name": "Home Page", "url": html_baseurl, "icon": "fas fa-home"},
        {
            "name": "GitHub",
            "url": "https://github.com/eqasim-org/ile-de-france",
            "icon": "fab fa-github-square",
        },
    ],
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
    "secondary_sidebar_items": ["page-toc", "edit-this-page"],
    "header_links_before_dropdown": 7,
}

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']

html_show_sourcelink = False
