import xmltodict
import json


def xml_to_json(xml_file, json_file):
    with open(xml_file, 'r', encoding='utf-8') as f:
        xml_data = f.read()

    # Parse XML data into a dictionary
    xml_dict = xmltodict.parse(xml_data)

    # Convert dictionary to JSON format
    json_data = json.dumps(xml_dict, indent=4, ensure_ascii=False)

    # Write JSON data to a file
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(json_data)


# Example usage
xml_file = 'data/CORPCODE.xml'
json_file = 'data/CORPCODE.json'

xml_to_json(xml_file, json_file)
