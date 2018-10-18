# -*- coding: utf-8 -*-
"""
    tests.DummyPersistenceFixture
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    :copyright: (c) Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""

from .Dummy import Dummy
from pip_services_commons.data import AnyValueMap

DUMMY1 = Dummy(None, 'Key 1', 'Content 1')
DUMMY2 = Dummy(None, 'Key 2', 'Content 2')

class DummyPersistenceFixture:
    
    _persistence = None

    def __init__(self, persistence):
        self._persistence = persistence

    def test_crud_operations(self):
        # Create one dummy
        dummy1 = self._persistence.create(None, DUMMY1)

        assert dummy1 != None
        assert dummy1['id'] != None
        assert DUMMY1['key'] == dummy1['key']
        assert DUMMY1['content'] == dummy1['content']

        # Create another dummy
        dummy2 = self._persistence.create(None, DUMMY2)

        assert dummy2 != None
        assert dummy2['id'] != None
        assert DUMMY2['key'] == dummy2['key']
        assert DUMMY2['content'] == dummy2['content']

        # Get all dummies
        dummies = self._persistence.get_page_by_filter(None, None, None)
        assert dummies != None
        assert 2 == len(dummies.data)

        # Update the dummy
        dummy1['content'] = "Updated Content 1";
        dummy = self._persistence.update(
            None,
            dummy1
        )

        # Partially update the dummy
        dummy = self._persistence.update_partially(
            None,
            dummy1['id'],
            AnyValueMap.from_tuples(
                'content', 'Partually Updated Content 1'
            )
        )

        assert dummy != None
        assert dummy1['id'] == dummy['id']
        assert dummy1['key'] == dummy['key']
        assert "Partually Updated Content 1" == dummy['content']

        # Delete the dummy
        self._persistence.delete_by_id(None, dummy1['id'])

        # Try to get deleted dummy
        dummy = self._persistence.get_one_by_id(None, dummy1['id'])
        assert dummy == None


    def test_batch_operations(self):
        # Create dummies
        dummy1 = self._persistence.create(None, DUMMY1)
        dummy2 = self._persistence.create(None, DUMMY2)

        # Get dummies
        dummies = self._persistence.get_list_by_ids(None, [ dummy1['id'], dummy2['id'] ])
        assert dummies != None
        assert 2 == len(dummies)

        # Delete
        self._persistence.delete_by_ids(None, [ dummy1['id'], dummy2['id'] ])

        # Try to get deleted dummies
        dummies = self._persistence.get_list_by_ids(None, [ dummy1['id'], dummy2['id'] ])
        assert dummies != None
        assert 0 == len(dummies)
