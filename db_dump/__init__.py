import datetime
import json
import logging
from sqlalchemy import Column, Table
from typing import Mapping, AnyStr

from marshmallow import fields, post_load, Schema
from marshmallow.fields import Field, Nested

from db_dump.dbd_fields import TypeField, ArgumentField
from db_dump.info import ColumnInfo, TableInfo
from db_dump.info import ForeignKeyInfo, ColumnInfo, TableInfo, TableColumnSpecInfo, RelationshipInfo, MapperInfo, \
    ProcessInfo, LocalRemotePairInfo

logger = logging.getLogger(__name__)

MapperResultKey = AnyStr
MapperResultValue = Mapping[AnyStr, dict]
MapperProcessorResult = Mapping[MapperResultKey, MapperResultValue]


#    result = IProcessor(MyMapper(None)).process()
# components.registerAdapter(TableProcessor)
class SchemaItemSchema(Schema):
    visit_name = fields.String(attribute='__visit_name__')


#
# class TypeSchema(SchemaItemSchema):
#     #compiled = fields.Function(lambda type_: type_.compiled())
#     python_type = fields.Function(lambda type_: str(type_))
class TypeSchema(Schema):
    python_type = TypeField()


class PairField(Field):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._column_schema = ColumnSchema(only=('key', 'table', 'type_'))
        self._column_field = Nested(ColumnSchema)

    def _serialize(self, value, attr, obj):
        x = []
        for local, remote in value:
            x.append({'local': self._column_schema.dump(local),
                      'remote': self._column_schema.dump(remote)})

            # x = self._column_field.__serialize(local, None, value)
        return x

    def _deserialize(self, value, attr, data):
        pairs = []
        for pair in value:
            pairs.append(LocalRemotePairInfo(
                local=TableColumnSpecInfo(table=pair['local']['table']['key'], column=pair['local']['key']),
                remote=TableColumnSpecInfo(table=pair['remote']['table']['key'], column=pair['remote']['key']),
            ))
        return pairs


class ForeignKeySchema(SchemaItemSchema):
    column = fields.Nested('ColumnSchema', only=['key', 'table'])  # do we need many = True?

    # uncovered
    @post_load
    def make_fk(self, data):
        return ForeignKeyInfo(**data)


class ColumnSchema(SchemaItemSchema):
    key = fields.String()
    name = fields.String()
    table = fields.Nested('TableSchema', only=('key',))
    type_ = fields.Nested(TypeSchema, attribute='type')
    foreign_keys = fields.Nested('ForeignKeySchema', many=True)

    @post_load
    def make_columninfo(self, data):
        return ColumnInfo(**data)


class TableSchema(SchemaItemSchema):
    key = fields.String()
    name = fields.String()
    columns = fields.Nested(ColumnSchema, many=True)

    @post_load
    def make_table_info(self, data):
        return TableInfo(**data)


class InspectionAttrSchema(Schema):
    is_mapper = fields.Boolean()
    is_property = fields.Boolean()
    is_attribute = fields.Boolean()
    pass


class TableColumnSpecSchema(Schema):
    table = fields.String(load_from='table.key')
    column = fields.String(attribute='key', data_key='column')
    type = fields.Nested(TypeSchema)

    @post_load
    def make_info(self, data):
        key = data['key']
        del data['key']
        data['column'] = key
        return TableColumnSpecInfo(**data)


class MappedProperty(InspectionAttrSchema):
    pass


class StrategizedPropertySchema(InspectionAttrSchema):
    pass


class RelationshipSchema(StrategizedPropertySchema):
    key = fields.String()
    argument = ArgumentField()
    secondary = fields.Nested(TableSchema, allow_none=True)
    direction = fields.String(attribute="direction.name")
    # local_remote_pairs = fields.Nested(ColumnSchema, many=True)
    local_remote_pairs = PairField(many=True)
    mapper = fields.Nested('MapperSchema', only=['local_table'])

    @post_load
    def make_relationship(self, data):
        data['direction'] = data['direction']['name']
        return RelationshipInfo(**data)


class MapperSchema(Schema):
    primary_key = fields.Nested(TableColumnSpecSchema, many=True)
    # attrs = fields.Nested(StrategizedPropertySchema, many=True)
    columns = fields.Nested(ColumnSchema, many=True)
    relationships = fields.Nested(RelationshipSchema, many=True)
    local_table = fields.Nested(TableSchema, required=True, only=['key'])
    entity = TypeField()

    @post_load
    def make_mapper(self, data):
        logger.debug("in make_mapper with %s", data)
        return MapperInfo(**data)


class ConfigVarsSchema(Schema):
    pass


class GenerationSchema(Schema):
    created = fields.DateTime()
    system_alias = fields.String(many=True)
    python_version = fields.String()
    config_vars = fields.Nested(ConfigVarsSchema)


# get rid of lame name
class ProcessSchema(Schema):
    generation = fields.Nested(GenerationSchema)
    mappers = fields.Nested(MapperSchema, many=True)
    tables = fields.Nested(TableSchema, many=True)

    # uncoverd
    @post_load
    def make_process_info(self, data):
        return ProcessInfo(**data);


# uncovered
def get_process_schema():
    schema = ProcessSchema()
    return schema


# uncovered
def get_mapper_schema():
    m = MapperSchema()
    return m


# uncovered
def process_mapper(ps, mapper: 'Mapper') -> 'MapperProcessorResult':
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
            column_map[t.key] = {col.key: col_index}
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
    # self.info.mappers[mapper_key] = mi


# uncovered
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
                if isinstance(obj, datetime.datetime):
                    return str(obj)
                try:
                    v = old_default(self, obj)
                except:
                    assert False, "%r (%s)" % (obj, type(obj))
                return v

        json.JSONEncoder.default = MyEncoder.default

    return do_setup


def process_table(ps, table_name: AnyStr, table: 'Table') -> TableInfo:
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
