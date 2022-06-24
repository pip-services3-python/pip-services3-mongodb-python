# -*- coding: utf-8 -*-
from typing import Any, Optional

import pymongo
from pip_services3_commons.config import ConfigParams
from pip_services3_commons.errors.ConnectionException import ConnectionException
from pip_services3_commons.refer import IReferenceable, IReferences
from pip_services3_commons.run.IOpenable import IOpenable
from pip_services3_components.log.CompositeLogger import CompositeLogger
from pymongo import database

from pip_services3_mongodb.connect.MongoDbConnectionResolver import MongoDbConnectionResolver


class MongoDbConnection(IReferenceable, IReferences, IOpenable):
    """
    MongoDB connection using plain driver.

    By defining a connection and sharing it through multiple persistence components
    you can reduce number of used database connections.

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
        - **\*:logger:\*:\*:1.0**           (optional)  :class:`ILogger <pip_services3_components.log.ILogger.ILogger>` components to pass log messages
        - **\*:discovery:\*:\*:1.0**        (optional)  :class:`IDiscovery <pip_services3_components.connect.IDiscovery.IDiscovery>` services
        - **\*:credential-store:\*:\*:1.0** (optional)  :class:`ICredentialStore <pip_services3_components.auth.ICredentialStore.ICredentialStore>` stores to resolve credentials
    """

    def __init__(self):
        """
        Creates a new instance of the connection component.
        """
        self.__default_config = ConfigParams.from_tuples(
            'options.max_pool_size', 2,
            'options.connect_timeout', 5000,
            'options.auto_reconnect', True,
            'options.max_page_size', 100,
            'options.debug', True
        )

        # The logger
        self._logger: CompositeLogger = CompositeLogger()
        # The connection resolver
        self._connection_resolver: MongoDbConnectionResolver = MongoDbConnectionResolver()
        # The configuration options.
        self._options: ConfigParams = ConfigParams()
        # The MongoDB connection object.
        self._connection: pymongo.MongoClient = None
        # The MongoDB database name.
        self._database_name: str = None
        # The MongoDb database object.
        self._db: database.Database = None

    def configure(self, config: ConfigParams):
        """
        Configures component by passing configuration parameters.

        :param config: configuration parameters to be set.
        """
        config = config.set_defaults(self.__default_config)
        self._connection_resolver.configure(config)
        self._options = self._options.override(config.get_section('options'))

    def set_references(self, references: IReferences):
        """
        Sets references to dependent components.

        :param references:  references to locate the component dependencies.
        """
        self._logger.set_references(references)
        self._connection_resolver.set_references(references)

    def is_open(self) -> bool:
        """
        Checks if the component is opened.

        :return: true if the component has been opened and false otherwise.
        """
        return self._connection is not None

    def __compose_settings(self) -> Any:
        max_pool_size = self._options.get_as_nullable_string('max_pool_size')
        connection_timeout_ms = self._options.get_as_nullable_integer('connect_timeout')
        socket_timeout_ms = self._options.get_as_nullable_integer('socket_timeout')
        auto_reconnect = self._options.get_as_nullable_boolean('auto_reconnect')
        reconnect_interval = self._options.get_as_nullable_integer('reconnect_interval')
        debug = self._options.get_as_nullable_boolean('debug')

        ssl = self._options.get_as_nullable_boolean('ssl')
        replica_set = self._options.get_as_nullable_string('replica_set')
        auth_source = self._options.get_as_nullable_string('auth_source')
        auth_user = self._options.get_as_nullable_string('auth_user')
        auth_password = self._options.get_as_nullable_string('auth_password')

        settings = {
            'maxPoolSize': max_pool_size,
            'connectTimeoutMS': connection_timeout_ms,
            'socketTimeoutMS': socket_timeout_ms,
        }

        if ssl is not None:
            settings['ssl'] = ssl
        if replica_set is not None:
            settings['replica_set'] = replica_set
        if auth_source is not None:
            settings['auth_source'] = auth_source
        if auth_user is not None:
            settings['auth.user'] = auth_user
        if auth_password is not None:
            settings['auth.password'] = auth_password

        return settings

    def open(self, correlation_id: Optional[str]):
        """
        Opens the component.

        :param correlation_id: (optional) transaction id to trace execution through call chain.
        """
        self._logger.debug(correlation_id, 'Connecting to mongodb')

        try:
            settings = self.__compose_settings()

            # settings['use_new_url_parser'] = True
            # settings['use_undefined_topology'] = True
            settings['appname'] = correlation_id

            uri = self._connection_resolver.resolve(correlation_id)
            settings = self.__del_none_objects(settings)
            client = pymongo.MongoClient(uri, **settings)
            self._connection = client
            self._db = client.get_database()
            self._database_name = self._db.name
        except Exception as ex:
            raise ConnectionException(correlation_id, 'CONNECT_FAILED', 'Connection to mongodb failed').with_cause(ex)

    def __del_none_objects(self, settings: dict):
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
        if self._connection is None:
            return

        try:
            self._connection.close()
            self._connection = None
            self._db = None
            self._database_name = None
            self._logger.debug(correlation_id, 'Disconnected from mongodb database {}'.format(self._database_name))
        except Exception as ex:
            raise ConnectionException(correlation_id, 'DISCONNECT_FAILED',
                                      'Disconnect from mongodb failed: ').with_cause(ex)

    def get_connection(self) -> pymongo.MongoClient:
        return self._connection

    def get_database(self) -> database.Database:
        return self._db

    def get_database_name(self) -> str:
        return self._database_name
