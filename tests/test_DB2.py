import sys
import os
import shutil
import json
from glob import glob

# sys.path.insert(0, os.path.abspath('..'))
# sys.path.insert(0, os.path.abspath('.'))
# print(sys.path)
import mimir.backend.database
from mimir.backend.database import DataBase, Model
from mimir.backend.entry import Item, ListItem
import unittest
import pytest
import coverage
import os
import copy
import datetime

# DEBUGGING
import tracemalloc

if os.getcwd().endswith("tests"):
    mimir_dir = os.getcwd()[0 : -len("/tests")]
    dir2tests = os.getcwd()
else:
    mimir_dir = os.getcwd()
    dir2tests = os.getcwd() + "/tests"

print(mimir_dir)
print(dir2tests)

files = [
    "testStructure/rootFile1.mp4",
    "testStructure/folder1/folder1file1.mp4",
    "testStructure/folder1/folder1file2.mp4",
    "testStructure/folder2/folder2file1.mp4",
    "testStructure/folder2/folder2file2.mp4",
]

folder = ["folder1", "folder2"]


def getDataTime():
    currently = datetime.datetime.now()
    day = currently.day
    month = currently.month
    year = currently.year
    hour = currently.hour
    minutes = currently.minute
    sec = currently.second
    fulldate = "{0:02}{3}{1:02}{3}{2:02}".format(day, month, year - 2000, ".")
    fulltime = "{0:02}:{1:02}:{2:02}".format(hour, minutes, sec)
    return fulldate, fulltime


@pytest.fixture(scope="module")
def preCreatedDB():
    os.system("touch " + dir2tests + "/testStructure/rootFile1")
    os.system("touch " + dir2tests + "/testStructure/folder2/folder2file1.mp4")
    os.system("touch " + dir2tests + "/testStructure/folder2/folder2file2.mp4")
    os.system("touch " + dir2tests + "/testStructure/folder2/folder3/folder3file1.mp4")
    os.system("touch " + dir2tests + "/testStructure/folder1/folder1file1.mp4")
    os.system("touch " + dir2tests + "/testStructure/folder1/folder1file2.mp4")
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    ## Set Ratings for furure tests
    # Expected Order: ["3", "2", "4", "1", "5", "0"]
    database.modifySingleEntry("1", "Rating", "2", byID=True)
    database.modifySingleEntry("2", "Rating", "4", byID=True)
    database.modifySingleEntry("3", "Rating", "5", byID=True)
    database.modifySingleEntry("4", "Rating", "3", byID=True)
    database.modifySingleEntry("5", "Rating", "1", byID=True)
    # Expected Order: ["5", "4", "3", "2", "1", "0"]
    database.modifySingleEntry("0", "SingleItem", "Xi", byID=True)
    database.modifySingleEntry("1", "SingleItem", "Tau", byID=True)
    database.modifySingleEntry("2", "SingleItem", "Ny", byID=True)
    database.modifySingleEntry("3", "SingleItem", "Eta", byID=True)
    database.modifySingleEntry("4", "SingleItem", "Bea", byID=True)
    database.modifySingleEntry("5", "SingleItem", "Alpha", byID=True)
    database.modifyListEntry("0", "ListItem", "Blue", byID=True)
    database.modifyListEntry("0", "ListItem", "Double Orange", byID=True)
    database.modifyListEntry("0", "ListItem", "Triple Orange", byID=True)
    database.modifyListEntry("3", "ListItem", "Lavender", byID=True)
    database.modifyListEntry("4", "ListItem", "Lavender", byID=True)
    database.modifyListEntry("4", "ListItem", "Pinkish", byID=True)
    database.modifyListEntry("4", "ListItem", "Spring", byID=True)
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
    Entry3.changeItemValue("Added", "29.01.19|00:00:00")  # Same time: Fall back to ID
    Entry4.changeItemValue("Added", "15.01.19|00:00:00")
    Entry5.changeItemValue("Added", "26.01.19|00:00:00")
    # Expected Order: ["0", "3", "4", "5", "1", "2"]
    Entry0.replaceItemValue(
        "Changed", "24.02.19|00:00:00", Entry0.getItem("Changed").value[0]
    )
    Entry1.replaceItemValue(
        "Changed", "10.02.19|00:00:00", Entry1.getItem("Changed").value[0]
    )
    Entry2.replaceItemValue(
        "Changed", "23.02.19|00:00:00", Entry2.getItem("Changed").value[0]
    )
    Entry3.replaceItemValue(
        "Changed", "22.02.19|00:00:00", Entry3.getItem("Changed").value[0]
    )
    Entry4.replaceItemValue(
        "Changed", "21.02.19|00:00:00", Entry4.getItem("Changed").value[0]
    )
    Entry5.replaceItemValue(
        "Changed", "20.02.19|00:00:00", Entry5.getItem("Changed").value[0]
    )
    Entry0.addItemValue("Changed", "25.03.19|00:00:00")
    Entry1.addItemValue("Changed", "19.03.19|00:00:00")
    Entry2.addItemValue("Changed", "23.01.19|00:00:00")
    Entry3.addItemValue("Changed", "22.03.19|00:00:00")
    Entry4.addItemValue("Changed", "21.03.19|00:00:00")
    Entry5.addItemValue("Changed", "20.03.19|00:00:00")
    database.saveMain()
    for item in database.model.allItems:
        database.cacheAllValuebyItemName(item)
    # shutil.copytree(dbRootPath+"/.mimir", dbRootPath+"/.mimir2") #For testing
    shutil.rmtree(dbRootPath + "/.mimir")
    return database


