import logging

from db_dump.columnschema import ColumnSchema, TableSchema
from db_dump.fields import TypeField, ArgumentField
from db_dump.pairfield import PairField
from db_dump.info import MapperInfo, ProcessInfo, RelationshipInfo, TableColumnSpecInfo
from marshmallow import Schema, fields, post_load

logger = logging.getLogger(__name__)

class MapperPropertySchema(Schema):
    class_attribute = TypeField()


class InspectionAttrSchema(Schema):
    is_mapper = fields.Boolean()
    is_property = fields.Boolean()
    is_attribute = fields.Boolean()
    pass


class MapperPropertySchema(InspectionAttrSchema):
    pass


# currently use solely for MapperInfo.primary_key
class TableColumnSpecSchema(Schema):
    table = fields.String(load_from='table.key')
    column = fields.String(attribute='key', data_key='column')
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


# class PairSchema(Schema):
#     local = fields.Function(lambda obj: obj[0])
#     remote = fields.Function(lambda obj: obj[0])
#     @post_load
#     def make_pair(self, data):
#         return PairInfo(**data)


class RelationshipSchema(StrategizedPropertySchema):
    key = fields.String()
    argument = ArgumentField()
    secondary = fields.Nested(TableSchema, allow_none=True)
    direction = fields.String(attribute="direction.name")
    local_remote_pairs = PairField(many=True)
    mapper = fields.Nested('MapperSchema', only=['local_table'])
    @post_load
    def make_relationship(self, data):
        data['direction'] = data['direction']['name']
        return RelationshipInfo(**data)


class MapperSchema(Schema):
    primary_key = fields.Nested(TableColumnSpecSchema, many=True)
    #attrs = fields.Nested(StrategizedPropertySchema, many=True)
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


class ProcessSchema(Schema):
    generation = fields.Nested(GenerationSchema)
    mappers = fields.Nested(MapperSchema, many=True)
    tables = fields.Nested(TableSchema, many=True)
    @post_load
    def make_process_info(self, data):
        return ProcessInfo(**data);


def get_process_schema():
    schema = ProcessSchema()
    return schema


def get_mapper_schema():
    m = MapperSchema()
    return m