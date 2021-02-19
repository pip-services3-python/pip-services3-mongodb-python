# -*- coding: utf-8 -*-

import os

from pip_services3_commons.config import ConfigParams

from pip_services3_mongodb.persistence.MongoDbConnection import MongoDbConnection


class TestDbConnection:
    persistence = None
    fixture = None

    connection = None

    mongoUri = os.getenv('MONGO_URI')
    mongoHost = os.getenv('MONGO_HOST') if os.getenv('MONGO_HOST') != None else 'localhost'
    mongoPort = os.getenv('MONGO_PORT') if os.getenv('MONGO_PORT') != None else 27017
    mongoDatabase = os.getenv('MONGO_DB') if os.getenv('MONGO_DB') != None else 'test'

    @classmethod
    def setup_class(cls):
        if cls.mongoUri is None and cls.mongoHost is None:
            return

        db_config = ConfigParams.from_tuples('connection.uri', cls.mongoUri,
                                             'connection.host', cls.mongoHost,
                                             'connection.port', cls.mongoPort,
                                             'connection.database', cls.mongoDatabase)
        cls.connection = MongoDbConnection()
        cls.connection.configure(db_config)
        cls.connection.open(None)

    @classmethod
    def teardown_class(cls):
        cls.connection.close(None)

    def test_open_and_close(self):
        assert hasattr(self.connection.get_connection(), '__iter__')
        assert hasattr(self.connection.get_database(), '__iter__')
        assert type(self.connection.get_database_name()) == str