def test_01_Model_init():
    config = mimir_dir + "/conf/modeltest.json"
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


def test_02_DB_init_new():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    print(database.model.listitems)
    filesindbRoot = glob(dbRootPath + "/**/*.mp4", recursive=True)
    filesindbRoot = [x.replace(dbRootPath + "/", "") for x in filesindbRoot]
    allEntriesSaved = True
    for entry in database.entries:
        if entry.Path not in filesindbRoot:
            allEntriesSaved = False
    assert allEntriesSaved
    for item in database.model.allItems:
        assert not database.cachedValuesChanged[item]
    del database


def test_03_DB_raise_RuntimeError_existing_mimirDir():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if not os.path.exists(dbRootPath + "/.mimir"):
        os.makedirs(dbRootPath + "/.mimir")
    with pytest.raises(RuntimeError):
        database = DataBase(dbRootPath, "new", config)
        del database


def test_04_DB_save():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    # Check database is save
    assert database.saveMain()
    assert database.saveMain()
    # shutil.copytree(dbRootPath+"/.mimir", dbRootPath+"/.mimir2")
    # assert validateDatabaseJSON(database, config, database.savepath)
    # check if backup was created
    day, month, year = (
        datetime.date.today().day,
        datetime.date.today().month,
        datetime.date.today().year,
    )
    fulldate = "{2:02}-{1:02}-{0:02}".format(day, month, year - 2000)
    assert (
        os.path.exists(dbRootPath + "/.mimir/mainDB.{0}.backup".format(fulldate))
        == True
    )
    del database


def test_05_DB_equal():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database1 = DataBase(dbRootPath, "new", config)
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database2 = DataBase(dbRootPath, "new", config)
    assert database1 == database2
    del database1, database2


def test_06_DB_notequal():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database1 = DataBase(dbRootPath, "new", config)
    os.system("rm " + dir2tests + "/testStructure/newfile.mp4")
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database2 = DataBase(dbRootPath, "new", config)
    os.system("touch " + dir2tests + "/testStructure/newfile.mp4")
    database2.findNewFiles()
    os.system("rm " + dir2tests + "/testStructure/newfile.mp4")
    assert database1 != database2
    del database1, database2


def test_07_DB_load():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    database.saveMain()
    loadedDB = DataBase(dbRootPath, "load")
    assert database == loadedDB
    assert loadedDB.maxID == len(loadedDB.entries) - 1  # Since 0 is a valid ID
    del database


def test_08_DB_getAllValues():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    with pytest.raises(KeyError):
        database.getAllValuebyItemName("Blubb")
    values = database.getAllValuebyItemName("Path")
    filesindbRoot = glob(dbRootPath + "/**/*.mp4", recursive=True)
    filesindbRoot = [x.replace(dbRootPath + "/", "") for x in filesindbRoot]
    assert values == set(filesindbRoot)
    del database


