import argparse
import logging
import sys

import plaster

logger = logging.getLogger(__name__)


class ConfigAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        logger.debug("__caall__")
        settings = plaster.get_settings(values, getattr(namespace, 'section'))
        setattr(namespace, 'config_uri', values)

        if hasattr(namespace, 'settings') is not None:
            setattr(namespace, 'settings', {values: settings})
        else:
            getattr(namespace, 'settings')[values] = settings


class AppendPath(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        sys.path.append(values)
        # sv = str(values)
        # split = sv.split('=', 2)
        # key = split[0].strip()
        # val = split[1].strip()
        # attr = getattr(namespace, self.dest)
        # if not attr:
        #     setattr(namespace, self.dest, {})
        #
        # getattr(namespace, self.dest)[key] = val


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


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--debug', '-d', action="store_true")
    parser.add_argument('--load', action="store_true")
    parser.add_argument('--path', action=AppendPath)
    parser.add_argument('--config-uri', '-c', help="Provide config_uri for configuration via plaster.",
                        action=ConfigAction)
    parser.add_argument('--dest-config-uri')
    parser.add_argument('--copy-config', action='store_true')
    parser.add_argument('--section', default='db_dump')
    parser.add_argument("--create-schema", help="Specify this to create the database schema.",
                        action="store_true")
    parser.add_argument("--input-file", "-i", type=argparse.FileType('r'))
    parser.add_argument("--output-file", "-o", type=argparse.FileType('w'))
    # parser.add_argument("-f", "--file", help="Output the primary JSON to this file.",
    #                     type=open)
    parser.add_argument("--stdout", help="Output JSON to standard output.",
                        action="store_true")
    parser.add_argument("--model", help="Load the specified module package.")
    parser.add_argument("--config", "-C", metavar="KEY=VALUE", action=OptionAction,
                        help="Specify additional configuration values.")
    return parser
