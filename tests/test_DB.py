import sys
import os
import shutil 
import json
from glob import glob
sys.path.insert(0, os.path.abspath('..'))
from backend.database import DataBase, Model, validateDatabaseJSON
from backend.entry import Item, ListItem
import unittest
import pytest
import coverage
import os

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
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database = DataBase(dbRootPath, "new", config)
        filesindbRoot = glob(dbRootPath+"/**/*.mp4", recursive = True)
        allEntriesSaved = True
        print(filesindbRoot)
        for entry in database.entries:
            print(type(entry.Path))
            if entry.Path not in filesindbRoot:
                allEntriesSaved = False
        assert allEntriesSaved

    def test_DB_raise_RuntimeError_existing_mimirDir(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if not os.path.exists(dbRootPath+"/.mimir"):
            os.makedirs(dbRootPath+"/.mimir")
        with self.assertRaises(RuntimeError):
            database = DataBase(dbRootPath, "new", config)
        os.rmdir(dbRootPath+"/.mimir")
        
    def test_DB_save(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database = DataBase(dbRootPath, "new", config)
        assert database.saveMain()
        #assert validateDatabaseJSON(database, config, database.savepath)
        
if __name__ == "__main__":
    unittest.main()
