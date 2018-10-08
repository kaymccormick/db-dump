import importlib
import logging



from marshmallow.fields import Field
import sys
from sqlalchemy.orm import Mapper

logger = logging.getLogger(__name__)


class TypeField(Field):
    def _serialize(self, value, attr, obj):
        logger.critical("serializing %r", value)
        if value is None:
            return None
        try:
            s = '%s.%s' % (value.__module__, value.__name__)
        except:
            s = repr(sys.exc_info()[1])
        return s
        #
        #
        # s = getattr(t, '_serialize', None)
        # if s:
        #     return s(self, value, attr, obj)
        # return super()._serialize(value, t, obj)

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


# class TypeField(Field):
#     def _serialize(self, value, attr, obj):
#         logger.critical("%s", self.name)
#         if value is None:
#             return None
#         t = type(value)
#         s = getattr(t, '_serialize', None)
#         if s:
#             return s(self, value, attr, obj)
#         return super()._serialize(value, t, obj)
#
#     def _deserialize(self, value, attr, data):
#         if isinstance(value, object):
#             return value
#         x = value.split('.')
#         name = x.pop(len(x) - 1)
#         package = x.pop(0)
#         try:
#             import sys
#             name_ = package + "." + ".".join(x)
#             if name_ in sys.modules:
#                 module = sys.modules[name_]
#             else:
#                 module = importlib.import_module('.'.join(x), package=package)
#         except ModuleNotFoundError:
#             return value
#
#         v = module.__dict__[name]
#         return v


class ArgumentField(TypeField):
    def _serialize(self, value, attr, obj):
        try:
            if callable(value):
                value = value()
            if isinstance(value, Mapper):
                value = value.entity
        except TypeError:
            pass

        try:
            return '.'.join((value.__module__, value.__name__,))
        except Exception as ex:
            return str(ex)
