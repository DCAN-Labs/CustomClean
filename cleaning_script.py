#! /usr/bin/env python3

# ------------------------------------------------------------------------
# CustomClean Cleaning Script
#
# Cleanup script that removes unwanted files/folders/links in a given directory
# based on a JSON created by the CustomClean GUI.
#
# Rachel Klein, January 2017

import sys
import os
import shutil
import json
import argparse
import glob
import re

files_to_delete = []
dirs_to_delete = []

PROG = 'CustomClean'
VERSION = '2.0.2'

program_desc = """%(prog)s v%(ver)s:
Cleanup script that removes unwanted files/folders/links in a given directory
based on a JSON created by the CustomClean GUI.
Use -j /path/to/cleaning/JSON and -d /path/to/directory/to/be/cleaned.
#""" % {'prog': PROG, 'ver': VERSION}


def get_parser():

    # ArgumentParser has no "version" parmeter. KJS 11/9/18.
    #parser = argparse.ArgumentParser(description=program_desc, prog=PROG, version=VERSION)
    parser = argparse.ArgumentParser(description=program_desc, prog=PROG)

    parser.add_argument('-j', '--json', dest='json', required=True,
                        help="""Absolute path to a cleaning JSON as created by the CustomClean
GUI.""")

    parser.add_argument('-d', '--dir', dest='dir', required=True,
                        help="""Absolute path to a folder that needs cleaning.
Should have an identical folder structure to the one in the cleaning JSON.""")

    parser.add_argument('-p', '--pattern', dest='pattern', required=False,
                        help="""Pattern string for names that should be
treated identically. E.g. task-rest* will cause task-rest01, task-rest02, etc. to
follow deletion pattern given for task-rest01 in the cleaning JSON.""")

    return parser

def is_dir(d):
    if ('folder' == d['type']):
        return True
    else:
        return False

def is_file(d):
    if ('file' == d['type']):
        return True
    else:
        return False

def get_files_to_delete(d):
    # files_to_delete is a global list.
    for k, v in d.items():
        if is_dir(v):
            get_files_to_delete(v['children'])
        else:
            if 'delete' == v['state']:
                files_to_delete.append(v['rel_path'])

def get_dirs_to_delete(d):
    # dirs_to_delete is a global list.
    for k, v in d.items():
        if is_dir(v):
            if 'delete' == v['state']:
                dirs_to_delete.append(v['rel_path'])
            get_dirs_to_delete(v['children'])



def remove(target_paths):
    """
    Takes a list of paths to be removed/deleted/unlinked and returns information on which ones were
    able to be deleted and which were not.
    """

    not_found = 'Expected and could not find: '
    success = ''

    for p in target_paths:
        str_p = str(p)

        if os.path.isdir(str_p):
            try:
                shutil.rmtree(str_p)
                success += 'Removed directory ' + str_p + '\n'
            except IOError as err:
                sys.stderr.write('You do not have permissions to delete all of the specified directories.')
                sys.stderr.write('IOError: %s.' % err)
                sys.exit(code=1)
            except OSError as err:
                sys.stderr.write('You do not have permissions to delete all of the specified directories.')
                sys.stderr.write('OSError: %s.' % err)
                sys.exit(code=1)
        elif os.path.islink(str_p):
            try:
                os.unlink(str_p)
                success += 'Unlinked ' + str_p + '\n'
            except IOError as err:
                sys.stderr.write('You do not have permissions to delete all of the specified links.')
                sys.stderr.write('IOError: %s.' % err)
                sys.exit(code=1)
            except OSError as err:
                sys.stderr.write('You do not have permissions to delete all of the specified links.')
                sys.stderr.write('OSError: %s.' % err)
                sys.exit(code=1)
        elif os.path.isfile(str_p):
            try:
                os.remove(str_p)
                success += 'Removed file ' + str_p + '\n'
            except IOError as err:
                sys.stderr.write('You do not have permissions to delete all of the specified files.')
                sys.stderr.write('IOError: %s.' % err)
                sys.exit(code=1)
            except OSError as err:
                sys.stderr.write('You do not have permissions to delete all of the specified files.')
                sys.stderr.write('OSError: %s.' % err)
                sys.exit(code=1)
        else:
            not_found += '\n' + str_p

    return not_found, success