def test_09_DB_getEntrybyItemName():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    with pytest.raises(KeyError):
        database.getEntryByItemName("Blubb", "folder2file")
    found = False
    for entry in database.entries:
        print(entry.getItem("Name").value)
        if entry.getItem("Name").value == "folder2file1":
            found = True
            break
    assert found
    entrybyItemName = database.getEntryByItemName("Name", "folder2file1")
    assert entry in entrybyItemName
    del database


def test_10_DB_removeEntry_exceptions():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    ##############################################
    # Raise exception for not specified vector
    #    No vector specified
    with pytest.raises(RuntimeError):
        database.remove(1)
    #    More than one vector specified
    with pytest.raises(RuntimeError):
        database.remove(1, byID=True, byName=True)
    ##############################################
    # Raise exception type
    #    ID
    with pytest.raises(TypeError):
        database.remove([], byID=True)
    with pytest.raises(TypeError):
        database.remove(1, byID=1)
    #    Name/Path
    with pytest.raises(TypeError):
        database.remove(1, byName=True)
    ##############################################
    # Raise exception by ID: out of range
    with pytest.raises(IndexError):
        database.remove(1000, byID=True)
    ##############################################
    # Raise exception by Name/Path: not in DB
    with pytest.raises(KeyError):
        database.remove("RandomName", byName=True)
    with pytest.raises(KeyError):
        database.remove("RandomPath", byPath=True)
    del database


def test_11_DB_removeEntry():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    # Remove by ID
    databaseID = copy.deepcopy(database)
    id2remove = 2
    entry2Remove = databaseID.getEntryByItemName("ID", str(id2remove))[0]
    databaseID.remove(id2remove, byID=True)
    assert not entry2Remove in databaseID.entries
    # Remove by Name
    databaseName = copy.deepcopy(database)
    name2remove = "folder2file1"
    entry2Remove = databaseName.getEntryByItemName("Name", name2remove)[0]
    databaseName.remove(name2remove, byName=True)
    assert not entry2Remove in databaseName.entries
    # Remove by Path
    databasePath = copy.deepcopy(database)
    file2remove = "folder2/folder2file1.mp4"
    path2remove = dbRootPath + "/" + file2remove
    entry2Remove = databasePath.getEntryByItemName("Path", file2remove)[0]
    databasePath.remove(file2remove, byPath=True)
    assert not entry2Remove in databasePath.entries
    del database


def test_12_DB_findNewFiles_append():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    lastIDbeforeAppend = database.maxID
    os.system("touch " + dir2tests + "/testStructure/newfile.mp4")
    newFiles, pairs = database.findNewFiles()
    os.system("rm " + dir2tests + "/testStructure/newfile.mp4")
    assert "newfile.mp4" in newFiles
    assert len(newFiles) == 1
    asEntry = False
    for entry in database.entries:
        if entry.Path == "newfile.mp4":
            asEntry = True
            newEntry = entry
            break
    assert asEntry
    assert int(newEntry.ID) == lastIDbeforeAppend + 1
    assert database.maxID == lastIDbeforeAppend + 1
    del database


def test_13_p1_DB_query():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    updatedEntry1 = database.getEntryByItemName("ID", "0")[0]
    updatedEntry2 = database.getEntryByItemName("ID", "1")[0]
    updatedEntry1.changeItemValue("SingleItem", "ReplacedValue")
    updatedEntry1.addItemValue("ListItem", "AddedValue")
    updatedEntry2.changeItemValue("SingleItem", "ReplacedValue")
    ########################################################
    # First names wrong
    with pytest.raises(KeyError):
        database.query(["Blubb", "SingleItem"], "SomeQuery")
    # Second names wrong
    with pytest.raises(KeyError):
        database.query(["SingleItem", "Blubb"], "SomeQuery")
    ########################################################
    resultEntry = database.query(["SingleItem", "ListItem"], ["ReplacedValue"])
    resultID = database.query(
        ["SingleItem", "ListItem"], ["ReplacedValue"], returnIDs=True
    )
    found1, found2 = False, False
    if updatedEntry1 in resultEntry:
        found1 = True
    if updatedEntry2 in resultEntry:
        found2 = True
    foundEntry = found1 and found2
    assert resultID == ["0", "1"]
    resultID = database.query(
        ["SingleItem", "ListItem"], ["AddedValue", "ReplacedValue"], returnIDs=True
    )
    assert resultID == ["0"]
    del database


