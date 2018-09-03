import logging
import importlib

from sqlalchemy.orm import Mapper

from marshmallow.fields import Field, Nested

logger = logging.getLogger(__name__)

class TypeField(Field):
    def _serialize(self, value, attr, obj):
        return '.'.join((value.__module__, value.__name__,))
    def _deserialize(self, value, attr, data):
        x = value.split('.')
        name = x.pop(len(x) - 1)
        module = importlib.import_module('.'.join(x))
        v = module.__dict__[name]
        return v


class ArgumentField(TypeField):
    def _serialize(self, value, attr, obj):
        if callable(value):
            value = value()
        if isinstance(value, Mapper):
            value = value.entity

        return '.'.join((value.__module__, value.__name__,))


