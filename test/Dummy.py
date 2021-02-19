# -*- coding: utf-8 -*-
"""
    test.Dummy
    ~~~~~~~~~~
    
    Dummy data object
    
    :copyright: Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""


class Dummy(dict):
    def __init__(self, id=None, key=None, content=None):
        self['id'] = id
        self['key'] = key
        self['content'] = content
