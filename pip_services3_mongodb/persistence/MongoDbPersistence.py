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

from pip_services3_commons.config import ConfigParams
from pip_services3_commons.config import IConfigurable
from pip_services3_commons.data import PagingParams, DataPage
from pip_services3_commons.errors import ConnectionException
from pip_services3_commons.refer import IReferenceable, DependencyResolver, IReferences
from pip_services3_commons.run import IOpenable, ICleanable
from pip_services3_components.log import CompositeLogger

from pip_services3_mongodb.persistence.MongoDbConnection import MongoDbConnection
from ..connect.MongoDbConnectionResolver import MongoDbConnectionResolver

filtered = filter


class MongoDbPersistence(IReferenceable, IConfigurable, IOpenable, ICleanable):
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
            - connect_timeout:           (optional) connection timeout in milliseconds (default: 5 sec)
            - auto_reconnect:            (optional) enable auto reconnection (default: true)
            - max_page_size:             (optional) maximum page size (default: 100)
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
    _default_config = ConfigParams.from_tuples(
        "collection", None,
        "dependencies.connection", "*:connection:mongodb:*:1.0",

        # "connect.type", "mongodb",
        # "connect.database", "test",
        # "connect.host", "localhost",
        # "connect.port", 27017,

        "options.max_pool_size", 2,
        "options.keep_alive", 1,
        "options.connect_timeout", 30000,
        "options.socket_timeout", 5000,
        "options.auto_reconnect", True,
        "options.max_page_size", 100,
        "options.debug", True
    )

    _lock = None
    _connection_resolver = None
    _options = None

    _config: ConfigParams = None
    _references: IReferences = None
    _opened = False
    _localConnection = False
    _indexes = []

    # The logger.
    _logger = None
    # The dependency resolver.
    _dependencyResolver = DependencyResolver(_default_config)
    # The MongoDB database name.
    _database_name = None
    # The MongoDB colleciton object.
    _collection_name = None
    # The MongoDb database object.
    _database = None
    # The MongoDb collection object.
    _collection = None
    # The MongoDB connection object.
    _client = None
    # The MongoDB connection component.
    _connection = None

    _max_page_size = 100

    def __init__(self, collection=None):
        """
        Creates a new instance of the persistence component.

        :param collection: (optional) a collection name.
        """
        self._lock = threading.Lock()
        self._logger = CompositeLogger()
        self._connection_resolver = MongoDbConnectionResolver()
        self._options = ConfigParams()

        self._collection_name = collection

    def configure(self, config):
        """
        Configures component by passing configuration parameters.

        :param config: configuration parameters to be set.
        """
        config = config.set_defaults(self._default_config)
        self._config = config

        self._logger.configure(config)
        self._connection_resolver.configure(config)
        self._dependencyResolver.configure(config)

        self._max_page_size = config.get_as_integer_with_default("options.max_page_size", self._max_page_size)
        self._collection_name = config.get_as_string_with_default('collection', self._collection_name)
        self._options = self._options.override(config.get_section('options'))

    def set_references(self, references):
        """
        Sets references to dependent components.

        :param references: references to locate the component dependencies.
        """
        self._references = references
        self._logger.set_references(references)
        self._connection_resolver.set_references(references)

        # Get connection
        self._dependencyResolver.set_references(references)
        self._connection = self._dependencyResolver.get_one_required('connection')
        # Or create a local one
        if self._connection is None:
            self._connection = self.__create_connection()
            self._localConnection = True
        else:
            self._localConnection = False

    def unset_references(self):
        """
        Unsets (clears) previously set references to dependent components.
        """
        self._connection = None

    def __create_connection(self):
        connection = MongoDbConnection()

        if self._config:
            connection.configure(self._config)

        if self._references:
            connection.set_references(self._references)

        return connection

    def _ensure_index(self, keys, options=None):
        if not keys:
            return
        self._indexes.append({
            'keys': keys,
            'options': options
        })

    def _clear_schema(self):
        """
        Clears all auto-created objects
        """
        self._indexes = []

    def _define_schema(self):
        # TODO: override in child class
        pass

    def _convert_to_public(self, value):
        """
        Converts object value from internal to public format.

        :param value: an object in internal format to convert.

        :return: converted object in public format.
        """
        if value is None: return None
        value['id'] = value['_id']
        value.pop('_id', None)
        return value

    def _convert_from_public(self, value):
        """
        Convert object value from public to internal format.

        :param value: an object in public format to convert.

        :return: converted object in internal format.
        """
        return value

    def is_opened(self):
        """
        Checks if the component is opened.

        :return: true if the component has been opened and false otherwise.
        """
        return self._opened

    def open(self, correlation_id):
        """
        Opens the component.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        """
        if self._opened:
            return

        if self._connection is None:
            self._connection = self.__create_connection()
            self._localConnection = True

        uri = self._connection_resolver.resolve(correlation_id)

        max_pool_size = self._options.get_as_nullable_integer("max_pool_size")
        keep_alive = self._options.get_as_nullable_boolean("keep_alive")
        connect_timeout = self._options.get_as_nullable_integer("connect_timeout")
        socket_timeout = self._options.get_as_nullable_integer("socket_timeout")
        auto_reconnect = self._options.get_as_nullable_boolean("auto_reconnect")
        max_page_size = self._options.get_as_nullable_integer("max_page_size")
        debug = self._options.get_as_nullable_boolean("debug")

        self._logger.debug(correlation_id, "Connecting to mongodb database ")

        try:
            if self._localConnection:
                self._connection.open(correlation_id)

            kwargs = {
                'maxPoolSize': max_pool_size,
                'connectTimeoutMS': connect_timeout,
                'socketKeepAlive': keep_alive,
                'socketTimeoutMS': socket_timeout,
                'appname': correlation_id
            }
            kwargs = self.__del_none_objects(kwargs)
            self._client = self._connection.get_connection()
            self._database = self._connection.get_database()
            self._database_name = self._connection.get_database_name()

            # Define database schema
            self._define_schema()

            self._collection = self._database.get_collection(self._collection_name)
            self._opened = True
        except Exception as ex:
            self._opened = False
            raise ConnectionException(correlation_id, "CONNECT_FAILED", "Connection to mongodb failed") \
                .with_cause(ex)

    def __del_none_objects(self, settings):
        new_settings = {}
        for k in settings.keys():
            if settings[k] is not None:
                new_settings[k] = settings[k]
        return new_settings

    def close(self, correlation_id):
        """
        Closes component and frees used resources.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        """
        try:
            if self._client != None:
                self._client.close()

            self._collection = None
            self._database = None
            self._client = None

            self._logger.debug(correlation_id, "Disconnected from mongodb database " + str(self._database_name))
        except Exception as ex:
            raise ConnectionException(None, 'DISCONNECT_FAILED', 'Disconnect from mongodb failed: ' + str(ex)) \
                .with_cause(ex)

    def clear(self, correlation_id):
        """
        Clears component state.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        """
        if self._collection_name == None:
            raise Exception("Collection name is not defined")

        self._database.drop_collection(self._collection_name)

    def create(self, correlation_id, item):
        """
        Creates a data item.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param item: an item to be created.

        :return: a created item
        """
        item = self._convert_from_public(item)
        new_item = dict(item)

        result = self._collection.insert_one(new_item)
        item = self._collection.find_one({'_id': result.inserted_id})

        item = self._convert_to_public(item)
        return item

    def delete_by_filter(self, correlation_id, filter):
        """
        Deletes data items that match to a given filter.

        This method shall be called by a public :func:`delete_by_filter` method from child class that
        receives :class:`FilterParams <pip_services3_commons.data.FilterParams.FilterParams>` and converts them into a filter function.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :param filter: (optional) a filter function to filter items.
        """
        self._collection.remove(filter)

    def get_one_random(self, correlation_id, filter):
        """
        Gets a random item from items that match to a given filter.

        This method shall be called by a public get_one_random method from child class
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

    def get_page_by_filter(self, correlation_id, filter, paging, sort=None, select=None):
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

    def get_list_by_filter(self, correlation_id, filter, sort=None, select=None):
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

    def get_count_by_filter(self, correlation_id: str, filter) -> int:
        count = self._connection.find(filter).count()

        return count