@pytest.mark.parametrize(
    "Query, IDsExp",
    [
        ("!Lavender", ["0", "1", "2", "5"]),
        ("!Xi", ["1", "2", "3", "4", "5"]),
        ("!Eta Lavender", ["4"]),
    ],
)
def test_13_p2_DB_query(Query, IDsExp, preCreatedDB):
    qList = Query.split(" ")
    resultID = preCreatedDB.query(["SingleItem", "ListItem"], qList, returnIDs=True)
    assert resultID == IDsExp


@pytest.mark.parametrize("Query, IDsExp", [("Triple Orange", ["0"])])
def test_13_p3_DB_query(Query, IDsExp, preCreatedDB):
    qList = Query.split(" ")
    resultID = preCreatedDB.query(["SingleItem", "ListItem"], qList, returnIDs=True)
    assert resultID == IDsExp


def test_14_DB_modifyEntry():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    thisDate, thisTime = getDataTime()
    # --------------------- SingleItem -------------------------
    # Replace single Item value
    database.modifySingleEntry("1", "SingleItem", "changedItemValue", byID=True)
    changedEntry = database.getEntryByItemName("ID", "1")[0]
    assert "changedItemValue" in changedEntry.getAllValuesbyName("SingleItem")
    change_datetime = changedEntry.getAllValuesbyName("Changed")
    change_datetime = list(change_datetime)[0]
    assert change_datetime != "emptyChanged"
    date, time = change_datetime.split("|")
    assert date == thisDate
    assert time[0:1] == thisTime[0:1]
    # Check if Item is present in database
    with pytest.raises(KeyError):
        database.modifySingleEntry("1", "BLubbb", "changedItemValue", byID=True)
    with pytest.raises(TypeError):
        database.modifySingleEntry("1", "ListItem", "changedItemValue", byID=True)
    # ---------------------- ListItem --------------------------
    with pytest.raises(TypeError):
        database.modifyListEntry(
            "1", "SingleItem", "appendedItemValue", "Append", byID=True
        )

    # Append but first default schould be remove when appending the fist actual value
    origEntry = database.getEntryByItemName("ID", "1")[0]
    database.modifyListEntry("1", "ListItem", "initialValue", "Append", byID=True)
    changedEntry = database.getEntryByItemName("ID", "1")[0]
    # print(database.model.getDefaultValue("ListItem"))
    assert (
        "initialValue" in changedEntry.getAllValuesbyName("ListItem")
        and database.model.getDefaultValue("ListItem")
        not in changedEntry.getAllValuesbyName("ListItem")
        and len(changedEntry.getAllValuesbyName("ListItem")) == 1
    )
    # Append
    change_datetime = changedEntry.getAllValuesbyName("Changed")
    change_datetime = list(change_datetime)[0]
    assert change_datetime != "emptyChanged"
    date, time = change_datetime.split("|")
    assert date == thisDate
    assert time[0:1] == thisTime[0:1]
    print("-------- Append ----------")
    origEntry = database.getEntryByItemName("ID", "1")[0]
    databaseAppend = copy.deepcopy(database)
    databaseAppend.modifyListEntry(
        "1", "ListItem", "appendedItemValue", "Append", byID=True
    )
    changedEntry = databaseAppend.getEntryByItemName("ID", "1")[0]
    assert "appendedItemValue" in changedEntry.getAllValuesbyName(
        "ListItem"
    ) and origEntry.getAllValuesbyName("ListItem").issubset(
        changedEntry.getAllValuesbyName("ListItem")
    )
    # Replace
    print("-------- Replace ----------")
    databaseReplace = copy.deepcopy(databaseAppend)
    databaseReplace.modifyListEntry(
        "1", "ListItem", "replacedItemValue", "Replace", "initialValue", byID=True
    )
    changedEntry = databaseReplace.getEntryByItemName("ID", "1")[0]
    assert "replacedItemValue" in changedEntry.getAllValuesbyName(
        "ListItem"
    ) and "initialValue" not in changedEntry.getAllValuesbyName("ListItem")

    # Remove
    print("-------- Remove I ----------")
    databaseAppend.modifyListEntry(
        "1", "ListItem", None, "Remove", "appendedItemValue", byID=True
    )
    changedEntry = databaseAppend.getEntryByItemName("ID", "1")[0]
    assert "appendedItemValue" not in changedEntry.getAllValuesbyName("ListItem")
    # Remove empty entry
    print("-------- Remove II ----------")
    databaseReplace.modifyListEntry(
        "1", "ListItem", None, "Remove", "appendedItemValue", byID=True
    )
    databaseReplace.modifyListEntry(
        "1", "ListItem", None, "Remove", "replacedItemValue", byID=True
    )
    changedEntry = databaseReplace.getEntryByItemName("ID", "1")[0]
    assert set(
        databaseReplace.model.listitems["ListItem"]["default"]
    ) == changedEntry.getAllValuesbyName("ListItem")
    print("-------- Change date for ListItem ----------")
    database.modifyListEntry("2", "ListItem", "initialValue", "Append", byID=True)
    changedEntry = database.getEntryByItemName("ID", "2")[0]
    change_datetime = changedEntry.getAllValuesbyName("Changed")
    change_datetime = list(change_datetime)[0]
    assert change_datetime != "emptyChanged"
    date, time = change_datetime.split("|")
    assert date == thisDate
    assert time[0:1] == thisTime[0:1]


