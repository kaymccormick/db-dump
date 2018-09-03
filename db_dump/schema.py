import logging
from datetime import date

from db_dump.info import MapperInfo, ProcessInfo, TableInfo
from marshmallow import Schema, fields, pprint, post_load

logger = logging.getLogger(__name__)

class InspectionAttrSchema(Schema):
    is_mapper = fields.Boolean()
    is_property = fields.Boolean()
    is_attribute = fields.Boolean()
    pass


class MapperPropertySchema(InspectionAttrSchema):
    pass


class SchemaItemSchema(Schema):
    visit_name = fields.String(attribute='__visit_name__')


class TableColumnSpec(Schema):
    table = fields.String(load_from='table.key')
    column = fields.String(attribute='key')


class TypeSchema(SchemaItemSchema):
    #compiled = fields.Function(lambda type_: type_.compiled())
    python_type = fields.Function(lambda type_: str(type_))


class ColumnSchema(SchemaItemSchema):
    key = fields.String()
    name = fields.String()
    type_ = fields.Nested(TypeSchema, attribute="type")


class TableSchema(SchemaItemSchema):
    key = fields.String()
    name = fields.String()
    columns = fields.Nested(ColumnSchema, many=True)
    @post_load
    def make_table_info(self, data):
        return TableInfo(**data)


class MappedProperty(InspectionAttrSchema):
    pass


class StrategizedPropertySchema(InspectionAttrSchema):
    pass


class RelationshipSchema(StrategizedPropertySchema):
    argument = fields.Function(lambda x: str(callable(x.argument) and x.argument() or x.argument))
    secondary = fields.Nested(TableSchema, allow_none=True)


class MapperSchema(Schema):
    primary_key = fields.Nested(TableColumnSpec, many=True)
    columns = fields.Nested(ColumnSchema, many=True)
    relationships = fields.Nested(RelationshipSchema, many=True)
    local_table = fields.Nested(TableSchema, required=True)

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