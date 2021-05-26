# -*- coding: utf-8 -*-
"""
    test.IDummyPersistence
    ~~~~~~~~~~~~~~~~~~~~~~
    
    Interface for dummy persistence components
    
    :copyright: Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""

from pip_services3_data import IGetter, IWriter, IPartialUpdater


class IDummyPersistence(IGetter, IWriter, IPartialUpdater):

    def get_page_by_filter(self, correlation_id, filter, paging):
        raise NotImplementedError('Method from interface definition')

    def get_one_by_id(self, correlation_id, id):
        raise NotImplementedError('Method from interface definition')

    def create(self, correlation_id, entity):
        raise NotImplementedError('Method from interface definition')

    def update(self, correlation_id, entity):
        raise NotImplementedError('Method from interface definition')

    def update_partially(self, correlation_id, id, data):
        raise NotImplementedError('Method from interface definition')

    def delete_by_id(self, correlation_id, id):
        raise NotImplementedError('Method from interface definition')
