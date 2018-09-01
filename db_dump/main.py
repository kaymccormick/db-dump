import importlib
import json
import os
import sys
from collections import OrderedDict
from configparser import ConfigParser, NoSectionError
from logging.config import fileConfig
from typing import Sequence, Optional, Union, Any, Callable, Iterable, Tuple

import plaster
from datauri import DataURI
from paste.deploy.compat import iteritems
from paste.deploy.loadwsgi import NicerConfigParser, _Loader
from plaster import setup_logging, ILoader, PlasterURL
from plaster_pastedeploy import Loader, ConfigDict
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
from db_dump.process import setup_jsonencoder, process_info

logger = logging.getLogger(__name__)

class DataUriConfigParser(ConfigParser, DataURI):
    def __init__(self, data_uri: DataURI):
        super(ConfigParser, self).__init__()
        self.data_uri = data_uri
    pass


class DataLoader(_Loader):
    def __init__(self, uri: PlasterURL):
        self.uri = uri
        #uri = uri.replace("://", ":")
        print("uri = ", uri)
        self.data_uri = DataURI("data:" + uri.path)
        self.parser = DataUriConfigParser(self.data_uri)
        self.parser.read_string(self.data_uri.data.decode('utf-8'))

    def _get_parser(self, defaults=None):
        defaults = self._get_defaults(defaults)
        loader = DataLoader(self.uri)
        loader.update_defaults(defaults)
        return loader.parser

    def update_defaults(self, new_defaults, overwrite=True):
        for key, value in iteritems(new_defaults):
            if not overwrite and key in self.parser._defaults:
                continue
            self.parser._defaults[key] = value

    def get_sections(self):
        """
        Find all of the sections in the config file.

        :return: A list of the section names in the config file.

        """
        parser = self._get_parser()
        return parser.sections()

    def get_settings(self, section=None, defaults=None):
        """
        Gets a named section from the configuration source.

        :param section: a :class:`str` representing the section you want to
            retrieve from the configuration source. If ``None`` this will
            fallback to the :attr:`plaster.PlasterURL.fragment`.
        :param defaults: a :class:`dict` that will get passed to
            :class:`configparser.ConfigParser` and will populate the
            ``DEFAULT`` section.
        :return: A :class:`plaster_pastedeploy.ConfigDict` of key/value pairs.

        """
        # This is a partial reimplementation of
        # ``paste.deploy.loadwsgi.ConfigLoader:get_context`` which supports
        # "set" and "get" options and filters out any other globals
        section = self._maybe_get_default_name(section)
        parser = self._get_parser(defaults)
        defaults = parser.defaults()

        try:
            raw_items = parser.items(section)
        except NoSectionError:
            return {}

        local_conf = OrderedDict()
        get_from_globals = {}
        for option, value in raw_items:
            if option.startswith('set '):
                name = option[4:].strip()
                defaults[name] = value
            elif option.startswith('get '):
                name = option[4:].strip()
                get_from_globals[name] = value
                # insert a value into local_conf to preserve the order
                local_conf[name] = None
            else:
                # annoyingly pastedeploy filters out all defaults unless
                # "get foo" is used to pull it in
                if option in defaults:
                    continue
                local_conf[option] = value
        for option, global_option in get_from_globals.items():
            local_conf[option] = defaults[global_option]
        return ConfigDict(local_conf, defaults, self)

    def setup_logging(self, defaults=None):
        """
        Set up logging via :func:`logging.config.fileConfig`.

        Defaults are specified for the special ``__file__`` and ``here``
        variables, similar to PasteDeploy config loading. Extra defaults can
        optionally be specified as a dict in ``defaults``.

        :param defaults: The defaults that will be used when passed to
            :func:`logging.config.fileConfig`.
        :return: ``None``.

        """
        if 'loggers' in self.get_sections():
            defaults = self._get_defaults(defaults)
            fileConfig(self.parser, defaults, disable_existing_loggers=False)

        else:
            logging.basicConfig()

    def _get_defaults(self, defaults=None):
        result = {}
        result['here'] = os.getcwd()
        if defaults:
            result.update(defaults)
        return result

    def _maybe_get_default_name(self, name):
        """Checks a name and determines whether to use the default name.

        :param name: The current name to check.
        :return: Either None or a :class:`str` representing the name.
        """
        if name is None and self.uri.fragment:
            name = self.uri.fragment
        return name

    def __repr__(self):
        return 'db_dump.Loader(uri="{0}")'.format(self.uri)



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
    parser.add_argument("--create-schema", help="Specify this to create the database schema.",
                        action="store_true")
    parser.add_argument("-o", "--output-file", help="Output the primary JSON to this file.")
    parser.add_argument("--stdout", help="Output JSON to standard output.",
                        action="store_true")
    parser.add_argument("--model", required=True, help="Load the specified module package.")
    parser.add_argument("--config", metavar="KEY=VALUE", action=OptionAction, help="Specify additional configuration values.")
    (args, remain) = parser.parse_known_args(sys.argv[1:])

    config_uri = args.config_uri
    defaults = {}
    if args.config:
        defaults = args.config

    loader = plaster.get_loader(config_uri)
    print(loader)



    sections = plaster.get_sections(config_uri)

    settings = plaster.get_settings(config_uri, 'db_dump')
    if args.config:
        settings = {**settings, **args.config}

    # DONT LOG BEFORE HERE
    setup_logging(config_uri)
    logger.debug("Settings is %s", settings)

    logger.debug("args = %s", args)

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
