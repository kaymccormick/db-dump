import logging

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

logger = logging.getLogger(__name__)

logger.critical("in model.py")
Base = declarative_base()
logger.critical("in model.py %s", Base.__class__.__bases__)


class Test1(Base):
    __tablename__= 'test1'
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('child.id'))
    child = relationship('Child')

class Child(Base):
    __tablename__ = 'child'
    id = Column(Integer, primary_key=True)
