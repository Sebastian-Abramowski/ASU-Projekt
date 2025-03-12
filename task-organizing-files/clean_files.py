import json
import os
from argparse import ArgumentParser

DEFAULT_CONFIG = {
    'suggested_file_permissions': 'rw-r--r--',
    'problematic_characters': [';', "'", ',', '*', '?', '*', '#', '`', '|'],
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

def get_all_files(main_dir, directories):
    all_files = []
    all_directories = [main_dir, *directories]

    for dir in all_directories:
        for dir_path, _, files in os.walk(dir):
            for file in files:
                file_path = os.path.join(dir_path, file)
                all_files.append(file_path)

    return all_files

def find_temporary_files(main_dir, directories, tmp_extensions):
    files = get_all_files(main_dir, directories)
    return [file for file in files if any(file.endswith(tmp_extension) for tmp_extension in tmp_extensions)]

def find_empty_files(main_dir, directories):
    all_files = get_all_files(main_dir, directories)
    return [file for file in all_files if os.path.getsize(file) == 0]

def find_files_with_problematic_names(main_dir, directories, problematic_characters):
    all_files = get_all_files(main_dir, directories)
    return [file for file in all_files if any(character in os.path.basename(file) for character in problematic_characters)]

def ask_before_deleting(empty_files, what_to_delete: str):
    choice = None
    for empty_file in empty_files:
        if choice == 'ay':
            os.remove(empty_file)
            print(f"Removing file {empty_file} (always yes mode)")
            continue

        print(f"{what_to_delete.capitalize()} was found at: {empty_file}. Do you want to remove it? ", end="")

        if choice == 'ay':
            os.remove(empty_file)
            continue

        choice = get_user_input()
        if choice == 'y' or choice == 'ay':
            print(f"Removing file {empty_file}")
            os.remove(empty_file)

        if choice == 'an':
            print("Skipping all deletions")
            break

def ask_before_renaming(problematic_files, problematic_characters, replacement_character):
    choice = None
    for file_path in problematic_files:
        directory = os.path.dirname(file_path)
        old_filename = os.path.basename(file_path)

        new_filename = old_filename
        for char in problematic_characters:
            new_filename = new_filename.replace(char, replacement_character)
        new_path = os.path.join(directory, new_filename)

        if choice == "ay":
            os.rename(file_path, new_path)
            print(f"Renamed: {file_path} -> {new_path} (always yes mode)")
            continue

        print(f"\nProblematic file found at: {file_path}. Suggest new name is: {new_filename} Do you want to change it? ", end="")
        choice = get_user_input()

        if choice == "y" or choice == "ay":
            os.rename(file_path, new_path)
            print(f"Renamed: {file_path} -> {new_path}")

        if choice == "an":
            print("Skipping all renaming")
            break

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
    parser.add_argument("--problematic-characters", action="store_true", help="Search for files with problematic characters and suggest renaming them")

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

    if (args.problematic_characters):
        problematic_files = find_files_with_problematic_names(args.main_dir, args.directories, config['problematic_characters'])
        print(problematic_files)
        ask_before_renaming(problematic_files, config['problematic_characters'], config['replacement_character'])