def apply_patterns(items_to_delete, pattern_list):
    # Handle patterns. Replace all matches in the paths.
    # Note: we make * match any number of numbers and nothing else.

    # Start with a copy of the items to be deleted.
    cur_items = []
    for item in items_to_delete:
        cur_items.append(item)

    remove_items = []
    new_items = []
    for pattern in pattern_list:

        # Make * match digits and nothing else.
        re_pattern = re.compile(pattern.replace('*', '[0-9]+'))

        for path in cur_items:
            # Replace all matches of re_pattern with pattern.
            new_path, subs = re.subn(re_pattern, pattern, path)
            if subs:
                if not new_path in new_items:
                    # One pattern can turn several paths into the same path.
                    # (Kind of the point.) Eliminate duplicates, or we'll try
                    # to delete the same path multiple times.
                    new_items.append(new_path)

                # Add the current path to a list to be removed from the list
                # outside of the loop.
                if not path in remove_items:
                    remove_items.append(path)

    # The paths in 'remove_items' are being replaced with one or more patterns.
    for item in remove_items:
        cur_items.remove(item)

    # Add the new paths.
    cur_items.extend(new_items)

    return cur_items


def make_paths(paths_to_delete):
    # Paths are relative. They have patterns embedded if any matched.
    # They will be 'expanded' into absolute paths that match, below.

    abs_paths = []
    # List contains relative paths. Get absolute paths. At the same time,
    # make the list we will work from here.
    for path in paths_to_delete:
        abs_path = os.path.join(base_path, path)
        abs_paths.append(abs_path)

    new_paths = []
    for path in abs_paths:
        # Use OS to deal with paths that have wildcards in them.
        if ('*' in path) or ('[0-9]' in path):
            wildcard_paths = glob.glob(path)
            new_paths.extend(wildcard_paths)
        else:
            new_paths.append(path)

    return new_paths



if __name__ == '__main__':

    parser = get_parser()

    args = parser.parse_args()
    json_data = {}
    pattern_list = []

    # Argument is path to JSON, and, optionally, a single pattern.
    # JSON data may contain patterns as well. If the user supplies a pattern,
    # it will be added to the list.
    try:
        with open(args.json) as j:
            whole_json_data = json.load(j)
            pattern_list = whole_json_data['pattern_list']
            json_data = whole_json_data['file_system_data']
    except IOError:
        sys.stderr.write('The specified cleaning JSON could not be read.')
        sys.exit(code=5)

    base_path = args.dir
    if not base_path.endswith('/'):
        base_path = base_path + '/'

    if args.pattern:
        pattern_list.append(args.pattern)

    # Get files to be deleted.
    get_files_to_delete(json_data) # data now in global list files_to_delete[]

    # Get dirs to be deleted.
    # Note: we get the dirs top down, but want to process bottom up.
    #       (we want to delete subdirs before we delete parent dirs).
    #       Thus the 'reverse'.
    get_dirs_to_delete(json_data) # data is now in global list dirs_to_delete[]
    dirs_to_delete.reverse()

    # Must process files before dirs, so add dirs to the end of the list.
    paths_to_delete = files_to_delete
    paths_to_delete.extend(dirs_to_delete)

    patterned_paths = apply_patterns(paths_to_delete, pattern_list)

    # Use os to expand *'s.
    target_paths = make_paths(patterned_paths)

    # Delete/remove/unlink all specified files/directories/links
    not_found_msg, success_msg = remove(target_paths)

    # Send output about files not found to stderr if applicable
    if '\n' in not_found_msg:
        sys.stderr.write(not_found_msg)

    # Save success output to file
    os.chdir(base_path)
    success_file = open('custom_clean_success_record.txt', 'w')
    success_file.write(success_msg)
