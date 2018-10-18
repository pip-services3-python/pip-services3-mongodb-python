# -*- coding: utf-8 -*-
"""
    pip_services_mongodb.persistence.MongoDbPersistence
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    MongoDb persistence implementation
    
    :copyright: Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""

import threading
import pymongo

from pip_services_commons.config import ConfigParams, IConfigurable
from pip_services_commons.refer import IReferenceable
from pip_services_commons.run import IOpenable, ICleanable
from pip_services_components.log import CompositeLogger
from pip_services_commons.errors import ConnectionException
from ..connect.MongoDbConnectionResolver import MongoDbConnectionResolver

class MongoDbPersistence(IReferenceable, IConfigurable, IOpenable, ICleanable):
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

    def __init__(self, collection = None):
        self._lock = threading.Lock()
        self._logger = CompositeLogger()
        self._connection_resolver = MongoDbConnectionResolver()
        self._options = ConfigParams()

        self._collection_name = collection

    def configure(self, config):
        config = config.set_defaults(self._default_config)
        self._logger.configure(config)
        self._connection_resolver.configure(config)

        self._collection_name = config.get_as_string_with_default('collection', self._collection_name)
        self._options = self._options.override(config.get_section('options'))

    def set_references(self, references):
        self._logger.set_references(references)
        self._connection_resolver.set_references(references)

    def _convert_to_public(self, value):
        if value == None: return None
        value['id'] = value['_id']
        value.pop('_id', None)
        return value


    def _convert_from_public(self, value):
        return value


    def is_opened(self):
        return self._client != None and self._database != None

    def open(self, correlation_id):
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
            self._client = pymongo.MongoClient(uri, **kwargs)

            self._database = self._client.get_database()

            self._collection = self._database.get_collection(self._collection_name)

        except Exception as ex:
            raise ConnectionException(correlation_id, "CONNECT_FAILED", "Connection to mongodb failed") \
                .with_cause(ex)


    def close(self, correlation_id):
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
        if self._collection_name == None:
            raise Exception("Collection name is not defined")

        self._database.drop_collection(self._collection_name)