# -*- coding: utf-8 -*-
"""
    test.Dummy
    ~~~~~~~~~~
    
    Dummy data object
    
    :copyright: Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""
from pip_services3_commons.data import IStringIdentifiable


class Dummy(IStringIdentifiable):
    def __init__(self, id: str = None, key: str = None, content: str = None):
        self.id = id
        self.key = key
        self.content = content
