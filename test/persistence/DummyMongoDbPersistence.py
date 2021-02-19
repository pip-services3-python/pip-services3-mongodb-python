# -*- coding: utf-8 -*-
"""
    test.persistence.DummyMongoDbPersistence
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Dummy MongoDb persistence implementation
    
    :copyright: Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""

from pip_services3_commons.data import FilterParams

from pip_services3_mongodb.persistence import IdentifiableMongoDbPersistence
from ..IDummyPersistence import IDummyPersistence


class DummyMongoDbPersistence(IdentifiableMongoDbPersistence, IDummyPersistence):

    def __init__(self):
        super(DummyMongoDbPersistence, self).__init__("dummies")

    def _define_schema(self):
        self._ensure_index({'key': 1})

    def get_page_by_filter(self, correlation_id, filter, paging, sort=None, select=None):
        filter = filter if filter is not None else FilterParams()
        return super(DummyMongoDbPersistence, self).get_page_by_filter(correlation_id, filter, paging, None, None)
