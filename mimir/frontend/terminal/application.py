import os
import logging
import json
from mimir.backend.database import DataBase
from mimir.frontend.terminal.display import Window, ListWindow

class App:
    """
    App class that manages the communication between the Window module and the database model
    """
    def __init__(self, dababase):
        self.database = dababase
        if not os.path.exists(self.database.mimirdir+"/MTF_model.json"):
            raise RuntimeError("No MTF configuration found in .mimir directory. Use make MTFconfig.py to create on from the database config")
        self.config = MTFConfig(self.database.mimirdir+"/MTF_model.json")
        self.windowHeight = self.config.height
        self.windowWidth = self.config.width

        self.currentWindow = None
        mainHeader = {"Title" : self.config.windows["Main"]["Title"],
                      "Text" : self.config.windows["Main"]["Text"],
                      "Options" : self.config.windows["Main"]["Options"],}
        self.mainWindow = Window(self.windowHeight,
                                 self.windowWidth,
                                 mainHeader)
        self.mainWindow.setHeader()
        self.currentWindow = self.mainWindow

    def start(self):
        logging.info("Starting App")
        retVal = None
        while retVal != "0":
            retVal = self.currentWindow.draw("Enter Value: ")
            if retVal not in self.currentWindow.validOptions:
                self.currentWindow.update("Please enter value present in %s"%self.currentWindow.validOptions)

    def saveDB(self):
        pass

    def about(self):
        """
        Method that returns the information for the about screen. Like python-version, number entryies, number if values per ListItem, most used Value

        Returns:
            aboutInfo (dict) : All values of interest
        """
        pass

class MTFConfig:
    """
    Class for processing and saving MTF confugurations
    """
    def __init__(self, config):
        logging.debug("Loading MTF config from %s", config)
        self.fileName = config
        configDict = None
        with open(config) as f:
            configDict = json.load(f)
        self.height = configDict["General"]["Height"]
        self.width = configDict["General"]["Width"]
        self.items = configDict["General"]["DisplayItems"]

        self.itemInfo = {}
        for iItem, item in enumerate(self.items):
            self.itemInfo[item] = {}
            self.itemInfo[item]["DisplayName"] = configDict[item]["DisplayName"]
            self.itemInfo[item]["Type"] = configDict[item]["Type"]
            if self.itemInfo[item]["Type"] == "ListItem":
                self.itemInfo[item]["Hide"] = configDict[item]["Hide"]
                self.itemInfo[item]["Priority"] = configDict[item]["Priority"]
                self.itemInfo[item]["nDisplay"] = configDict[item]["nDisplay"]
            else:
                self.itemInfo[item]["maxLen"] = configDict[item]["maxLen"]

        self.definedWindows = configDict["General"]["Windows"]
        self.windows = {}
        for window in configDict["General"]["Windows"]:
            self.windows[window] = {}
            self.windows[window]["Type"] = configDict["Window"][window]["Type"]
            self.windows[window]["Title"] = configDict["Window"][window]["Title"]
            self.windows[window]["Text"] = configDict["Window"][window]["Text"]
            self.windows[window]["Options"] = configDict["Window"][window]["Options"]
            for iopt, opt in enumerate(self.windows[window]["Options"]):
                self.windows[window]["Options"][iopt] = tuple(opt)

def initDatabase(basedir, config = None):
    """
    Function for initializing the databse when running Mimir3 with the MTF frontend.

    Args:
        basedir (str) : Base direcotry for the databse run in the forntend
        config (str) : Only necessary if a new database should be initialized

    Raises:
        RuntimeError : Raised if no .mimir dir is found in basedir and config is None

    Returns:
        databse (DataBase) : Initialized/loaded database
        initType (str) : Either "new" or "loaded"
    """
    if os.path.exists(basedir+"/.mimir"):
        logging.debug("Found .mimir dir for %s",basedir)
        database = DataBase(basedir, "load")
        initType = "loaded"
    else:
        if config is None:
            raise RuntimeError("Found no .mimir in %s. Please pass initial config"%basedir)
        else:
            logging.debug("Creating new databse")
            database = DataBase(basedir, "new", config)
            initType = "new"

    return database, initType
