# -*- coding: utf-8 -*-
"""
    pip_services3_mongodb.build.DefaultMongoDbFactory
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from pip_services3_components.build.Factory import Factory
from pip_services3_commons.refer.Descriptor import Descriptor

from ..persistence.MongoDbConnection import MongoDbConnection


class DefaultMongoDbFactory(Factory):
    """
    Creates MongoDb components by their descriptors.
    See :class:`Factory <pip_services3_components.build.Factory.Factory>`, :class:`MongoDbConnection <pip_services3_mongodb.persistence.MongoDbConnection.MongoDbConnection>`
    """
    __descriptor = Descriptor("pip-services", "factory", "rpc", "default", "1.0")
    __mongo_db_connection_descriptor = Descriptor("pip-services", "connection", "mongodb", "*", "1.0")

    def __init__(self):
        """
        Create a new instance of the factory.
        """
        super(DefaultMongoDbFactory, self).__init__()
        self.register_as_type(DefaultMongoDbFactory.mongo_db_connection_descriptor, MongoDbConnection)

    @property
    def mongo_db_connection_descriptor(self):
        return self.__mongo_db_connection_descriptor

    @property
    def descriptor(self):
        return self.__descriptor
