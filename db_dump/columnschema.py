
from db_dump.baseschema import SchemaItemSchema, TypeSchema
from db_dump.info import TableInfo, ColumnInfo, ForeignKeyInfo
from marshmallow import fields, post_load


class ForeignKeySchema(SchemaItemSchema):
    column = fields.Nested('ColumnSchema', only=['key', 'table']) # do we need many = True?
    @post_load
    def make_fk(self, data):
        return ForeignKeyInfo(**data)


class ColumnSchema(SchemaItemSchema):
    key = fields.String()
    name = fields.String()
    table = fields.Nested('TableSchema', only=('key',))
    type_ = fields.Nested(TypeSchema, attribute="type")
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