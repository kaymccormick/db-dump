from unittest.mock import MagicMock

import pytest

from db_dump.schema import MapperSchema, TableColumnSpecSchema


@pytest.fixture
def mapper_schema():
    return MapperSchema()

@pytest.fixture
def mapper_primary_key_mock():
    return MagicMock()

@pytest.fixture
def table_column_spec_schema():
    return TableColumnSpecSchema()