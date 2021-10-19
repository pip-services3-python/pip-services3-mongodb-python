# -*- coding: utf-8 -*-
"""
    pip_services3_mongodb.connect.MongoDbConnectionResolver
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    MongoDbConnectionResolver implementation.

    :copyright: Conceptual Vision Consulting LLC 2018-2019, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""
from typing import Optional, List

from pip_services3_commons.config import IConfigurable, ConfigParams
from pip_services3_commons.errors import ConfigException
from pip_services3_commons.refer import IReferenceable, IReferences
from pip_services3_components.auth import CredentialResolver, CredentialParams
from pip_services3_components.connect import ConnectionResolver, ConnectionParams


class MongoDbConnectionResolver(IReferenceable, IConfigurable):
    """
    MongoDbConnectionResolver implementation.
    Helper class that resolves MongoDB connection
    and credential parameters, validates them and generates a connection URI.

    It is able to process multiple connections to MongoDB cluster nodes.

    ### Configuration parameters ###
        - connection(s):
            - discovery_key:               (optional) a key to retrieve the connection from IDiscovery
            - host:                        host name or IP address
            - port:                        port number (default: 27017)
            - database:                    database name
            - uri:                         resource URI or connection string with all parameters in it
        - credential(s):
            - store_key:                   (optional) a key to retrieve the credentials from ICredentialStore
            - username:                    user name
            - password:                    user password

    ### References ###
        - `*:discovery:*:*:1.0`             (optional) :class:`IDiscovery <pip_services3_components.connect.IDiscovery.IDiscovery>` services
        - `*:credential-store:*:*:1.0`      (optional) :class:`ICredentialStore <pip_services3_components.auth.ICredentialStore.ICredentialStore>` stores to resolve credentials
    """

    def __init__(self):
        self._connection_resolver: ConnectionResolver = ConnectionResolver()
        self._credential_resolver: CredentialResolver = CredentialResolver()

    def configure(self, config: ConfigParams):
        """
        Configures component by passing configuration parameters.

        :param config: configuration parameters to be set.
        """
        self._connection_resolver.configure(config)
        self._credential_resolver.configure(config)

    def set_references(self, references: IReferences):
        """
        Sets references to dependent components.

        :param references: references to locate the component dependencies.
        """
        self._connection_resolver.set_references(references)
        self._credential_resolver.set_references(references)

    def __validate_connection(self, correlation_id: Optional[str], connection: ConnectionParams):
        uri = connection.get_uri()
        if uri is None:
            return None

        host = connection.get_host()
        if host is None:
            return ConfigException(correlation_id, "NO_HOST", "Connection host is not set")

        port = connection.get_port()
        if port == 0:
            return ConfigException(correlation_id, "NO_PORT", "Connection port is not set")

        database = connection.get_as_nullable_string("database")
        if database is None:
            return ConfigException(correlation_id, "NO_DATABASE", "Connection database is not set")

    def __validate_connections(self, correlation_id: Optional[str], connections: List[ConnectionParams]):
        if connections is None or len(connections) == 0:
            return ConfigException(correlation_id, "NO_CONNECTION", "Database connection is not set")

        for connection in connections:
            error = self.__validate_connection(correlation_id, connection)

    def __compose_uri(self, connections: List[ConnectionParams], credential: CredentialParams) -> str:
        for connection in connections:
            uri = connection.get_uri()
            if uri:
                return uri

        hosts = ''
        for connection in connections:
            host = connection.get_host()
            port = connection.get_port()

            if len(hosts) > 0:
                hosts = hosts + ','
            hosts = hosts + host + (':' + str(port) if port is not None else '')

        database = ''
        for connection in connections:
            database = connection.get_as_nullable_string("database") \
                if connection.get_as_nullable_string("database") is not None \
                else database

            if len(database) > 0:
                database = '/' + database

        auth = ''
        if credential is not None:
            username = credential.get_username()
            if username is not None:
                password = credential.get_password()
                if password is not None:
                    auth = username + ':' + password + '@'
                else:
                    auth = username + '@'

        options = ConfigParams()
        for connection in connections:
            options = options.override(connection)
        if not (credential is None):
            options = options.override(credential)

        options.remove("uri")
        options.remove("host")
        options.remove("port")
        options.remove("database")
        options.remove("username")
        options.remove("password")

        parameters = ''
        keys = options.get_keys()
        for key in keys:
            if len(parameters) > 0:
                parameters += '&'

            parameters += key

            value = options.get_as_string(key)
            if value is not None:
                parameters += '=' + value

        if len(parameters) > 0:
            parameters = '?' + parameters

        uri = "mongodb://" + auth + hosts + database + parameters

        return uri

    def resolve(self, correlation_id: Optional[str]) -> str:
        """
        Resolves MongoDB connection URI from connection and credential parameters.

        :param correlation_id: (optional) transaction id to trace execution through call chain.

        :return: a resolved URI
        """
        connections = self._connection_resolver.resolve_all(correlation_id)
        credential = self._credential_resolver.lookup(correlation_id)

        self.__validate_connections(correlation_id, connections)

        return self.__compose_uri(connections, credential)
