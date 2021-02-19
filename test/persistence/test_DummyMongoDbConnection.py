# -*- coding: utf-8 -*-

import os

from pip_services3_commons.config.ConfigParams import ConfigParams
from pip_services3_commons.refer.Descriptor import Descriptor
from pip_services3_commons.refer.References import References

from pip_services3_mongodb.persistence.MongoDbConnection import MongoDbConnection
from .DummyMongoDbPersistence import DummyMongoDbPersistence
from ..DummyPersistenceFixture import DummyPersistenceFixture


class TestDummyMongoDbConnection:
    persistence = None
    fixture = None

    connection = None

    mongoUri = os.getenv('MONGO_URI')
    mongoHost = os.getenv('MONGO_HOST') if os.getenv('MONGO_HOST') != None else 'localhost'
    mongoPort = os.getenv('MONGO_PORT') if os.getenv('MONGO_PORT') != None else 27017
    mongoDatabase = os.getenv('MONGO_DB') if os.getenv('MONGO_DB') != None else 'test'

    def setup_class(cls):
        if cls.mongoUri is None and cls.mongoHost is None:
            return

        db_config = ConfigParams.from_tuples('connection.uri', cls.mongoUri,
                                             'connection.host', cls.mongoHost,
                                             'connection.port', cls.mongoPort,
                                             'connection.database', cls.mongoDatabase)
        cls.connection = MongoDbConnection()
        cls.connection.configure(db_config)
        cls.persistence = DummyMongoDbPersistence()
        cls.persistence.set_references(References.from_tuples(
            Descriptor("pip-services", "connection", "mongodb", "default", "1.0"), cls.connection
        ))
        cls.fixture = DummyPersistenceFixture(cls.persistence)
        cls.connection.open(None)
        cls.persistence.open(None)
        cls.persistence.clear(None)

    @classmethod
    def teardown_class(cls):
        cls.connection.close(None)
        cls.persistence.close(None)

    def test_crud_operations(self):
        self.fixture.test_crud_operations()

    def test_batch_operations(self):
        self.fixture.test_batch_operations()
