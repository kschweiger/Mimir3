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
import copy

mimir_dir = os.getcwd()[0:-len("/tests")]

files = ["testStructure/rootFile1.mp4",
         "testStructure/folder1/folder1file1.mp4",
         "testStructure/folder1/folder1file2.mp4",
         "testStructure/folder2/folder2file1.mp4",
         "testStructure/folder2/folder2file2.mp4"]

folder = ["folder1", "folder2"]


class TestItem(unittest.TestCase):
    def test_01_Model_init(self):
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

    def test_02_DB_init_new(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database = DataBase(dbRootPath, "new", config)
        filesindbRoot = glob(dbRootPath+"/**/*.mp4", recursive = True)
        allEntriesSaved = True
        for entry in database.entries:
            if entry.Path not in filesindbRoot:
                allEntriesSaved = False
        assert allEntriesSaved

    def test_03_DB_raise_RuntimeError_existing_mimirDir(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if not os.path.exists(dbRootPath+"/.mimir"):
            os.makedirs(dbRootPath+"/.mimir")
        with self.assertRaises(RuntimeError):
            database = DataBase(dbRootPath, "new", config)
        
    def test_04_DB_save(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database = DataBase(dbRootPath, "new", config)
        assert database.saveMain()
        #assert validateDatabaseJSON(database, config, database.savepath)

    def test_05_DB_equal(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database1 = DataBase(dbRootPath, "new", config)
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database2 = DataBase(dbRootPath, "new", config)
        assert database1 == database2
        
    def test_06_DB_notequal(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database1 = DataBase(dbRootPath, "new", config)
        os.system("rm "+os.getcwd()+"/testStructure/newfile.mp4")
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database2 = DataBase(dbRootPath, "new", config)
        os.system("touch "+os.getcwd()+"/testStructure/newfile.mp4")
        database2.findNewFiles()
        os.system("rm "+os.getcwd()+"/testStructure/newfile.mp4")
        assert database1 != database2

    def test_07_DB_load(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database = DataBase(dbRootPath, "new", config)
        database.saveMain()
        loadedDB = DataBase(dbRootPath, "load")
        assert database == loadedDB

    def test_08_DB_getAllValues(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database = DataBase(dbRootPath, "new", config)
        with self.assertRaises(KeyError):
            database.getAllValuebyItemName("Blubb")
        values = database.getAllValuebyItemName("Path")
        filesindbRoot = glob(dbRootPath+"/**/*.mp4", recursive = True)
        assert values == set(filesindbRoot)

    def test_09_DB_getEntrybyItemName(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database = DataBase(dbRootPath, "new", config)
        with self.assertRaises(KeyError):
            database.getEntryByItemName("Blubb", "folder2file")
        found = False
        for entry in database.entries:
            if entry.getItem("Name").value == "folder2file2":
                found = True
                break
        assert found
        entrybyItemName = database.getEntryByItemName("Name", "folder2file2")
        assert entry in entrybyItemName
                
    def test_10_DB_removeEntry_exceptions(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database = DataBase(dbRootPath, "new", config)
        ##############################################
        #Raise exception for not specified vector
        #    No vector specified 
        with self.assertRaises(RuntimeError):
            database.remove(1)
        #    More than one vector specified 
        with self.assertRaises(RuntimeError):
            database.remove(1, byID = True, byName = True)
        ##############################################
        #Raise exception type
        #    ID
        with self.assertRaises(TypeError):
            database.remove([], byID = True)
        with self.assertRaises(TypeError):
            database.remove(1, byID = 1)
        #    Name/Path
        with self.assertRaises(TypeError):
            database.remove(1, byName = True)
        ##############################################
        #Raise exception by ID: out of range
        with self.assertRaises(IndexError):
            database.remove(1000, byID = True)
        ##############################################
        #Raise exception by Name/Path: not in DB
        with self.assertRaises(KeyError):
            database.remove("RandomName", byName = True)
        with self.assertRaises(KeyError):
            database.remove("RandomPath", byPath = True)
            
    def test_11_DB_removeEntry(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database = DataBase(dbRootPath, "new", config)
        #Remove by ID
        databaseID = copy.deepcopy(database)
        id2remove = 2
        entry2Remove = databaseID.getEntryByItemName("ID",str(id2remove))[0]
        databaseID.remove(id2remove, byID = True)
        assert not entry2Remove in databaseID.entries
        #Remove by Name
        databaseName = copy.deepcopy(database)
        name2remove = "folder2file1"
        entry2Remove = databaseName.getEntryByItemName("Name",name2remove)[0]
        databaseName.remove(name2remove, byName = True)
        assert not entry2Remove in databaseName.entries
        #Remove by Path
        databasePath = copy.deepcopy(database)
        path2remove = "/Users/korbinianschweiger/Code/Mimir3/tests/testStructure/folder2/folder2file1.mp4"
        entry2Remove = databasePath.getEntryByItemName("Path",path2remove)[0]
        databasePath.remove(path2remove, byPath = True)
        assert not entry2Remove in databasePath.entries
        
    def test_12_DB_findNewFiles_append(self):
        config = mimir_dir+"/conf/modeltest.json"
        dbRootPath = os.getcwd()+"/testStructure"
        if os.path.exists(dbRootPath+"/.mimir"):
            shutil.rmtree(dbRootPath+"/.mimir")
        database = DataBase(dbRootPath, "new", config)
        lastIDbeforeAppend = database.maxID 
        os.system("touch "+os.getcwd()+"/testStructure/newfile.mp4")
        newFiles = database.findNewFiles()
        os.system("rm "+os.getcwd()+"/testStructure/newfile.mp4")
        assert os.getcwd()+"/testStructure/newfile.mp4" in newFiles
        assert len(newFiles) == 1
        asEntry = False
        for entry in database.entries:
            if entry.Path == os.getcwd()+"/testStructure/newfile.mp4":
                asEntry = True
                newEntry = entry
                break
        assert asEntry
        assert int(newEntry.ID) == lastIDbeforeAppend+1

        
if __name__ == "__main__":
    unittest.main()
