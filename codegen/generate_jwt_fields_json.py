import json
import os

def generate_jwt_fields_json(jwt_fields, output_path='jwt_fields.json'):
    data = {"jwt_field": jwt_fields}
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
