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
    list of all the comma separated values after. tags are not allowed to have
    spaces, so it replaces them with -. Only unique values returned"""
    tags = []
    with open(file_path, "r") as file:
        for line in file.readlines():
            tag_keyword, *rest = line.strip().split(":")
            if tag_keyword.lower() == "tags" and rest:
                t = rest[0].split(",")
                t = map(lambda x: x.strip(), t)
                t = map(lambda x: x.replace(" ", "-"), t)
                t = filter(lambda x: x, t)
                tags.extend(t)
    return list(set(tags))


def search_tags(tags_string, log_dir):
    """Finds the files with the tags given and adds it to the last results
    value"""
    db_data = get_db_data(log_dir)
    inv_index = {}
    for file, data in db_data["files"].items():
        for tag in data["tags"]:
            if tag not in inv_index:
                inv_index[tag] = set()
            inv_index[tag].add(file)
    tags = tags_string.strip().split(" ")
    tags = list(map(lambda x: x.strip(), tags))
    files_result = set()
    for i in range(len(tags)):
        if tags[i] in inv_index:
            files_result = files_result.union(inv_index.get(tags[i]))
    files_result = list(files_result)
    db_data["last_search_results"] = files_result
    write_json(os.path.join(log_dir, DATABASE_FILE_NAME), db_data)
    return files_result


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


def update_data(log_dir, data):
    """Read the database file and write the data if changed from before which is
    passed into the function. checks if the files have been changed or deleted.
    Return true if updated the database"""
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
    if is_updated:
        write_json(os.path.join(log_dir, DATABASE_FILE_NAME), data)
    return is_updated


def get_db_data(log_dir):
    """Creates and returns skeleton data structure if there was no database file
    present, else returns the data from the file"""
    db_file_path = os.path.join(log_dir, DATABASE_FILE_NAME)
    data = {
        "last_search_results": [],
        "files": {},
    }
    if os.path.exists(db_file_path):
        data = read_json(db_file_path)
    return data


def read_args():
    """Read the arguments and return them"""
    parser = argparse.ArgumentParser(
        prog = "Journey",
        description = "Command line journaling utility. Run without arguments to open entry for current date."
    )
    parser.add_argument("-s", "--search",
        help="Search for tags in your journal. If your tag has spaces, replace those with \"-\" for search.")
    parser.add_argument("-o", "--open",
        help="Open the journal entry at the given index from the previous search result. Use \"n\" or \"p\" as index to get next or previous entry.")
    parser.add_argument("-u", "--force_update", action="store_true",
        help="Force update the database after manual change to an entry.")
    return parser.parse_args()


def run(args):
    """Run the program"""
    config = read_validate_config()
    if args.force_update:
        data = get_db_data(config["log_dir"])
        if update_data(config["log_dir"], data):
            print("Updated the database!")
        else:
            print("There was nothing to be updated.")
    elif args.search:
        data = get_db_data(config["log_dir"])
        results = search_tags(args.search, config["log_dir"])
        print("Search results:\n")
        for i, result in enumerate(results):
            print(f"{i + 1}: {result[:-3]}")
        print()
        print("Use -o flag with the index to open one of the files.")
    else:
        open_log_file_by_date(
            config["log_dir"],
            config["editor"],
            datetime.datetime.now()
        )


if __name__ == "__main__":
    run(read_args())