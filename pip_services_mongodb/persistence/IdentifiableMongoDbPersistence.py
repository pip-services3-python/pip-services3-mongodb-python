# -*- coding: utf-8 -*-
"""
    pip_services_mongodb.persistence.IdentifiableMongoDbPersistence
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Identifiable MongoDb persistence implementation
    
    :copyright: Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""

import random
import pymongo

from pip_services_commons.refer import IReferenceable
from pip_services_commons.config import IReconfigurable
from pip_services_commons.run import IOpenable, IClosable, ICleanable
from pip_services_components.log import CompositeLogger
from pip_services_commons.data import FilterParams, PagingParams, DataPage
from pip_services_commons.data import AnyValueMap, IdGenerator

from .MongoDbPersistence import MongoDbPersistence

class IdentifiableMongoDbPersistence(MongoDbPersistence):
    _max_page_size = 100

    def __init__(self, collection = None):
        super(IdentifiableMongoDbPersistence, self).__init__(collection)

    def configure(self, config):
        super(IdentifiableMongoDbPersistence, self).configure(config)
        self._max_page_size = config.get_as_integer_with_default("options.max_page_size", self._max_page_size)


    def get_page_by_filter(self, correlation_id, filter, paging, sort = None, select = None):
        # Adjust max item count based on configuration
        paging = paging if paging != None else PagingParams()
        skip = paging.get_skip(-1)
        take = paging.get_take(self._max_page_size)

        # Configure statement
        statement = self._collection.find(filter)

        if skip >= 0:
            statement = statement.skip(skip)
        statement = statement.limit(take)
        if sort != None:
            statement = statement.sort(sort)
        if select != None:
            statement = statement.select(select)

        # Retrive page items
        items = []
        for item in statement:
            item = self._convert_to_public(item)
            items.append(item)

        # Calculate total if needed
        total = None
        if paging.total:
            total = self._collection.find(filter).count()
        
        return DataPage(items, total)


    def get_list_by_filter(self, correlation_id, filter, sort = None, select = None):
        # Configure statement
        statement = self._collection.find(filter)

        if sort != None:
            statement = statement.sort(sort)
        if select != None:
            statement = statement.select(select)

        # Retrive page items
        items = []
        for item in statement:
            item = self._convert_to_public(item)
            items.append(item)

        return items


    def get_list_by_ids(self, correlation_id, ids):
        filter = { '_id': { '$in': ids } }
        return self.get_list_by_filter(correlation_id, filter)


    def get_one_random(self, correlation_id, filter):
        count = self._connection.find(filter).count()

        pos = random.randint(0, count)

        statement = self._connection.find(filter).skip(pos).limit(1)
        for item in statement:
            item = self._convert_to_public(item)
            return item

        return None


    def get_one_by_id(self, correlation_id, id):
        item = self._collection.find_one({ '_id': id })
        item = self._convert_to_public(item)
        return item


    def create(self, correlation_id, item):
        item = self._convert_from_public(item)
        new_item = dict(item)

        # Replace _id or generate a new one
        new_item.pop('_id', None)            
        new_item['_id'] = item['id'] if 'id' in item and item['id'] != None else IdGenerator.next_long()

        result = self._collection.insert_one(new_item)
        item = self._collection.find_one({ '_id': result.inserted_id })

        item = self._convert_to_public(item)
        return item


    def set(self, correlation_id, item):
        item = self._convert_from_public(item)
        new_item = dict(item)

        # Replace _id or generate a new one
        new_item.pop('_id', None)            
        new_item['_id'] = item['id'] if 'id' in item and item['id'] != None else IdGenerator.next_long()
        id = new_item['_id']

        item = self._collection.find_one_and_update( \
            { '_id': id }, { '$set': new_item }, \
            return_document = pymongo.ReturnDocument.AFTER, \
            upsert = True \
        )

        item = self._convert_to_public(item)
        return item


    def update(self, correlation_id, new_item):
        new_item = self._convert_from_public(new_item)
        id = new_item['id']
        new_item = dict(new_item)
        new_item.pop('_id', None)
        new_item.pop('id', None)

        item = self._collection.find_one_and_update( \
            { '_id': id }, { '$set': new_item }, \
            return_document = pymongo.ReturnDocument.AFTER \
        )

        item = self._convert_to_public(item)
        return item


    def update_partially(self, correlation_id, id, data):
        new_item = data.get_as_object() if isinstance(data, AnyValueMap) else dict(data)
        new_item.pop('_id', None)
        new_item.pop('id', None)

        item = self._collection.find_one_and_update( \
            { '_id': id }, { '$set': new_item }, \
            return_document = pymongo.ReturnDocument.AFTER \
        )

        item = self._convert_to_public(item)
        return item


    # The method must return deleted value to be able to do clean up like removing references 
    def delete_by_id(self, correlation_id, id):
        item = self._collection.find_one_and_delete({ '_id': id })
        item = self._convert_to_public(item)
        return item


    def delete_by_filter(self, correlation_id, filter):
        self._collection.remove(filter)


    def delete_by_ids(self, correlation_id, ids):
        filter = { '_id': { '$in': ids } }
        self.delete_by_filter(correlation_id, filter)
