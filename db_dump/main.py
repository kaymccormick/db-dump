import importlib
import json
import sys

import plaster
from plaster import setup_logging
from sqlalchemy import inspect, Table, engine_from_config
import logging
import argparse

from sqlalchemy.dialects.postgresql.base import PGInspector
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import base, DeclarativeMeta
from sqlalchemy.orm import Mapper

from db_dump.events import handle_after_create, handle_mapper_configured, mappers
#from db_dump.model import Test1, Base

from zope.component.hooks import setSite, getSiteManager

from db_dump import FooImpl, IFoo, Site, MapperProcessor, IProcessor, TableProcessor, TableImpl, register_components, \
    process_mapper
from db_dump.info import MapperInfo
from db_dump.process import setup_jsonencoder

logger = logging.getLogger(__name__)


def get_engine(settings, prefix='sqlalchemy.'):
    return engine_from_config(settings, prefix)


def handle_parent_attach(target, parent):
    logger.debug("handle_parent_attach: %s, %s", target, parent)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config_uri')
    parser.add_argument("--create-schema", help="create the database schema",
                        action="store_true")
    parser.add_argument("--model", required=True)
    (args, remain) = parser.parse_known_args(sys.argv[1:])
    config_uri = args.config_uri
    settings = plaster.get_settings(config_uri, section='db_dump')

    setup_logging(config_uri)
    logger.debug("Settings = %s", repr(settings))

    model_module = importlib.import_module(args.model)


    #logger.debug("base = %s", Base)
    base = None


    set_site()
    registry = getSiteManager()
    register_components(registry)

    listen(Mapper, 'mapper_configured', handle_mapper_configured)
    listen(Table, 'after_parent_attach', handle_parent_attach)
    listen(Table, 'after_create', handle_after_create)
    engine = get_engine(settings)

    for k,v in model_module.__dict__.items():
        if k == "Base":
            logger.debug("hi")

        if isinstance(v, type) and isinstance(v, DeclarativeMeta):
            logger.debug("! %s=%s", k, v)
            if hasattr(v, '__tablename__'):
                logger.debug("! %s=%s", k, v)
                myo = v()
                logger.debug("my o is %s", myo)
            else:
                base = v

    if args.create_schema:
        logger.info("Creating database schema")
        base.metadata.create_all(engine)

    (setup_jsonencoder())()

    for k, v in mappers.items():
        v: MapperInfo
        print(v.to_json())

    inspect1 = inspect(engine) # type: PGInspector
    logger.debug("inspect1 = %s", inspect1)
    for x in inspect1.get_table_names():
        logger.debug("x=%s", x)


    # registry.registerAdapter(MapperProcessor)
    # registry.registerAdapter(TableProcessor)

    # t = TableImpl()
    # adapter = registry.queryAdapter(t, IProcessor)
    # p = adapter.process()
    # logger.debug("process is %s", p)

#    logger.debug("adapter is %s", adapter)

    #registry.queryAdapter()

    foo = FooImpl()

    registry.registerUtility(foo, IFoo, 'foo')
    utility = registry.getUtility(IFoo, 'foo')
    print(utility.foo())


def set_site():
    setSite(Site())
