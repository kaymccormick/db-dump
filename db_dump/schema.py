from datetime import date
from marshmallow import Schema, fields, pprint


class TableColumnSpec(Schema):
    table = fields.String(load_from='table.key')
    column = fields.String(load_from='key')


class MapperSchema(Schema):
    primary_key = fields.Nested(TableColumnSpec, many=True)

