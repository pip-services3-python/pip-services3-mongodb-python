# -*- coding: utf-8 -*-
"""
    tests.persistence.test_DummyMongoDbPersistence
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    :copyright: (c) Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""

import os

from pip_services3_commons.config import ConfigParams

from .DummyMongoDbPersistence import DummyMongoDbPersistence
from ..DummyPersistenceFixture import DummyPersistenceFixture


class TestDummyMongoDbPersistence:
    persistence = None
    fixture = None

    mongoUri = os.getenv('MONGO_URI')
    mongoHost = os.getenv('MONGO_HOST') if os.getenv('MONGO_HOST') else 'localhost'
    mongoPort = os.getenv('MONGO_PORT') if os.getenv('MONGO_PORT') else 27017
    mongoDatabase = os.getenv('MONGO_DB') if os.getenv('MONGO_DB') else 'test'

    @classmethod
    def setup_class(cls):
        if cls.mongoUri is None and cls.mongoHost is None:
            return

        db_config = ConfigParams.from_tuples('connection.uri', cls.mongoUri,
                                             'connection.host', cls.mongoHost,
                                             'connection.port', cls.mongoPort,
                                             'connection.database', cls.mongoDatabase)
        cls.persistence = DummyMongoDbPersistence()
        cls.fixture = DummyPersistenceFixture(cls.persistence)

        cls.persistence.configure(db_config)
        cls.persistence.open(None)

    @classmethod
    def teardown_class(cls):
        cls.persistence.close(None)

    def setup_method(self, method):
        self.persistence.clear(None)

    def test_crud_operations(self):
        self.fixture.test_crud_operations()

    def test_batch_operations(self):
        self.fixture.test_batch_operations()
