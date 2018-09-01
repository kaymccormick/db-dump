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

from db_dump.events import handle_after_create, handle_mapper_configured
#from db_dump.model import Test1, Base

from zope.component.hooks import setSite, getSiteManager

from db_dump import Site, register_components
from db_dump.process import setup_jsonencoder, process_info

logger = logging.getLogger(__name__)


def get_engine(settings, prefix='sqlalchemy.'):
    return engine_from_config(settings, prefix)


def handle_parent_attach(target, parent):
    logger.debug("handle_parent_attach: %s (%s), %s", target, type(target), parent)


class OptionAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        sv = str(values)
        split = sv.split('=', 2)
        key = split[0].strip()
        val = split[1].strip()
        attr = getattr(namespace, self.dest)
        if not attr:
            setattr(namespace, self.dest, {})

        getattr(namespace, self.dest)[key] = val



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config_uri', help="Provide config_uri for configuration via plaster.")
    parser.add_argument('--section', default='db_dump')
    parser.add_argument("--create-schema", help="Specify this to create the database schema.",
                        action="store_true")
    parser.add_argument("-o", "--output-file", help="Output the primary JSON to this file.")
    parser.add_argument("--stdout", help="Output JSON to standard output.",
                        action="store_true")
    parser.add_argument("--model", required=True, help="Load the specified module package.")
    parser.add_argument("--config", metavar="KEY=VALUE", action=OptionAction, help="Specify additional configuration values.")
    (args, remain) = parser.parse_known_args(sys.argv[1:])

    config_uri = args.config_uri

    #loader = plaster.get_loader(config_uri)
    #print(loader)

    #sections = plaster.get_sections(config_uri)

    settings = plaster.get_settings(config_uri, args.section)
    if args.config:
        settings = {**settings, **args.config}

    # DONT LOG BEFORE HERE
    setup_logging(config_uri)

    set_site()
    registry = getSiteManager()
    register_components(registry)

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

    f = None
    if args.output_file == "-":
        f = sys.stdout
    elif args.output_file:
        f = open(args.output_file, 'w')

    json = process_info.to_json()
    if args.stdout:
        print(json)
    if f:
        f.write(json)
        f.close()

    # for k, v in mappers.items():
    #     v: MapperInfo
    #     print(v.to_json())

    inspect1 = inspect(engine) # type: PGInspector
#    logger.debug("inspect1 = %s", inspect1)
#    for x in inspect1.get_table_names():
#        logger.debug("x=%s", x)



def set_site():
    setSite(Site())
