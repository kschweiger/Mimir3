# flake8: noqa
import copy
import datetime
import json
import os
import shutil
import sys
import unittest
from glob import glob

import coverage

# sys.path.insert(0, os.path.abspath('..'))
# sys.path.insert(0, os.path.abspath('.'))
# print(sys.path)
import hachoir.metadata
import pytest

import mimir.backend.plugin
from mimir.backend.database import DataBase, Model
from mimir.backend.entry import Item, ListItem

if os.getcwd().endswith("tests"):
    mimir_dir = os.getcwd()[0 : -len("/tests")]
    dir2tests = os.getcwd()
else:
    mimir_dir = os.getcwd()
    dir2tests = os.getcwd() + "/tests"


def test_01_plugin_VideoMetaData_valid(mocker):
    def returnMeta(SomeInput):
        return {"width": 100, "height": 200, "duration": "01:02:03.4444"}

    mocker.patch("hachoir.metadata.extractMetadata", new=returnMeta)
    mocker.patch("hachoir.parser.createParser", new=returnMeta)
    metadata = mimir.backend.plugin.get_VideoMetaData(
        "SomeFilename"
    )  # Valid filename will always be passed
    assert metadata == {"width": "100", "height": "200", "duration": "01:02:03"}


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
    metadata = mimir.backend.plugin.get_VideoMetaData(
        "SomeFilename"
    )  # Valid filename will always be passed
    assert metadata == {"width": "-1", "height": "-1", "duration": "00:00:00"}


def test_03_plugin_VideoMetaData_None(mocker):
    def returnMeta(SomeInput):
        return None

    mocker.patch("hachoir.metadata.extractMetadata", new=returnMeta)
    mocker.patch("hachoir.parser.createParser", new=returnMeta)
    metadata = mimir.backend.plugin.get_VideoMetaData(
        "SomeFilename"
    )  # Valid filename will always be passed
    assert metadata == {"width": "-1", "height": "-1", "duration": "00:00:00"}


@pytest.mark.parametrize(
    "fileSize,fileSizeGB",
    [(126730706, 126730706 / 1e9), (1126730706, 1126730706 / 1e9)],
)
def test_04_plugin_osData(fileSize, fileSizeGB, mocker):
    mocker.patch.object(os.path, "getsize", return_value=fileSize)
    fileSizeGB = mimir.backend.plugin.get_osData("SomeFileName")
    assert fileSizeGB == {"size": "{0:.2f}".format(fileSize / 1e9)}


@pytest.mark.parametrize(
    "fileSize,fileSizeGB,height,width,duration,durationExp",
    [(126730706, 126730706 / 1e9, "100", "200", "01:02:03.4444", "01:02:03")],
)
def test_05_plugin_getPluginValues(
    fileSize, fileSizeGB, height, width, duration, durationExp, mocker
):
    def returnMeta(SomeInput):
        return {"width": width, "height": height, "duration": duration}

    mocker.patch("hachoir.metadata.extractMetadata", new=returnMeta)
    mocker.patch("hachoir.parser.createParser", new=returnMeta)
    mocker.patch.object(os.path, "getsize", return_value=fileSize)
    with pytest.raises(ValueError):
        metadata = mimir.backend.plugin.getPluginValues("SomeFileName", ["blubb"])
    with pytest.raises(ValueError):
        metadata = mimir.backend.plugin.getPluginValues("SomeFileName", ["aaa:bbb:ccc"])
    with pytest.raises(ValueError):
        metadata = mimir.backend.plugin.getPluginValues("SomeFileName", ["blubb:width"])

    pluginDefs = [
        "VideoMetaData:width",
        "VideoMetaData:height",
        "VideoMetaData:duration",
        "osData:size",
    ]

    pluginValues = mimir.backend.plugin.getPluginValues("SomeFileName", pluginDefs)

    assert list(pluginValues.keys()) == pluginDefs
    assert pluginValues["VideoMetaData:width"] == width
    assert pluginValues["VideoMetaData:height"] == height
    assert pluginValues["VideoMetaData:duration"] == durationExp
    assert pluginValues["osData:size"] == "{0:.2f}".format(fileSizeGB)

    pluginValues = mimir.backend.plugin.getPluginValues("SomeFileName", ["osData:size"])

    assert pluginValues.keys() == set(["osData:size"])
    assert pluginValues["osData:size"] == "{0:.2f}".format(fileSizeGB)

    pluginValues = mimir.backend.plugin.getPluginValues(
        "SomeFileName", ["VideoMetaData:width"]
    )

    assert pluginValues.keys() == set(["VideoMetaData:width"])
    assert pluginValues["VideoMetaData:width"] == width


def test_06_plugin_newEntry_wPlugin(mocker):
    fileSize = 126730706
    fileSizeGB = "{0:.2f}".format(fileSize / 1e9)
    height = "100"
    width = "200"
    duration = "01:02:03.4444"
    durationExp = "01:02:03"

    def returnMeta(SomeInput):
        return {"width": width, "height": height, "duration": duration}

    mocker.patch("hachoir.metadata.extractMetadata", new=returnMeta)
    mocker.patch("hachoir.parser.createParser", new=returnMeta)
    mocker.patch.object(os.path, "getsize", return_value=fileSize)
    mocker.spy(mimir.backend.plugin, "getPluginValues")
    ########################################################################
    # CREATE A DATABASE
    config = mimir_dir + "/conf/modeltest.json"
    with open(config) as f:
        modelDict = json.load(f)

    modelDict["Width"] = {
        "Type": "Item",
        "default": "-1",
        "hide": "",
        "itemType": "str",
        "plugin": "VideoMetaData:width",
    }
    modelDict["Height"] = {
        "Type": "Item",
        "default": "-1",
        "hide": "",
        "itemType": "str",
        "plugin": "VideoMetaData:height",
    }
    modelDict["Duration"] = {
        "Type": "Item",
        "default": "-1",
        "hide": "",
        "itemType": "str",
        "plugin": "VideoMetaData:duration",
    }
    modelDict["Size"] = {
        "Type": "Item",
        "default": "-1",
        "hide": "",
        "itemType": "str",
        "plugin": "osData:size",
    }
    with open("conf/plugin_modeltest.json", "w") as outfile:
        json.dump(modelDict, outfile, sort_keys=True, indent=4, separators=(",", ": "))
    pluginConf = mimir_dir + "/conf/plugin_modeltest.json"
    dbRootPath = dir2tests + "/testStructure"
    if os.path.exists(dbRootPath + "/.mimir"):
        shutil.rmtree(dbRootPath + "/.mimir")

    database = DataBase(dbRootPath, "new", pluginConf)
    database.saveMain()
    # shutil.copytree(dbRootPath+"/.mimir", dbRootPath+"/.mimir2") #For testing
    shutil.rmtree(dbRootPath + "/.mimir")
    ########################################################################

    aEntry = database.getEntryByItemName("ID", "0")[0]
    metadata_height = list(aEntry.getAllValuesbyName("Height"))[0]
    metadata_width = list(aEntry.getAllValuesbyName("Width"))[0]
    metadata_duration = list(aEntry.getAllValuesbyName("Duration"))[0]
    osData_size = list(aEntry.getAllValuesbyName("Size"))[0]
    assert metadata_height == height
    assert metadata_width == width
    assert metadata_duration == durationExp
    assert osData_size == fileSizeGB
