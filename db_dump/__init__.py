import logging
from typing import NewType, Mapping, AnyStr

from sqlalchemy import Table
from sqlalchemy.orm import Mapper
from zope import component
from zope.component import adapter
from zope.interface import implementer, Interface, Attribute
from zope.interface.registry import Components

from db_dump.process import process_mapper

logger = logging.getLogger(__name__)


class IFoo(Interface):
    def foo(self):
        pass
    pass

@implementer(IFoo)
class FooImpl:
    def foo(self):
        return 'foo'
    pass


MapperResultKey = AnyStr
MapperResultValue = Mapping[AnyStr, dict]
MapperProcessorResult = Mapping[MapperResultKey, MapperResultValue]


class IMapper(Interface):
    def mapper():
        "return a mapper"



class IProcessor(Interface):
    def process():
        ""


@adapter(IMapper)
@implementer(IProcessor)
class MapperProcessor:
    def __init__(self, imapper: IMapper) -> None:
        self.imapper = imapper

    def process(self):
        return process_mapper(self.imapper.mapper())


class Site:
    def __init__(self):
        self.registry = Components('components')

    def getSiteManager(self):
        return self.registry


class ISchemaItem(Interface):
    __visit_name__ = Attribute('__visit__name')


class ITable(Interface):
    pass


@implementer(ITable)
class TableImpl:
    def __init__(self) -> None:
        pass


@implementer(IMapper)
class MyMapper:
    def __init__(self, mapper: Mapper) -> None:
        logger.info("inMyMapper init I am a mapper! %s", mapper)
        self._mapper = mapper

    def mapper(self):
        return self._mapper


@adapter(ITable)
@implementer(IProcessor)
class TableProcessor:
    def __init__(self, table):
        self.table = table

    def process(self):
        return {}

# @adapter(IMapper)
# @implementer(IProcessor)
# class MapperProcessor:
#     def __init__(self, mapper) -> None:
#         self.mapper = mapper
#
#     def process(self):
#         return {}

    # def process_mapper(self, mapper: Mapper) -> MapperProcessorResult:
    #     pass


def register_components(components: Components):
#    logger.critical("REGISTERING COMPONENTS")
#    logger.info("adapted = %s", component.adaptedBy(MapperProcessor))
    components.registerAdapter(MapperProcessor)
#    result = IProcessor(MyMapper(None)).process()
    #components.registerAdapter(TableProcessor)
