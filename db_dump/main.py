import importlib
import json
import sys

import plaster
from plaster import setup_logging
from sqlalchemy import inspect, Table, engine_from_config
import logging

from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import Mapper

from db_dump.args import argument_parser
from db_dump.events import handle_after_create

from zope.component.hooks import setSite, getSiteManager

from db_dump import Site, register_components
from db_dump.process import setup_jsonencoder, process_table, ProcessStruct
from db_dump.schema import ProcessSchema
from marshmallow import pprint

logger = logging.getLogger(__name__)


def get_engine(settings, prefix='sqlalchemy.'):
    return engine_from_config(settings, prefix)


def handle_parent_attach(target, parent):
    logger.debug("handle_parent_attach: %s (%s), %s", target, type(target), parent)


def main():
    parser = argument_parser()
    args = parser.parse_args()

    settings = args.settings[args.config_uri] #plaster.get_settings(config_uri, args.section)
    if args.config:
        settings = {**settings, **args.config}

    # DONT LOG BEFORE HERE
    setup_logging(args.config_uri)

    set_site()
    registry = getSiteManager()
    register_components(registry)

    if args.load:
        pi = ProcessInfo.from_json()
        for mapper in pi.mappers.values():
            Mapper()

    mappers_configured = []

    def handle_mapper_configured(*args, **kwargs):
        (mapper, entity) = args
        mapper: Mapper
        logger.debug("handle_mapper_configured: %s, %s", args, kwargs)
        # all our other routine does is stuff the mapper into a dict
        mappers_configured.append((mapper,entity,))

    listen(Mapper, 'mapper_configured', handle_mapper_configured)
    listen(Table, 'after_parent_attach', handle_parent_attach)
    listen(Table, 'after_create', handle_after_create)
    if 'sqlalchemy.url' not in settings:
        print("No sqlalchemy.url supplied.", file=sys.stderr)
        return 1

    engine = get_engine(settings)

    base = None
    if args.model:
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
    else:
        base = declarative_base()


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


    schema = ProcessSchema()
    ps = ProcessStruct()
    for mapper, entity in mappers_configured:
        ps.mappers.append(mapper)

    inspect1 = inspect(engine)  # type: Inspector
    for table in inspect1.get_table_names():
        table_o = Table(table, base.metadata)
        ps.tables.append(table_o)#process_table(table, table_o)

    json_str = json.dumps(schema.dump(ps))
    if args.debug:
        logger.debug("json_str = %s", json_str)

    if args.output_file:
        args.output_file.write(json_str)
        args.output_file.close()

    if args.stdout:
        print(json_str)

    # for k, v in mappers.items():
    #     v: MapperInfo
    #     print(v.to_json())


def set_site():
    setSite(Site())
