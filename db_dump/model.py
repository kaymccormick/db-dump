import logging

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

logger = logging.getLogger(__name__)

Base = declarative_base()


class Test1(Base):
    """
    Test1 entity class
    """
    __tablename__= 'test1'
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey('child.id'))
    child = relationship('Child')


class Child(Base):
    """
    Child entity class
    """
    __tablename__ = 'child'
    id = Column(Integer, primary_key=True)
