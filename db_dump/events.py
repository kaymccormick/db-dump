import logging

from sqlalchemy.orm import Mapper
from zope.component import getSiteManager
from zope.component.hooks import getSite

from db_dump import IProcessor, MyMapper, IMapper, process_mapper

logger = logging.getLogger(__name__)

mappers = {}

def handle_after_create(target, connection, **kwargs):
    logger.debug("after create %s", target)


def handle_mapper_configured(*args, **kwargs):
    (mapper, entity) = args
    mapper: Mapper
    logger.debug("handle_mapper_configured: %s, %s", args, kwargs)
    logger.debug("table is %s", mapper.mapped_table)
    # all our other routine does is stuff the mapper into a dict
    logger.debug("site = %s", getSite())
    result = process_mapper(mapper)
    #result = IProcessor(MyMapper(mapper)).process()
    logger.debug("result is %s", result)
    mappers[mapper.local_table.key] = result
    #adapter = getSiteManager().queryAdapter(MyMapper(mapper), IProcessor)
    #logger.debug("adapter is %s", adapter)
