#! /usr/bin/env python3

# ------------------------------------------------------------------------
# CustomClean GUI
#
# GUI that helps user create a JSON showing a pattern of unwanted files/folders/links
# that can be later applied to many directories using the main CustomClean script.
#
# Rachel Klein, January 2017

import functools
import json
import os
import re
import sys
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

appId = 'Custom Clean'
mainWin = None


class SelectionWindow(QDialog):
    """
    GUI window where user selects items to be deleted in the chosen directory.
    """

    def __init__(self, parent=None, model=None):
        QDialog.__init__(parent)

        if not model:
            return

        self.view = QTreeView()
        self.view.setModel = model

        layout = QVBoxLayout(self)


        # KJS TODO: this needs to be done for each column (aka 'section') in Qt5
        # Make window resize to contents
        #self.view.header().setResizeMode(QHeaderView.ResizeToContents)
        #self.view.header().setStretchLastSection(False)

        # Set root directory to example path chosen earlier by user
        self.view.setRootIndex(model.index(example_path))

        # Set appearance of SelectionWindow object
        self.resize(1000, 500)
        self.setWindowTitle("Choose Items to Delete")
        layout.addWidget(self.view)

        # Add OK and Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(model.makeJSON)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class CheckableDirModel(QAbstractItemModel):
    """
    Model populated by a directory tree. The model's data may be from
    a 'walk' of the directory chosen by the user, or may be loaded
    from an existing JSON file written by the program.
    To the viewer, it is all the same.
    """

    def __init__(self, data, pattern_list=None, parent=None):
        QAbstractItemModel.__init__(self, parent)

        self.rootdir = None
        self.fs_data = None
        self.patterns = {}

        # Check data for a path to a directory
        if isinstance(data, str):
            if os.path.isdir(data):
                self.rootdir = data.rstrip(os.sep)
                for pattern in pattern_list:
                    re_pattern = re.compile(pattern.replace('*', '.*'))
                    self.patterns[pattern] = re_pattern

                self.fs_data = self.pop_model_from_file_system()

        else:
            # Must be data from a JSON file.
            print ('Data must have come from a JSON file')
            self.pop_model_from_data(data)

    def getFSData(self):
        """
        Return file system data to caller.
        """
        return self.fs_data

    def make_file_dict(self, name, rel_path, size):
        file_dict = {}
        file_dict['name'] = name
        file_dict['type'] = 'file'
        file_dict['state'] = 'keep'
        file_dict['rel_path'] = rel_path
        file_dict['size'] = size

        return file_dict

    def make_dir_dict(self, name, rel_path):
        dir_dict = {}
        dir_dict['name'] = name
        dir_dict['type'] = 'folder'
        dir_dict['state'] = 'keep'
        dir_dict['rel_path'] = rel_path
        dir_dict['children'] = {}
        # We don't try to add up all of the space taken by the dir.
        # But keep this 'just in case'.
        dir_dict['size'] = 0

        return dir_dict

    def handle_patterns(self, dirs):
        # Look for pattern matches in the list of dirs.
        # Return the new list of dirs that os.walk should process, and
        # information about substitutions.

        substitutes = {}

        for pattern, re_pattern in self.patterns.items():

            if not dirs: break

            dirs.sort()
            for cur_dir in dirs:

                if re_pattern.match(cur_dir):
                    # Make an entry for this pattern.
                    print('KJS: Add an entry for pattern %s' % pattern)
                    substitutes[pattern] = {}

                    # Patterns can match different strings with different results,
                    # so add an entry for this particular match.
                    name_pattern = re.sub(re_pattern, pattern, cur_dir)
                    print('KJS: \tAdd a sub-entry for name_pattern %s' % name_pattern)
                    substitutes[pattern][name_pattern]= {}

                    # Add an entry for the current subdir. It will have a list of
                    # siblings that will match.
                    substitutes[pattern][name_pattern][cur_dir] = []

                    print('KJS: \t\tUse %s for dir %s' % (name_pattern, cur_dir))

                    # Remove this dir from dirs, so we don't try to process it again.
                    print('KJS: \t\tRemove dir %s' % cur_dir)
                    if not dirs: break

                    sib_dirs = dirs.copy()
                    print('KJS: \t\t\tLoop thru %s' % sib_dirs)
                    for sib_dir in sib_dirs:

                        sib_name_pattern = re.sub(re_pattern, pattern, sib_dir)

                        # Does the sibling match the pattern in the same way?
                        if sib_name_pattern == name_pattern:
                            # Add basename to those to be treated like cur_dir.
                            print('KJS: \t\t\tTreat %s like %s' % (sib_dir, cur_dir))
                            substitutes[pattern][name_pattern][cur_dir].append(sib_dir)

                            #  Take this dir out of the list to be processed.
                            print('KJS: \t\t\tRemove dir %s from outer dirs' % sib_dir)
                            dirs.remove(sib_dir)
                            if not dirs: break

                    print('KJS: Directories with this pattern: %s' % substitutes[pattern][name_pattern][cur_dir])

            # Finished with siblings of cur_dir, and cur_dir.

        return dirs, substitutes

    def pop_model_from_file_system(self):
        """
        We have a root directory from which to get subdirectories and files.
        """
        fs_data = {}
        rootdir = self.rootdir
        start = self.get_start_of_rel_path(rootdir)

        # Walk the file system; os.walk loops for each directory, so only
        # worry about files.
        for cur_path, dirs, files in os.walk(rootdir):
            # When top-down, os.walk allows us to "meddle with" how to
            # walk the subdirectories (this is documented, so is
            # "intended").
            # For those subdirs that match patterns, we need to skip
            # all but one 'representative' subdir; so check the patterns
            # for the dirs in the current path and remove those we don't
            # want to process.

            dirs.sort()

            """ This is for the NEXT version.
            # KJS: For this version, copy dirs into temp_dirs. We'll want to use the
            # real dirs later....
            temp_dirs = []
            for dir in dirs:
                temp_dirs

            substitutes = {}
            if self.patterns:
                temp_dirs, substitutes = self.handle_patterns(dirs)

            if not len(temp_dirs) == len(dirs):
                print ('KJS: After pattern handling, temp_dirs = %s' % temp_dirs)
            if substitutes:
                print ('KJS: After pattern handling, substitutes has:')
                for pattern, v1  in substitutes.items():
                    for name_pattern, v2 in v1.items():
                        for rep_dir, v3 in v2.items():
                            print ('KJS: \t\tpattern %s with name_pattern %s:' % (pattern, name_pattern))
                            print ('KJS: \t\t\tUse %s for %s' % (rep_dir, v3))
            """

            # Get the list of subdirs that gets us from root to current subdir.
            # This will be used as the list of keys for the dictionary.
            path_as_list = cur_path[start:].split(os.sep)
            path_as_list[0] = rootdir

            cur_dir = path_as_list[-1]
            dir_rel_path = os.path.relpath(cur_path, rootdir)

            # It is possible the directory name matches pattern(s).
            # FOR NOW: assume we may only match one - KJS 11/12/18.
            # TODO: If it matches more than one, add *each* of the
            # matching patterns. Use greediest???? Use all????

            # Make a dictionary for the current directory.
            cur_dir_dict = self.make_dir_dict(cur_dir, dir_rel_path)

            # Make the list of files.
            for filename in files:
                file_path = os.path.join(cur_path, filename)
                file_rel_path = os.path.relpath(file_path, rootdir)
                size = os.stat(file_path).st_size
                cur_file_dict = self.make_file_dict(filename, file_rel_path, size)
                # Add this dictionary using the filename as its key.
                cur_dir_dict['children'][filename] = cur_file_dict

            # Use each subdir (-1) in the list of subdirs, as the key to
            # walk down the DB of directories to the level that contains
            # our siblings.
            sib_dir = fs_data
            for dir in path_as_list[:-1]:
                sib_dir = sib_dir[dir]['children']

            sib_dir[cur_dir] = cur_dir_dict

        return fs_data


    def pop_model_from_data(self, json_data):
        # JSON file contains 2 objects - list of patterns and dictionary
        # model of a file system directory with prior choices made.
        # TODO: This one is for the next version.
        raise NotImplementedError


    def get_start_of_rel_path(self, root):
        # Let's say our root is /mnt/...../files.
        # Basically, we're finding the index of 'files'.
        # That will be the start of relative paths.
        root = root.rstrip(os.sep)
        start = root.rfind(os.sep) + 1

        return start

    """
    The following methods are required if the model is to be readable and
    editable.
    Note: Models have these index thingies that Qt creates. The index of the
          root is always invalid. To make an invalid index: QModelIndex().
    """
    def data(self, index, role=Qt.DisplayRole):
        if (Qt.CheckStateRole == role) and (0 == index.column()):
            return self.checkState(index)
        return QAbstractItemModel.data(self,index, role)

    def checkState(self, index):
        while index.isvalid():
            if index in self.checks:
                return self.checks[index]
            index = index.parent()
        # Must be at root.
        return Qt.Unchecked

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        return ['Name' 'Size' 'Type']

    def getIndex(self, row, col, parentIndex=QModelIndex()):
        if isValid(parentIndex):
            if (0 <= row) and (row < rowCount(parentIndex)):
                    if (0 <= col) and (col < columnCount(parent)):
                        return createIndex(row, col, items.at(row))
        # Must be at root.
        return QModelIndex()

    def getParent(self, index):
        if isValid(index):
            return index.parent()
        # Must be at root.
        return QModelIndex()

    def rowCount(self, parentIndex=QModelIndex()):
        return 0 # TODO

    def columnCount(self, parentIndex=QModelIndex()):
        return 3 # TODO; note: all nodes must have the same number of columns.

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate | Qt.ItemIsEnabled

    def setData(self, index, value, role=Qt.EditRole):
        raise NotImplementedError

    def setHeaderData(self, index, value, role=Qt.EditRole):
        raise NotImplementedError

    def insertColumns(self, position, numColumns, parentIndex=QModelIndex()):
        raise NotImplementedError

    def removeColumns(self, position, numColumns, parentIndex=QModelIndex()):
        raise NotImplementedError

    def insertRows(self, position, numRows, parentIndex=QModelIndex()):
        raise NotImplementedError

    def removeRows(self, position, numRows, parentIndex=QModelIndex()):
        raise NotImplementedError



