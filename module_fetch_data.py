import os
import json
from typing import List

def find_and_load_json(partial_names: List[str], directory):
    filename = ''.join(partial_names) + '.json'
    print(filename)
    filepath = os.path.join('backend2', directory, filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception:
        return None