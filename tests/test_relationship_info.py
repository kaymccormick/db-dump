er_json = """{
          "secondary": null,
          "is_property": true,
          "mapper": {
            "local_table": {
              "key": "person"
            }
          },
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
          "argument": "email_mgmt_app.model.email_mgmt.Person",
          "key": "owner",
          "is_attribute": false,
          "direction": "MANYTOONE",
          "is_mapper": false
        }"""