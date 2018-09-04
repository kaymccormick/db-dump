from marshmallow import Schema, fields

class SchemaItemSchema(Schema):
    visit_name = fields.String(attribute='__visit_name__')


class TypeSchema(SchemaItemSchema):
    #compiled = fields.Function(lambda type_: type_.compiled())
    python_type = fields.Function(lambda type_: str(type_))