import json
import logging

from db_dump import RelationshipSchema

logger = logging.getLogger(__name__)

def test_relationship_schema_load():
    schema = RelationshipSchema()
    the_json = '{"is_property": true, "is_mapper": false, "secondary": null, "local_remote_pairs": [{"local": {"key": "owner_id", "table": {"key": "file"}}, "remote": {"key": "id", "table": {"key": "person"}}}], "direction": "MANYTOONE", "is_attribute": false, "argument": "heptet_app.model.email_mgmt.Person"}'
    #data = json.loads(the_json)
    the_direction = 'MANYTOONE'
    data = {'is_property': True, 'is_mapper': False, 'secondary': None, 'local_remote_pairs': [{'local': {'key': 'owner_id', 'table': {'key': 'file'}}, 'remote': {'key': 'id', 'table': {'key': 'person'}}}], 'direction': the_direction, 'is_attribute': False, 'argument': 'heptet_app.model.email_mgmt.Person'}
    logger.warning("data = %s", data)
    result = schema.load(data)
    logger.warning("result is %s", result)
    assert result.direction == the_direction

