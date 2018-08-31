import sys

import plaster
from sqlalchemy import create_engine
import logging
import argparse

logger = logging.getLogger(__name__)
def main():
    logger.critical("entering main")

    parser = argparse.ArgumentParser()

    parser.add_argument('config_uri')
    args = parser.parse_args(sys.argv[1:])

    settings = plaster.get_settings(args.config_uri, section='db_dump')
    logger.critical("Settings = %s", repr(settings))

