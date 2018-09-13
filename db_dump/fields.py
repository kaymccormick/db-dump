import logging
import importlib

from sqlalchemy.orm import Mapper

from marshmallow.fields import Field, Nested

logger = logging.getLogger(__name__)

class TypeField(Field):
    def _serialize(self, value, attr, obj):
        logger.critical("%s", self.name)
        if value is None:
            return None
        t = type(value)
        s = getattr(t, '_serialize', None)
        if s:
            return s(self, value, attr, obj)
        return super()._serialize(value, t, obj)

    def _deserialize(self, value, attr, data):
        if isinstance(value, object):
            return value
        x = value.split('.')
        name = x.pop(len(x) - 1)
        package = x.pop(0)
        try:
            import sys
            name_ = package + "." + ".".join(x)
            if name_ in sys.modules:
                module = sys.modules[name_]
            else:
                module = importlib.import_module('.'.join(x), package=package)
        except ModuleNotFoundError:
            return value

        v = module.__dict__[name]
        return v


class ArgumentField(TypeField):
    def _serialize(self, value, attr, obj):
        if callable(value):
            value = value()
        if isinstance(value, Mapper):
            value = value.entity

        return '.'.join((value.__module__, value.__name__,))


