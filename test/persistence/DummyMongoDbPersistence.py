# -*- coding: utf-8 -*-
"""
    test.persistence.DummyMongoDbPersistence
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Dummy MongoDb persistence implementation
    
    :copyright: Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""

from pip_services_commons.data import FilterParams
from pip_services_mongodb.persistence import IdentifiableMongoDbPersistence
from ..IDummyPersistence import IDummyPersistence

class DummyMongoDbPersistence(IdentifiableMongoDbPersistence, IDummyPersistence):
    
    def __init__(self):
        super(DummyMongoDbPersistence, self).__init__("dummies")

    def get_page_by_filter(self, correlation_id, filter, paging):
        filter = filter if filter != None else FilterParams()
        return super(DummyMongoDbPersistence, self).get_page_by_filter(correlation_id, filter, paging, None, None)
