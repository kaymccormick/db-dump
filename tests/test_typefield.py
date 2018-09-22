import logging
import sys

from db_dump import TypeField
from marshmallow import Schema

logger = logging.getLogger(__name__)


class MySchema(Schema):
    f = TypeField(attribute='field_value')


def test_typefield_schema_dump():
    class FieldClass:
        def __init__(self, field_value) -> None:
            super().__init__()
            self.field_value = field_value

    f = FieldClass(type(object))
    s = MySchema()
    d = s.dump(f)

    logger.critical("d is %r", d)
    assert 0


def test_typefield_schema():
    d = dict(f=type(object))
    s = MySchema()
    d2 = s.load(d)
    logger.critical("d2 = %r", d2)
    assert 0


def test_typefield_1():
    field = TypeField()
    s = field.serialize(int, 'type', None)
    print(s, file=sys.stderr)
    assert 0
