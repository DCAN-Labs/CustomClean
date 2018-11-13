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

to_delete = []

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
                        help="""Pattern string for folders that should be
treated identically. E.g. task-rest* will cause task-rest01, task-rest)2, etc. to
follow deletion pattern given for contents of task-rest01 in the cleaning JSON.""")

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

def next(d):
    return d['children']

def get_files_to_delete(d):
    # to_delete is a global list.
    for k, v in d.items():
        if is_dir(v):
            get_files_to_delete(next(v))
        else:
            if 'delete' == v['state']:
                # to_delete.insert(0, d[k]['rel_path'])
                to_delete.append(v['rel_path'])

def get_dirs_to_delete(d):
    # to_delete is a global list.
    for k, v in d.items():
        if is_dir(v):
            if 'delete' == v['state']:
                to_delete.append(v['rel_path'])
            get_dirs_to_delete(next(v))



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

    abs_paths = []

    # To delete contains relative paths. Get absolute paths.
    # At the same time, make the list we will work from
    # here.
    for item in items_to_delete:
        abs_path = os.path.join(base_path, item)
        abs_paths.append(abs_path)

    # Handle patterns. Replace matches in the paths.
    for pattern in pattern_list:

        for idx, path in enumerate(abs_paths):

            # First, just see if we find each of the parts of the pattern
            # in the whole path. Doesn't mean it's a match - just a candidate
            # for further processing.
            patt_parts = pattern.split('*')
            found = 0
            for part in patt_parts:
                if part in path:
                    found += 1
                else:
                    break

            if len(patt_parts) == found:

                # Break up the path into all of its parts. Only an
                # actual match if the pattern is wholly in one or more
                # of its subdirectories.
                subdirs = path.split(os.sep)

                # To replace whole pattern, use re.
                re_pattern = re.compile(pattern.replace('*', '.*'))

                new_path = ''
                for subdir in subdirs:
                    # In each subdirectory, replace whatever matches
                    # with the original pattern string.
                    new_subdir = re.sub(re_pattern, pattern, subdir)
                    new_path += (os.sep + new_subdir)

                abs_paths[idx]=new_path

    return abs_paths


def make_paths(paths_to_delete):
    # All paths are absolute, and all have patterns imbedded if any matched.
    # They will be 'expanded' into all paths that match, below.

    if all(paths_to_delete):  #If there are no false/empty values in to_delete

        new_paths = []

        for path in paths_to_delete:
            # Deal with paths that have wildcards in them
            if '*' in path:
                wildcard_paths = glob.glob(path)
                new_paths.extend(wildcard_paths)
            else:
                new_paths.append(path)

        return new_paths

    else:
        sys.stderr.write('JSON prescribes deleting entire target directory. Please generate another JSON and try again.')
        sys.exit(code=4)



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

    # Make list of all files/folders/etc. to be removed
    # Note: This is done in reverse: we get dirs first, top down. Then files.
    #       But we do the processing in reverse, because we need to delete
    #       files, then subdirectories, then parent directories.
    #       Thus the 'reverse' at the end.
    get_dirs_to_delete(json_data)
    get_files_to_delete(json_data)
    to_delete.reverse()

    # Create absolute paths, with patterns in them, for items in to_delete
    patterned_paths = apply_patterns(to_delete, pattern_list)

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
