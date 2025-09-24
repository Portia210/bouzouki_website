import json

file_path = "jsons/collections.json"

with open(file_path, "r") as file:
    imported_json = json.load(file)

with open(file_path, "w", encoding="utf-8") as file:
    json.dump(imported_json, file, ensure_ascii=False, indent=4)







