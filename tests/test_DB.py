import sys
import os
import json
from glob import glob
sys.path.insert(0, os.path.abspath('..'))
from backend.database import DataBase, Model
from backend.entry import Item, ListItem
import unittest
import pytest
import coverage

mimir_dir = os.getcwd()[0:-len("/tests")]

files = ["testStructure/rootFile1.mp4",
         "testStructure/folder1/folder1file1.mp4",
         "testStructure/folder1/folder1file2.mp4",
         "testStructure/folder2/folder2file1.mp4",
         "testStructure/folder2/folder2file2.mp4"]

folder = ["folder1", "folder2"]

class TestItem(unittest.TestCase):
    def test_Model_init(self):
        config = mimir_dir+"/conf/modeltest.json"
        jsonModel = None
        with open(config) as f:
            jsonModel = json.load(f)
        testModel = Model(config)
        bools = []
        bools.append(testModel.modelName == jsonModel["General"]["Name"])
        bools.append(testModel.modelDesc == jsonModel["General"]["Description"])
        bools.append(testModel.extentions == jsonModel["General"]["Types"])
        
        allitems = {}
        allitems.update(testModel.items)
        allitems.update(testModel.listitems)
        for item in allitems:
            for spec in allitems[item]:
                 bools.append(jsonModel[item][spec] == allitems[item][spec])

        res = True
        for b in bools:
            if not b:
                res = b
                break
        assert res

    def test_DB_init_new(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        database = DataBase(dbRootPath, "new", config)
        filesindbRoot = glob(dbRootPath+"/**/*.mp4", recursive = True)
        allEntriesSaved = True
        print(filesindbRoot)
        for entry in database.entries:
            print(type(entry.Path))
            if entry.Path not in filesindbRoot:
                allEntriesSaved = False
        assert allEntriesSaved
        
if __name__ == "__main__":
    unittest.main()
