#! /usr/global/bin/python

import sys
import os
import re
import json
import datetime
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *

def are_parent_and_child(parent, child):
    while child.isValid():
        if child == parent:
            return True
        child = child.parent()
    return False

class SelectionWindow(QtGui.QDialog):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        layout = QtGui.QVBoxLayout(self)

        # Add checkable directory tree
        model = CheckableDirModel()
        self.view = QtGui.QTreeView()
        self.view.setModel(model)
        self.view.setColumnWidth(0, 800)

        self.view.setRootIndex(model.index(example_path))
        
        self.resize(1000, 500)
        self.setWindowTitle("Choose Items to Delete")
        
        layout.addWidget(self.view)

        # Add OK and Cancel buttons
        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(model.makeJSON)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class CheckableDirModel(QtGui.QDirModel):
    def __init__(self, parent=None):
        QtGui.QDirModel.__init__(self, None)
        self.checks = {}

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            return self.checkState(index)
        return QtGui.QDirModel.data(self, index, role)

    def flags(self, index):
        return QtGui.QDirModel.flags(self, index) | QtCore.Qt.ItemIsUserCheckable

    def checkState(self, index):
        while index.isValid():
            if index in self.checks:
                return self.checks[index]
            index = index.parent()
        return QtCore.Qt.Unchecked

    def setData(self, index, value, role):
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            self.layoutAboutToBeChanged.emit()
            for i, v in self.checks.items():
                if are_parent_and_child(index, i):
                    self.checks.pop(i)
            self.checks[index] = value
            self.layoutChanged.emit()
            return True 

        return QtGui.QDirModel.setData(self, index, value, role)

    def get_savepath(self):
        savepath = str(QFileDialog.getSaveFileName(anchor_win, 'Save As'))

        if not savepath.endswith('.json'):
            savepath += '.json'

	return savepath

    # Provide user-friendly message about what happened
    def end_message(self, text):

        msg = QMessageBox()
	msg.setIcon(QMessageBox.Information)
	msg.setText(text)
	msg.setWindowTitle('JSON creation process finished')

	msg.setStandardButtons(QMessageBox.Ok)
	msg.exec_()


    def get_directory_structure(self):

        dir_dict = {}
        rootdir = example_path.rstrip(os.sep)
        start = rootdir.rfind(os.sep) + 1
        for path, dirs, files in os.walk(rootdir):
            path_as_list = path[start:].split(os.sep)

            files_in_dir = {'files': {}}
            for f in files:

                filepath = os.path.join(path, f)
                rel_path = os.path.relpath(filepath, rootdir).lstrip(os.sep)

		if ('REST' not in rel_path) or ('1' in rel_path):
                    files_in_dir['files'][f] = {}
                    if rel_path == f:
                        rel_path = '.'
                    files_in_dir['files'][f]['rel_path'] = rel_path

                if f in files_in_dir['files']:
                    if self.checkState(self.index(os.path.join(path, f))) == QtCore.Qt.Checked:
                        files_in_dir['files'][f]['state'] = 'delete'
                    else:
                        files_in_dir['files'][f]['state'] = 'keep'                    

            full_dir = reduce(dict.get, path_as_list[:-1], dir_dict)
            full_dir[path_as_list[-1]] = files_in_dir

        return dir_dict

    def makeJSON(self):

	d = self.get_directory_structure()

	savepath = self.get_savepath()

	try:
	    with open(savepath, 'w') as json_file:
                json.dump(d, json_file, indent=4)
                msg_text = 'JSON created successfully.'
        except:
	    msg_text = 'JSON creation process was not successful. Please try again.'

	self.end_message(msg_text)

        QtCore.QCoreApplication.instance().quit()


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    anchor_win = QMainWindow()

    example_path = str(QFileDialog.getExistingDirectory(anchor_win, 'Select Example Directory'))

    win = SelectionWindow()

    win.show()

    sys.exit(app.exec_())

