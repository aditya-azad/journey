import argparse
import json
import datetime
import subprocess
import os
import re
import hashlib

CONFIG_FILE_PATH = "./journey_config.json"
DATABASE_FILE_NAME = ".journey_db.json"


def write_json(file_path, data):
    """Write the data into the file, throw an error if cannot find the path"""
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    except:
        error(f"Cannot write data into: {file_path}, check if path exists.")


def read_json(file_path):
    """Read json file and return the data, throw error if unable to read file"""
    if not os.path.exists(file_path):
        error(f"Cannot find the file: {file_path}")
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def error(message):
    """Print error message and exit"""
    print(f"ERROR: {message}")
    exit(1)


def get_file_hash(file_path):
    """Get MD5 hash of the file given, no checks on opening the file"""
    with open(file_path, "rb") as file:
        data = file.read()
    return hashlib.md5(data).hexdigest()


def get_file_tags(file_path):
    """Read all the lines starting with \"tags:\" (case insensitive) and return
    list of all the comma separated values after. Only unique values returned"""
    tags = []
    with open(file_path, "r") as file:
        for line in file.readlines():
            tag_keyword, *rest = line.strip().split(":")
            if tag_keyword.lower() == "tags" and rest:
                t = rest[0].split(",")
                t = map(lambda x: x.strip(), t)
                t = filter(lambda x: x, t)
                tags.extend(t)
    return list(set(tags))


def read_validate_config():
    """Read the config file and return validate the entries (see documentation).
    Return the data"""
    data = read_json(CONFIG_FILE_PATH)
    # log dir validation
    if "log_dir" not in data:
        error("Please specify a log_dir in the config file.")
    if not os.path.isdir(data["log_dir"]):
        error("log_dir must be a folder, recheck the path or create one.")
    # editor validation
    if "editor" not in data:
        error("Please specify an editor in the config file.")
    return data


def open_log_file_by_date(log_dir, editor, date):
    """Open the log file with the specific date in desired editor"""
    file_path = os.path.join(log_dir, date.strftime("%Y-%m-%d") + ".md")
    subprocess.run([editor, file_path])


def update_data_in_memory(log_dir, data):
    """Read the database file and change the data variable passed into the
    function if the files have changed or deleted. Return true if the data was
    changed, else false"""
    is_updated = False
    relevant_files_in_dir = set()
    for file in os.listdir(log_dir):
        if re.search("^\d{4}-\d{2}-\d{2}.md$", file):
            relevant_files_in_dir.add(file)
            file_path = os.path.join(log_dir, file)
            file_hash = get_file_hash(file_path)
            if (file in data["files"]) and \
               (data["files"][file]["hash"] == file_hash):
                continue
            is_updated = True
            file_tags = get_file_tags(file_path)
            data["files"][file] = {
                "hash": file_hash,
                "tags": file_tags
            }
    files_to_delete = []
    for file in data["files"]:
        if file not in relevant_files_in_dir:
            files_to_delete.append(file)
    for file in files_to_delete:
        is_updated = True
        del data["files"][file]
    return is_updated


def update_get_db_data(log_dir):
    """Calls update data, creates and returns skeleton data structure if there
    was no database file present"""
    db_file_path = os.path.join(log_dir, DATABASE_FILE_NAME)
    data = {
        "last_search_results": [],
        "files": {},
    }
    if os.path.exists(db_file_path):
        data = read_json(db_file_path)
        if update_data_in_memory(log_dir, data):
            write_json(db_file_path, data)
    else:
        write_json(db_file_path, data)
    return data


def read_args():
    parser = argparse.ArgumentParser(
        prog = "Journey",
        description = "Command line journaling utility"
    )
    parser.add_argument("-s", "--search")
    parser.add_argument("-o", "--open")
    return parser.parse_args()


def run(args):
    config = read_validate_config()
    if args.search:
        data = update_get_db_data(config["log_dir"])
        # TODO: 
    else:
        open_log_file_by_date(
            config["log_dir"],
            config["editor"],
            datetime.datetime.now()
        )


if __name__ == "__main__":
    run(read_args())