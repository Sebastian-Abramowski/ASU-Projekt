import json
import os
from argparse import ArgumentParser

DEFAULT_CONFIG = {
    'suggested_file_permissions': 'rw-r--r--',
    'problematic_characters': [':', "'", '.', ',', '*', '?', '*', '#', '`', '|', '\\'],
    'replacement_character': '_',
    'temporary_file_extensions': ['.tmp', '.log']
}

def load_config(filepath):
    try:
        with open(filepath) as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Configuration file was not found at {filepath}. Using default configuration.")
        return DEFAULT_CONFIG

def find_temporary_files(main_dir, directories, tmp_extensions):
    temporary_files = []
    all_directores = [main_dir, *directories]

    for dir in all_directores:
        for dir_path, _, files in os.walk(dir):
            for file in files:
                file_path = os.path.join(dir_path, file)

                if any(file.endswith(tmp_extension) for tmp_extension in tmp_extensions):
                    temporary_files.append(file_path)

    return temporary_files



def find_empty_files(main_dir, directories):
    empty_files = []
    all_directories = [main_dir, *directories]

    for dir in all_directories:
        for dir_path, _, files in os.walk(dir):
            for file in files:
                file_path = os.path.join(dir_path, file)

                if os.path.getsize(file_path) == 0:
                    empty_files.append(file_path)

    return empty_files

def ask_before_deleting(empty_files, what_to_delete: str):

    choice = None
    for empty_file in empty_files:
        if choice == 'an':
            continue
        print(f"{what_to_delete.capitalize()} was found at: {empty_file}. Do you want to remove it? ")

        if choice == 'ay':
            os.remove(empty_file)
            continue

        choice = get_user_input()
        if choice == 'y':
            print(f"Removing file {empty_file}")
            os.remove(empty_file)

def get_user_input():
    accepted_values = ['y', 'n', 'ay', 'an']
    while True:
        user_input = input("[Y]/n/ay/an? ").lower()

        if not user_input:
            return 'y'

        if user_input in accepted_values:
            return user_input

        print("Invalid input. Please enter your choice again. ")




def parse_arguments():
    parser = ArgumentParser(description="Clean files from given directories")

    parser.add_argument("main_dir", help="Main directory to organize files to")
    parser.add_argument("directories", nargs="+", help="Directories to clean")
    parser.add_argument("-c", "--config", help="Path to json configuration file")

    parser.add_argument("--empty", action="store_true", help="Search for empty files and suggest deleting them")
    parser.add_argument("--temporary", action="store_true", help="Search for temporary files and suggest deleting them")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    config = load_config(args.config)

    print("Main directory: ", args.main_dir)
    print("Directories: ", args.directories)
    print("Configuration: ", config)

    if (args.empty):
        empty_files = find_empty_files(args.main_dir, args.directories)
        ask_before_deleting(empty_files, "empty file")

    if (args.temporary):
        temporary_files = find_temporary_files(args.main_dir, args.directories, config['temporary_file_extensions'])
        ask_before_deleting(temporary_files, "temporary file")




