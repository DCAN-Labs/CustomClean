#! /usr/global/bin/python

# ------------------------------------------------------------------------
# CustomClean version 1.0.0
#  
# Cleanup script that removes unwanted files/folders/links in a given directory
# based on a JSON created by the CustomClean GUI.
#
# Rachel Klein, November 2016

import sys
import os
import shutil
import json
import ntpath

to_delete = []


def get_files_to_delete(d):    
    for k in d:
        if 'state' not in d[k]:
            get_files_to_delete(d[k])
        else:
            if d[k]['state'] == 'delete':
                to_delete.append(d[k]['rel_path'])


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

# Arguments are path to JSON, then path to folder on which to apply cleaning pattern within JSON
try:
    with open(sys.argv[1]) as j:
        json_data = json.load(j)
except IOError:
    print 'The specified cleaning JSON could not be found. Exiting...'
    sys.exit()

base_path = sys.argv[2]
if not base_path.endswith('/'):
    base_path = base_path + '/'

# Make list of all files/folders/etc. to be removed
get_files_to_delete(json_data)
get_dirs_to_delete(json_data)

# Make sure all entries within to_delete are unique
to_delete = list(set(to_delete))

# Create absolute paths for items in to_delete and delete them
paths = []

if all(to_delete):  #If there are no false/empty values in to_delete
    for d in to_delete:
        abs_path = ntpath.join(base_path, d)
	paths.append(abs_path)
	# Create corresponding paths for REST2 to REST20 if REST1 is present
        if 'REST1' in abs_path:
            for x in xrange(2, 21):
                rest_str = 'REST' + str(x)
                paths.append(abs_path.replace('REST1', rest_str))

# Delete/remove/unlink all specified files/directories/links
# If some items cannot be located, notify user

for p in paths:
    str_p = str(p)
    
    # TODO: Test with symbolic links
    if os.path.isdir(str_p):
	try:
	    shutil.rmtree(str_p)
	    print 'Removing directory ' + str_p 
	except IOError, OSError:
	    print 'You do not have permissions to delete all of the specified directories. Exiting...'
            sys.exit()
    elif os.path.islink(str_p):
	try:
	    os.unlink(str_p)
	    print 'Unlinking ' + str_p 
	except IOError, OSError:
	    print 'You do not have permissions to remove all of the specified links. Exiting...'
            sys.exit()
    elif os.path.isfile(str_p):
	try:
	    os.remove(str_p)
	    print 'Removing file ' + str_p 
	except IOError, OSError:
	    print 'You do not have permissions to delete all of the specified files. Exiting...'
            sys.exit()
    else:
	print '\nExpected and could not find:'
	print str_p

