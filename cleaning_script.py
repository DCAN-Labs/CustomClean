#! /usr/global/bin/python

# ------------------------------------------------------------------------
# CustomClean version 1.2.0
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

to_delete = []

PROG = 'CustomClean'
VERSION = '1.2.0'
LAST_MOD = '4-27-16'

program_desc = """%(prog)s v%(ver)s:
Cleanup script that removes unwanted files/folders/links in a given directory
based on a JSON created by the CustomClean GUI.
Use -j /path/to/cleaning/JSON and -d /path/to/directory/to/be/cleaned.
#""" % {'prog': PROG, 'ver': VERSION}


def get_parser():

    parser = argparse.ArgumentParser(description=program_desc, prog=PROG, version=VERSION)

    parser.add_argument('-j', '--json', dest='json', required=True,
                        help="""Absolute path to a cleaning JSON as created by the CustomClean
GUI.""")

    parser.add_argument('-d', '--dir', dest='dir', required=True,
                        help="""Absolute path to a folder that needs cleaning.
Should have an identical folder structure to the one in the cleaning JSON.""")

    parser.add_argument('-p', '--pattern', dest='pattern', required=False,
                        help="""String that a series of folders that should be
treated identically will contain. e.g. REST will cause REST1, REST2, etc. to 
follow deletion pattern given for contents of REST1 in the cleaning JSON.""")

    return parser



def get_files_to_delete(d):    
    for k in d:
        if 'state' not in d[k]:
            get_files_to_delete(d[k])
        else:
            if d[k]['state'] == 'delete':
                to_delete.insert(0, d[k]['rel_path'])


def get_file_states(d):
    status_list = []
    for k, v in d.iteritems():
        if type(d[k]) == dict:
            if 'state' in d[k].keys():
                status_list.append(d[k]['state'])
                status_list.extend(get_file_states(v))
    return status_list

def get_dirs_to_delete(d):
    for k in d:
        files = {}
        if k != 'files':
            get_dirs_to_delete(d[k])
        else:
            files.update(d[k])
            file_statuses = get_file_states(files)

            unique_file_statuses = set(file_statuses)
   
            if len(unique_file_statuses) == 1:
                file_status_value = unique_file_statuses.pop()
                if (file_status_value == 'delete'):
                    dir_child_key = files.keys()[-1]
                    dir_to_delete = '/'.join(files[dir_child_key]['rel_path'].split('/')[0:-1])
                    to_delete.append(dir_to_delete)

def get_num_dirs(pattern):

    # Get number of folders following pattern given
    pattern_num = 0
    for k in json_data:
        if type(json_data[k]) == dict:
            for subk in json_data[k]:
                if pattern in subk:
                    pattern_num += 1

    return pattern_num

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
	    except IOError, OSError:
	        print 'You do not have permissions to delete all of the specified directories. Exiting...'
                sys.exit()
        elif os.path.islink(str_p):
	    try:
	        os.unlink(str_p)
	        success += 'Unlinked ' + str_p + '\n'
	    except IOError, OSError:
	        print 'You do not have permissions to remove all of the specified links. Exiting...'
                sys.exit()
        elif os.path.isfile(str_p):
	    try:
	        os.remove(str_p)
	        success += 'Removed file ' + str_p + '\n'
	    except IOError, OSError:
	        print 'You do not have permissions to delete all of the specified files. Exiting...'
                sys.exit()
        else:
            not_found += '\n' + str_p

    return not_found, success

### MAIN SCRIPT ###

parser = get_parser()

args = parser.parse_args()

# Arguments are path to JSON, then path to folder on which to apply cleaning pattern within JSON
try:
    with open(args.json) as j:
        json_data = json.load(j)
except IOError:
    print 'The specified cleaning JSON could not be found. Exiting...'
    sys.exit()

base_path = args.dir
if not base_path.endswith('/'):
    base_path = base_path + '/'

if args.pattern:
    pattern = args.pattern
    dirs_with_pattern = get_num_dirs(pattern)

# Make list of all files/folders/etc. to be removed
get_dirs_to_delete(json_data)  # Get directories first
to_delete.reverse()  # Make sure lower level directories get deleted before those above them
get_files_to_delete(json_data)  # Now add files at beginning so they get deleted first of all

# Create absolute paths for items in to_delete and delete them
paths = make_paths(to_delete)

if all(to_delete):  #If there are no false/empty values in to_delete
    for d in to_delete:
        abs_path = os.path.join(base_path, d)
        # Deal with paths that have wildcards in them
	if '*' in abs_path:
            wildcard_paths = glob.glob(abs_path)
            paths.extend(wildcard_paths)
        else:
            paths.append(abs_path)

        if args.pattern:
    	    # Create corresponding paths for all other folders containing pattern if [pattern]1 is present
            pattern1 = pattern + '1'
            if pattern in abs_path:
                if dirs_with_pattern:
                    for x in xrange(2, dirs_with_pattern + 1):
                        pattern_str = pattern + str(x)
                        paths.append(abs_path.replace(pattern1, pattern_str))
else:
    print "Error: JSON prescribes deleting entire target directory. Please generate another JSON and try again."
    sys.exit()

# Delete/remove/unlink all specified files/directories/links
# If anything is not found, print message.

not_found_msg, success_msg = remove(paths)

# Print output about files not found if applicable
if '\n' in not_found_msg:
    print not_found_msg

# Save success output to file
os.chdir(base_path)
success_file = open('custom_clean_success_record.txt', 'w')
success_file.write(success_msg)
