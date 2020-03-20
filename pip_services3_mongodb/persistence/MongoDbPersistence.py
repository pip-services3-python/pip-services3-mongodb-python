# -*- coding: utf-8 -*-
"""
    pip_services3_mongodb.persistence.MongoDbPersistence
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    MongoDb persistence implementation
    
    :copyright: Conceptual Vision Consulting LLC 2018-2019, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""

import threading
import pymongo

from pip_services3_commons.config import ConfigParams, IConfigurable
from pip_services3_commons.refer import IReferenceable
from pip_services3_commons.run import IOpenable, ICleanable
from pip_services3_components.log import CompositeLogger
from pip_services3_commons.errors import ConnectionException
from ..connect.MongoDbConnectionResolver import MongoDbConnectionResolver


class MongoDbPersistence(IReferenceable, IConfigurable, IOpenable, ICleanable):
    """
    Abstract persistence component that stores data in MongoDB
    and is based using Mongoose object relational mapping.

    This is the most basic persistence component that is only
    able to store data items of any type. Specific CRUD operations
    over the data items must be implemented in child classes by
    accessing <code>this._collection</code> or <code>this._model</code> properties.

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

        - *:logger:*:*:1.0           (optional) ILogger components to pass log messages
        - *:discovery:*:*:1.0        (optional) IDiscovery services
        - *:credential-store:*:*:1.0 (optional) Credential stores to resolve credentials

    Example:
        class MyMongoDbPersistence(MongoDbPersistence):
            def __init__(self):
                super(MyMongoDbPersistence, self).__init__("mydata", MyData)

            def get_by_name(self, correlationId, name):
                item =  self._collection.find_one({ 'name': name })
                return item

            def set(self, correlationId, item):
                item = self._collection.find_one_and_update( \
                    { '_id': item.id }, { '$set': item }, \
                    return_document = pymongo.ReturnDocument.AFTER, \
                    upsert = True \
                    )

        persistence = MyMongoDbPersistence()
        persistence.configure(ConfigParams.from_tuples("host", "localhost", "port", 27017))

        persitence.open("123")

        persistence.set("123", { name: "ABC" })
        item = persistence.get_by_name("123", "ABC")

        print item
    """
    _default_config = ConfigParams.from_tuples(
        "collection", None,

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
    _logger = None
    _connection_resolver = None
    _options = None

    _database_name = None
    _collection_name = None
    _database = None
    _collection = None
    _client = None

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
        self._logger.configure(config)
        self._connection_resolver.configure(config)

        self._collection_name = config.get_as_string_with_default('collection', self._collection_name)
        self._options = self._options.override(config.get_section('options'))

    def set_references(self, references):
        """
        Sets references to dependent components.

        :param references: references to locate the component dependencies.
        """
        self._logger.set_references(references)
        self._connection_resolver.set_references(references)

    def _convert_to_public(self, value):
        """
        Converts object value from internal to public format.

        :param value: an object in internal format to convert.

        :return: converted object in public format.
        """
        if value == None: return None
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
        return self._client != None and self._database != None

    def open(self, correlation_id):
        """
        Opens the component.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        """
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
            kwargs = {
                'maxPoolSize': max_pool_size,
                'connectTimeoutMS': connect_timeout,
                'socketKeepAlive': keep_alive,
                'socketTimeoutMS': socket_timeout,
                'appname': correlation_id
            }
            kwargs = self.__del_none_objects(kwargs)
            self._client = pymongo.MongoClient(uri, **kwargs)

            self._database = self._client.get_database()

            self._collection = self._database.get_collection(self._collection_name)

        except Exception as ex:
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
