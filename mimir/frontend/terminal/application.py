import os
import logging
import json
import re
from copy import deepcopy

from mimir.backend.database import DataBase
from mimir.backend.entry import Item, ListItem
from mimir.frontend.terminal.display import Window, ListWindow
import mimir.backend.helper

class App:
    """
    App class that manages the communication between the Window module and the database model

    Args:
        dababase (DataBase) : Initialized mimir DataBase
        enableStartupSeatch (bool) : If True, a search for new files will be enabled on startup
    """
    def __init__(self, dababase, enableStartupSeatch=True):
        self.database = dababase
        if not os.path.exists(self.database.mimirdir+"/MTF_model.json"):
            raise RuntimeError("No MTF configuration found in .mimir directory. Use make MTFconfig.py to create on from the database config")
        self.config = MTFConfig(self.database.mimirdir+"/MTF_model.json")
        self.lastIDList = self.database.getAllValuebyItemName("ID")
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
        self.firstInteraction = True
        self.inOverflow = False
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
        self.allMultiModWindow = {}

        self.modSingleItems = []
        self.modListItems = []
        for item in self.config.modItems:
            if item in self.database.model.items:
                self.modSingleItems.append(item)
            else:
                self.modListItems.append(item)

    def start(self):
        """
        Start point for the app. Launches the mainWindow.
        """
        logging.info("Starting App")
        self.runMainWindow(None)

    def runMainWindow(self, startVal):
        """
        Function defining the interactions of the main window
        """
        logging.info("Switching to main window")
        retVal = startVal
        while retVal != "0":
            retVal = self.mainWindow.draw("Enter Value")
            if retVal == "1":
                executeID = self.mainWindow.draw("Enter ID to execute")
                self.execute(executeID, self.mainWindow)
            elif retVal == "2":
                self.runModWindow(None, fromMain=True, fromList=False)
            elif retVal == "3":
                self.runListWindow(None)
            elif retVal == "4":
                self.executeRandom(self.mainWindow)
            elif retVal == "5":
                self.runDBWindow(None)
            elif retVal == "0":
                self.terminate()
            else:
                self.mainWindow.update("Please enter value present in %s"%self.mainWindow.validOptions)

    def runListWindow(self, startVal):
        """
        Function defining the interactions of the List window
        """
        logging.info("Switching to ListWindow")
        retVal = startVal
        if self.listWindow.nLinesPrinted > self.windowHeight:
            logging.info("Listwindow in overflow -> nPrinted %s", self.listWindow.nLinesPrinted)
            self.inOverflow = True
        logging.debug("self.inOverflow=%s  self.listWindowDrawn=%s", self.inOverflow, self.listWindowDrawn)
        self.listWindow.draw(skipHeader=self.inOverflow,
                             skipTable=(not self.listWindowDrawn),
                             fillWindow=(not self.inOverflow))
        self.listWindowDrawn = True
        #retVal = self.listWindow.interact("Enter Value:", None)
        while retVal != "0":
            retVal = self.listWindow.interact("Enter Value", None, onlyInteraction=self.firstInteraction)
            if self.firstInteraction:
                self.firstInteraction = False
            if retVal == "1": #Print All
                allIDs = sorted(list(self.database.getAllValuebyItemName("ID")), key=lambda x: int(x))
                tableElements = self.generateList(allIDs*6)
                #tableElements = self.generateList("All")
                self.listWindow.lines = []
                self.listWindow.update(tableElements)
                #print("=========================================")
                #self.listWindow.draw(skipHeader = True, skipTable = False, fillWindow = False)
                #print("+++++++++++++++++++++++++++++++++++++++++")
                #retVal = self.listWindow.interact("Enter Value", None, onlyInteraction = False)
            elif retVal == "2":
                self.runModWindow(None, fromMain=False, fromList=True)
            elif retVal == "3":
                executeID = self.listWindow.interact("Enter ID to execute")
                self.execute(executeID, self.listWindow)
            elif retVal == "4":
                self.executeRandom(self.listWindow, fromList=True)
            elif retVal == "5":
                queryString = self.listWindow.interact("Enter Query", None, onlyInteraction=True)
                thisQuery = queryString.split(" ")
                queryIDs = self.database.query(self.config.queryItems, thisQuery, returnIDs=True)
                queryIDs = sorted(queryIDs, key=lambda x: int(x))
                tableElements = self.generateList(queryIDs)
                self.listWindow.lines = []
                self.listWindow.update(tableElements)
            elif retVal == "6":
                sortedIDs = self.database.getSortedIDs("Added", reverseOrder=True)[0:3]
                tableElements = self.generateList(sortedIDs)
                self.listWindow.lines = []
                self.listWindow.update(tableElements)
                #self.listWindow.draw(fillWindow = True)
                #input("sss")
            else:
                self.listWindow.print("Please enter value present in %s"%self.listWindow.validOptions)
                tableElements = self.generateList("All")
        self.runMainWindow(None)

    def runDBWindow(self, startVal):
        """
        Function defining the interactions of the DB interaction window
        """
        logging.info("Switching to main window")
        retVal = startVal
        while retVal != "0":
            retVal = self.dbWindow.draw("Enter Value: ")
            if retVal == "1":
                self.dbWindow.update("Saving database")
                self.database.saveMain()
            elif retVal == "2":
                newFiles, file_id_pair = self.database.findNewFiles()
                for newFile, ID in file_id_pair:
                    self.dbWindow.update("Found file: %s"%newFile)
                    suggestedOptions = self.database.getItemsPyPath(newFile)
                    foundOne = False
                    for item in suggestedOptions:
                        if suggestedOptions[item] != set():
                            foundOne = True
                    if not foundOne:
                        continue
                    for item in suggestedOptions:
                        for option in suggestedOptions[item]:
                            answer = self.dbWindow.draw("Do you want to add %s to %s [Yes/No]"%(option, item))
                            if answer.lower() == "yes":
                                if item in self.database.model.items:
                                    self.database.modifySingleEntry(ID, item, option, byID=True)
                                elif item in self.database.model.listitems:
                                    self.database.modifyListEntry(ID, item, option, "Append", byID=True)
                                else:
                                    raise RuntimeError("This should not happen!")

            else:
                self.dbWindow.update("Please enter value present in %s"%self.dbWindow.validOptions)
        self.runMainWindow(None)

    def runModWindow(self, startVal, fromMain, fromList):
        """
        Function defining the interactions of the modification window
        """
        logging.info("Switching to modification window")
        retVal = startVal
        while retVal != "0":
            retVal = self.modWindow.draw("Enter Value: ")
            if retVal == "0":
                pass
            elif retVal == "1":
                ID = self.modWindow.draw("Enter ID: ")
                if ID in self.database.getAllValuebyItemName("ID"):
                    newWindow = False
                    if ID not in self.allMultiModWindow.keys():
                        self.allMultiModWindow[ID] = deepcopy(self.multiModWindow)
                        newWindow = True
                    self.runMultiModWindow(None, ID, newWindow, fromMain, fromList)
                else:
                    self.modWindow.update("ID %s not in database"%ID)
            elif retVal == "2":
                IDs = self.modWindow.draw("Enter IDs as XXX - YYY")
                IDs = IDs.replace(" ", "")
                res = re.search("[0-9]+-[0-9]+", IDs)
                validInput = False
                if res is not None:
                    if res.span() == (0, len(IDs)):
                        validInput = True
                if validInput:
                    self.modWindow.update("%s is a valid intput"%IDs)
                    fistID, lastID = IDs.split("-")
                    IDList = [str(x) for x in list(range(int(fistID), int(lastID)+1))]
                    self.processListOfModification(self.modWindow, IDList)
                else:
                    self.modWindow.update("%s is a invalid intput"%IDs)
            elif retVal == "3":
                IDs = self.modWindow.draw("Enter IDs as XXX,YYY,..")
                IDs = IDs.replace(" ", "")
                res = re.search("([0-9],)+[0-9]", IDs)
                validInput = False
                if res is not None:
                    if res.span() == (0, len(IDs)):
                        validInput = True
                if validInput:
                    IDList = IDs.split(",")
                    self.processListOfModification(self.modWindow, IDList)
                else:
                    self.modWindow.update("%s is a invalid intput"%IDs)
            else:
                self.modWindow.update("Please enter value present in %s"%self.modWindow.validOptions)
        if fromMain:
            self.runMainWindow(None)
        if fromList:
            self.runListWindow(None)

    def processListOfModification(self, window, IDList):
        """
        Function prevalidating the IDs set in the ModWindows for bulk updating of Entries
        """
        IDList = sorted(IDList, key=lambda x: int(x))
        _validIDs = []
        _rmIDs = []
        for ID in IDList:
            if int(ID) > len(self.database.entries)-1:
                _rmIDs.append(ID)
            else:
                _validIDs.append(ID)
        if len(_rmIDs) > 0:
            window.update("IDs %s are larger than max (%s)"%(_rmIDs, len(self.database.entries)-1))
        if len(_validIDs) > 0:
            window.update("IDList : %s"%_validIDs)
            self.modListOfItems(self.modWindow, _validIDs)

    def runMultiModWindow(self, startVal, ID, isNewWindow, fromMain, fromList):
        """
        Function defining the interactions of the multi modification window. Will spawn a new one for each ID modified in the current scope of the app
        """
        logging.info("Switching to multi modification window for ID %s", ID)
        thisWindow = self.allMultiModWindow[ID]
        if isNewWindow:
            thisWindow.headerText.append("Currently modifying ID: %s"%ID)
        retVal = startVal
        while retVal != "0":
            retVal = thisWindow.draw("Enter Value: ")
            if retVal == "0":
                pass
            elif retVal in thisWindow.validOptions:
                for elem in thisWindow.headerOptions:
                    modID, name, comment = elem
                    if modID == retVal:
                        thisWindow.update("%s, %s"%(modID, name)) ###TEMP
                        if name in self.database.model.items.keys():
                            thisWindow.update("%s is a Item"%name)###TEMP
                        elif name in self.database.model.listitems.keys():
                            thisWindow.update("%s is a ListItem"%name)###TEMP
                            self.modListItem(thisWindow, [ID], name)
                        else:
                            thisWindow.update("%s -- %s ??"%(name, itemType))
            else:
                thisWindow.update("Please enter value present in %s"%thisWindow.validOptions)
        self.runModWindow(None, fromMain, fromList)

    def modListItem(self, window, IDs, name, verbose=True):
        """
        Wrapper for the different modification options and how they are called in the database

        Args:
            windows (Window or ListWindows) : Current window
            IDs (list) : List of IDs to be modified
            name (str) : Item name to be modified
        """
        method = window.draw("Choose Method (Append | Replace | Remove)")
        if method in ["Append", "Replace", "Remove"]:
            if method == "Append":
                newValue = window.draw("New Value")
                for ID in IDs:
                    self.makeListModifications(ID, name, "Append", None, newValue)
                    if verbose:
                        window.update("Appended %s"%newValue)
            elif method == "Remove":
                oldValue = window.draw("Remove Value")
                for ID in IDs:
                    sucess = self.makeListModifications(ID, name, "Remove", oldValue, None)
                    if sucess:
                        if verbose:
                            window.update("Removed %s from entry"%oldValue)
                    else:
                        window.update("Value %s no in entry"%oldValue)
            else:
                oldValue = window.draw("Value to replace")
                newValue = window.draw("New Value")
                for ID in IDs:
                    sucess = self.makeListModifications(ID, name, "Replace", oldValue, newValue)
                    if not sucess:
                        window.update("Value %s no in entry"%oldValue)
                    else:
                        if verbose:
                            window.update("Replaces %s with %s"%(oldValue, newValue))
        else:
            window.update("!!! - %s is Invalid Method"%method)

    def modListOfItems(self, window, IDs):
        """
        Multiple modification of a single Item
        """
        item = window.draw("Change item ({0})".format(" | ".join(self.config.modItems)))
        if item in self.modSingleItems:
            newValue = window.draw("New Value for %s"%item)
            for ID in IDs:
                self.database.modifySingleEntry(ID, item, newValue, byID=True)
        elif item in self.modListItems:
            self.modListItem(window, IDs, item, verbose=False)
        else:
            window.update("Input is no valid item")

    def modSingleItem(self, window, IDs):
        """
        Wrapper for modifying a Single Item
        """
        item = window.draw("Change item ({0})".format(" | ".join(self.modSingleItems)))
        if item in self.modSingleItems:
            newValue = window.draw("New Value for %s"%item)
            for ID in IDs:
                self.database.modifySingleEntry(ID, item, newValue, byID=True)

    def makeListModifications(self, ID, name, method, oldValue, newValue):
        """
        Making a singel modification to a ListItem
        """
        if method == "Append":
            self.database.modifyListEntry(ID, name, newValue, "Append", byID=True)
            return True
        elif method == "Remove":
            try:
                self.database.modifyListEntry(ID, name, None, "Remove", oldValue, byID=True)
            except ValueError:
                return False
            else:
                return True
        elif method == "Replace":
            try:
                self.database.modifyListEntry(ID, name, newValue, "Replace", oldValue, byID=True)
            except ValueError:
                return False
            else:
                return True
        else:
            pass

    def execute(self, ID, window):
        """
        Function called when a entry should be executed. The idea is, that for a desired execution program etc. a shell script with the called (as done in the terminal) is placed in the executable folder.
        After execution the **Opened** will be incrememented.
        """
        if ID not in self.database.getAllValuebyItemName("ID"):
            window.update("ID %s not in database"%ID)
        else:
            entry2Exec = self.database.getEntryByItemName("ID", ID)[0]
            path2Exec = self.database.databaseRoot + "/" + entry2Exec.Path
            window.update("Path: %s"%path2Exec)
            os.system("{0} {1}".format(self.config.executable, path2Exec))
            self.database.modifyListEntry(ID, "Opened",
                                          mimir.backend.helper.getTimeFormatted("Full"),
                                          byID=True)

    def executeRandom(self, window, fromList=False):
        """
        Function for getting a random entry from the last printed List of entries (if none printed from all)
        """
        randID = self.database.getRandomEntry(chooseFrom=self.lastIDList)
        _listIDList = self.lastIDList
        if fromList:
            tableElements = self.generateList([randID])
            self.lastIDList = _listIDList
            window.lines = []
            window.update(tableElements)
        else:
            window.update("Executing entry with ID {0}".format(randID))
        self.execute(randID, window)

    def terminate(self):
        """
        Function called form the main window to terminate the app
        """
        logging.info("Checking if database was saved")
        #TODO: CHeck if database is modified but nit saved
        logging.info("Terminating app")
        exit()

    def generateList(self, get="All"):
        """
        Function generating the necessary table elements win using the ListWindow. Will used all items set in the DisplayItems configuration option

        TODO: Factorize
        """
        #TODO Check get input
        tableElements = []
        ids2Print = None
        if get == "All":
            ids2Print = self.database.getAllValuebyItemName("ID")
            ids2Print = sorted(list(ids2Print), key=lambda x: int(x))
        elif isinstance(get, list):
            ids2Print = get
        self.lastIDList = ids2Print
        logging.info(ids2Print)
        for id in ids2Print:
            entryElements = []
            thisEntry = self.database.getEntryByItemName("ID", id)[0]
            for item in self.tableColumnItems:
                isCounter = False
                if self.config.itemInfo[item]["Type"] == "Counter":
                    thisItem = None
                    isCounter = True
                else:
                    thisItem = thisEntry.getItem(item)
                if isinstance(thisItem, ListItem):
                    thisValue = []
                    for priority in self.config.itemInfo[item]["Priority"]:
                        if priority in thisItem.value:
                            thisValue.append(priority)
                    for val in thisItem.value:
                        if val not in thisValue and len(thisValue) <= self.config.itemInfo[item]["nDisplay"]:
                            #print(val, self.database.model.getDefaultValue(item))
                            if (val == self.database.model.getDefaultValue(item) and
                                    self.config.itemInfo[item]["DisplayDefault"] is not None):
                                thisValue.append(self.config.itemInfo[item]["DisplayDefault"])
                            else:
                                if "modDisplay" in self.config.itemInfo[item].keys():
                                    if self.config.itemInfo[item]["modDisplay"] == "Date":
                                        val = val.split("|")[0]
                                    elif self.config.itemInfo[item]["modDisplay"] == "Time":
                                        val = val.split("|")[1]
                                    elif self.config.itemInfo[item]["modDisplay"] == "Full":
                                        pass
                                    else:
                                        raise NotImplementedError("modDisplay value %s not implemented"%self.config.itemInfo[item]["modDisplay"])
                                thisValue.append(val)
                        if len(thisValue) >= self.config.itemInfo[item]["nDisplay"]:
                            thisValue.append("..")
                            break
                    #TODO: Add maxlen to ListItems and make sure the joind sting is shorter
                    value = ", ".join(thisValue)
                elif isCounter:
                    value = str(self.database.getCount(id, self.config.itemInfo[item]["Base"], byID=True))
                else:
                    if (thisItem.value == self.database.model.getDefaultValue(item) and
                            self.config.itemInfo[item]["DisplayDefault"] is not None):
                        itemValue = self.config.itemInfo[item]["DisplayDefault"]
                    else:
                        val = thisItem.value
                        if "modDisplay" in self.config.itemInfo[item].keys():
                            if self.config.itemInfo[item]["modDisplay"] == "Date":
                                val = val.split("|")[0]
                            elif self.config.itemInfo[item]["modDisplay"] == "Time":
                                val = val.split("|")[1]
                            elif self.config.itemInfo[item]["modDisplay"] == "Full":
                                pass
                            else:
                                raise NotImplementedError("modDisplay value %s not implemented"%self.config.itemInfo[item]["modDisplay"])
                        itemValue = val
                    if len(itemValue) > self.config.itemInfo[item]["maxLen"]:
                        value = itemValue[:self.config.itemInfo[item]["maxLen"]]+".."
                    else:
                        value = itemValue
                entryElements.append(value)
            tableElements.append(tuple(entryElements))
        return tableElements

    def about(self):
        """
        Method that returns the information for the about screen. Like python-version, number entryies, number if values per ListItem, most used Value

        Returns:
            aboutInfo (dict) : All values of interest

        TODO: Implement
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
        self.alltems = configDict["General"]["AllItems"]
        self.queryItems = configDict["General"]["QueryItems"]
        self.modItems = configDict["General"]["ModItems"]
        self.executable = configDict["General"]["Executable"]
        self.itemInfo = {}
        for iItem, item in enumerate(self.alltems):
            self.itemInfo[item] = {}
            self.itemInfo[item]["DisplayName"] = configDict[item]["DisplayName"]
            self.itemInfo[item]["DisplayDefault"] = configDict[item]["DisplayDefault"]
            self.itemInfo[item]["Type"] = configDict[item]["Type"]
            if self.itemInfo[item]["Type"] == "ListItem":
                self.itemInfo[item]["Hide"] = configDict[item]["Hide"]
                self.itemInfo[item]["Priority"] = configDict[item]["Priority"]
                self.itemInfo[item]["nDisplay"] = configDict[item]["nDisplay"]
            elif self.itemInfo[item]["Type"] == "Item":
                self.itemInfo[item]["maxLen"] = configDict[item]["maxLen"]
            elif self.itemInfo[item]["Type"] == "Counter":
                self.itemInfo[item]["Base"] = configDict[item]["Base"]
            else:
                raise KeyError("Item %s has unsupported type %s"%(item, self.itemInfo[item]["Type"]))
            if "modDisplay" in configDict[item].keys():
                self.itemInfo[item]["modDisplay"] = configDict[item]["modDisplay"]

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

def initDatabase(basedir, config=None):
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
        logging.debug("Found .mimir dir for %s", basedir)
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
