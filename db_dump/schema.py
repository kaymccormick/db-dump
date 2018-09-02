from datetime import date
from marshmallow import Schema, fields, pprint


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
    compiled = fields.String()
    python_type = fields.Function(lambda type_: str(type_))


class ColumnSchema(SchemaItemSchema):
    key = fields.String()
    name = fields.String()
    type_ = fields.Nested(TypeSchema, attribute="type")

class TableSchema(SchemaItemSchema):
    key = fields.String()
    name = fields.String()



class MappedProperty(InspectionAttrSchema):
    pass

class StrategizedPropertySchema(InspectionAttrSchema):
    pass



class RelationshipSchema(StrategizedPropertySchema):
    argument = fields.Function(lambda x: str(callable(x.argument) and x.argument() or x.argument))
    secondary = fields.Nested(TableSchema)



class MapperSchema(InspectionAttrSchema):
    primary_key = fields.Nested(TableColumnSpec, many=True)
    columns = fields.Nested(ColumnSchema, many=True)
    relationships = fields.Nested(RelationshipSchema, many=True)


class ProcessSchema(Schema):
    mappers = fields.Nested(MapperSchema, many=True)
    tables = fields.Nested(TableSchema, many=True)