def test_15_DB_status():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    # DB not saved
    assert not database.getStatus()
    # DB saved
    database.saveMain()
    assert database.getStatus()
    # DB changed - new File
    os.system("touch " + dir2tests + "/testStructure/newfile.mp4")
    newFiles = database.findNewFiles()
    os.system("rm " + dir2tests + "/testStructure/newfile.mp4")
    assert not database.getStatus()
    database.saveMain()
    assert database.getStatus()
    # DB changed - changed Entry


def test_16_DB_random():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    allIDs = database.getAllValuebyItemName("ID")
    randID = database.getRandomEntry(chooseFrom=allIDs)
    assert randID in allIDs


def test_17_DB_random_all():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    allIDs = database.getAllValuebyItemName("ID")
    randID = database.getRandomEntryAll()
    assert randID in allIDs


def test_18_DB_random_weighted():
    config = mimir_dir + "/conf/modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")
    database = DataBase(dbRootPath, "new", config)
    allIDs = database.getAllValuebyItemName("ID")

    with pytest.raises(NotImplementedError):
        randID = database.getRandomEntry(chooseFrom=allIDs, weighted=True)
    # assert randID in allIDs


def test_19_DB_getSortedIDs(preCreatedDB):
    with pytest.raises(KeyError):
        sorted_addedIDs = preCreatedDB.getSortedIDs("BLUBB")
    with pytest.raises(NotImplementedError):
        sorted_addedIDs = preCreatedDB.getSortedIDs("ListItem")
    # Get sorted by Added (SingleItem with datetime)
    expected_added = ["0", "2", "3", "5", "1", "4"]
    sorted_addedIDs = preCreatedDB.getSortedIDs("Added", reverseOrder=True)
    print(sorted_addedIDs)
    for iId, expected_id in enumerate(expected_added):
        assert expected_id == sorted_addedIDs[iId]
    # Same but with reverse order --> Test if ID sorting is independent of reverse
    expected_added = ["4", "1", "5", "2", "3", "0"]
    sorted_addedIDs = preCreatedDB.getSortedIDs("Added", reverseOrder=False)
    for iId, expected_id in enumerate(expected_added):
        assert expected_id == sorted_addedIDs[iId]
    # Get sorted by Changed (Listentry with datetime)
    expected_changed = ["0", "3", "4", "5", "1", "2"]
    sorted_changedIDs = preCreatedDB.getSortedIDs("Changed")
    for iId, expected_id in enumerate(expected_changed):
        assert expected_id == sorted_changedIDs[iId]
    # Get sorted by Singleitem (alphabetically)
    expected_singleItem = ["5", "4", "3", "2", "1", "0"]
    sorted_singleIDs = preCreatedDB.getSortedIDs("SingleItem", reverseOrder=False)
    for iId, expected_id in enumerate(expected_singleItem):
        assert expected_id == sorted_singleIDs[iId]
    # Get sorted by Rating (numerically)
    expected_rating = ["3", "2", "4", "1", "5", "0"]
    sorted_ratingIDs = preCreatedDB.getSortedIDs("Rating")
    for iId, expected_id in enumerate(expected_rating):
        assert expected_id == sorted_ratingIDs[iId]


