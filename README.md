# CustomClean

> Cleanup script that removes unwanted files/folders/links in a given directory based on a JSON.

## Installation

1. Requires Python.
2. Clone custom-clean repo to the desired location.

## Cleaning JSON file

> The file of rules and patterns to be applied to the folder being cleaned.

The JSON file contains 2 elements:
  * The directory tree of the folder being cleaned in the "file_system_data" of
  the json. This is the "rules" portion that tells the script what to do (keep
  or delete) for each file and folder. The tree must match the directory tree
  of the folder being cleaned.
  * The "pattern_list" whose value is a list of pattern strings.

## Patterns

> If the data to be cleaned contains numbered files or folders, you can choose
to apply a rule (keep or delete) for one numbered file to all matching,
numbered files and folders.

To do this, either add a pattern to the "pattern_list" or use the pattern flag
in the cleaning script, below.

#### Example 1

> You have BIDS data and a lot of files and folder contain strings like
"task-rest_run-01". You don't know how many runs there are going to be, but
you want the rules for all task-rest runs to be the same.

 * Put rules in your tree for files and folders whose names contain "task-rest_run-01".
 * Add the pattern "task-rest_run-\*" to the list value of the "pattern_list"
element. (The \* is shorthand for all numbers.)

All rules containing "task-rest_run-" followed by any number will be applied to
all files and folders whose names contain "task-rest_run-" followed by any
number.

Note that if you want the same rules to apply to all of your tasks (not just
task-rest), your pattern can be just "run-\*". Just be a little careful with
patterns until you get used to them.

#### Example 2

> There is a set of files in your data called temp01, temp02, .... Again, you
don't know how many there will be, but you want them all gone.

* Make a rule for a file called temp0 (or temp6 or temp382 - doesn't matter,
just temp followed by a number). Set the value of its "state" to "delete".
* Add a pattern to the list for "temp*".

Don't worry, all of your files with "template" in their names will not
disappear. Only files with the string "temp" followed directly by a number.


## CustomClean Cleaning Script (`cleaning_script.py`)

> Delete things in a given directory based on the rules and patterns given in
the JSON.

Required arguments:
  * -j --json [path to JSON]
  * -d --dir [path to target directory]

Optional arguments:
  * -p --pattern [string to use for numbered series]

Error information will display on the console.
Success information (i.e. what files, directories, and links were removed) will
be written to a file called `custom_clean_success_record.txt` at the top level
of the target directory.


