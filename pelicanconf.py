#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Ahmad Jarara'
SITENAME = 'No Odd Cycles'
SITEURL = ''




PATH = 'content'

TIMEZONE = 'EST'

DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
# ('Pelican', 'http://getpelican.com/'),
# ('Jinja2', 'http://jinja.pocoo.org/'),
LINKS = (('Source', 'https://github.com/alphor/jarmac.org'),
         ('NixOS', 'http://jarmac.org/category/nix.html'),
         ('linux', 'http://jarmac.org/category/linux.html'),
         ('meta', 'http://jarmac.org/category/meta.html'),
         ('math', 'http://jarmac.org/category/math.html'),)

# Social widget
SOCIAL = (('Github', 'https://github.com/alphor/jarmac.org'),)

DEFAULT_PAGINATION = False

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

# Begin Flex config
# PLUGIN_PATHS = ['./pelican-plugins']
# PLUGINS = ['i18n_subsites', 'piwik']
THEME='./Flex'
