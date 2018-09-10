import importlib
import json
import re
import sys
from pathlib import PurePosixPath
from pprint import pprint

import plaster
from kazoo.client import KazooClient
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

from db_dump import Site, register_components, get_process_schema, get_mapper_schema, setup_jsonencoder
from db_dump.info import get_process_struct, GenerationInfo
from marshmallow import ValidationError

logger = logging.getLogger(__name__)


def get_engine(settings, prefix='sqlalchemy.'):
    return engine_from_config(settings, prefix)


def handle_parent_attach(target, parent):
    logger.debug("handle_parent_attach: %s (%s), %s", target, type(target), parent)


def main(argv=sys.argv):
    parser = argument_parser()
    args = parser.parse_args(argv[1:])

    settings = args.settings[args.config_uri]  # plaster.get_settings(config_uri, args.section)
    if args.config:
        settings = {**settings, **args.config}

    # DONT LOG BEFORE HERE
    setup_logging(args.config_uri)

    if args.copy_config:
        src = args.config_uri
        dst = args.dest_config_uri
        loader = plaster.get_loader(dst, protocols=('zc', 'zc+tcp'))  # ZooKeeperLoader
        for section in plaster.get_sections(src):
            config = plaster.get_settings(src, section)
            zk = loader.zk
            section_p = loader.path.joinpath(section)
            for k, v in config.items():
                config_p = section_p.joinpath(k)
                zk.ensure_path(str(config_p))
                zk.set(str(config_p), bytes(v, encoding='utf-8'))

        # for k in ('logger', 'handler', 'formatter'):
        #     _config[k] = dict()
        #     key = k + 's'
        #     p = loader.path # type: PurePosixPath
        #     sp = p.joinpath(key)
        #     zk = loader.zk
        #     zk.ensure_path(str(sp))
        #     config = plaster.get_settings(uri, key)
        #     for k, v in config.items():
        #         sp2 = sp.joinpath(k)
        #         zk.ensure_path(str(sp2))
        #         zk.set(str(sp2), bytes(v, encoding='utf-8'))
        #
        #     for x in re.split(', *', config['keys']):
        #         logger.critical("x = %s", x)
        #         key2 = "%s_%s" % (k, x)
        #         lconfig = plaster.get_settings(uri, key2)
        #         sp2 = sp.joinpath(key2)
        #         for k, v in lconfig.items():
        #             sp3 = sp2.joinpath(k)
        #             zk.ensure_path(str(sp3))
        #             zk.set(str(sp3), bytes(v, encoding='utf-8'))
        #
        #         #                _config[k][x] = lconfig
        #         zk = loader.zk # type: KazooClient
        #         px = loader.path # type: PurePosixPath
        #         root = px.joinpath(key).joinpath(key2)
        #
        #         for k, v in lconfig.items():
        #
        #             joinpath = root.joinpath(k)
        #             zk.ensure_path(str(joinpath))
        #             zk.set(str(joinpath), bytes(v, encoding='utf-8'))
        #







        # for section in plaster.get_sections(uri):
        #     settings = plaster.get_settings(uri, section)

    set_site()
    registry = getSiteManager()
    register_components(registry)

    if args.load:
        raise NotImplementedError()
        # pi = ProcessInfo.from_json()
        # for mapper in pi.mappers.values():
        #     Mapper()

    mappers_configured = []

    def handle_mapper_configured(*args, **kwargs):
        (mapper, entity) = args
        mapper: Mapper
        logger.debug("handle_mapper_configured: %s, %s", args, kwargs)
        # all our other routine does is stuff the mapper into a dict
        mappers_configured.append((mapper, entity,))

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
        for k, v in model_module.__dict__.items():
            if k == "Base":
                pass

            if isinstance(v, type) and isinstance(v, DeclarativeMeta):
                if hasattr(v, '__tablename__'):
                    myo = v()
                    # logger.debug("my o is %s", myo)
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

    schema = get_process_schema()
    ps = get_process_struct()
    ps.generation = GenerationInfo()
    assert ps.generation
    assert ps.generation.created

    # mappers_configured comes from events
    for mapper, entity in mappers_configured:
        dump_and_load_mapper(mapper)
        # we append our mapper to our list of mappers in the process struct
        # which is what is dumped to json
        ps.mappers.append(mapper)

    inspect_engine(base, engine, ps)

    json_str = json.dumps(schema.dump(ps))
    if args.debug:
        logger.debug("json_str = %s", json_str)

    if args.output_file:
        args.output_file.write(json_str)
        args.output_file.close()

    #    o = schema.load(json_str)

    if args.stdout:
        print(json_str)

    # for k, v in mappers.items():
    #     v: MapperInfo
    #     print(v.to_json())


def inspect_engine(base, engine, ps):
    inspect1 = inspect(engine)  # type: Inspector
    for table in inspect1.get_table_names():
        table_o = Table(table, base.metadata)
        ps.tables.append(table_o)  # process_table(table, table_o)


def dump_and_load_mapper(mapper):
    # this is for dumping our mapper - we only need it because we
    # try to dump and load the object for testing purposes.
    m = get_mapper_schema()
    try:
        dumps = json.dumps(m.dump(mapper))
        v = m.load(json.loads(dumps))
        logger.debug("value = %s", v)
    except TypeError:
        logger.critical("Can't reconstitute mapper: %s", sys.exc_info()[1])
        import traceback
        traceback.print_tb(tb=sys.exc_info()[2], file=sys.stderr)
        print(sys.exc_info()[1], file=sys.stderr)
        # print("ZZZ", traceback.format_stack(), file=sys.stderr)


    except ValidationError as err:
        logger.critical("Can't reconstitute mapper: %s, %s", err.messages, dumps)


def set_site():
    setSite(Site())
