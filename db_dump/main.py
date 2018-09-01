import importlib
import sys

import plaster
from plaster import setup_logging
from sqlalchemy import inspect, Table, engine_from_config
import logging
import argparse

from sqlalchemy.dialects.postgresql.base import PGInspector
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Mapper

from db_dump.args import OptionAction
from db_dump.events import handle_after_create, handle_mapper_configured
#from db_dump.model import Test1, Base

from zope.component.hooks import setSite, getSiteManager

from db_dump import Site, register_components
from db_dump.process import setup_jsonencoder, process_info, ProcessInfo

logger = logging.getLogger(__name__)


def get_engine(settings, prefix='sqlalchemy.'):
    return engine_from_config(settings, prefix)


def handle_parent_attach(target, parent):
    logger.debug("handle_parent_attach: %s (%s), %s", target, type(target), parent)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--load', action="store_true")
    parser.add_argument('--path', action="append")
    parser.add_argument('config_uri', help="Provide config_uri for configuration via plaster.")
    parser.add_argument('--section', default='db_dump')
    parser.add_argument("--create-schema", help="Specify this to create the database schema.",
                        action="store_true")
    parser.add_argument("--input-file", "-i", type=argparse.FileType('r'))
    parser.add_argument("--output-file", "-o", type=argparse.FileType('w'))
    # parser.add_argument("-f", "--file", help="Output the primary JSON to this file.",
    #                     type=open)
    parser.add_argument("--stdout", help="Output JSON to standard output.",
                        action="store_true")
    parser.add_argument("--model", required=True, help="Load the specified module package.")
    parser.add_argument("--config", metavar="KEY=VALUE", action=OptionAction, help="Specify additional configuration values.")
    (args, remain) = parser.parse_known_args(sys.argv[1:])

    config_uri = args.config_uri
    if args.path:
        sys.path.extend(args.path)

    settings = plaster.get_settings(config_uri, args.section)
    if args.config:
        settings = {**settings, **args.config}

    # DONT LOG BEFORE HERE
    setup_logging(config_uri)

    set_site()
    registry = getSiteManager()
    register_components(registry)

    if args.load:
        ProcessInfo.from_json()


    listen(Mapper, 'mapper_configured', handle_mapper_configured)
    listen(Table, 'after_parent_attach', handle_parent_attach)
    listen(Table, 'after_create', handle_after_create)
    engine = get_engine(settings)

    model_module = importlib.import_module(args.model)
    base = None
    for k,v in model_module.__dict__.items():
        if k == "Base":
            pass

        if isinstance(v, type) and isinstance(v, DeclarativeMeta):
            if hasattr(v, '__tablename__'):
                myo = v()
                #logger.debug("my o is %s", myo)
            else:
                base = v

    if args.create_schema:
        logger.info("Creating database schema")
        base.metadata.create_all(engine)

    (setup_jsonencoder())()

    # f = None
    # if args.file == "-":
    #     f = sys.stdout
    # elif args.output_file:
    if args.input_file:
        struct = ProcessInfo.from_json(''.join(args.input_file.readlines()))
        logger.debug(struct)

    json = process_info.to_json()

    if args.output_file:
        args.output_file.write(json)
        args.output_file.close()

    if args.stdout:
        print(json)

    # for k, v in mappers.items():
    #     v: MapperInfo
    #     print(v.to_json())

    inspect1 = inspect(engine) # type: PGInspector
#    logger.debug("inspect1 = %s", inspect1)
#    for x in inspect1.get_table_names():
#        logger.debug("x=%s", x)



def set_site():
    setSite(Site())
