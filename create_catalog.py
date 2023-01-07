import json
import copy

INPUT_FILE = 'discover.json'
OUTPUT_FILE = 'singer_catalog/qa/source_salesforce_catalog.json'

output_data = {'streams': []}

with open(INPUT_FILE, 'r') as f:
    data_dict = json.load(f)

for stream in data_dict['streams']:
    current_stream = copy.deepcopy(stream)
    for field in stream['schema']['properties']:
        if 'OldValue' in current_stream['schema']['properties'] and current_stream['schema']['properties']['OldValue'] == {}:
            current_stream['schema']['properties']['OldValue'] = {"type": ["null","string"]}
        if 'NewValue' in current_stream['schema']['properties'] and current_stream['schema']['properties']['NewValue'] == {}:
            current_stream['schema']['properties']['NewValue'] = {"type": ["null","string"]}        
        if current_stream['schema']['properties'][field] == {}:
            current_stream['schema']['properties'].pop(field, None)
    replication_key = stream['metadata'][-1]['metadata']['valid-replication-keys'][0]
    current_stream['metadata'][-1]['metadata']['replication-key'] = replication_key
    current_stream['metadata'][-1]['metadata']['selected'] = "true"
    current_stream['metadata'][-1]['metadata']['replication-method'] = "INCREMENTAL"
    output_data['streams'].append(current_stream)

with open(OUTPUT_FILE, 'w') as f:
    json.dump(output_data, f, indent=4)