class MainWindow(QMainWindow):
    """
    GUI window where user elects to browse a directory tree or to load a file.
    """

    def __init__(self):
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(300, 200))
        self.setWindowTitle(appId)
        self.setWindowIcon(QIcon('pythonlogo.png'))

        browseButton = QPushButton('Browse', self)
        browseButton.clicked.connect(self.browse)
        browseButton.resize(100, 32)
        browseButton.move(50, 60)
        browseButton.setToolTip('Choose files to be deleted from a directory (or representative directory), ' +
                                'and save choices to a JSON file.')

        editButton = QPushButton('Edit JSON', self)
        editButton.clicked.connect(self.edit)
        editButton.resize(100, 32)
        editButton.move(50, 20)
        editButton.setToolTip('Edit an exisiting JSON file.')
        # TODO Not yet implemented.
        editButton.setEnabled(False)

        quitButton = QPushButton('Exit', self)
        quitButton.clicked.connect(self.exit)
        quitButton.resize(100, 32)
        quitButton.move(50, 100)
        quitButton.setToolTip('Exit the program.')


    def browse(self):

        # Allow user to choose the root directory
        rootdir = str(QFileDialog.getExistingDirectory(self, 'Select Directory'))

        # Allow user to enter patterns.
        pattern_list = self.get_pattern_list()

        # Populate the model by walking the directory.
        model = CheckableDirModel(rootdir, pattern_list, self)

        # Give model to selection window, allow user to choose files and/or
        # directories to be deleted, save the data.
        #TODO
        #win = SelectionWindow(model)
        #win.show()

        # Selection window is gone, but all data is in the model.
        fsData = model.getFSData()

        # Combine the patterns and the file system data into one JSON object.
        json_dict = {}
        json_dict['pattern_list'] = pattern_list
        json_dict['file_system_data'] = fsData

        self.saveJson(json_dict)


    def edit(self):

        # Allow user to choose the file to be edited.
        path = self.get_editable_json()

        # If the user cancelled, return to top level.
        if not path:
            return

        # Open the file for read.
        # The file will be closed when it goes out of scope;
        # we will reopen for write later.
        with open(path, 'r') as j:
            json_data = json.load(j)

        # Populate the model with data from the JSON file.
        #model = CheckableDirModel(json_data, self)

        # Give model to selection window, allow user to choose files and/or
        # directories to be deleted, save the data.
        #TODO
        #win = SelectionWindow(model)
        #win.show()

        return


    def exit(self):
        self.close()


    def get_pattern_list(self):

        pattern_list = []

        patternstr, okay = QInputDialog.getMultiLineText(self,
                'Pattern selection',
                'Patterns allow you to treat the files in multiple \n' +
                'folders alike. For example, if there will be several \n' +
                'folders with task-rest in their names, and you want \n' +
                'to delete the same files in all such folders, enter:\n' +
                '\t *task-rest*. \n' +
                'Be careful, because * is greedy (it will match \n' +
                'everything), so, in the example, since it is before \n' +
                'and after task-rest it will match all folders with \n' +
                'task-rest anywhere in the name. You might want to \n' +
                'match only folders whose names start with task-rest \n' +
                'by using the pattern: \n' +
                '\t task-rest*. \n' +
                'Or you might want to specify more of the name \n' +
                'in your pattern. \n\n' +
                'Enter zero or more patterns separated by commas. \n' +
                'Each pattern should include one or more wildcards (*). \n'
                )

        if (okay) and (patternstr):
            # Split by commas, strip whitespace, and save re version for each pattern.
            for pattern in patternstr.split(','):
                pattern = pattern.strip()
                if pattern:
                    pattern_list.append(pattern)

        print ('KJS: pattern_list contains:\n\t%s' % pattern_list)
        return pattern_list


    def get_editable_json(self):

        json_path = None

        # Loop until user gets a JSON file that he can edit or until he cancels.
        while (not json_path):

            json_path, _ = QFileDialog.getOpenFileName(self, 'Open a JSON file', os.getcwd(), 'JSON files (*.json)')

            # If user pushed cancel, the path is null.
            if not json_path:
                break

            print ('KJS: QFileDialog.getOpenFileName returned %s' % json_path)

            # Make sure user has write access to the file as well as read,
            # since the intent is to edit the file.
            if not ((os.access(json_path, os.W_OK)) and (os.access(json_path, os.R_OK))):
                path = None

                print('KJS: User does not have permission to edit file:\n')
                print('KJS:\t%s' % json_path)

                # User can try to get another file to edit, or can quit.
                button = QMessageBox.warning(self, appId,
                        'You do not have permission to edit the file.\n' +
                        'Please choose another file.',
                        QMessageBox.Ok | QMessageBox.Cancel)
                if (QMessageBox.Ok == button):
                    continue
                else:
                    break

        return json_path

    def saveJson(self, json_data):

        save_path = None

        # Loop until user successfully saves the file or quits.
        while (not save_path):

            save_path, status = QFileDialog.getSaveFileName(self, 'Save File', os.getcwd(), 'JSON files (*.json)')

            # User canceled
            if not save_path:
                button = QMessageBox.warning(self, appId,
                        'If you do not save the file, your data will be lost.\n' +
                        'Do you want to return to the selection dialog?',
                        QMessageBox.Yes | QMessageBox.No)

                if not QMessageBox.Yes == button:
                    break

            else:
                try:
                    # User has picked a path. Try to write to it.
                    with open(save_path, 'w') as json_file:
                        json.dump(json_data, json_file, indent=4, sort_keys=True)
                        msg_text = 'JSON created successfully.'
                        button = (self, appId, msg_text, QMessageBox.Ok)

                except OSError as error:
                    save_path = None
                    msg_text = 'JSON creation process was not successful:\n%s\nPlease try again.' % error
                    button = QMessageBox.warning(self, appId, msg_text, QMessageBox.Ok | QMessageBox.Cancel)

        return



if __name__ == '__main__':

    app = QApplication(sys.argv)

    # From the main window, user can choose to edit an existing
    # JSON file, to browse a directory for files to delete, or
    # to exit. When that window closes, the application is done.
    mainWin = MainWindow()
    mainWin.show()

    # Start the application's message loop.
    app.exec_()

