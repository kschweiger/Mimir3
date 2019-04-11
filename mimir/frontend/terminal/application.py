import os
import logging
import json
from mimir.backend.database import DataBase
from mimir.backend.entry import Item, ListItem
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
        self.tableColumns = len(self.config.items)
        self.tableColumnItems = self.config.items
        self.tableColumnNames = []
        for item in self.config.items:
            self.tableColumnNames.append(self.config.itemInfo[item]["DisplayName"])
        self.tableColumnNames = tuple(self.tableColumnNames)

        ################### Main Window ###################
        mainHeader = {"Title" : self.config.windows["Main"]["Title"],
                      "Text" : ["Mimir base dir: {0}".format(self.database.databaseRoot)] +
                               self.config.windows["Main"]["Text"],
                      "Options" : self.config.windows["Main"]["Options"],}
        self.mainWindow = Window(self.windowHeight,
                                 self.windowWidth,
                                 mainHeader)
        self.mainWindow.setHeader()
        ################### List Window ###################
        listHeader = {"Title" : self.config.windows["List"]["Title"],
                      "Options" : self.config.windows["List"]["Options"],}
        self.listWindow = ListWindow(self.windowHeight,
                                     self.windowWidth,
                                     listHeader,
                                     self.tableColumns,
                                     self.tableColumnNames)
        self.listWindow.setHeader()
        self.listWindowDrawn = False
        ################### DB Window ###################
        dbHeader = {"Title" : self.config.windows["DB"]["Title"],
                      "Text" : self.config.windows["DB"]["Text"],
                      "Options" : self.config.windows["DB"]["Options"],}
        self.dbWindow = Window(self.windowHeight,
                                 self.windowWidth,
                                 dbHeader)
        self.dbWindow.setHeader()
        for key in self.config.windows:
            print(self.config.windows[key])
        ################### Modification Window ###################
        modHeader = {"Title" : self.config.windows["Modify"]["Title"],
                     "Text" : self.config.windows["Modify"]["Text"],
                     "Options" : self.config.windows["Modify"]["Options"],}
        self.modWindow = Window(self.windowHeight,
                               self.windowWidth,
                               modHeader)
        self.modWindow.setHeader()
        ################### Mulit Modification Window ###################
        multiModHeader = {"Title" : self.config.windows["MultiModify"]["Title"],
                     "Text" : self.config.windows["MultiModify"]["Text"],
                     "Options" : self.config.windows["MultiModify"]["Options"],}
        self.multiModWindow = Window(self.windowHeight,
                               self.windowWidth,
                               multiModHeader)
        self.multiModWindow.setHeader()

    def start(self):
        logging.info("Starting App")
        self.runMainWindow(None)
        logging.info("Terminating App")

    def runMainWindow(self, startVal):
        logging.info("Switching to main window")
        retVal = startVal
        while retVal != "0":
            retVal = self.mainWindow.draw("Enter Value: ")
            if retVal == "1":
                pass
            elif retVal == "2":
                self.runModWindow(None, fromMain=True, fromList=False)
            elif retVal == "3":
                self.runListWindow(None)
            elif retVal == "4":
                pass
            elif retVal == "5":
                self.runDBWindow(None)
            elif retVal == "0":
                self.terminate()
            else:
                self.mainWindow.update("Please enter value present in %s"%self.mainWindow.validOptions)

    def runListWindow(self, startVal):
        logging.info("Switching to ListWindow")
        retVal = startVal
        self.listWindow.draw(skipHeader = self.listWindowDrawn, skipTable = True, fillWindow = True)
        self.listWindowDrawn = True
        #retVal = self.listWindow.interact("Enter Value:", None)
        while retVal != "0":
            retVal = self.listWindow.interact("Enter Value:", None)
            if retVal == "1": #Print All
                tableElements = self.generateList("All")
                self.listWindow.lines = []
                self.listWindow.update(tableElements)
                #print("=========================================")
                #self.listWindow.draw(skipHeader = True, skipTable = False, fillWindow = False)
                #print("+++++++++++++++++++++++++++++++++++++++++")
                retVal = self.listWindow.interact("Enter Value:", None, onlyInteraction = False)
            elif retVal == "2": #Print Quary
                self.runModWindow(None, fromMain=False, fromList=True)
            elif retVal == "3": #Print Newest
                pass
            else:
                self.listWindow.print("Please enter value present in %s"%self.listWindow.validOptions)
        self.runMainWindow(None)

    def runDBWindow(self, startVal):
        logging.info("Switching to main window")
        retVal = startVal
        while retVal != "0":
            retVal = self.dbWindow.draw("Enter Value: ")
            if retVal == "1":
                pass
            elif retVal == "2":
                pass
            else:
                self.dbWindow.update("Please enter value present in %s"%self.dbWindow.validOptions)
        self.runMainWindow(None)

    def runModWindow(self, startVal, fromMain, fromList):
        logging.info("Switching to modification window")
        retVal = startVal
        while retVal != "0":
            retVal = self.modWindow.draw("Enter Value: ")
            if retVal == "1":
                self.runMultiModWindow(None)
            elif retVal == "2":
                pass
            else:
                self.modWindow.update("Please enter value present in %s"%self.modWindow.validOptions)
        if fromMain:
            self.runMainWindow(None)
        if fromList:
            self.runListWindow(None)

    def runMultiModWindow(self, startVal):
        logging.info("Switching to multi modification window")
        retVal = startVal
        while retVal != "0":
            retVal = self.multiModWindow.draw("Enter Value: ")
            if retVal == "1":
                pass
            elif retVal == "2":
                pass
            else:
                self.multiModWindow.update("Please enter value present in %s"%self.multiModWindow.validOptions)
        self.runModWindow(None)

    def terminate(self):
        logging.info("Checking if database was saved")
        #TODO: CHeck if database is modified but nit saved
        logging.info("Terminating app")
        exit()

    def modify(self):
        pass

    def generateList(self, get="All"):
        #TODO Check get input
        tableElements = []
        ids2Print = None
        if get == "All":
            ids2Print = self.database.getAllValuebyItemName("ID")
            ids2Print = sorted(list(ids2Print), key=lambda x: int(x))
        elif isinstance(get, list):
            ids2Print = get
        logging.info(ids2Print)
        for id in ids2Print:
            entryElements = []
            thisEntry = self.database.getEntryByItemName("ID", id)[0]
            for item in self.tableColumnItems:
                thisItem = thisEntry.getItem(item)
                if isinstance(thisItem, ListItem):
                    thisValue = []
                    for priority in self.config.itemInfo[item]["Priority"]:
                        if priority in thisItem.value:
                            thisValue.append(priority)
                    for val in thisItem.value:
                        if val not in thisValue and len(thisValue) <= self.config.itemInfo[item]["nDisplay"]:
                            print(val, self.database.model.getDefaultValue(item))
                            if (val == self.database.model.getDefaultValue(item) and
                                self.config.itemInfo[item]["DisplayDefault"] is not None):
                                thisValue.append(self.config.itemInfo[item]["DisplayDefault"])
                            else:
                                thisValue.append(val)
                        if len(thisValue) >= self.config.itemInfo[item]["nDisplay"]:
                            thisValue.append("..")
                            break
                    #TODO: Add maxlen to ListItems and make sure the joind sting is shorter
                    value = ", ".join(thisValue)
                else:
                    if (thisItem.value == self.database.model.getDefaultValue(item) and
                        self.config.itemInfo[item]["DisplayDefault"] is not None):
                        itemValue = self.config.itemInfo[item]["DisplayDefault"]
                    else:
                        itemValue = thisItem.value
                    if len(itemValue) > self.config.itemInfo[item]["maxLen"]:
                        value = itemValue[:self.config.itemInfo[item]["maxLen"]]+".."
                    else:
                        value = itemValue
                entryElements.append(value)
            tableElements.append(tuple(entryElements))
        return tableElements

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
            self.itemInfo[item]["DisplayDefault"] = configDict[item]["DisplayDefault"]
            self.itemInfo[item]["Type"] = configDict[item]["Type"]
            if self.itemInfo[item]["Type"] == "ListItem":
                self.itemInfo[item]["Hide"] = configDict[item]["Hide"]
                self.itemInfo[item]["Priority"] = configDict[item]["Priority"]
                self.itemInfo[item]["nDisplay"] = configDict[item]["nDisplay"]
            else:
                self.itemInfo[item]["maxLen"] = configDict[item]["maxLen"]

        self.definedWindows = configDict["General"]["Windows"]
        self.windows = {}
        print(configDict["General"]["Windows"])
        for window in configDict["General"]["Windows"]:
            print(window)
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
