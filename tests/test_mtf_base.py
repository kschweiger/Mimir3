import sys
import os
import shutil
import json
import unittest
import pytest
import coverage
import os
import copy

from glob import glob

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('.'))
print(sys.path)
from mimir.backend.database import DataBase, Model
import mimir.frontend.terminal.application as MTF

if os.getcwd().endswith("tests"):
    mimir_dir = os.getcwd()[0:-len("/tests")]
    dir2tests = os.getcwd()
else:
    mimir_dir = os.getcwd()
    dir2tests = os.getcwd()+"/tests"

@pytest.fixture(scope="module")
def preCreatedDB():
    config = mimir_dir+"/conf/modeltest.json"
    dbRootPath = dir2tests+"/testStructure"
    if os.path.exists(dbRootPath+"/.mimir"):
        shutil.rmtree(dbRootPath+"/.mimir")
    database = DataBase(dbRootPath, "new", config)
    shutil.copy2(mimir_dir+"/conf/MTF_modeltest.json", dbRootPath+"/.mimir/MTF_model.json")
    ## Set Ratings for furure tests
    # Expected Order: ["3", "2", "4", "1", "5", "0"]
    database.modifySingleEntry("1", "Rating", "2", byID = True )
    database.modifySingleEntry("2", "Rating", "4", byID = True )
    database.modifySingleEntry("3", "Rating", "5", byID = True )
    database.modifySingleEntry("4", "Rating", "3", byID = True )
    database.modifySingleEntry("5", "Rating", "1", byID = True )
    # Expected Order: ["5", "4", "3", "2", "1", "0"]
    database.modifySingleEntry("0", "SingleItem", "Xi", byID = True )
    database.modifySingleEntry("1", "SingleItem", "Tau", byID = True )
    database.modifySingleEntry("2", "SingleItem", "Ny", byID = True )
    database.modifySingleEntry("3", "SingleItem", "Eta", byID = True )
    database.modifySingleEntry("4", "SingleItem", "Bea", byID = True )
    database.modifySingleEntry("5", "SingleItem", "Alpha", byID = True )
    database.modifyListEntry("0", "ListItem", "Blue", byID = True)
    database.modifyListEntry("0", "ListItem", "Double Orange", byID = True)
    database.modifyListEntry("0", "ListItem", "Triple Orange", byID = True)
    Entry0 = database.getEntryByItemName("ID", "0")[0]
    Entry1 = database.getEntryByItemName("ID", "1")[0]
    Entry2 = database.getEntryByItemName("ID", "2")[0]
    Entry3 = database.getEntryByItemName("ID", "3")[0]
    Entry4 = database.getEntryByItemName("ID", "4")[0]
    Entry5 = database.getEntryByItemName("ID", "5")[0]
    # Expected Order: ["0", "2", "3", "5", "1", "4"]
    Entry0.changeItemValue("Added", "30.01.19|00:00:00")
    Entry1.changeItemValue("Added", "20.01.19|00:00:00")
    Entry2.changeItemValue("Added", "29.01.19|00:00:00")
    Entry3.changeItemValue("Added", "29.01.19|00:00:00")# Same time: Fall back to ID
    Entry4.changeItemValue("Added", "15.01.19|00:00:00")
    Entry5.changeItemValue("Added", "26.01.19|00:00:00")
    # Expected Order: ["0", "3", "4", "5", "1", "2"]
    Entry0.replaceItemValue("Changed", "24.02.19|00:00:00", Entry0.getItem("Changed").value[0])
    Entry1.replaceItemValue("Changed", "10.02.19|00:00:00", Entry1.getItem("Changed").value[0])
    Entry2.replaceItemValue("Changed", "23.02.19|00:00:00", Entry2.getItem("Changed").value[0])
    Entry3.replaceItemValue("Changed", "22.02.19|00:00:00", Entry3.getItem("Changed").value[0])
    Entry4.replaceItemValue("Changed", "21.02.19|00:00:00", Entry4.getItem("Changed").value[0])
    Entry5.replaceItemValue("Changed", "20.02.19|00:00:00", Entry5.getItem("Changed").value[0])
    Entry0.addItemValue("Changed", "25.03.19|00:00:00")
    Entry1.addItemValue("Changed", "19.03.19|00:00:00")
    Entry2.addItemValue("Changed", "23.01.19|00:00:00")
    Entry3.addItemValue("Changed", "22.03.19|00:00:00")
    Entry4.addItemValue("Changed", "21.03.19|00:00:00")
    Entry5.addItemValue("Changed", "20.03.19|00:00:00")
    database.saveMain()
    #shutil.copytree(dbRootPath+"/.mimir", dbRootPath+"/.mimir2") #For testing
    yield database
    #shutil.rmtree(dbRootPath+"/.mimir")


def test_01_MTF_initDatabase():
    dbRootPath = dir2tests+"/testStructure"
    if os.path.exists(dbRootPath+"/.mimir"):
        shutil.rmtree(dbRootPath+"/.mimir")
    with pytest.raises(RuntimeError):
        newDatabase, status = MTF.initDatabase(dir2tests+"/testStructure")

    newDatabase, status = MTF.initDatabase(dir2tests+"/testStructure", mimir_dir+"/conf/modeltest.json")
    assert isinstance(newDatabase, DataBase)
    assert status == "new"
    newDatabase.saveMain()
    loadedDatabase, status = MTF.initDatabase(dir2tests+"/testStructure")
    assert isinstance(loadedDatabase, DataBase)
    assert status == "loaded"
    shutil.rmtree(dir2tests+"/testStructure"+"/.mimir")

def test_02_MTF_init_error(preCreatedDB):
    dir = preCreatedDB.mimirdir
    os.system("mv {0}/MTF_model.json {0}/moved_MTF_model.json".format(dir))
    with pytest.raises(RuntimeError):
        MTF.App(preCreatedDB)
    os.system("mv {0}/moved_MTF_model.json {0}/MTF_model.json".format(dir))

def test_03_MTF_initApp(preCreatedDB):
    app = MTF.App(preCreatedDB)
    assert isinstance(app.database, DataBase)
    assert isinstance(app.config, MTF.MTFConfig)


# def test_01_MTF_loadMTFConfig(preCreatedDB):
#     assert not os.path.exists(preCreatedDB.mimirdir+"/MTF.json")
#     assert MTF.initFrontend()
#     assert os.path.exists(preCreatedDB.mimirdir+"/MTF.json")
#
# def test_02_MTF_load_database():
#     database = createNewDB()
#     with self.assertRaises(RuntimeError):
#         MTF.loadDB(dir2tests+"/someFolderWoMimirFolder")
#
#     assert MTF.loadDB(dir2tests+"/testStructure")
#
# def test_03_MTF_save_database(preCreatedDB):
#     assert False
