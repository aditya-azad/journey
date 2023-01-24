import sys
import json
import datetime
import subprocess
import os


CONFIG_FILE_PATH = "./journey_config.json"


def error(message):
    print(f"ERROR: {message}")
    sys.exit(1)


def read_validate_config():
    if not os.path.exists(CONFIG_FILE_PATH):
        error("Cannot find the config file, read the documentation.")
    with open(CONFIG_FILE_PATH, "r") as file:
        data = json.load(file)
    # log dir validation
    if "log_dir" not in data:
        error("Please specify a log_dir in the config file.")
    if not os.path.isdir(data["log_dir"]):
        error("log_dir must be a folder, recheck the path or create one.")
    # editor validation
    if "editor" not in data:
        error("Please specify an editor in the config file.")
    return data


if __name__ == "__main__":
    config = read_validate_config()
    file_path = os.path.join(config["log_dir"], datetime.datetime.now().strftime("%Y-%m-%d") + ".md")
    subprocess.run([config["editor"], file_path])
