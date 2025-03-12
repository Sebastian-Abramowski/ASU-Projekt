import json
import os
import stat
from argparse import ArgumentParser
from collections import defaultdict
from hashlib import md5
import shutil
import sys

DEFAULT_CONFIG = {
    'suggested_file_permissions': 'rw-r--r--',
    'problematic_characters': [';', "'", ',', '*', '?', '*', '#', '`', '|'],
    'replacement_character': '_',
    'temporary_file_extensions': ['.tmp', '.log']
}

YES = 'y'
NO = 'n'
ALWAYS_YES = 'ay'
ALWAYS_NO = 'an'

def load_config(filepath):
    try:
        with open(filepath) as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Configuration file was not found at {filepath}. Using default configuration.")
        return DEFAULT_CONFIG


def yield_all_files(directories):
    for dir in directories:
        for dir_path, _, files in os.walk(dir):
            for file in files:
                yield os.path.join(dir_path, file)


def find_files(main_dir, directories, condition_func):
    return [file for file in yield_all_files([main_dir, *directories]) if condition_func(file)]


def find_temporary_files(main_dir, directories, tmp_extensions):
    return find_files(main_dir, directories, lambda file: any(file.endswith(tmp_extension) for tmp_extension in tmp_extensions))


def find_empty_files(main_dir, directories):
    return find_files(main_dir, directories, lambda file: os.path.getsize(file) == 0)


def find_files_with_problematic_names(main_dir, directories, problematic_characters):
    return find_files(main_dir, directories, lambda file: any(character in os.path.basename(file) for character in problematic_characters))


def get_file_hash(file_path):
    with open(file_path, "rb") as f:
        return md5(f.read()).hexdigest()


def handle_files_with_duplicate_content(main_dir, directories) -> None:
    files_content_dict = defaultdict(list)

    for file_path in yield_all_files([main_dir, *directories]):
        file_hash = get_file_hash(file_path)
        files_content_dict[file_hash].append(file_path)

    for file_hash, paths in files_content_dict.items():
        if len(paths) <= 1:
            continue

        paths.sort(key=os.path.getmtime)

        print(f"Files with duplicate content (hash: {file_hash}), from oldest to latest:")
        for num, path in enumerate(paths, start=1):
            print(f"{num}. {path} ", "(OLDEST)" if num == 1 else "")

        num_of_file_to_keep = choose_number_of_file_to_keep(len(paths))
        if num_of_file_to_keep is None:
            print(f"Keeping all files with hash {file_hash}")
            continue

        index_of_file_to_keep = num_of_file_to_keep - 1
        files_to_delete = [path for index, path in enumerate(paths) if index != index_of_file_to_keep]
        for filepath in files_to_delete:
            os.remove(filepath)
            print(f"Deleted: {filepath})")


def handle_files_with_repeated_names(main_dir, directories):
    files_dict = defaultdict(list)

    for file_path in yield_all_files([main_dir, *directories]):
        filename = os.path.basename(file_path)
        files_dict[filename].append(file_path)

    for filename, paths in files_dict.items():
        if len(paths) <= 1:
            continue

        paths.sort(key=os.path.getmtime, reverse=True)

        print(f"Repeated files with name (from latest to oldest): {filename}")
        for num, path in enumerate(paths, start=1):
            print(f"{num}. {path} ", "(LATEST)" if num == 1 else "")

        num_of_file_to_keep = choose_number_of_file_to_keep(len(paths))
        if num_of_file_to_keep is None:
            print(f"Keeping all files with name {filename}")
            continue

        index_of_file_to_keep = num_of_file_to_keep - 1
        files_to_delete = [path for index, path in enumerate(paths) if index != index_of_file_to_keep]
        for filepath in files_to_delete:
            os.remove(filepath)
            print(f"Deleted: {filepath}")


def choose_number_of_file_to_keep(number_of_files):
    valid_choices = [str(i) for i in range(1, number_of_files + 1)]
    while True:
        user_input = input(f"Enter number of the file to keep [1-{number_of_files}] (rest of the files will be deleted) or press Enter to keep all: ").strip()

        if not user_input:
            return None

        if user_input in valid_choices:
            return int(user_input)

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
    for file in yield_all_files([main_dir, *directories]):
        file_stat = os.stat(file)
        file_permissions = stat.filemode(file_stat.st_mode)[1:]

        if (file_permissions != suggested_permissions):
            print(f"File {file} has unusual permissions: {file_permissions}. Suggested permissions are {suggested_permissions}. Do you want to change them? ", end="")

            if choice == ALWAYS_YES:
                os.chmod(file, octal_suggested_permissions)
                print(f"Changed permissions for file {file} to {suggested_permissions} (always yes mode)")
                continue

            choice = get_user_input()
            if choice == YES or choice == ALWAYS_YES:
                os.chmod(file, octal_suggested_permissions)
                print(f"Changed permissions for file {file} to {suggested_permissions}")

            if choice == ALWAYS_NO:
                print("Skipping all permission changes")
                break

