import json
import logging
import os
import re
from copy import deepcopy

import mimir.backend.helper
from mimir.backend.database import DataBase
from mimir.frontend.terminal.display import ListWindow, Window

logger = logging.getLogger(__name__)


class App:
    """
    App class that manages the communication between the Window module and the database
    model

    Args:
        dababase (DataBase) : Initialized mimir DataBase
        enableStartupSeatch (bool) : If True, a search for new files will be enabled
                                     on startup
    """

    def __init__(self, dababase: DataBase, enableStartupSeatch=True):
        self.database = dababase
        if not os.path.exists(self.database.mimirdir + "/MTF_model.json"):
            raise RuntimeError(
                "No MTF configuration found in .mimir directory. "
                "Use make MTFconfig.py to create on from the database config"
            )
        self.config = MTFConfig(self.database.mimirdir + "/MTF_model.json")
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
        mainHeader = {
            "Title": self.config.windows["Main"]["Title"],
            "Text": ["Mimir base dir: {0}".format(self.database.databaseRoot)]
            + self.config.windows["Main"]["Text"],
            "Options": self.config.windows["Main"]["Options"],
        }
        self.mainWindow = Window(self.windowHeight, self.windowWidth, mainHeader)
        self.mainWindow.setHeader()
        ################### List Window ###################
        listHeader = {
            "Title": self.config.windows["List"]["Title"],
            "Options": self.config.windows["List"]["Options"],
        }
        self.listWindow = ListWindow(
            self.windowHeight,
            self.windowWidth,
            listHeader,
            self.tableColumns,
            self.tableColumnNames,
        )
        self.listWindow.setHeader()
        self.listWindowDrawn = False
        self.firstInteraction = True
        self.inOverflow = False
        ################### DB Window ###################
        dbHeader = {
            "Title": self.config.windows["DB"]["Title"],
            "Text": self.config.windows["DB"]["Text"],
            "Options": self.config.windows["DB"]["Options"],
        }
        self.dbWindow = Window(self.windowHeight, self.windowWidth, dbHeader)
        self.dbWindow.setHeader()
        for key in self.config.windows:
            print(self.config.windows[key])
        ################### Modification Window ###################
        modHeader = {
            "Title": self.config.windows["Modify"]["Title"],
            "Text": self.config.windows["Modify"]["Text"],
            "Options": self.config.windows["Modify"]["Options"],
        }
        self.modWindow = Window(self.windowHeight, self.windowWidth, modHeader)
        self.modWindow.setHeader()
        ################### Mulit Modification Window ###################
        self.mulitModExecVal = len(self.config.windows["MultiModify"]["Options"])
        self.config.windows["MultiModify"]["Options"].append(
            ("Silent Execute", "Will not count to opened")
        )
        multiModHeader = {
            "Title": self.config.windows["MultiModify"]["Title"],
            "Text": self.config.windows["MultiModify"]["Text"],
            "Options": self.config.windows["MultiModify"]["Options"],
        }
        self.multiModWindow = Window(
            self.windowHeight, self.windowWidth, multiModHeader
        )
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
        logger.info("Starting App")
        self.runMainWindow(None)

    def runMainWindow(self, startVal):
        """
        Function defining the interactions of the main window
        """
        logger.info("Switching to main window")
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
                if retVal != "0":
                    self.mainWindow.update(
                        "Please enter value present in %s"
                        % self.mainWindow.validOptions
                    )

    def runListWindow(self, startVal):
        """
        Function defining the interactions of the List window
        """
        logger.info("Switching to ListWindow")
        retVal = startVal
        if self.listWindow.nLinesPrinted > self.windowHeight:
            logger.info(
                "Listwindow in overflow -> nPrinted %s", self.listWindow.nLinesPrinted
            )
            self.inOverflow = True
        logger.debug(
            "self.inOverflow=%s  self.listWindowDrawn=%s",
            self.inOverflow,
            self.listWindowDrawn,
        )
        self.listWindow.draw(
            skipHeader=self.inOverflow,
            skipTable=(not self.listWindowDrawn),
            fillWindow=(not self.inOverflow),
        )
        self.listWindowDrawn = True
        # retVal = self.listWindow.interact("Enter Value:", None)
        while retVal != "0":
            retVal = self.listWindow.interact(
                "Enter Value", None, onlyInteraction=self.firstInteraction
            )
            if self.firstInteraction:
                self.firstInteraction = False
            if retVal == "1":  # Print All
                allIDs = sorted(
                    list(self.database.getAllValuebyItemName("ID")),
                    key=lambda x: int(x),
                )
                tableElements = self.generateList(allIDs)
                self.listWindow.lines = []
                self.listWindow.update(tableElements)
            elif retVal == "2":
                self.runModWindow(None, fromMain=False, fromList=True)
            elif retVal == "3" or retVal == "03":
                executeID = self.listWindow.interact("Enter ID to execute")
                self.execute(
                    executeID,
                    self.listWindow,
                    fromList=True,
                    silent=retVal.startswith("0"),
                )
            elif retVal == "4" or retVal == "04":
                self.executeRandom(
                    self.listWindow, fromList=True, silent=retVal.startswith("0")
                )
            elif retVal == "5":
                queryString = self.listWindow.interact(
                    "Enter Query", None, onlyInteraction=True
                )
                thisQuery = queryString.split(" ")
                queryIDs = self.database.query(
                    self.config.queryItems, thisQuery, returnIDs=True
                )
                queryIDs = sorted(queryIDs, key=lambda x: int(x))
                tableElements = self.generateList(queryIDs)
                self.listWindow.lines = []
                self.listWindow.update(tableElements)
            elif retVal == "6":
                sortedIDs = self.database.getSortedIDs("Added", reverseOrder=True)[
                    0 : self.config.restrictedListLen
                ]
                tableElements = self.generateList(sortedIDs)
                self.listWindow.lines = []
                self.listWindow.draw_pre_table_title("-", [(" ", "-")])
                self.listWindow.draw_pre_table_title(
                    f"_{self.config.restrictedListLen}_last_added_entries_",
                    [(" ", "-"), ("_", " ")],
                )
                self.listWindow.draw_pre_table_title("-", [(" ", "-")])
                self.listWindow.update(tableElements)
            elif retVal == "7":
                sortedIDs = self.database.getSortedIDs("Opened", reverseOrder=True)[
                    0 : self.config.restrictedListLen
                ]
                tableElements = self.generateList(sortedIDs)
                self.listWindow.lines = []
                self.listWindow.draw_pre_table_title("-", [(" ", "-")])
                self.listWindow.draw_pre_table_title(
                    f"_{self.config.restrictedListLen}_last_opened_entries_",
                    [(" ", "-"), ("_", " ")],
                )
                self.listWindow.draw_pre_table_title("-", [(" ", "-")])
                self.listWindow.update(tableElements)
            elif retVal == "8":
                sortedIDs = self.database.getSortedIDs("Changed", reverseOrder=True)[
                    0 : self.config.restrictedListLen
                ]
                tableElements = self.generateList(sortedIDs)
                self.listWindow.lines = []
                self.listWindow.draw_pre_table_title("-", [(" ", "-")])
                self.listWindow.draw_pre_table_title(
                    f"_{self.config.restrictedListLen}_last_changed_entries_",
                    [(" ", "-"), ("_", " ")],
                )
                self.listWindow.draw_pre_table_title("-", [(" ", "-")])
                self.listWindow.update(tableElements)
            elif retVal == "9":
                del_ID = self.listWindow.interact(
                    "Enter ID to be marked/unmarked for deletion"
                )
                self.toggle_for_deletion(del_ID, self.listWindow)
            elif retVal == "10":
                queryIDs = self.database.query(["DeletionMark"], "1", returnIDs=True)
                queryIDs = sorted(queryIDs, key=lambda x: int(x))
                tableElements = self.generateList(queryIDs)
                self.listWindow.lines = []
                self.listWindow.update(tableElements)
            else:
                if retVal != "0":
                    self.listWindow.print(
                        "Please enter value present in %s"
                        % self.listWindow.validOptions
                    )
                # tableElements = self.generateList("All")
        self.runMainWindow(None)

    def runDBWindow(self, startVal):
        """
        Function defining the interactions of the DB interaction window
        """
        logger.info("Switching to main window")
        retVal = startVal
        while retVal != "0":
            retVal = self.dbWindow.draw("Enter Value: ")
            if retVal == "1":
                self.dbWindow.update("Saving database")
                self.database.saveMain()
            elif retVal == "2":
                newFiles, file_id_pair = self.database.findNewFiles()
                for newFile, ID in file_id_pair:
                    self.dbWindow.update("Added file %s with ID %s" % (newFile, ID))
                    suggestedOptions = self.database.getItemsPyPath(newFile)
                    foundOne = False
                    for item in suggestedOptions:
                        if suggestedOptions[item] != set():
                            foundOne = True
                    if not foundOne:
                        continue
                    for item in suggestedOptions:
                        for option in suggestedOptions[item]:
                            answer = self.dbWindow.draw(
                                "Do you want to add %s to %s [Yes/No]" % (option, item)
                            )
                            if answer.lower() == "yes":
                                if item in self.database.model.items:
                                    self.database.modifySingleEntry(
                                        ID, item, option, byID=True
                                    )
                                elif item in self.database.model.listitems:
                                    self.database.modifyListEntry(
                                        ID, item, option, "Append", byID=True
                                    )
                                else:
                                    raise RuntimeError("This should not happen!")
            elif retVal == "3":
                updatedFiles = self.database.checkChangedPaths()
                if updatedFiles:
                    for id_, oldPath_, newPath_ in updatedFiles:
                        self.dbWindow.update(
                            "Moved entry with ID %s now has path %s" % (id_, newPath_)
                        )
                else:
                    self.dbWindow.update("No files with changed paths")

            elif retVal == "4":
                IDchanges = self.database.checkMissingFiles()
                if IDchanges:
                    for oldID, newID in IDchanges:
                        self.dbWindow.update(
                            "Moved entry from ID %s to %s" % (oldID, newID)
                        )
                else:
                    self.dbWindow.update("No Files removed")
            elif retVal == "5":
                queryIDs = self.database.query(["DeletionMark"], "1", returnIDs=True)
                queryIDs = sorted(queryIDs, key=lambda x: int(x))
                if len(queryIDs) > 0:
                    total_size = 0
                    for id_ in queryIDs:
                        e = self.database.getEntryByItemName("ID", id_)[0]
                        total_size += float(e.Size)
                        self.dbWindow.update(
                            f"{id_} is marked for deletion "
                            f"(Name: {e.Name}; Size: {e.Size} GB)"
                        )
                    self.dbWindow.update(
                        f"{len(queryIDs)} entries marked for deletion "
                        f"with a total size of {total_size} GB"
                    )
                    del_q = self.dbWindow.draw(
                        "Are you sure you want to delete these entries? [Y/n]: "
                    )
                    if del_q == "Y":
                        self.del_ids(queryIDs, self.dbWindow)
                        IDchanges = self.database.checkMissingFiles()
                        if IDchanges:
                            for oldID, newID in IDchanges:
                                self.dbWindow.update(
                                    "Moved entry from ID %s to %s" % (oldID, newID)
                                )
                else:
                    self.dbWindow.update("No entries marked for deletion")
            else:
                if retVal != "0":
                    self.dbWindow.update(
                        "Please enter value present in %s" % self.dbWindow.validOptions
                    )
        self.runMainWindow(None)

    def runModWindow(self, startVal, fromMain, fromList):
        """
        Function defining the interactions of the modification window
        """
        logger.info("Switching to modification window")
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
                    self.modWindow.update("ID %s not in database" % ID)
            elif retVal == "2":
                IDs = self.modWindow.draw("Enter IDs as XXX - YYY")
                IDs = IDs.replace(" ", "")
                res = re.search("[0-9]+-[0-9]+", IDs)
                validInput = False
                if res is not None:
                    if res.span() == (0, len(IDs)):
                        validInput = True
                if validInput:
                    self.modWindow.update("%s is a valid intput" % IDs)
                    fistID, lastID = IDs.split("-")
                    IDList = [str(x) for x in list(range(int(fistID), int(lastID) + 1))]
                    self.processListOfModification(self.modWindow, IDList)
                else:
                    self.modWindow.update("%s is a invalid intput" % IDs)
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
                    self.modWindow.update("%s is a invalid intput" % IDs)
            else:
                if retVal != "0":
                    self.modWindow.update(
                        "Please enter value present in %s" % self.modWindow.validOptions
                    )
        if fromMain:
            self.runMainWindow(None)
        if fromList:
            self.runListWindow(None)

    def processListOfModification(self, window, IDList):
        """
        Function prevalidating the IDs set in the ModWindows for bulk updating of
        Entries
        """
        IDList = sorted(IDList, key=lambda x: int(x))
        _validIDs = []
        _rmIDs = []
        for ID in IDList:
            if int(ID) > len(self.database.entries) - 1:
                _rmIDs.append(ID)
            else:
                _validIDs.append(ID)
        if len(_rmIDs) > 0:
            window.update(
                "IDs %s are larger than max (%s)"
                % (_rmIDs, len(self.database.entries) - 1)
            )
        if len(_validIDs) > 0:
            window.update("IDList : %s" % _validIDs)
            self.modListOfItems(self.modWindow, _validIDs)

    def runMultiModWindow(self, startVal, ID, isNewWindow, fromMain, fromList):
        """
        Function defining the interactions of the multi modification window. Will spawn
        a new one for each ID modified in the current scope of the app
        """
        logger.info("Switching to multi modification window for ID %s", ID)
        thisWindow = self.allMultiModWindow[ID]
        entry = self.database.getEntrybyID(ID)
        if isNewWindow:
            thisWindow.headerText.append("Entry information:")
            thisWindow.headerText.append("ID: %s" % ID)
            thisWindow.headerText.append("Path: %s" % entry.getItem("Path").value)
        for elem in thisWindow.headerOptions:
            modID, name, comment = elem
            if name in self.database.model.allItems:
                thisWindow.headerTextSecondary[name] = self.getPrintItemValues(
                    ID, name, joinFull=True
                )
        retVal = startVal
        while retVal != "0":
            retVal = thisWindow.draw("Enter Value: ")
            if retVal == "0":
                pass
            elif retVal in thisWindow.validOptions:
                if retVal == str(self.mulitModExecVal):
                    thisWindow.update("Silent Execute triggered")  # TEMP
                    self.execute(ID, thisWindow, silent=True)
                else:
                    for elem in thisWindow.headerOptions:
                        modID, name, comment = elem
                        if modID == retVal:
                            thisWindow.update("%s, %s" % (modID, name))  # TEMP
                            if name in self.database.model.items.keys():
                                thisWindow.update("%s is a Item" % name)  # TEMP
                                self.modSingleItem(
                                    thisWindow, [ID], name, fromMultiMod=True
                                )
                            elif name in self.database.model.listitems.keys():
                                thisWindow.update("%s is a ListItem" % name)  # TEMP
                                self.modListItem(
                                    thisWindow, [ID], name, fromMultiMod=True
                                )
                            else:
                                thisWindow.update(
                                    "Something weird happend for %s" % (name)
                                )
            else:
                thisWindow.update(
                    "Please enter value present in %s" % thisWindow.validOptions
                )
        self.runModWindow(None, fromMain, fromList)

    def modListItem(self, window, IDs, name, verbose=True, fromMultiMod=False):
        """
        Wrapper for the different modification options and how they are called in the
        database

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
                        window.update("Appended %s" % newValue)
            elif method == "Remove":
                oldValue = window.draw("Remove Value")
                for ID in IDs:
                    sucess = self.makeListModifications(
                        ID, name, "Remove", oldValue, None
                    )
                    if sucess:
                        if verbose:
                            window.update("Removed %s from entry" % oldValue)
                    else:
                        window.update("Value %s no in entry" % oldValue)
            else:
                oldValue = window.draw("Value to replace")
                newValue = window.draw("New Value")
                for ID in IDs:
                    sucess = self.makeListModifications(
                        ID, name, "Replace", oldValue, newValue
                    )
                    if not sucess:
                        window.update("Value %s no in entry" % oldValue)
                    else:
                        if verbose:
                            window.update("Replaces %s with %s" % (oldValue, newValue))
        else:
            window.update("!!! - %s is Invalid Method" % method)
        if fromMultiMod:
            window.headerTextSecondary[name] = self.getPrintItemValues(
                IDs[0], name, joinFull=True
            )

    def modListOfItems(self, window, IDs):
        """
        Multiple modification of a single Item
        """
        item = window.draw("Change item ({0})".format(" | ".join(self.config.modItems)))
        if item in self.modSingleItems:
            newValue = window.draw("New Value for %s" % item)
            for ID in IDs:
                self.database.modifySingleEntry(ID, item, newValue, byID=True)
        elif item in self.modListItems:
            self.modListItem(window, IDs, item, verbose=False)
        else:
            window.update("Input is no valid item")

    def modSingleItem(self, window, IDs, name=None, fromMultiMod=False):
        """
        Wrapper for modifying a Single Item
        """
        if name is None:
            name = window.draw(
                "Change item ({0})".format(" | ".join(self.modSingleItems))
            )
        if name in self.modSingleItems:
            newValue = window.draw("New Value for %s" % name)
            for ID in IDs:
                self.database.modifySingleEntry(ID, name, newValue, byID=True)
            if fromMultiMod:
                window.headerTextSecondary[name] = self.getPrintItemValues(
                    IDs[0], name, joinFull=True
                )

    def makeListModifications(self, ID, name, method, oldValue, newValue):
        """
        Making a singel modification to a ListItem
        """
        if method == "Append":
            self.database.modifyListEntry(ID, name, newValue, "Append", byID=True)
            return True
        elif method == "Remove":
            try:
                self.database.modifyListEntry(
                    ID, name, None, "Remove", oldValue, byID=True
                )
            except ValueError:
                return False
            else:
                return True
        elif method == "Replace":
            try:
                self.database.modifyListEntry(
                    ID, name, newValue, "Replace", oldValue, byID=True
                )
            except ValueError:
                return False
            else:
                return True
        else:
            pass

    def execute(self, ID, window, fromList=False, silent=False):
        """
        Function called when a entry should be executed. The idea is, that for a desired
        execution program etc. a shell script with the called (as done in the terminal)
        is placed in the executable folder.

        After execution the **Opened** will be incrememented.
        """
        if ID not in self.database.getAllValuebyItemName("ID"):
            if isinstance(window, ListWindow):
                window.print("ID %s not in database" % ID)
            else:
                window.update("ID %s not in database" % ID)
        else:
            entry2Exec = self.database.getEntryByItemName("ID", ID)[0]
            path2Exec = self.database.databaseRoot + "/" + entry2Exec.Path
            if not fromList:
                if isinstance(window, ListWindow):
                    window.print("Path: %s" % path2Exec)
                else:
                    window.update("Path: %s" % path2Exec)

            os.system("{0} {1}".format(self.config.executable, path2Exec))
            if not silent:
                self.database.modifyListEntry(
                    ID,
                    "Opened",
                    mimir.backend.helper.getTimeFormatted("Full"),
                    byID=True,
                )

    def executeRandom(self, window, fromList=False, silent=False):
        """
        Function for getting a random entry from the last printed List of entries
        (if none printed from all)
        """
        if not self.lastIDList:
            window.print("No entries to choose from. Maybe requery?")
        else:
            randID = self.database.getRandomEntry(
                choose_from=self.lastIDList, weighted=True
            )
            _listIDList = self.lastIDList
            if fromList:
                tableElements = self.generateList([randID])
                self.lastIDList = _listIDList
                window.lines = []
                window.update(tableElements)
            else:
                window.update("Executing entry with ID {0}".format(randID))
            self.execute(randID, window, fromList, silent=silent)

    def toggle_for_deletion(self, ID, window):
        if ID not in self.database.getAllValuebyItemName("ID"):
            window.update("ID %s not in database" % ID)
        else:
            e = self.database.getEntryByItemName("ID", ID)[0]
            if e.DeletionMark == "0":
                logger.info("Marking ID %s for deletion", ID)
                self.database.modifySingleEntry(ID, "DeletionMark", "1", byID=True)
            else:
                logger.info("Unmarking ID %s for deletion", ID)
                self.database.modifySingleEntry(ID, "DeletionMark", "0", byID=True)

    def del_ids(self, ids, window):
        window.update("Will delete entries...")
        for id_ in ids:
            e = self.database.getEntryByItemName("ID", id_)[0]
            path2del = self.database.databaseRoot + "/" + e.Path
            window.update(f"Removing {path2del}")
            os.remove(path2del)
        window.update("...done deleting entries.")

    def terminate(self):
        """
        Function called form the main window to terminate the app
        """
        logger.info("Checking if database was saved")
        # TODO: CHeck if database is modified but nit saved
        logger.info("Terminating app")
        exit()

    def generateList(self, get="All"):
        """
        Function generating the necessary table elements win using the ListWindow.
        Will used all items set in the DisplayItems configuration option
        """
        # TODO Check get input
        tableElements = []
        ids2Print = None
        if get == "All":
            ids2Print = self.database.getAllValuebyItemName("ID")
            ids2Print = sorted(list(ids2Print), key=lambda x: int(x))
        elif isinstance(get, list):
            ids2Print = get
        self.lastIDList = ids2Print
        # logger.info(ids2Print)
        for id in ids2Print:
            entryElements = []
            for item in self.tableColumnItems:
                isCounter = False
                if self.config.itemInfo[item]["Type"] == "Counter":
                    isCounter = True
                if isCounter:
                    value = str(
                        self.database.getCount(
                            id, self.config.itemInfo[item]["Base"], byID=True
                        )
                    )
                else:
                    value = self.getPrintItemValues(id, item)
                entryElements.append(value)
            tableElements.append(tuple(entryElements))
        return tableElements

    def getPrintItemValues(self, ID, item, joinWith=", ", joinFull=False):
        retValue = None
        thisEntry = self.database.getEntryByItemName("ID", ID)[0]
        if item in self.database.model.items:
            value = thisEntry.getItem(item).value
            self.modDisaply(item, value)
            if len(value) > self.config.itemInfo[item]["maxLen"] and not joinFull:
                retValue = value[: self.config.itemInfo[item]["maxLen"]] + ".."
            else:
                retValue = value
        elif item in self.database.model.listitems:
            retValue = self.joinItemValues(thisEntry, item, joinWith, joinFull)
        else:
            raise KeyError("Item %s no listitem or singelitem")

        return retValue

    def joinItemValues(self, entry, item, joinWith=", ", joinFull=False):
        """
        Will join all values in a ListItem. Will use the config settings Priority,
        DisplayDefault and nDisplay to format the return value. nDisplay can be
        overruled by the joinFull argument.

        Args:
            entry (DataBaseEntry)
            item (str) : ListItem to be joined (Function expects listitem no check
                         implemented)
            joinWith (str) : String that will be used to join values
            joinFull (bool) : Will overrule the maximum lenghts

        Returns:
            value (str) : Joined values
        """
        thisValue = []
        for priority in self.config.itemInfo[item]["Priority"]:
            if priority in entry.getItem(item).value:
                thisValue.append(priority)
        loopVals = deepcopy(entry.getItem(item).value)
        if self.config.itemInfo[item]["Sorting"] == "reverse":
            loopVals.reverse()
        for val in loopVals:
            if (
                val not in thisValue
                and len(thisValue) <= self.config.itemInfo[item]["nDisplay"]
            ):
                if (
                    val == self.database.model.getDefaultValue(item)
                    and self.config.itemInfo[item]["DisplayDefault"] is not None
                ):
                    if self.config.itemInfo[item]["DisplayDefault"] != "":
                        thisValue.append(self.config.itemInfo[item]["DisplayDefault"])
                else:
                    thisValue.append(self.modDisaply(item, val))
            if len(thisValue) >= self.config.itemInfo[item]["nDisplay"]:
                if item not in ["Opened", "Changed"]:
                    thisValue.append("..")
                break
        value = joinWith.join(thisValue)
        return value

    def modDisaply(self, item, value):
        """
        Function processes the modDisplay setting from the config.
        """
        if "modDisplay" in self.config.itemInfo[item].keys():
            if self.config.itemInfo[item]["modDisplay"] == "Date":
                value = value.split("|")[0]
            elif self.config.itemInfo[item]["modDisplay"] == "Time":
                value = value.split("|")[1]
            elif self.config.itemInfo[item]["modDisplay"] == "Full":
                pass
            else:
                raise NotImplementedError(
                    "modDisplay value %s not implemented"
                    % self.config.itemInfo[item]["modDisplay"]
                )
        return value

    def modifyItemDisplay(self, item, value):
        """
        Function for processing the modDisplay option in the MTF coniguration:

        Args:
            value (str) : Item Value
            item (str) : Item name

        Returns: If modDispaly set will return modified value otherwise passed one
        """
        if "modDisplay" in self.config.itemInfo[item].keys():
            if self.config.itemInfo[item]["modDisplay"] == "Date":
                value = value.split("|")[0]
            elif self.config.itemInfo[item]["modDisplay"] == "Time":
                value = value.split("|")[1]
            elif self.config.itemInfo[item]["modDisplay"] == "Full":
                pass
            else:
                raise NotImplementedError(
                    "modDisplay value %s not implemented"
                    % self.config.itemInfo[item]["modDisplay"]
                )

        return value

    def about(self):
        """
        Method that returns the information for the about screen. Like python-version,
        number entr/ies, number if values per ListItem, most used Value

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
        logger.debug("Loading MTF config from %s", config)
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
        self.restrictedListLen = int(configDict["General"]["nListRestricted"])
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
                if "Sorting" in configDict[item]:
                    if configDict[item]["Sorting"] == "reverse":
                        self.itemInfo[item]["Sorting"] = "reverse"
                    elif configDict[item]["Sorting"] == "regular":
                        self.itemInfo[item]["Sorting"] = "regular"
                    else:
                        raise RuntimeError(
                            "Only **reverse** and **regular** (default) are supported"
                        )
                else:
                    self.itemInfo[item]["Sorting"] = "regular"
            elif self.itemInfo[item]["Type"] == "Item":
                self.itemInfo[item]["maxLen"] = configDict[item]["maxLen"]
            elif self.itemInfo[item]["Type"] == "Counter":
                self.itemInfo[item]["Base"] = configDict[item]["Base"]
            else:
                raise KeyError(
                    "Item %s has unsupported type %s"
                    % (item, self.itemInfo[item]["Type"])
                )
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
    if os.path.exists(basedir + "/.mimir"):
        logger.debug("Found .mimir dir for %s", basedir)
        database = DataBase(basedir, "load")
        initType = "loaded"
    else:
        if config is None:
            raise RuntimeError(
                "Found no .mimir in %s. Please pass initial config" % basedir
            )
        else:
            logger.debug("Creating new databse")
            database = DataBase(basedir, "new", config)
            initType = "new"

    return database, initType
