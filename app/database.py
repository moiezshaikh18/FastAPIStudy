"""
Database module: Loads and saves shipment data to JSON file.
"""

import json
from pathlib import Path

# Path to the shipments.json file
FILE_PATH = Path(__file__).parent / "shipments.json"

shipments = {}

# 1. Load data from JSON file
with open(FILE_PATH) as file:
    data = json.load(file)
    for value in data:
        shipments[value["id"]] = value

print(shipments)


# 2. Save function to write changes back to JSON file
def save():
    """Saves current shipments dictionary back to shipments.json."""
    with open(FILE_PATH, "w") as file:
        json.dump(list(shipments.values()), file, indent=2)
