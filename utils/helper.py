import tempfile
import json
import os

def save_uploaded_zip(uploaded_file):
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, uploaded_file.name)
    with open(zip_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return zip_path

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def file_exists(path):
    return os.path.exists(path)