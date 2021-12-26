# -*- coding: utf-8 -*-
"""
    tests.DummyPersistenceFixture
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) Conceptual Vision Consulting LLC 2015-2016, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""

from pip_services3_commons.data import AnyValueMap

from .Dummy import Dummy
from .IDummyPersistence import IDummyPersistence

DUMMY1 = Dummy(None, 'Key 1', 'Content 1')
DUMMY2 = Dummy(None, 'Key 2', 'Content 2')


class DummyPersistenceFixture:
    _persistence = None

    def __init__(self, persistence: IDummyPersistence):
        self._persistence: IDummyPersistence = persistence

    def test_crud_operations(self):
        # Create one dummy
        dummy1 = self._persistence.create(None, DUMMY1)

        assert dummy1 is not None
        assert dummy1.id is not None
        assert DUMMY1.key == dummy1.key
        assert DUMMY1.content == dummy1.content

        # Create another dummy
        dummy2 = self._persistence.create(None, DUMMY2)

        assert dummy2 is not None
        assert dummy2.id is not None
        assert DUMMY2.key == dummy2.key
        assert DUMMY2.content == dummy2.content

        # Get all dummies
        dummies = self._persistence.get_page_by_filter(None, None, None)
        assert dummies is not None
        assert 2 == len(dummies.data)

        # Update the dummy
        dummy1.content = "Updated Content 1"
        result = self._persistence.update(
            None,
            dummy1
        )

        assert result is not None
        assert dummy1.id == result.id
        assert dummy1.key == result.key
        assert dummy1.content == result.content

        # Partially update the dummy
        result = self._persistence.update_partially(
            None,
            dummy1.id,
            AnyValueMap.from_tuples(
                'content', 'Partially Updated Content 1'
            )
        )

        assert result is not None
        assert dummy1.id == result.id
        assert dummy1.key == result.key
        assert "Partially Updated Content 1" == result.content

        # Get the dummy by Id
        result = self._persistence.get_one_by_id(None, dummy1.id)
        assert result is not None
        assert result.id == dummy1.id
        assert result.key == dummy1.key
        assert 'Partially Updated Content 1' == result.content

        # Delete the dummy
        self._persistence.delete_by_id(None, dummy1.id)
        assert result is not None
        assert result.id == dummy1.id
        assert result.key == dummy1.key
        assert 'Partially Updated Content 1' == result.content

        # Try to get deleted dummy
        result = self._persistence.get_one_by_id(None, dummy1.id)
        assert result is None

        count = self._persistence.get_count_by_filter(None, None)
        assert count == 1

    def test_batch_operations(self):
        # Create one dummy
        dummy1 = self._persistence.create(None, DUMMY1)
        assert dummy1 is not None
        assert dummy1.id is not None
        assert DUMMY1.key == dummy1.key
        assert DUMMY1.content == dummy1.content

        # Create one dummy
        dummy2 = self._persistence.create(None, DUMMY2)

        assert dummy2 is not None
        assert dummy2.id is not None
        assert DUMMY2.key == dummy2.key
        assert DUMMY2.content == dummy2.content

        # Read batch
        dummies = self._persistence.get_list_by_ids(None, [dummy1.id, dummy2.id])
        assert isinstance(dummies, list)
        assert 2 == len(dummies)

        # Delete batch
        self._persistence.delete_by_ids(None, [dummy1.id, dummy2.id])

        # Read empty batch
        dummies = self._persistence.get_list_by_ids(None, [dummy1.id, dummy2.id])
        assert isinstance(dummies, list)
        assert 0 == len(dummies)
