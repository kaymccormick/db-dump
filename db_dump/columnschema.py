
from db_dump.baseschema import SchemaItemSchema, TypeSchema
from db_dump.info import TableInfo, ColumnInfo
from marshmallow import fields, post_load


class ColumnSchema(SchemaItemSchema):
    key = fields.String()
    name = fields.String()
    table = fields.Nested('TableSchema', only=('key',))
    type_ = fields.Nested(TypeSchema, attribute="type")
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