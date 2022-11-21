# -*- coding: utf-8 -*-
"""
    pip_services3_mongodb.persistence.MongoDbPersistence
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    MongoDb persistence implementation

    :copyright: Conceptual Vision Consulting LLC 2018-2019, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""
import random
import threading
from copy import deepcopy
from typing import List, Any, Optional, TypeVar

import pymongo
from pip_services3_commons.config import ConfigParams
from pip_services3_commons.config import IConfigurable
from pip_services3_commons.data import PagingParams, DataPage
from pip_services3_commons.errors import ConnectionException, InvalidStateException
from pip_services3_commons.refer import IReferenceable, DependencyResolver, IReferences, IUnreferenceable
from pip_services3_commons.reflect import PropertyReflector
from pip_services3_commons.run import IOpenable, ICleanable
from pip_services3_components.log import CompositeLogger
from pymongo.collection import Collection

from pip_services3_mongodb.connect.MongoDbConnection import MongoDbConnection
from .MongoDbIndex import MongoDbIndex
from ..connect.MongoDbConnectionResolver import MongoDbConnectionResolver

filtered = filter

T = TypeVar('T')  # Declare type variable


class MongoDbPersistence(IReferenceable, IUnreferenceable, IConfigurable, IOpenable, ICleanable):
    """
    Abstract persistence component that stores data in MongoDB
    using the official MongoDB driver.

    This is the most basic persistence component that is only
    able to store data items of any type. Specific CRUD operations
    over the data items must be implemented in child classes by
    accessing **self.__collection** or **self.__model** properties.

    ### Configuration parameters ###
        - collection:                  (optional) MongoDB collection name
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
        - `*:logger:*:*:1.0`           (optional) :class:`ILogger <pip_services3_components.log.ILogger.ILogger>` components to pass log messages
        - `*:discovery:*:*:1.0`        (optional) :class:`IDiscovery <pip_services3_components.connect.IDiscovery.IDiscovery>` services
        - `*:credential-store:*:*:1.0` (optional) :class:`ICredentialStore <pip_services3_components.auth.ICredentialStore.ICredentialStore>` stores to resolve credentials

    Example:

    .. code-block:: python

        class MyMongoDbPersistence(MongoDbPersistence):
            def __init__(self):
                super(MyMongoDbPersistence, self).__init__("mydata", MyData)

            def get_by_name(self, correlationId, name):
                item =  self._collection.find_one({ 'name': name })
                return item

            def set(self, correlationId, item):
                item = self._collection.find_one_and_update(
                    { '_id': item.id }, { '$set': item },
                    return_document = pymongo.ReturnDocument.AFTER,
                    upsert = True
                    )

        persistence = MyMongoDbPersistence()
        persistence.configure(ConfigParams.from_tuples("host", "localhost", "port", 27017))

        persitence.open("123")

        persistence.set("123", { name: "ABC" })
        item = persistence.get_by_name("123", "ABC")

        print (item)
    """
    __default_config = ConfigParams.from_tuples(
        "collection", None,
        "dependencies.connection", "*:connection:mongodb:*:1.0",

        # "connect.type", "mongodb",
        # "connect.database", "test",
        # "connect.host", "localhost",
        # "connect.port", 27017,

        "options.max_pool_size", 2,
        "options.keep_alive", 1,
        "options.connect_timeout", 5000,
        "options.auto_reconnect", True,
        "options.max_page_size", 100,
        "options.debug", True
    )

    def __init__(self, collection: str = None):
        """
        Creates a new instance of the persistence component.

        :param collection: (optional) a collection name.
        """
        self._lock: threading.Lock = threading.Lock()
        self._connection_resolver: MongoDbConnectionResolver = MongoDbConnectionResolver()
        self._options: ConfigParams = ConfigParams()

        # The logger.
        self._logger: CompositeLogger = CompositeLogger()

        # The dependency resolver.
        self._dependency_resolver = DependencyResolver(self.__default_config)

        # The MongoDB database name.
        self._database_name: str = None
        # The MongoDb database object.
        self._db: Any = None
        # The MongoDb collection object.
        self._collection: Collection = None
        # The MongoDB connection object.
        self._client: Any = None
        # The MongoDB connection component.
        self._connection: MongoDbConnection = None

        self._max_page_size = 100

        # The MongoDB colleciton object.
        self._collection_name: str = collection

        self.__config: ConfigParams = None
        self.__references: IReferences = None
        self.__opened = False
        self.__local_connection = False
        self.__indexes: List[MongoDbIndex] = []

    def configure(self, config: ConfigParams):
        """
        Configures component by passing configuration parameters.

        :param config: configuration parameters to be set.
        """
        config = config.set_defaults(self.__default_config)
        self.__config = config

        self._logger.configure(config)
        self._connection_resolver.configure(config)
        self._dependency_resolver.configure(config)

        self._max_page_size = config.get_as_integer_with_default("options.max_page_size", self._max_page_size)
        self._collection_name = config.get_as_string_with_default('collection', self._collection_name)

    def set_references(self, references: IReferences):
        """
        Sets references to dependent components.

        :param references: references to locate the component dependencies.
        """
        self.__references = references
        self._logger.set_references(references)
        self._connection_resolver.set_references(references)

        # Get connection
        self._dependency_resolver.set_references(references)
        self._connection = self._dependency_resolver.get_one_optional('connection')
        # Or create a local one
        if self._connection is None:
            self._connection = self.__create_connection()
            self.__local_connection = True
        else:
            self.__local_connection = False

    def unset_references(self):
        """
        Unsets (clears) previously set references to dependent components.
        """
        self._connection = None

    def __create_connection(self) -> MongoDbConnection:
        connection = MongoDbConnection()

        if self.__config:
            connection.configure(self.__config)

        if self.__references:
            connection.set_references(self.__references)

        return connection

    def _ensure_index(self, keys: Any, options: Any = None):
        """
        Adds index definition to create it on opening

        :param keys: index keys (fields)
        :param options: index options
        """
        if not keys:
            return
        self.__indexes.append(MongoDbIndex(keys, options))

    def _clear_schema(self):
        """
        Clears all auto-created objects
        """
        self.__indexes = []

    def _define_schema(self):
        # TODO: override in child class
        pass

    def _convert_to_public(self, value: Any) -> Any:
        """
        Converts object value from internal to public format.

        :param value: an object in internal format to convert.

        :return: converted object in public format.
        """
        if value is None: return None
        if '_id' in value.keys():
            value['id'] = value['_id']
            value.pop('_id', None)

        return type('object', (object,), value)

    def _convert_from_public(self, value: Any) -> Any:
        """
        Convert object value from public to internal format.

        :param value: an object in public format to convert.

        :return: converted object in internal format.
        """
        if isinstance(value, dict):
            return deepcopy(value)

        value = PropertyReflector.get_properties(value)

        if 'id' in value.keys():
            value['_id'] = value.get('id') or value.get('_id')
            value.pop('id', None)
        return value

    def is_open(self) -> bool:
        """
        Checks if the component is opened.

        :return: true if the component has been opened and false otherwise.
        """
        return self.__opened

    def open(self, correlation_id: Optional[str]):
        """
        Opens the component.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        """
        if self.__opened:
            return

        if self._connection is None:
            self._connection = self.__create_connection()
            self.__local_connection = True

        if self.__local_connection:
            self._connection.open(correlation_id)

        if self._connection is None:
            raise InvalidStateException(correlation_id, 'NO_CONNECTION', 'MongoDB connection is missing')

        if not self._connection.is_open():
            raise ConnectionException(correlation_id, "CONNECT_FAILED", "MongoDB connection is not opened")

        self.__opened = False

        self._client = self._connection.get_connection()
        self._db = self._connection.get_database()
        self._database_name = self._connection.get_database_name()

        try:
            self._collection = self._db.get_collection(self._collection_name)

            # Define database schema
            self._define_schema()

            # Recreate indexes
            for index in self.__indexes:
                keys = [(k, pymongo.ASCENDING) if v > 0 else (k, pymongo.DESCENDING) for k, v in index.keys.items()]
                index.options = index.options or {}

                self._collection.create_index(keys, **(index.options or {}))

                index_name = index.options.get('name') or ','.join(deepcopy(index.keys))
                self._logger.debug(correlation_id, "Created index %s for collection %s", index_name,
                                   self._collection_name)

            self.__opened = True
            self._logger.debug(correlation_id, "Connected to mongodb database %s, collection %s", self._database_name,
                               self._collection_name)
        except Exception as ex:
            raise ConnectionException(correlation_id, "CONNECT_FAILED", "Connection to mongodb failed").with_cause(ex)

    def __del_none_objects(self, settings):
        new_settings = {}
        for k in settings.keys():
            if settings[k] is not None:
                new_settings[k] = settings[k]
        return new_settings

    def close(self, correlation_id: Optional[str]):
        """
        Closes component and frees used resources.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        """
        if not self.__opened:
            return

        try:
            if self._client is not None:
                self._client.close()

            if self._connection is None:
                raise InvalidStateException(correlation_id, 'NO_CONNECTION', 'MongoDb connection is missing')

            if self.__local_connection:
                self._connection.close(correlation_id)

            self._collection = None
            self._db = None
            self._client = None

            self.__opened = False
            self._logger.debug(correlation_id, "Disconnected from mongodb database " + str(self._database_name))
        except Exception as ex:
            raise ConnectionException(None, 'DISCONNECT_FAILED', 'Disconnect from mongodb failed: ' + str(ex)) \
                .with_cause(ex)

    def clear(self, correlation_id: Optional[str]):
        """
        Clears component state.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        """
        if self._collection_name is None:
            raise Exception("Collection name is not defined")

        self._collection.delete_many({})

    def create(self, correlation_id: Optional[str], item: T) -> T:
        """
        Creates a data item.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param item: an item to be created.

        :return: a created item
        """
        if item is None:
            return

        new_item = self._convert_from_public(item)

        result = self._collection.insert_one(new_item)
        item = self._collection.find_one({'_id': result.inserted_id})

        item = self._convert_to_public(item)
        return item

    def delete_by_filter(self, correlation_id: Optional[str], filter: Any):
        """
        Deletes data items that match to a given filter.

        This method shall be called by a public :func:`delete_by_filter` method from child class that
        receives :class:`FilterParams <pip_services3_commons.data.FilterParams.FilterParams>` and converts them into a filter function.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param filter: (optional) a filter function to filter items.
        """
        result = self._collection.delete_many(filter or {})
        count = 0 if result is None else result.deleted_count
        self._logger.trace(correlation_id, "Deleted %d items from %s", count, self._collection_name)

    def get_one_random(self, correlation_id: Optional[str], filter: Any) -> Optional[T]:
        """
        Gets a random item from items that match to a given filter.

        This method shall be called by a public get_one_random method from child class
        that receives FilterParams and converts them into a filter function.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :return: a random item.
        """
        count = self._collection.count_documents(filter or {})

        pos = random.randint(0, count)

        statement = self._collection.find(filter).skip(pos if pos > 0 else 0).limit(1)

        for item in statement:
            if item is None:
                self._logger.trace(correlation_id, "Random item wasn't found from %s", self._collection_name)
            else:
                self._logger.trace(correlation_id, "Retrieved random item from %s", self._collection_name)

            item = self._convert_to_public(item)

            return item

        return None

    def get_page_by_filter(self, correlation_id: Optional[str], filter: Any, paging: PagingParams,
                           sort: Any = None, select: Any = None) -> DataPage:
        """
        Gets a page of data items retrieved by a given filter and sorted according to sort parameters.

        This method shall be called by a public get_page_by_filter method from child class that
        receives FilterParams and converts them into a filter function.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        :param filter: (optional) a filter JSON object
        :param paging: (optional) paging parameters
        :param sort: (optional) sorting JSON object
        :param select: (optional) projection JSON object
        :return: a data page of result by filter
        """
        # Adjust max item count based on configuration
        paging = paging if paging is not None else PagingParams()
        skip = paging.get_skip(-1)
        take = paging.get_take(self._max_page_size)
        paging_enabled = paging.total
        filter = filter or {}

        # Configure statement
        statement = self._collection.find(filter, projection=select or {})

        if skip >= 0:
            statement = statement.skip(skip)
        statement = statement.limit(take)
        if sort is not None:
            statement = statement.sort(sort)

        # Retrive page items
        items = []
        for item in statement:
            item = self._convert_to_public(item)
            items.append(item)

        if items:
            self._logger.trace(correlation_id, "Retrieved %d from %s", len(items), self._collection_name)

        # Calculate total if needed
        total = None
        if paging_enabled:
            total = self._collection.count_documents(filter)

        return DataPage(items, total)

    def get_list_by_filter(self, correlation_id: Optional[str], filter: Any,
                           sort: Any = None, select: Any = None) -> List[T]:
        """
        Gets a list of data items retrieved by a given filter and sorted according to sort parameters.

        This method shall be called by a public get_list_by_filter method from child class that
        receives FilterParams and converts them into a filter function.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param filter: (optional) a filter function to filter items

        :param sort: (optional) sorting parameters

        :param select: (optional) projection parameters (not used yet)

        :return: a data list of results by filter.
        """
        # Configure statement
        filter = filter or {}
        statement = self._collection.find(filter, projection=select or {})

        if sort is not None:
            statement = statement.sort(sort)

        # Retrive page items
        items = []
        for item in statement:
            item = self._convert_to_public(item)
            items.append(item)

        if items:
            self._logger.trace(correlation_id, "Retrieved %d from %s", len(items), self._collection_name)

        return items

    def get_count_by_filter(self, correlation_id: Optional[str], filter: Any) -> int:
        """
        Gets a number of data items retrieved by a given filter.

        This method shall be called by a public get_count_by_filter method from child class that
        receives FilterParams and converts them into a filter function.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        :param filter: (optional) a filter JSON object
        :return: a number of filtered items.
        """
        filter = filter or {}
        count = self._collection.count_documents(filter)

        if count is not None:
            self._logger.trace(correlation_id, "Counted %d items in %s", count, self._collection_name)

        return count
