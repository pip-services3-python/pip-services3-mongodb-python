# -*- coding: utf-8 -*-
"""
    pip_services_mongodb.connect.MongoDbConnectionResolver
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    MongoDbConnectionResolver implementation

    :copyright: Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""
from pip_services_commons.config import IConfigurable, ConfigParams
from pip_services_commons.errors import ConfigException
from pip_services_commons.refer import IReferenceable
from pip_services_components.auth import CredentialResolver
from pip_services_components.connect import ConnectionResolver


class MongoDbConnectionResolver(IReferenceable, IConfigurable):
    _connection_resolver = ConnectionResolver()
    _credential_resolver = CredentialResolver()



    def configure(self, config):
        self._connection_resolver.configure(config)
        self._credential_resolver.configure(config)

    def set_references(self, references):
        self._connection_resolver.set_references(references)
        self._credential_resolver.set_references(references)

    def validate_connection(self, correlation_id, connection):
        uri = connection.get_uri()
        if uri == None:
            return None

        host = connection.get_host()
        if host == None:
            return ConfigException(correlation_id, "NO_HOST", "Connection host is not set")

        port = connection.get_port()
        if port == 0:
            return ConfigException(correlation_id, "NO_PORT", "Connection port is not set")

        database = connection.get_as_nullable_string("database")
        if database == None:
            return ConfigException(correlation_id, "NO_DATABASE", "Connection database is not set")

    def validate_connections(self, correlation_id, connections):
        if connections == None or len(connections) == 0:
            return ConfigException(correlation_id, "NO_CONNECTION", "Database connection is not set")

        for connection in connections:
            error = self.validate_connection(correlation_id, connection)

    def compose_uri(self, connections, credential):
        for connection in connections:
            uri = connection.get_uri()
            if uri != None:
                return uri

        hosts = ''
        for connection in connections:
            host = connection.get_host()
            port = connection.get_port()

            if len(hosts) > 0:
                hosts = hosts + ','
            hosts = hosts + host + (':' + str(port) if port != None else '')

        database = ''
        for connection in connections:
            database = connection.get_as_nullable_string("database") \
                if connection.get_as_nullable_string("database") != None \
                else database

            if len(database) > 0:
                database = '/' + database

        auth = ''
        if credential != None:
            username = credential.get_username()
            if username != None:
                password = credential.get_password()
                if password != None:
                    auth = username + ':' + password + '@'
                else:
                    auth = username + '@'

        options = ConfigParams()
        for connection in connections:
            options = options.override(connection)
        if credential != None:
            options = options.override(credential)

        options.remove("uri")
        options.remove("host")
        options.remove("port")
        options.remove("database")
        # options.remove("username")
        # options.remove("password")

        parameters = ''
        keys = options.get_key_names()
        for key in keys:
            if len(parameters) > 0:
                parameters += '&'

            parameters += key

            value = options.get_as_string(key)
            if value != None:
                parameters += '=' + value

        if len(parameters) > 0:
            parameters = '?' + parameters

        uri = "mongodb://" + auth + hosts + database + parameters

        return uri

    def resolve(self, correlation_id):
        connections = self._connection_resolver.resolve_all(correlation_id)
        credential = self._credential_resolver.lookup(correlation_id)

        self.validate_connections(correlation_id, connections)

        return self.compose_uri(connections, credential)





