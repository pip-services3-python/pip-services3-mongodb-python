# -*- coding: utf-8 -*-
"""
    pip_services3_mongodb.persistence.IdentifiableMongoDbPersistence
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Identifiable MongoDb persistence implementation
    
    :copyright: Conceptual Vision Consulting LLC 2018-2019, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""
from copy import deepcopy
from typing import Any, Optional, List, TypeVar

import pymongo
from pip_services3_commons.data import AnyValueMap, IdGenerator

from .MongoDbPersistence import MongoDbPersistence

T = TypeVar('T')  # Declare type variable


class IdentifiableMongoDbPersistence(MongoDbPersistence):
    """
    Abstract persistence component that stores data in MongoDB
    and implements a number of CRUD operations over data items with unique ids.
    The data items must implement IIdentifiable interface.

    In basic scenarios child classes shall only override :func:`get_page_by_filter <pip_services3_mongodb.persistence.MongoDbPersistence.get_page_by_filter>`,
    :func:`get_list_by_filter` or :func:`delete_by_filter` operations with specific filter function.
    All other operations can be used out of the box.

    In complex scenarios child classes can implement additional operations by
    accessing **self.__collection** and **self.__model** properties.

    ### Configuration parameters ###

        - connection(s):
            - discovery_key:             (optional) a key to retrieve the connection from :class:`IDiscovery <pip_services3_components.connect.IDiscovery.IDiscovery>`
            - host:                      host name or IP address
            - port:                      port number (default: 27017)
            - uri:                       resource URI or connection string with all parameters in it
        - credential(s):
            - store_key:                 (optional) a key to retrieve the credentials from :class:`ICredentialStore <pip_services3_components.auth.ICredentialStore.ICredentialStore>`
            - username:                  (optional) user name
            - password:                  (optional) user password
        - options:
            - max_pool_size:             (optional) maximum connection pool size (default: 2)
            - keep_alive:                (optional) enable connection keep alive (default: true)
            - connect_timeout:           (optional) connection timeout in milliseconds (default: 5000)
            - socket_timeout:            (optional) socket timeout in milliseconds (default: 360000)
            - auto_reconnect:            (optional) enable auto reconnection (default: true)
            - reconnect_interval:        (optional) reconnection interval in milliseconds (default: 1000)
            - max_page_size:             (optional) maximum page size (default: 100)
            - replica_set:               (optional) name of replica set
            - ssl:                       (optional) enable SSL connection (default: false)
            - auth_source:               (optional) authentication source
            - debug:                     (optional) enable debug output (default: false).

    ### References ###
        - `*:logger:*:*:1.0`           (optional) :class:`ILogger <pip_services3_components.log.ILogger.ILogger>` components to pass log messages components to pass log messages
        - `*:discovery:*:*:1.0`        (optional) :class:`IDiscovery <pip_services3_components.connect.IDiscovery.IDiscovery>` services
        - `*:credential-store:*:*:1.0` (optional) :class:`ICredentialStore <pip_services3_components.auth.ICredentialStore.ICredentialStore>` stores to resolve credentials

    Example:

    .. code-block:: python
    
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

        print(mydata)

        persistence.delete_by_id("123", "1")
        # ...
    """

    def __init__(self, collection: str = None):
        """
        Creates a new instance of the persistence component.

        :param collection: (optional) a collection name.
        """
        super(IdentifiableMongoDbPersistence, self).__init__(collection)

        # Flag to turn on automated string ID generation
        self._auto_generate_id: bool = True

    def _convert_from_public_partial(self, value: Any) -> Any:
        """
        Converts the given object from the public partial format.

        :param value: the object to convert from the public partial format.
        :return: the initial object.
        """
        return self._convert_from_public(value)

    def get_list_by_ids(self, correlation_id: Optional[str], ids: List[Any]) -> List[T]:
        """
        Gets a list of data items retrieved by given unique ids.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param ids: ids of data items to be retrieved

        :return: a data list of results by ids.
        """
        filters = {'_id': {'$in': ids}}
        return self.get_list_by_filter(correlation_id, filters)

    def get_one_by_id(self, correlation_id: Optional[str], id: Any) -> T:
        """
        Gets a data item by its unique id.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param id: an id of data item to be retrieved.

        :return: data item by id.
        """
        item = self._collection.find_one({'_id': id})
        if item:
            self._logger.trace(correlation_id, "Nothing found from %s with id = %s", self._collection_name, id)
        else:
            self._logger.trace(correlation_id, "Retrieved from %s with id = %s", self._collection_name, id)

        item = self._convert_to_public(item)
        return item

    def create(self, correlation_id: Optional[str], item: T) -> T:
        """
        Creates a data item.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param item: an item to be created.

        :return: a created item
        """
        if item is None:
            return

        item = self._convert_from_public(item)
        new_item = deepcopy(item)

        # Replace _id or generate a new one
        if new_item.get('_id') is None and self._auto_generate_id:
            new_item['_id'] = IdGenerator.next_long()

        return super().create(correlation_id, new_item)

    def set(self, correlation_id: Optional[str], item: T) -> T:
        """
        Sets a data item. If the data item exists it updates it, otherwise it create a new data item.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param item: an item to be set.

        :return: an updated item
        """
        if item is None:
            return

        item = self._convert_from_public(item)
        new_item = dict(item)

        # Replace _id or generate a new one
        if new_item.get('_id') is None and self._auto_generate_id:
            new_item['_id'] = IdGenerator.next_long()

        new_item = self._convert_from_public(new_item)

        item = self._collection.find_one_and_replace(
            {'_id': new_item['_id']}, new_item,
            return_document=pymongo.ReturnDocument.AFTER,
            upsert=True
        )

        item = self._convert_to_public(item)

        if item:
            self._logger.trace(correlation_id, "Set in %s with id = %s", self._collection_name, item.id)

        return item

    def update(self, correlation_id: Optional[str], item: T) -> Optional[T]:
        """
        Updates a data item.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param item: an item to be updated.

        :return: an updated item.
        """
        if item is None or item.id is None:
            return

        new_item = deepcopy(item)
        new_item = self._convert_from_public(new_item)

        result = self._collection.find_one_and_update(
            {'_id': item.id}, {'$set': new_item},
            return_document=pymongo.ReturnDocument.AFTER
        )

        new_item = self._convert_to_public(result)

        self._logger.trace(correlation_id, "Updated in %s with id = %s", self._collection_name, item.id)

        return new_item

    def update_partially(self, correlation_id: Optional[str], id: Any, data: AnyValueMap) -> T:
        """
        Updates only few selected fields in a data item.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param id: an id of data item to be updated.

        :param data: a map with fields to be updated.

        :return: an updated item.
        """
        if data is None or id is None:
            return

        new_item = data.get_as_object()
        new_item = self._convert_from_public_partial(new_item)

        item = self._collection.find_one_and_update(
            {'_id': id}, {'$set': new_item},
            return_document=pymongo.ReturnDocument.AFTER
        )

        self._logger.trace(correlation_id, "Updated partially in %s with id = %s", self._collection_name, id)

        item = self._convert_to_public(item)
        return item

    # The method must return deleted value to be able to do clean up like removing references
    def delete_by_id(self, correlation_id: Optional[str], id: Any) -> T:
        """
        Deleted a data item by it's unique id.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param id: an id of the item to be deleted

        :return: a deleted item.
        """
        item = self._collection.find_one_and_delete({'_id': id})

        self._logger.trace(correlation_id, "Deleted from %s with id = %s", self._collection_name, id)

        old_item = self._convert_to_public(item)
        return old_item

    def delete_by_ids(self, correlation_id: Optional[str], ids: List[Any]):
        """
        Deletes multiple data items by their unique ids.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param ids: ids of data items to be deleted.
        """
        filter = {'_id': {'$in': ids}}
        self.delete_by_filter(correlation_id, filter)
