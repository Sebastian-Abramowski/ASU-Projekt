import json
import os
import stat
from argparse import ArgumentParser
from collections import defaultdict

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

def handle_files_with_repeated_names(main_dir, directories):
    all_files = get_all_files(main_dir, directories)
    files_dict = defaultdict(list)

    for file_path in all_files:
        filename = os.path.basename(file_path)
        files_dict[filename].append(file_path)

    for filename, paths in files_dict.items():
        if len(paths) <= 1:
            continue

        paths.sort(key=os.path.getmtime, reverse=True)

        print(f"Repeated files with name: {filename}")
        for num, path in enumerate(paths, start=1):
            print(f"{num}. {path} ", "(LATEST)" if num == 1 else "")

        index_of_file_to_keep = select_file_to_keep(len(paths))

        if index_of_file_to_keep is None:
            print(f"Keeping all files with name {filename}")
            continue

        print(f"Deleting all files with repeated names except {paths[index_of_file_to_keep]}")
        files_to_delete = [path for index, path in enumerate(paths) if index != index_of_file_to_keep]
        for filepath in files_to_delete:
            os.remove(filepath)
            print(f"Deleted: {filepath}")

def select_file_to_keep(number_of_files):
    valid_choices = [str(i) for i in range(1, number_of_files + 1)]
    while True:
        user_input = input(f"Enter number of the file to keep [1-{number_of_files}] or press Enter to keep all: ").strip()

        if not user_input:
            return None

        if user_input in valid_choices:
            return int(user_input) - 1

        print("Invalid input. Please enter your choice again. ")

def convert_str_permissions_to_octal(permissions):
    permission_map = {
        "r": 4, "w": 2, "x": 1
    }

    octal_str = ""
    for i in range(0, len(permissions), 3):
        part = permissions[i:i+3]
        octal_str += str(sum(permission_map.get(char, 0) for char in part))

    return int(octal_str, 8)


def handle_files_with_unusual_attributes(main_dir, directories, suggested_permissions):
    octal_suggested_permissions = convert_str_permissions_to_octal(suggested_permissions)


    choice = None
    all_files = get_all_files(main_dir, directories)

    for file in all_files:
        file_stat = os.stat(file)
        file_permissions = stat.filemode(file_stat.st_mode)[1:]

        if (file_permissions != suggested_permissions):
            print(f"File {file} has unusual permissions: {file_permissions}. Suggested permissions are {suggested_permissions}. Do you want to change them? ", end="")

            if choice == 'ay':
                os.chmod(file, octal_suggested_permissions)
                print(f"Changed permissions for file {file} to {suggested_permissions} (always yes mode)")
                continue

            choice = get_user_input()
            if choice == 'y' or choice == 'ay':
                os.chmod(file, octal_suggested_permissions)
                print(f"Changed permissions for file {file} to {suggested_permissions}")

            if choice == 'an':
                print("Skipping all permission changes")
                break

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
    parser.add_argument("--unusual-attributes", action="store_true", help="Search for files with unusual attributes and suggest changing them")
    parser.add_argument("--repeated-names", action="store_true", help="Search for files with repeated names and suggest renaming them")


    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    config = load_config(args.config)

    print("Main directory: ", args.main_dir)
    print("Directories: ", args.directories)
    print("Configuration: ", config)

    # TODO: walidacja permissions 9 wyraozwego

    if (args.empty):
        empty_files = find_empty_files(args.main_dir, args.directories)
        ask_before_deleting(empty_files, "empty file")

    if (args.temporary):
        temporary_files = find_temporary_files(args.main_dir, args.directories, config['temporary_file_extensions'])
        ask_before_deleting(temporary_files, "temporary file")

    if (args.problematic_characters):
        problematic_files = find_files_with_problematic_names(args.main_dir, args.directories, config['problematic_characters'])
        ask_before_renaming(problematic_files, config['problematic_characters'], config['replacement_character'])

    if (args.unusual_attributes):
        handle_files_with_unusual_attributes(args.main_dir, args.directories, config['suggested_file_permissions'])

    if (args.repeated_names):
        handle_files_with_repeated_names(args.main_dir, args.directories)






