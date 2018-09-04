from db_dump.columnschema import ColumnSchema
from db_dump.info import LocalRemotePairInfo, TableColumnSpecInfo
from marshmallow.fields import Field, Nested


class PairField(Field):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._column_schema = ColumnSchema(only=('key', 'table'))
        self._column_field = Nested(ColumnSchema)

    def _serialize(self, value, attr, obj):
        x = []
        for local,remote in value:
            x.append({ 'local': self._column_schema.dump(local),
                     'remote': self._column_schema.dump(remote) })

            #x = self._column_field.__serialize(local, None, value)
        return x
    def _deserialize(self, value, attr, data):
        pairs = []
        for pair in value:
            pairs.append(LocalRemotePairInfo(
                local=TableColumnSpecInfo(table=pair['local']['table']['key'], column=pair['local']['key']),
                remote=TableColumnSpecInfo(table=pair['remote']['table']['key'], column=pair['remote']['key']),
            ))
        return pairs