def test_20_DB_updatedOpened(preCreatedDB):
    preCreatedDB.updateOpened("1")
    thisDate, thisTime = getDataTime()
    changedEntry = preCreatedDB.getEntryByItemName("ID", "1")[0]
    change_datetime = list(changedEntry.getAllValuesbyName("Opened"))[0]
    date, time = change_datetime.split("|")
    assert date == thisDate
    assert time[0:1] == thisTime[0:1]


def test_21_DB_guessSecondaryDBItembyPath(preCreatedDB):
    # 1: Test if "elements" are part of the secondaryDB
    newFile = "testStructure/Blue/Xi.mp4"
    options = preCreatedDB.getItemsPyPath(newFile)
    assert "Xi" in options["SingleItem"]
    assert "Blue" in options["ListItem"]
    assert options["SingleItem"] == set(["Xi"]) and options["ListItem"] == set(["Blue"])
    # 2: Test if it works when subparts of a "element" are part of secondaryDB
    # 2.1: Fast version which will not try to split strings
    newFile = "testStructure/Pink/BlueXi.mp4"
    options = preCreatedDB.getItemsPyPath(newFile, fast=True)
    assert "Xi" not in options["SingleItem"]
    assert "Blue" not in options["ListItem"]
    assert options["SingleItem"] == set([]) and options["ListItem"] == set([])
    # 2.2; Test with enables splitting
    options = preCreatedDB.getItemsPyPath(newFile)
    assert "Xi" in options["SingleItem"]
    assert "Blue" in options["ListItem"]
    assert options["SingleItem"] == set(["Xi"]) and options["ListItem"] == set(["Blue"])
    # 2.3: Test lowercase match
    newFile = "testStructure/Pink/bluexi.mp4"
    options = preCreatedDB.getItemsPyPath(newFile)
    assert "Xi" in options["SingleItem"]
    assert "Blue" in options["ListItem"]
    assert options["SingleItem"] == set(["Xi"]) and options["ListItem"] == set(["Blue"])
    # 3: Test for items with whitespace - Find exact match
    newFile = "testStructure/Pink/Double_Orange.mp4"
    options = preCreatedDB.getItemsPyPath(newFile, whitespaceMatch=True)
    assert options["ListItem"] == set(["Double Orange"])
    # 3.1 Test whitespace lowercase:
    newFile = "testStructure/Pink/double_orange.mp4"
    options = preCreatedDB.getItemsPyPath(newFile, whitespaceMatch=True)
    assert options["ListItem"] == set(["Double Orange"])
    # 4: Test for items with whitespace - find partial match
    newFile = "testStructure/Pink/Orange_Hand.mp4"
    options = preCreatedDB.getItemsPyPath(newFile)
    assert "Double Orange" in options["ListItem"]
    assert "Triple Orange" in options["ListItem"]
    assert options["ListItem"] == set(["Triple Orange", "Double Orange"])
    # 5: Test for items with whitespace - find partial match, exact mathc deactivated
    newFile = "testStructure/Pink/Double_Orange.mp4"
    options = preCreatedDB.getItemsPyPath(newFile, whitespaceMatch=False)
    assert options["ListItem"] == set(["Triple Orange", "Double Orange"])
    # Check if it works with ne values that are added before save/load
    newFile = "testStructure/folder/Red.mp4"
    options = preCreatedDB.getItemsPyPath(newFile)
    assert "Red" not in options["ListItem"]
    preCreatedDB.modifyListEntry("0", "ListItem", "Red", byID=True)
    options = preCreatedDB.getItemsPyPath(newFile)
    print("-------------------", options)
    assert "Red" in options["ListItem"]


def test_22_DB_splitBySep(preCreatedDB):
    split1 = preCreatedDB.splitBySep(".", ["a.b", "c.d-e"])
    assert ["a", "b", "c", "d-e"] == split1
    split2 = preCreatedDB.splitBySep("-", split1)
    assert ["a", "b", "c", "d", "e"] == split2


