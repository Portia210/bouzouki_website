import json

# Open the JSON file for reading
with open('collections.json', 'r') as file:
    # Load the JSON data
    collections = json.load(file)

for index, collection in enumerate(collections):
    print(collection['title'])   # Access the value associated with the 'href' key
    print(f"number of songs {collection['songs_number']}")

    collection["download"] = "waiting"

collections_file_path = "collections.json"

# Write collections data to the JSON file
with open(collections_file_path, "w") as json_file:
    json.dump(collections, json_file, indent=4)
