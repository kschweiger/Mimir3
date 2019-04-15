import sys
import os
import shutil
import json
from glob import glob
#sys.path.insert(0, os.path.abspath('..'))
#sys.path.insert(0, os.path.abspath('.'))
#print(sys.path)
import hachoir.metadata
from mimir.backend.database import DataBase, Model
from mimir.backend.entry import Item, ListItem
import mimir.backend.plugin
import unittest
import pytest
import coverage
import os
import copy
import datetime

if os.getcwd().endswith("tests"):
    mimir_dir = os.getcwd()[0:-len("/tests")]
    dir2tests = os.getcwd()
else:
    mimir_dir = os.getcwd()
    dir2tests = os.getcwd()+"/tests"

@pytest.fixture(scope="module")
def preCreatedDB():
    config = mimir_dir+"/conf/modeltest.json"
    with open(config) as f:
        modelDict = json.load(f)

    modelDict["Width"] = {"Type" : "Item", "default" : "-1", "hide" : "",
                          "itemType" : "int" ,"plugin" : "VideoMetaData:width"}
    modelDict["Height"] = {"Type" : "Item", "default" : "-1", "hide" : "",
                           "itemType" : "int" ,"plugin" : "VideoMetaData:height"}
    modelDict["Duration"] = {"Type" : "Item", "default" : "-1", "hide" : "",
                             "itemType" : "str" ,"plugin" : "VideoMetaData:duration"}
    modelDict["Size"] = {"Type" : "Item", "default" : "-1", "hide" : "",
                             "itemType" : "str" ,"plugin" : "osData:size"}
    with open("conf/plugin_modeltest.json", 'w') as outfile:
        json.dump(modelDict, outfile, sort_keys=True, indent=4, separators=(',', ': '))
    pluginConf = mimir_dir+"/conf/plugin_modeltest.json"
    dbRootPath = dir2tests+"/testStructure"
    if os.path.exists(dbRootPath+"/.mimir"):
        shutil.rmtree(dbRootPath+"/.mimir")
    database = DataBase(dbRootPath, "new", pluginConf)
    database.saveMain()
    #shutil.copytree(dbRootPath+"/.mimir", dbRootPath+"/.mimir2") #For testing
    shutil.rmtree(dbRootPath+"/.mimir")
    return database


def test_01_plugin_VideoMetaData_valid(mocker):
    def returnMeta(SomeInput):
        return {"width" : 100,
                "height" : 200,
                "duration" : "01:02:03.4444"}
    mocker.patch("hachoir.metadata.extractMetadata", new=returnMeta)
    mocker.patch("hachoir.parser.createParser", new=returnMeta)
    metadata = mimir.backend.plugin.get_VideoMetaData("SomeFilename") #Valid filename will always be passed
    assert metadata == {"width" : 100, "height" : 200, "duration" : "01:02:03"}

def test_02_plugin_VideoMetaData_ValueError(mocker):
    class MockMeta:
        def __init__(self):
            pass
        def get(self):
            raise ValueError

    def returnMeta(SomeInput):
        return MockMeta
    mocker.patch("hachoir.metadata.extractMetadata", new=returnMeta)
    mocker.patch("hachoir.parser.createParser", new=returnMeta)
    metadata = mimir.backend.plugin.get_VideoMetaData("SomeFilename") #Valid filename will always be passed
    assert metadata == {"width" : -1, "height" : -1, "duration" : "00:00:00"}

def test_03_plugin_VideoMetaData_None(mocker):
    def returnMeta(SomeInput):
        return None
    mocker.patch("hachoir.metadata.extractMetadata", new=returnMeta)
    mocker.patch("hachoir.parser.createParser", new=returnMeta)
    metadata = mimir.backend.plugin.get_VideoMetaData("SomeFilename") #Valid filename will always be passed
    assert metadata == {"width" : -1, "height" : -1, "duration" : "00:00:00"}

@pytest.mark.parametrize("fileSize,fileSizeGB", [(126730706, 126730706/1e9), (1126730706, 1126730706/1e9)])
def test_04_plugin_osData(fileSize,fileSizeGB,mocker):
    fileSize = 126730706
    class stat:
        def __init__(self, filename):
            self.st_size = fileSize
    mocker.patch("os.stat", new=stat)
    fileSizeGB = mimir.backend.plugin.get_osData("SomeFileName")
    assert fileSizeGB == {"size" : "{0:.2f}".format(fileSize/1e9)}

@pytest.mark.parametrize("fileSize,fileSizeGB,height,width,duration,durationExp", [(126730706, 126730706/1e9, 100, 200, "01:02:03.4444", "01:02:03")])
def test_05_plugin_getPluginValues(fileSize,fileSizeGB,height,width,
                                   duration,durationExp, preCreatedDB, mocker):
    def returnMeta(SomeInput):
        return {"width" : width,
                "height" : height,
                "duration" : duration}
    mocker.patch("hachoir.metadata.extractMetadata", new=returnMeta)
    mocker.patch("hachoir.parser.createParser", new=returnMeta)
    class stat:
        def __init__(self, filename):
            self.st_size =fileSize
    mocker.patch("os.stat", new=stat)
    with pytest.raises(ValueError):
        metadata = mimir.backend.plugin.getPluginValues("SomeFileName", ["blubb"])
    with pytest.raises(ValueError):
        metadata = mimir.backend.plugin.getPluginValues("SomeFileName", ["aaa:bbb:ccc"])
    with pytest.raises(ValueError):
        metadata = mimir.backend.plugin.getPluginValues("SomeFileName", ["blubb:width"])

    pluginValues = mimir.backend.plugin.getPluginValues("SomeFileName", preCreatedDB.model.pluginDefinitions)

    assert pluginValues.keys() == preCreatedDB.model.pluginDefinitions
    assert pluginValues["VideoMetaData:width"] == width
    assert pluginValues["VideoMetaData:height"] == height
    assert pluginValues["VideoMetaData:duration"] == durationExp
    assert pluginValues["osData:size"] == "{0:.2f}".format(fileSizeGB)

    pluginValues = mimir.backend.plugin.getPluginValues("SomeFileName", ["osData:size"])

    assert pluginValues.keys() == set(["osData:size"])
    assert pluginValues["osData:size"] == "{0:.2f}".format(fileSizeGB)

    pluginValues = mimir.backend.plugin.getPluginValues("SomeFileName", ["VideoMetaData:width"])

    assert pluginValues.keys() == set(["VideoMetaData:width"])
    assert pluginValues["VideoMetaData:width"] == width
