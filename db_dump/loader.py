import gzip
import logging
import os
import re
from collections.__init__ import OrderedDict
from configparser import ConfigParser, NoSectionError
from logging.config import fileConfig
from pathlib import PurePath, PurePosixPath

from datauri import DataURI
from kazoo.client import KazooClient
from paste.deploy.compat import iteritems
from paste.deploy.loadwsgi import _Loader
from plaster import PlasterURL
from plaster_pastedeploy import ConfigDict

logger = logging.getLogger(__name__)


class ZooKeeperConfigParser(ConfigParser):

    def __init__(self, uri):
        super().__init__()


class DataUriConfigParser(ConfigParser, DataURI):
    def __init__(self, data_uri: DataURI):
        super(ConfigParser, self).__init__()
        self.data_uri = data_uri

    pass


class ZooKeeperLoader(_Loader):
    def __init__(self, uri: PlasterURL):
        self.uri = uri
        from urllib.parse import urlparse
        o = urlparse(str(uri))
        self.path = PurePosixPath(o.path or '/') # type: PurePosixPath
        self.strpath = str(self.path)
        self.netloc = str(o.netloc)
        #re.match('')
        logger.critical("attempting connection to %s", o.hostname)
        d = dict(hosts="%s:%d" % (o.hostname, o.port))
        logger.critical("%s", d)
        self.d = d
        self.zk = KazooClient(**d)
        self.zk.start()
        self.zk.ensure_path(self.strpath)
        logger.critical("ensureing path exists %s", self.strpath)
        #self.zk.ensure_path(self.strpath)
        logger.critical("done ensureing path exists %s", self.strpath)

    def get_sections(self):
        children = self.zk.get_children(self.strpath)
        return children
        # zk.ensure_path(self.o.path)
        # zk_get = zk.get(self.o.path)
        # self.path = zk_get
        # return self.path.get_children()

    def get_settings(self, section, defaults):
        settings = {}
        p = self.path.joinpath(section)
        self.zk.ensure_path(str(p))
        for c in self.zk.get_children(str(p)):
            data, stat = self.zk.get(str(p.joinpath(c)))
            settings[c] = data.decode('utf-8')
        return settings

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


    def setup_logging(self, defaults=None):
        logging.config.dictConfig(dict(version=1, formatters={}))

        pass
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



class DataLoader(_Loader):
    def __init__(self, uri: PlasterURL):
        self.uri = uri

        self.data_uri = DataURI("data:" + uri.path)
        self.parser = DataUriConfigParser(self.data_uri)
        #        if self.data_uri.co
        if self.data_uri.mimetype == "application/x-gzip":
            self.parser.read_string(gzip.decompress(self.data_uri.data).decode('utf-8'))
        else:
            self.parser.read_string(self.data_uri.data.decode(self.data_uri.charset or 'utf-8'))

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
