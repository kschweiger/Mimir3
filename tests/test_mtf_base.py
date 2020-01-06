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
    jsonConf = None
    with open(dbRootPath+"/.mimir/MTF_model.json", "r") as f:
        jsonConf = json.load(f)
    jsonConf["General"]["DisplayItems"] = ["ID", "Name", "SingleItem", "ListItem", "Rating", "Opened", "timesOpened"]
    with open(dbRootPath+"/.mimir/MTF_model.json", 'w') as o:
        json.dump(jsonConf, o, sort_keys=True, indent=4, separators=(',', ': '))
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
    database.modifyListEntry("1", "ListItem", "Blue", byID = True)
    database.modifyListEntry("1", "ListItem", "Red", byID = True)
    database.modifyListEntry("1", "ListItem", "Orange", byID = True)
    database.modifyListEntry("1", "ListItem", "Magenta", byID = True)
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
    Entry0.addItemValue("Changed", "25.03.19|01:00:00")
    Entry1.addItemValue("Changed", "19.03.19|01:00:00")
    Entry2.addItemValue("Changed", "23.01.19|01:00:00")
    Entry3.addItemValue("Changed", "22.03.19|01:00:00")
    Entry4.addItemValue("Changed", "21.03.19|01:00:00")
    Entry5.addItemValue("Changed", "20.03.19|01:00:00")
    ####
    Entry0.replaceItemValue("Opened", "27.02.19|00:00:00", Entry0.getItem("Opened").value[0])
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

def test_04_MTF_generateList(preCreatedDB):
    app = MTF.App(preCreatedDB)
    #make sure that displayitems is: "ID", "Name", "SingleItem", "ListItem", "Rating", "Opened", "timesOpened"
    app.config.items = ["ID", "Name", "SingleItem", "ListItem", "Rating", "Opened", "timesOpened"]
    app.tableColumnItems = ["ID", "Name", "SingleItem", "ListItem", "Rating", "Opened", "timesOpened"]
    checkThis = app.generateList(["0"])
    print(checkThis)
    entry = preCreatedDB.getEntryByItemName("ID", "0")[0]
    entry1 = preCreatedDB.getEntryByItemName("ID", "1")[0]

    expectation = [(entry.getItem("ID").value, entry.getItem("Name").value,
                    entry.getItem("SingleItem").value,
                    ", ".join(entry.getItem("ListItem").value),
                    entry.getItem("Rating").value,
                    ", ".join(entry.getItem("Opened").value),
                    str(preCreatedDB.getCount("0", "Opened", byID = True))) ]
    assert expectation == checkThis
    app.config.itemInfo["ListItem"]["Priority"] = ["Orange","Magenta"]
    app.config.itemInfo["Name"]["maxLen"] = 8
    checkThis = app.generateList(["1"])
    print(checkThis)
    expectation_ListItem = "Orange, Magenta, Blue, Red"
    expectation_name = entry1.getItem("Name").value[:8]+".."
    assert checkThis[0][3] == expectation_ListItem
    assert checkThis[0][1] == expectation_name
    checkThis = app.generateList(["2"])
    app.config.itemInfo["ListItem"]["nDisplay"] = 2
    checkThis = app.generateList(["0"])
    expectation_LitItem_nDisplay = ", ".join(entry.getItem("ListItem").value[:2]+[".."])
    assert checkThis[0][3] == expectation_LitItem_nDisplay

def test_05_MTF_generateList_dateFormatting(preCreatedDB):
    app = MTF.App(preCreatedDB)
    app.config.items = ["Opened","Changed","Added"]
    app.tableColumnItems = ["Opened","Changed","Added"]
    app.config.itemInfo["Opened"]["modDisplay"] = "Date"
    app.config.itemInfo["Changed"]["modDisplay"] = "Time"
    checkThis = app.generateList(["0"])
    entry = preCreatedDB.getEntryByItemName("ID", "0")[0]
    print(checkThis)
    formattedOpened = [x.split("|")[0] for x in entry.getItem("Opened").value]
    formattedChanged = [x.split("|")[1] for x in entry.getItem("Changed").value]
    expectation = [((", ".join(formattedOpened)),
                   (", ".join(formattedChanged)),
                   (entry.getItem("Added").value))]
    print(expectation)
    assert expectation == checkThis

def test_06_MTF_modify(preCreatedDB):
    app = MTF.App(preCreatedDB)
    ### Append
    assert app.makeListModifications("1", "ListItem", "Append", None, "Magenta")
    Entry1 = preCreatedDB.getEntryByItemName("ID", "1")[0]
    assert "Magenta" in Entry1.getItem("ListItem").value
    ##Remove
    assert app.makeListModifications("1", "ListItem", "Remove", "Magenta", None)
    Entry1 = preCreatedDB.getEntryByItemName("ID", "1")[0]
    assert "Magenta" not in Entry1.getItem("ListItem").value
    assert not app.makeListModifications("1", "ListItem", "Remove", "SomeColor", None)
    ##Replace
    assert app.makeListModifications("1", "ListItem", "Append", None, "Cyan")
    Entry1 = preCreatedDB.getEntryByItemName("ID", "1")[0]
    assert "Cyan" in Entry1.getItem("ListItem").value
    assert app.makeListModifications("1", "ListItem", "Replace", "Cyan", "Yellow")
    Entry1 = preCreatedDB.getEntryByItemName("ID", "1")[0]
    assert "Cyan" not in Entry1.getItem("ListItem").value
    assert "Yellow" in Entry1.getItem("ListItem").value

def test_07_MTF_findnewFiles(preCreatedDB):
    app = MTF.App(preCreatedDB)

def test_08_MTF_printItemValues_error(preCreatedDB):
    app = MTF.App(preCreatedDB)
    with pytest.raises(KeyError):
        app.getPrintItemValues("0", "Blubb")

@pytest.mark.parametrize("id, item, expValue, printFull, maxLen, nMax", [
        ("0", "ListItem", "Blue, Double Orange, ..", False, 99, 2),
        ("0", "ListItem", "Blue, Double Orange, Triple Orange", True, 99, 99),
        ("0", "SingleItem", "Xi", True, 99, 99),
        ("0", "SingleItem", "X..", False, 1, 99),
    ])
def test_09_MTF_printItemValues(id, item, expValue, printFull, maxLen, nMax, preCreatedDB):
    app = MTF.App(preCreatedDB)
    app.config.itemInfo[item]["maxLen"] = maxLen
    app.config.itemInfo[item]["nDisplay"] = nMax
    assert app.getPrintItemValues(id, item, joinFull=printFull) == expValue

@pytest.mark.parametrize("item, value, expValue, modDisplay", [
        ("Opened", "30.01.19|00:00:00", "30.01.19", "Date"),
        ("Opened", "30.01.19|00:00:00", "00:00:00", "Time"),
        ("Opened", "30.01.19|00:00:00", "30.01.19|00:00:00", "Full"),
    ])
def test_10_MTF_modDisaply(item, value, expValue, modDisplay, preCreatedDB):
    app = MTF.App(preCreatedDB)
    app.config.itemInfo[item]["modDisplay"] = modDisplay
    assert app.modDisaply(item, value) == expValue
