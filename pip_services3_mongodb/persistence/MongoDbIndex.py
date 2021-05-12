# -*- coding: utf-8 -*-
from typing import Any


class MongoDbIndex:
    """
    Index definition for mongodb
    """

    def __init__(self, keys: Any, options: Any = None):
        # Index keys (fields)
        self.keys: Any = keys
        # Index options
        self.options: Any = options
