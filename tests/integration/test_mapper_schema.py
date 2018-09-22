import importlib
import json
import logging
import sys
import textwrap

import pytest

from db_dump import MapperSchema, ColumnSchema
from examples.adjacency_list import adjacency_list
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

logger = logging.getLogger(__name__)

Base = declarative_base()


@pytest.fixture(params=["examples.association.basic_association", "examples.association.dict_of_sets_with_default.py"])
def model_fixture(request):
    module = importlib.import_module(request.param)
    logger.critical("module is %r", module)
    return module




class MyObj:
    pass


class Entity1(Base):
    __tablename__ = 'entity_1'
    id = Column(Integer, primary_key=True)


class Entity2(Base):
    __tablename__ = 'entity_2'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    entity1_id = Column(Integer, ForeignKey('entity_1.id'))
    entity1 = relationship('Entity1')


def test_dump_1():
    s = MapperSchema()
    logger.critical("mapper is %r", Entity1.__mapper__)
    d = s.dump(Entity1.__mapper__)

    assert 0 == len(d['relationships'])
    assert 1 == len(d['columns'])
    assert 1 == len(d['primary_key'])
    pk = d['primary_key'][0]
    assert 'id' is pk['column']
    assert 'entity_1' == pk['table']

    logger.critical("d is %r", d)

    assert 0


def test_dump_2():
    s = MapperSchema()
    d = s.dump(Entity2.__mapper__)
    print(textwrap.fill(repr(d), 120), file=sys.stderr)
    logger.critical("dump for Entity2 is %r", d)
    assert 1 == len(d['relationships'])
    logger.critical("type is %r", d['columns'][0]['type_'])
    assert 2 == len(d['columns'])

    assert 1 == len(d['primary_key'])
    pk = d['primary_key'][0]
    assert 'id' is pk['column']
    assert 'entity_2' == pk['table']


def test_column_schema():
    s = ColumnSchema()
    logger.critical("schema is %r", s)
    logger.critical("type field is %r", s._declared_fields['type_'])

    assert 0


def test_dump_column():
    s = ColumnSchema()
    d = s.dump(Entity2.__mapper__.columns.id)
    print(textwrap.fill(repr(d), 120), file=sys.stderr)
    assert d['name'] is 'id'
    assert d['table']['key'] == 'entity_2'

    assert 0


def test_1():
    mapper = adjacency_list.TreeNode.__mapper__
    s = MapperSchema()
    d = s.dump(mapper)
    print(textwrap.fill(repr(d), 120), file=sys.stderr)
    json.dump(d, indent=4, fp=sys.stderr)

    assert 0

@pytest.fixture(scope="session")
def tempdir_fixture():
    import tempfile
    return tempfile.mkdtemp()

def test_2(model_fixture, tempdir_fixture):
    import pathlib

    x = getattr(model_fixture, 'Base')
    m = list()
    for o in dir(model_fixture):
        y = getattr(model_fixture, o)
        if y is not x and isinstance(y, type) and issubclass(y, x):
            logger.critical("y = %s", repr(y))

            s = MapperSchema()
            m.append(s.dump(y.__mapper__))
            #print(repr(s.dump(y.__mapper__)), file=sys.stderr)

    print(textwrap.fill(repr(m), 120), file=sys.stderr)
    json.dump(m, fp=sys.stderr)
    assert 0




