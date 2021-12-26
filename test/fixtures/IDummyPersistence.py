# -*- coding: utf-8 -*-
"""
    test.IDummyPersistence
    ~~~~~~~~~~~~~~~~~~~~~~
    
    Interface for dummy persistence components
    
    :copyright: Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""
from typing import Optional, List

from pip_services3_commons.data import FilterParams, PagingParams, DataPage, AnyValueMap
from pip_services3_data import IGetter, IWriter, IPartialUpdater

from test.fixtures.Dummy import Dummy


class IDummyPersistence(IGetter, IWriter, IPartialUpdater):

    def get_page_by_filter(self, correlation_id: Optional[str], filter: Optional[FilterParams], paging: Optional[PagingParams]) -> DataPage:
        raise NotImplementedError('Method from interface definition')

    def get_count_by_filter(self, correlation_id: Optional[str], filter: Optional[FilterParams]) -> int:
        raise NotImplementedError('Method from interface definition')

    def get_one_by_id(self, correlation_id: Optional[str], id: str) -> Dummy:
        raise NotImplementedError('Method from interface definition')

    def get_list_by_ids(self, correlation_id: Optional[str], ids: List[str]) -> List[Dummy]:
        raise NotImplementedError('Method from interface definition')

    def create(self, correlation_id: Optional[str], entity: Dummy) -> Dummy:
        raise NotImplementedError('Method from interface definition')

    def update(self, correlation_id: Optional[str], entity) -> Dummy:
        raise NotImplementedError('Method from interface definition')

    def update_partially(self, correlation_id: Optional[str], id: str, data: AnyValueMap) -> Dummy:
        raise NotImplementedError('Method from interface definition')

    def delete_by_id(self, correlation_id: Optional[str], id: str) -> Dummy:
        raise NotImplementedError('Method from interface definition')

    def delete_by_ids(self, correlation_id: Optional[str], ids: List[str]):
        raise NotImplementedError('Method from interface definition')