def test_23_DB_recursiveSplit(preCreatedDB):
    strings2Split = "A-b_c+d.e"
    strings2Expect = set(["A", "b", "c", "d", "e"])
    assert strings2Expect == preCreatedDB.splitStr(strings2Split)


@pytest.mark.parametrize("ID, nExpected", [("4", 3), ("1", 0), ("3", 1)])
def test_24_DB_countListItem(ID, nExpected, preCreatedDB):
    assert preCreatedDB.getCount(ID, "ListItem", byID=True) == nExpected


def test_25_DB_cachedValues(mocker, preCreatedDB):
    assert preCreatedDB.cachedValuesChanged.keys() == preCreatedDB.model.allItems
    mocker.spy(DataBase, "cacheAllValuebyItemName")
    ###### Test caching for ListItem entries
    values_ListItem_preChange = preCreatedDB.getAllValuebyItemName("ListItem")
    assert DataBase.cacheAllValuebyItemName.call_count == 0
    preCreatedDB.modifyListEntry("4", "ListItem", "Cyan", byID=True)
    values_ListItem_postChange = preCreatedDB.getAllValuebyItemName("ListItem")
    assert DataBase.cacheAllValuebyItemName.call_count == 1
    assert list(set(values_ListItem_postChange) - set(values_ListItem_preChange)) == [
        "Cyan"
    ]
    ###### Test caching for SingleItem Entries
    Entry4 = preCreatedDB.getEntryByItemName("ID", "4")[0]
    oldValue = Entry4.getItem("SingleItem").value
    newValue = "Gamma"
    preCreatedDB.modifySingleEntry("4", "SingleItem", newValue, byID=True)
    values_ListItem_postChange = preCreatedDB.getAllValuebyItemName("SingleItem")
    assert DataBase.cacheAllValuebyItemName.call_count == 2
    assert (
        oldValue not in values_ListItem_postChange
        and newValue in values_ListItem_postChange
    )


def test_26_DB_changedPaths(preCreatedDB):
    updatedFiles = preCreatedDB.checkChangedPaths()
    assert updatedFiles == []
    preCreatedDB.modifySingleEntry(
        "folder2/folder2file2.mp4", "Path", "folder2file2.mp4", byPath=True
    )
    thisID = (
        preCreatedDB.getEntryByItemName("Path", "folder2file2.mp4")[0]
        .getItem("ID")
        .value
    )
    updatedFiles = preCreatedDB.checkChangedPaths()
    thisNewPath = preCreatedDB.getEntryByItemName("ID", thisID)[0].getItem("Path").value
    theID, oldPath, newPath = updatedFiles[0]
    assert theID == thisID
    assert oldPath == "folder2file2.mp4"
    assert newPath == "folder2/folder2file2.mp4"
    assert thisNewPath == "folder2/folder2file2.mp4"


def test_27_DB_missingFiles(preCreatedDB):
    missingFiles = preCreatedDB.getMissingFiles()
    assert missingFiles == []
    os.system("rm " + dir2tests + "/testStructure/folder2/folder2file2.mp4")
    missingFiles = preCreatedDB.getMissingFiles()
    assert missingFiles == ["folder2/folder2file2.mp4"]
    os.system("touch " + dir2tests + "/testStructure/folder2/folder2file2.mp4")


def test_28_DB_checkMissingFileAndReSort(preCreatedDB):
    preCreatedDB2 = copy.deepcopy(preCreatedDB)
    os.system("rm " + dir2tests + "/testStructure/folder2/folder2file2.mp4")
    removedID = (
        preCreatedDB2.getEntryByItemName("Path", "folder2/folder2file2.mp4")[0]
        .getItem("ID")
        .value
    )
    movedPath = (
        preCreatedDB2.getEntryByItemName("ID", str(preCreatedDB2.maxID))[0]
        .getItem("Path")
        .value
    )
    oldMaxID = preCreatedDB2.maxID
    IDChanges = preCreatedDB2.checkMissingFiles()
    os.system("touch " + dir2tests + "/testStructure/folder2/folder2file2.mp4")
    oldID, newID = IDChanges[0]
    assert newID == removedID
    assert oldID == oldMaxID
    assert (
        movedPath
        == preCreatedDB2.getEntryByItemName("ID", removedID)[0].getItem("Path").value
    )


if __name__ == "__main__":
    unittest.main()
