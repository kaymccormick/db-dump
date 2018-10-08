from db_dump.model import Child
import logging

logger = logging.getLogger(__name__)


class MyMeta(type):
    def __new__(cls, name, bases, dict):
        return super().__new__(cls, name, bases, dict)



class Entity(metaclass=MyMeta):
    def __init__(self, identifier, *args, **kwargs):
        self.id = identifier
        if hasattr(self.id, '__mapper__'):
            mapper = self.id.__mapper__
            logger.critical("%r", mapper)


def test_mapper_info():
    entity = Entity(Child)
    assert 0, '%r' % entity
