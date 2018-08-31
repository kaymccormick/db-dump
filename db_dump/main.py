import sys

import plaster
from plaster import setup_logging
from sqlalchemy import create_engine, inspect
import logging
import argparse

from sqlalchemy.dialects.postgresql.base import PGInspector
from sqlalchemy.event import listen
from sqlalchemy.orm import Mapper
from zope import component

import db_dump.model
from db_dump import FooImpl, IFoo
from db_dump.registry import Registry

logger = logging.getLogger(__name__)


def handle_mapper_configured(mapper: Mapper):
    logger.debug("handle_mapper_configured: %s", mapper)



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('config_uri')
    args = parser.parse_args(sys.argv[1:])

    config_uri = args.config_uri
    settings = plaster.get_settings(config_uri, section='db_dump')
    setup_logging(config_uri)
    logger.debug("Settings = %s", repr(settings))

    listen(Mapper, 'mapper_configured', handle_mapper_configured)
    engine = create_engine(settings.get('sqlalchemy.url'))

    inspect1 = inspect(engine) # type: PGInspector
    logger.debug("inspect1 = %s", inspect1)

    registry = Registry()

    foo = FooImpl()

    registry.registerUtility(foo, IFoo, 'foo')
    utility = registry.getUtility(IFoo, 'foo')
    print(utility.foo())
