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
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    except:
        error(f"Cannot write data into: {file_path}, check if path exists.")


def read_json(file_path):
    if not os.path.exists(file_path):
        error(f"Cannot find the file: {file_path}")
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def error(message):
    print(f"ERROR: {message}")
    exit(1)


def get_file_hash(file_path):
    with open(file_path, "rb") as file:
        data = file.read()
    return hashlib.md5(data).hexdigest()


def get_file_tags(file_path):
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
    file_path = os.path.join(log_dir, date.strftime("%Y-%m-%d") + ".md")
    subprocess.run([editor, file_path])


def update_data_in_memory(log_dir, data):
    is_updated = False
    for file in os.listdir(log_dir):
        if re.search("^\d{4}-\d{2}-\d{2}.md$", file):
            file_path = os.path.join(log_dir, file)
            file_hash = get_file_hash(file_path)
            if (file in data["files"]) and (data["files"][file]["hash"] == file_hash):
                continue
            is_updated = True
            file_tags = get_file_tags(file_path)
            data["files"][file] = {
                "hash": file_hash,
                "tags": file_tags
            }
    return is_updated


def update_get_db_data(log_dir):
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
        open_log_file_by_date(config["log_dir"], config["editor"], datetime.datetime.now())


if __name__ == "__main__":
    run(read_args())