def ask_before_deleting(empty_files, what_to_delete):
    choice = None
    for empty_file in empty_files:
        if choice == ALWAYS_YES:
            os.remove(empty_file)
            print(f"Removing file {empty_file} (always yes mode)")
            continue

        print(f"{what_to_delete.capitalize()} was found at: {empty_file}. Do you want to remove it? ", end="")

        choice = get_user_input()
        if choice == YES or choice == ALWAYS_YES:
            print(f"Removing file {empty_file}")
            os.remove(empty_file)

        if choice == ALWAYS_NO:
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

        if choice == ALWAYS_YES:
            os.rename(file_path, new_path)
            print(f"Renamed: {file_path} -> {new_path} (always yes mode)")
            continue

        print(f"Problematic file found at: {file_path}. Suggest new name is: {new_filename} Do you want to change it? ", end="")
        choice = get_user_input()

        if choice == YES or choice == ALWAYS_YES:
            os.rename(file_path, new_path)
            print(f"Renamed: {file_path} -> {new_path}")

        if choice == ALWAYS_NO:
            print("Skipping all renaming")
            break

def get_user_input():
    accepted_values = [YES, NO,
                       ALWAYS_YES, ALWAYS_NO]
    while True:
        user_input = input("[Y]/n/ay/an? ").lower()

        if not user_input:
            return YES

        if user_input in accepted_values:
            return user_input

        print("Invalid input. Please enter your choice again. ")


def transfer_files_to_main_dir(main_dir, directories, transfer_func):
    action_names = {
        shutil.move: "Moved",
        shutil.copy2: "Copied"
    }
    action_performed = action_names.get(transfer_func, "Transferred")

    for directory in directories:
        for dir_path, _, files in os.walk(directory):
            for file in files:
                source_path = os.path.join(dir_path, file)
                relative_path = os.path.relpath(source_path, directory)

                destination_path = os.path.join(main_dir, relative_path)
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)

                transfer_func(source_path, destination_path)
                print(f"{action_performed} file from: {source_path} to: {destination_path}")

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
    parser.add_argument("--find-duplicate-content", action="store_true", help="Search for file with duplicate content and suggest deleting some of them")

    parser.add_argument("--copy-files-to-main-dir", action="store_true", help="Copy all files to main directory")
    parser.add_argument("--move-files-to-main-dir", action="store_true", help="Move all files to main directory")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    config = load_config(args.config)

    print(f"Main directory set to: {args.main_dir}")
    print(f"Additional directories are set to: {args.directories}\n")
    print("=" * 25)

    if (config['suggested_file_permissions'] and len(config['suggested_file_permissions']) != 9):
        print("Invalid permissions format. Please provide permissions in 9 characters format (e.g. rw-r--r--). Exiting.")
        sys.exit(1)

    if args.empty:
        empty_files = find_empty_files(args.main_dir, args.directories)
        ask_before_deleting(empty_files, "empty file")
        print("=" * 25)

    if args.temporary:
        temporary_files = find_temporary_files(args.main_dir, args.directories, config['temporary_file_extensions'])
        ask_before_deleting(temporary_files, "temporary file")
        print("=" * 25)

    if args.problematic_characters:
        problematic_files = find_files_with_problematic_names(args.main_dir, args.directories, config['problematic_characters'])
        ask_before_renaming(problematic_files, config['problematic_characters'], config['replacement_character'])
        print("=" * 25)

    if args.unusual_attributes:
        handle_files_with_unusual_attributes(args.main_dir, args.directories, config['suggested_file_permissions'])
        print("=" * 25)

    if args.repeated_names:
        handle_files_with_repeated_names(args.main_dir, args.directories)
        print("=" * 25)

    if args.find_duplicate_content:
        handle_files_with_duplicate_content(args.main_dir, args.directories)
        print("=" * 25)

    if args.move_files_to_main_dir:
        transfer_files_to_main_dir(args.main_dir, args.directories, shutil.move)
        print("=" * 25)

    if args.copy_files_to_main_dir:
        transfer_files_to_main_dir(args.main_dir, args.directories, shutil.copy2)
        print("=" * 25)

