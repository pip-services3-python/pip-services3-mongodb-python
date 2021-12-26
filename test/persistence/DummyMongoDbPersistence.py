# -*- coding: utf-8 -*-
"""
    test.persistence.DummyMongoDbPersistence
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Dummy MongoDb persistence implementation
    
    :copyright: Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""
from typing import Optional

from pip_services3_commons.data import FilterParams, DataPage, PagingParams

from pip_services3_mongodb.persistence import IdentifiableMongoDbPersistence
from test.fixtures.IDummyPersistence import IDummyPersistence


class DummyMongoDbPersistence(IdentifiableMongoDbPersistence, IDummyPersistence):

    def __init__(self):
        super(DummyMongoDbPersistence, self).__init__("dummies")

    def _define_schema(self):
        self._ensure_index({'key': 1})

    def get_page_by_filter(self, correlation_id: Optional[str], filter: FilterParams, paging: PagingParams) -> DataPage:
        filter = filter or FilterParams()
        key = filter.get_as_nullable_string('key')

        filter_condition = {}
        if key is not None:
            filter_condition['key'] = key

        return super().get_page_by_filter(correlation_id, filter, paging, None, None)

    def get_count_by_filter(self, correlation_id: Optional[str], filter: FilterParams) -> int:
        filter = filter or FilterParams()
        key = filter.get_as_nullable_string('key')

        filter_condition = {}
        if key is not None:
            filter_condition['key'] = key

        return super().get_count_by_filter(correlation_id, filter)
