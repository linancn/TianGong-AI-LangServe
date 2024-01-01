import json

with open("src/tools/lca_data_schema/schema_origin.json", "r") as file:
    data = json.load(file)

with open("src/tools/lca_data_schema/schema.json", "w") as file:
    json.dump(data, file, separators=(",", ":"))
