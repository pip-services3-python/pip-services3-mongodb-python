# -*- coding: utf-8 -*-
"""
    pip_services3_mongodb.persistence.IdentifiableMongoDbPersistence
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Identifiable MongoDb persistence implementation
    
    :copyright: Conceptual Vision Consulting LLC 2018-2019, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""

import random
import pymongo

from pip_services3_commons.refer import IReferenceable
from pip_services3_commons.config import IReconfigurable
from pip_services3_commons.run import IOpenable, IClosable, ICleanable
from pip_services3_components.log import CompositeLogger
from pip_services3_commons.data import FilterParams, PagingParams, DataPage
from pip_services3_commons.data import AnyValueMap, IdGenerator

from .MongoDbPersistence import MongoDbPersistence

class IdentifiableMongoDbPersistence(MongoDbPersistence):
    """
    Abstract persistence component that stores data in MongoDB
    and implements a number of CRUD operations over data items with unique ids.
    The data items must implement IIdentifiable interface.

    In basic scenarios child classes shall only override [[getPageByFilter]],
    [[getListByFilter]] or [[deleteByFilter]] operations with specific filter function.
    All other operations can be used out of the box.

    In complex scenarios child classes can implement additional operations by
    accessing <code>this._collection</code> and <code>this._model</code> properties.

    ### Configuration parameters ###

        - collection:                  (optional) MongoDB collection name
        - connection(s):
            - discovery_key:             (optional) a key to retrieve the connection from IDiscovery
            - host:                      host name or IP address
            - port:                      port number (default: 27017)
            - uri:                       resource URI or connection string with all parameters in it
        - credential(s):
            - store_key:                 (optional) a key to retrieve the credentials from ICredentialStore
            - username:                  (optional) user name
            - password:                  (optional) user password
        - options:
            - max_pool_size:             (optional) maximum connection pool size (default: 2)
            - keep_alive:                (optional) enable connection keep alive (default: true)
            - connect_timeout:           (optional) connection timeout in milliseconds (default: 5 sec)
            - auto_reconnect:            (optional) enable auto reconnection (default: true)
            - max_page_size:             (optional) maximum page size (default: 100)
            - debug:                     (optional) enable debug output (default: false).

    ### References ###

        - *:logger:*:*:1.0           (optional) ILogger components to pass log messages components to pass log messages
        - *:discovery:*:*:1.0        (optional) IDiscovery services
        - *:credential-store:*:*:1.0 (optional) Credential stores to resolve credentials

    Example:
        class MyMongoDbPersistence(MongoDbPersistence):
            def __init__(self):
                super(MyMongoDbPersistence, self).__init__("mydata", MyData)

            def get_page_by_filter(self, correlation_id, filter, paging, sort = None, select = None):
                super().def get_page_by_filter(correlation_id, filter, paging, None, None):

        persistence = MyMongoDbPersistence()
        persistence.configure(ConfigParams.from_tuples("host", "localhost", "port", 27017))

        persitence.open("123")
        persistence.create("123", { id: "1", name: "ABC" })
        mydata = persistence.get_page_by_filter("123", FilterParams.from_tuples("name", "ABC"), None, None)

        print mydata

        persistence.delete_by_id("123", "1")
        ...
    """
    _max_page_size = 100

    def __init__(self, collection = None):
        """
        Creates a new instance of the persistence component.

        :param collection: (optional) a collection name.
        """
        super(IdentifiableMongoDbPersistence, self).__init__(collection)

    def configure(self, config):
        """
        Configures component by passing configuration parameters.

        :param config: configuration parameters to be set.
        """
        super(IdentifiableMongoDbPersistence, self).configure(config)
        self._max_page_size = config.get_as_integer_with_default("options.max_page_size", self._max_page_size)


    def get_page_by_filter(self, correlation_id, filter, paging, sort = None, select = None):
        """
        Gets a page of data items retrieved by a given filter and sorted according to sort parameters.

        This method shall be called by a public getPageByFilter method from child class that
        receives FilterParams and converts them into a filter function.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param filter: (optional) a filter JSON object

        :param paging: (optional) paging parameters

        :param sort: (optional) sorting JSON object

        :param select: (optional) projection JSON object

        :return: a data page of result by filter
        """
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
        """
        Gets a list of data items retrieved by a given filter and sorted according to sort parameters.

        This method shall be called by a public getListByFilter method from child class that
        receives FilterParams and converts them into a filter function.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param filter: (optional) a filter function to filter items

        :param sort: (optional) sorting parameters

        :param select: (optional) projection parameters (not used yet)

        :return: a data list of results by filter.
        """
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
        """
        Gets a list of data items retrieved by given unique ids.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param ids: ids of data items to be retrieved

        :return: a data list of results by ids.
        """
        filter = { '_id': { '$in': ids } }
        return self.get_list_by_filter(correlation_id, filter)


    def get_one_random(self, correlation_id, filter):
        """
        Gets a random item from items that match to a given filter.

        This method shall be called by a public getOneRandom method from child class
        that receives FilterParams and converts them into a filter function.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :return: a random item.
        """
        count = self._connection.find(filter).count()

        pos = random.randint(0, count)

        statement = self._connection.find(filter).skip(pos).limit(1)
        for item in statement:
            item = self._convert_to_public(item)
            return item

        return None


    def get_one_by_id(self, correlation_id, id):
        """
        Gets a data item by its unique id.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param id: an id of data item to be retrieved.

        :return: data item by id.
        """
        item = self._collection.find_one({ '_id': id })
        item = self._convert_to_public(item)
        return item


    def create(self, correlation_id, item):
        """
        Creates a data item.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param item: an item to be created.

        :return: a created item
        """
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
        """
        Sets a data item. If the data item exists it updates it, otherwise it create a new data item.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param item: an item to be set.

        :return: an updated item
        """
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
        """
        Updates a data item.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param new_item: an item to be updated.

        :return: an updated item.
        """
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
        """
        Updates only few selected fields in a data item.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param id: an id of data item to be updated.

        :param data: a map with fields to be updated.

        :return: an updated item.
        """
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
        """
        Deleted a data item by it's unique id.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param id: an id of the item to be deleted

        :return: a deleted item.
        """
        item = self._collection.find_one_and_delete({ '_id': id })
        item = self._convert_to_public(item)
        return item


    def delete_by_filter(self, correlation_id, filter):
        """
        Deletes data items that match to a given filter.

        This method shall be called by a public deleteByFilter method from child class that
        receives FilterParams and converts them into a filter function.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param filter: (optional) a filter function to filter items.
        """
        self._collection.remove(filter)


    def delete_by_ids(self, correlation_id, ids):
        """
        Deletes multiple data items by their unique ids.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param ids: ids of data items to be deleted.
        """
        filter = { '_id': { '$in': ids } }
        self.delete_by_filter(correlation_id, filter)
