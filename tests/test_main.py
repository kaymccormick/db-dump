from db_dump.info import MapperInfo, TableColumnSpecInfo


def test_table_column_spec_schema_load(table_column_spec_schema):
    my_table = 'test1'
    my_column = 'test1_id'
    data = {'table': my_table, 'column': my_column }
    result = table_column_spec_schema.load(data)
    assert isinstance(result, TableColumnSpecInfo)


def test_mapper_schema_load(mapper_schema):
    json_data = """
        {
      "primary_key": [
        {
          "table": "public_key",
          "column": "id"
        }
      ],
      "entity": "email_mgmt_app.model.email_mgmt.PublicKey",
      "columns": [
        {
          "visit_name": "column",
          "table": {
            "key": "public_key"
          },
          "name": "id",
          "type_": {
            "visit_name": "integer",
            "python_type": "INTEGER"
          },
          "key": "id"
        },
        {
          "visit_name": "column",
          "table": {
            "key": "public_key"
          },
          "name": "owner_id",
          "type_": {
            "visit_name": "integer",
            "python_type": "INTEGER"
          },
          "key": "owner_id"
        },
        {
          "visit_name": "column",
          "table": {
            "key": "public_key"
          },
          "name": "public_key_text",
          "type_": {
            "visit_name": "string",
            "python_type": "VARCHAR"
          },
          "key": "public_key_text"
        }
              ],
      "relationships": [
        {
          "is_property": true,
          "argument": "email_mgmt_app.model.email_mgmt.Person",
          "is_attribute": false,
          "is_mapper": false,
          "secondary": null,
          "local_remote_pairs": [
            {
              "local": {
                "table": {
                  "key": "public_key"
                },
                "key": "owner_id"
              },
              "remote": {
                "table": {
                  "key": "person"
                },
                "key": "id"
              }
            }
          ],
          "direction": "MANYTOONE"
        }
      ],
      "local_table": {
        "columns": [
          {
            "visit_name": "column",
            "table": {
              "key": "public_key"
            },
            "name": "id",
            "type_": {
              "visit_name": "integer",
              "python_type": "INTEGER"
            },
            "key": "id"
          },
          {
            "visit_name": "column",
            "table": {
              "key": "public_key"
            },
            "name": "owner_id",
            "type_": {
              "visit_name": "integer",
              "python_type": "INTEGER"
            },
            "key": "owner_id"
          },
          {
            "visit_name": "column",
            "table": {
              "key": "public_key"
            },
            "name": "public_key_text",
            "type_": {
              "visit_name": "string",
              "python_type": "VARCHAR"
            },
            "key": "public_key_text"
          }
        ],
        "visit_name": "table",
        "key": "public_key",
        "name": "public_key"
      }
    }
"""
    table_name = 'public_key'
    pkey_col = 'id'

    data = {'primary_key': [{'table': table_name, 'column': pkey_col}],
            'entity': 'email_mgmt_app.model.email_mgmt.PublicKey',
            'columns': [{'visit_name': 'column', 'table': {'key': table_name}, 'name': pkey_col,
                         'type_': {'visit_name': 'integer', 'python_type': 'INTEGER'}, 'key': pkey_col},
                        {'visit_name': 'column', 'table': {'key': 'public_key'}, 'name': 'owner_id',
                         'type_': {'visit_name': 'integer', 'python_type': 'INTEGER'}, 'key': 'owner_id'},
                        {'visit_name': 'column', 'table': {'key': 'public_key'}, 'name': 'public_key_text',
                         'type_': {'visit_name': 'string', 'python_type': 'VARCHAR'}, 'key': 'public_key_text'}],
            'relationships': [
                {'is_property': True, 'argument': 'email_mgmt_app.model.email_mgmt.Person', 'is_attribute': False,
                 'is_mapper': False, 'secondary': None, 'local_remote_pairs': [
                    {'local': {'table': {'key': 'public_key'}, 'key': 'owner_id'},
                     'remote': {'table': {'key': 'person'}, 'key': 'id'}}], 'direction': 'MANYTOONE'}], 'local_table': {
            'columns': [{'visit_name': 'column', 'table': {'key': 'public_key'}, 'name': 'id',
                         'type_': {'visit_name': 'integer', 'python_type': 'INTEGER'}, 'key': 'id'},
                        {'visit_name': 'column', 'table': {'key': 'public_key'}, 'name': 'owner_id',
                         'type_': {'visit_name': 'integer', 'python_type': 'INTEGER'}, 'key': 'owner_id'},
                        {'visit_name': 'column', 'table': {'key': 'public_key'}, 'name': 'public_key_text',
                         'type_': {'visit_name': 'string', 'python_type': 'VARCHAR'}, 'key': 'public_key_text'}],
            'visit_name': 'table', 'key': 'public_key', 'name': 'public_key'}}
    result = mapper_schema.load(data)
    assert isinstance(result, MapperInfo)
    assert result.local_table.key == table_name
    assert len(result.primary_key) == 1
    assert result.primary_key[0].table == table_name
    assert result.primary_key[0].column == pkey_col


    print(result)
