import json
import logging
from dataclasses import dataclass, field
from typing import MutableSequence, AnyStr, Mapping

from dataclasses_json import DataClassJsonMixin
from sqlalchemy import Column
from sqlalchemy.orm import Mapper

from db_dump.info import ColumnInfo, TypeInfo, \
    MapperInfo, LocalRemotePairInfo, PairInfo, RelationshipInfo

logger = logging.getLogger(__name__)

@dataclass
class ProcessInfo(DataClassJsonMixin):
    mappers: Mapping[AnyStr, MapperInfo]=field(default_factory=lambda: {})

process_info = ProcessInfo()

def process_relationship(mapper_key, rel):
    logger.info("entering process_relationship")
    y = rel.argument
    if callable(y):
        z = y()
    else:
        z = y.entity

    pairs = []
    for pair in rel.local_remote_pairs:
        pairs.append(LocalRemotePairInfo(local=PairInfo(table=pair[0].table.name, column=pair[0].name),
                                         remote=PairInfo(table=pair[1].table.name, column=pair[1].name))
                     )
        secondary = None
        if rel.secondary:
            secondary = rel.secondary.name
        if rel.backref and not isinstance(rel.backref, str):
            print(rel.backref)

        i = RelationshipInfo(mapper_key=mapper_key,
                             local_remote_pairs=pairs, argument=[z.__module__, z.__name__],
                             key=rel.key,
                             secondary=secondary, backref=rel.backref,
                             direction=rel.direction.name,
                             )
    return i


def process_mapper(mapper: Mapper) -> 'MapperProcessorResult':
    logger.info("entering process_mapper")
    mapped_table = mapper.mapped_table  # type: Table
    mapper_key = mapper.local_table.key

    primary_key = []
    for pkey in mapper.primary_key:
        primary_key.append([pkey.table.key, pkey.key])

    column_map = {}
    columns = []
    col_index = 0
    col: Column
    for col in mapper.columns:
        coltyp = col.type
        t = col.table  # type: Table
        i = ColumnInfo(key=col.key, compiled=str(col.compile()),
                       table=t.name,
                       type_=TypeInfo(compiled=str(coltyp.compile())), )

        columns.append(i)
        if t.key not in column_map:
            column_map[t.key] = { col.key: col_index }
        else:
            column_map[t.key][col.key] = col_index

        col_index = col_index + 1

    relationships = []
    for relationship in mapper.relationships:
        relationships.append(process_relationship(mapper_key, relationship))

    mi = MapperInfo(columns=columns,
                    relationships=relationships,
                    primary_key=primary_key,
                    mapped_table=mapped_table.key,
                    column_map=column_map,
                    mapper_key=mapper_key)
    process_info.mappers[mapper_key] = mi
    return mi
    #self.info.mappers[mapper_key] = mi

def setup_jsonencoder():
    logger.info("entering setup_jsonencoder")

    def do_setup():
        old_default = json.JSONEncoder.default

        class MyEncoder(json.JSONEncoder):
            def default(self, obj):
                # logging.critical("type = %s", type(obj))
                v = None
                # This is not a mistake.
                if isinstance(obj, Column):
                    return ['Column', obj.name, obj.table.name]

                try:
                    v = old_default(self, obj)
                except:

                    assert False, type(obj)
                return v

        json.JSONEncoder.default = MyEncoder.default

    return do_setup
