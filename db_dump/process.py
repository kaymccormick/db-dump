import json
import logging
import platform
import sysconfig
from dataclasses import dataclass, field
from datetime import datetime
from typing import MutableSequence, AnyStr, Dict, NewType, Tuple

from dataclasses_json import DataClassJsonMixin
from sqlalchemy import Column, Table
from sqlalchemy.orm import Mapper

from db_dump.info import ColumnInfo, TypeInfo, \
    MapperInfo, LocalRemotePairInfo, PairInfo, RelationshipInfo, TableInfo
from db_dump.schema import MapperSchema, TableSchema
from marshmallow import Schema

logger = logging.getLogger(__name__)

DateTime = NewType('DateTime', datetime)

@dataclass
class GenerationInfo(DataClassJsonMixin):
    created: DateTime=field(default_factory=lambda: datetime.now())
    system_alias: Tuple[AnyStr, AnyStr, AnyStr]=field(default_factory=lambda: platform.system_alias(platform.system(), platform.release(), platform.version()))
    python_version: AnyStr=field(default_factory=lambda: platform.python_version())
    config_vars: Dict[AnyStr, object]=field(default_factory=sysconfig.get_config_vars)
    #environ: Dict=field(default_factory=lambda: os.environ)


@dataclass
class GenerationMixin:
    generation: GenerationInfo=field(default_factory=GenerationInfo)


@dataclass
class ProcessStruct:
    mappers: MutableSequence[Mapper]=field(default_factory=lambda: [])
    tables: MutableSequence[Table]=field(default_factory=lambda: [])


@dataclass
class ProcessInfo(GenerationMixin, DataClassJsonMixin):
    mappers: MutableSequence[MapperInfo]=field(default_factory=lambda: [])
    tables: MutableSequence[TableInfo]=field(default_factory=lambda: {})

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
            pass
            #print(rel.backref)

        i = RelationshipInfo(mapper_key=mapper_key,
                             local_remote_pairs=pairs, argument=[z.__module__, z.__name__],
                             key=rel.key,
                             secondary=secondary, backref=rel.backref,
                             direction=rel.direction.name,
                             )
    return i


def process_mapper(ps, mapper: Mapper) -> 'MapperProcessorResult':
    logger.info("entering process_mapper")
    schema = MapperSchema()
    result = schema.dump(mapper)
    return result
    print(result)
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
    process_info.mappers.append(mi)
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
                if isinstance(obj, Table):
                    return ['Table', obj.name]
                if isinstance(obj, datetime):
                    return str(obj)
                try:
                    v = old_default(self, obj)
                except:
                    assert False, type(obj)
                return v

        json.JSONEncoder.default = MyEncoder.default

    return do_setup

# to avoid confusion, this adapts SQLalchemy-related information
# to our @dataclasses. There needs to be another layer
# to adapt the data class information into application objects
# such as ResourceManager, ResourceOperation.


def process_table(ps, table_name: AnyStr, table: Table) -> TableInfo:
    tables = ps.tables
    assert table_name == table.name
    i = TableInfo(name=table.name, key=table.key,
                  columns=[], primary_key=[]
                  )

    tables[table_name] = i

    primary_key = table.primary_key
    for key_col in primary_key:
        i.primary_key.append(key_col.key)

    col: Column
    for col in table.columns:
        _i = ColumnInfo(name=col.name, key=col.key)
        i.columns.append(_i)

    return i
