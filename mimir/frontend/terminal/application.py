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

    def __init__(self, dababase: DataBase, enableStartupSeatch=True) -> None:
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
        self.run_main_window(None)

    def run_main_window(self, startVal):
        """
        Function defining the interactions of the main window
        """
        logger.info("Switching to main window")
        ret_val = startVal
        while ret_val != "0":
            ret_val = self.mainWindow.draw("Enter Value")
            if ret_val == "1":
                execute_id = self.mainWindow.draw("Enter ID to execute")
                self.execute(execute_id, self.mainWindow)
            elif ret_val == "2":
                self.run_mod_window(None, fromMain=True, fromList=False)
            elif ret_val == "3":
                self.run_list_window(None)
            elif ret_val == "4":
                self.execute_random(self.mainWindow)
            elif ret_val == "5":
                self.run_db_window(None)
            elif ret_val == "0":
                self.terminate()
            else:
                if ret_val != "0":
                    self.mainWindow.update(
                        "Please enter value present in %s"
                        % self.mainWindow.validOptions
                    )

    def run_list_window(self, startVal):
        """
        Function defining the interactions of the List window
        """
        logger.info("Switching to ListWindow")
        ret_val = startVal
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
        # ret_val = self.listWindow.interact("Enter Value:", None)
        while ret_val != "0":
            full_ret_val = self.listWindow.interact(
                "Enter Value", None, onlyInteraction=self.firstInteraction
            )

            ret_vals = full_ret_val.split(" ")
            ret_val = ret_vals[0]
            add_vals: None | list[str] = None
            if len(ret_vals) > 1:
                add_vals = ret_vals[1:]
            if self.firstInteraction:
                self.firstInteraction = False
            if ret_val == "1":  # Print All
                all_ids = sorted(
                    list(self.database.getAllValuebyItemName("ID")),
                    key=lambda x: int(x),
                )
                table_elements = self.generate_list(all_ids)
                self.listWindow.lines = []
                self.listWindow.update(table_elements)
            elif ret_val == "2":
                self.run_mod_window(None, fromMain=False, fromList=True)
            elif ret_val == "3" or ret_val == "03":
                execute_id = self.listWindow.interact("Enter ID to execute")
                self.execute(
                    execute_id,
                    self.listWindow,
                    fromList=True,
                    silent=ret_val.startswith("0"),
                )
            elif ret_val == "4" or ret_val == "04":
                self.execute_random(
                    self.listWindow,
                    fromList=True,
                    silent=ret_val.startswith("0"),
                    weighted=(not ret_val.startswith("0")),
                )
            elif ret_val == "5":
                query_string = self.listWindow.interact(
                    "Enter Query", None, onlyInteraction=True
                )
                this_query = query_string.split(" ")
                query_ids = self.database.query(
                    self.config.queryItems, this_query, returnIDs=True
                )
                query_ids = sorted(query_ids, key=lambda x: int(x))
                table_elements = self.generate_list(query_ids)
                self.listWindow.lines = []
                self.listWindow.update(table_elements)
            elif ret_val == "6":
                n_display = self.config.restrictedListLen
                if add_vals is not None:
                    try:
                        n_display = int(add_vals[0])
                    except ValueError:
                        pass
                sorted_ids = self.database.getSortedIDs("Added", reverseOrder=True)[
                    0:n_display
                ]
                table_elements = self.generate_list(sorted_ids)
                self.listWindow.lines = []
                self.listWindow.draw_pre_table_title("-", [(" ", "-")])
                self.listWindow.draw_pre_table_title(
                    f"_{n_display}_last_added_entries_",
                    [(" ", "-"), ("_", " ")],
                )
                self.listWindow.draw_pre_table_title("-", [(" ", "-")])
                self.listWindow.update(table_elements)
            elif ret_val == "7":
                n_display = self.config.restrictedListLen
                if add_vals is not None:
                    try:
                        n_display = int(add_vals[0])
                    except ValueError:
                        pass
                sorted_ids = self.database.getSortedIDs("Opened", reverseOrder=True)[
                    0:n_display
                ]
                table_elements = self.generate_list(sorted_ids)
                self.listWindow.lines = []
                self.listWindow.draw_pre_table_title("-", [(" ", "-")])
                self.listWindow.draw_pre_table_title(
                    f"_{n_display}_last_opened_entries_",
                    [(" ", "-"), ("_", " ")],
                )
                self.listWindow.draw_pre_table_title("-", [(" ", "-")])
                self.listWindow.update(table_elements)
            elif ret_val == "8":
                n_display = self.config.restrictedListLen
                if add_vals is not None:
                    try:
                        n_display = int(add_vals[0])
                    except ValueError:
                        pass
                sorted_ids = self.database.getSortedIDs("Changed", reverseOrder=True)[
                    0:n_display
                ]
                table_elements = self.generate_list(sorted_ids)
                self.listWindow.lines = []
                self.listWindow.draw_pre_table_title("-", [(" ", "-")])
                self.listWindow.draw_pre_table_title(
                    f"_{n_display}_last_changed_entries_",
                    [(" ", "-"), ("_", " ")],
                )
                self.listWindow.draw_pre_table_title("-", [(" ", "-")])
                self.listWindow.update(table_elements)
            elif ret_val == "9":
                del_id = self.listWindow.interact(
                    "Enter ID to be marked/unmarked for deletion"
                )
                self.toggle_for_deletion(del_id, self.listWindow)
            elif ret_val == "10":
                query_ids = self.database.query(["DeletionMark"], "1", returnIDs=True)
                query_ids = sorted(query_ids, key=lambda x: int(x))
                table_elements = self.generate_list(query_ids)
                self.listWindow.lines = []
                self.listWindow.update(table_elements)
            else:
                if ret_val != "0":
                    self.listWindow.print(
                        "Please enter value present in %s"
                        % self.listWindow.validOptions
                    )
                # tableElements = self.generateList("All")
        self.run_main_window(None)

    def run_db_window(self, startVal):
        """
        Function defining the interactions of the DB interaction window
        """
        logger.info("Switching to main window")
        ret_val = startVal
        while ret_val != "0":
            ret_val = self.dbWindow.draw("Enter Value: ")
            if ret_val == "1":
                self.dbWindow.update("Saving database")
                self.database.saveMain()
            elif ret_val == "2":
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
                                "Do you want to add %s to %s [Yes/No] or Add and Quit %s by appending Quit"
                                % (option, item, item)
                            )
                            answer_elements = [a.lower() for a in answer.split(" ")]
                            if any(e in answer_elements for e in ["y", "yes"]):
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
                                if any(e in answer_elements for e in ["q", "quit"]):
                                    break
            elif ret_val == "3":
                updatedFiles = self.database.checkChangedPaths()
                if updatedFiles:
                    for id_, oldPath_, newPath_ in updatedFiles:
                        self.dbWindow.update(
                            "Moved entry with ID %s now has path %s" % (id_, newPath_)
                        )
                else:
                    self.dbWindow.update("No files with changed paths")

            elif ret_val == "4":
                IDchanges = self.database.checkMissingFiles()
                if IDchanges:
                    for oldID, newID in IDchanges:
                        self.dbWindow.update(
                            "Moved entry from ID %s to %s" % (oldID, newID)
                        )
                else:
                    self.dbWindow.update("No Files removed")
            elif ret_val == "5":
                query_ids = self.database.query(["DeletionMark"], "1", returnIDs=True)
                query_ids = sorted(query_ids, key=lambda x: int(x))
                if len(query_ids) > 0:
                    total_size = 0
                    for id_ in query_ids:
                        e = self.database.getEntryByItemName("ID", id_)[0]
                        total_size += float(e.Size)
                        self.dbWindow.update(
                            f"{id_} is marked for deletion "
                            f"(Name: {e.Name}; Size: {e.Size} GB)"
                        )
                    self.dbWindow.update(
                        f"{len(query_ids)} entries marked for deletion "
                        f"with a total size of {total_size} GB"
                    )
                    del_q = self.dbWindow.draw(
                        "Are you sure you want to delete these entries? [Y/n]: "
                    )
                    if del_q == "Y":
                        self.del_ids(query_ids, self.dbWindow)
                        IDchanges = self.database.checkMissingFiles()
                        if IDchanges:
                            for oldID, newID in IDchanges:
                                self.dbWindow.update(
                                    "Moved entry from ID %s to %s" % (oldID, newID)
                                )
                else:
                    self.dbWindow.update("No entries marked for deletion")
            else:
                if ret_val != "0":
                    self.dbWindow.update(
                        "Please enter value present in %s" % self.dbWindow.validOptions
                    )
        self.run_main_window(None)

    def run_mod_window(self, startVal, fromMain, fromList):
        """
        Function defining the interactions of the modification window
        """
        logger.info("Switching to modification window")
        ret_val = startVal
        while ret_val != "0":
            ret_val = self.modWindow.draw("Enter Value: ")
            if ret_val == "0":
                pass
            elif ret_val == "1":
                entered_id = self.modWindow.draw("Enter ID: ")
                if entered_id in self.database.getAllValuebyItemName("ID"):
                    new_window = False
                    if entered_id not in self.allMultiModWindow.keys():
                        self.allMultiModWindow[entered_id] = deepcopy(
                            self.multiModWindow
                        )
                        new_window = True
                    self.run_multi_mod_window(
                        None, entered_id, new_window, fromMain, fromList
                    )
                else:
                    self.modWindow.update("ID %s not in database" % entered_id)
            elif ret_val == "2":
                ids = self.modWindow.draw("Enter ids as XXX - YYY")
                ids = ids.replace(" ", "")
                res = re.search("[0-9]+-[0-9]+", ids)
                valid_input = False
                if res is not None:
                    if res.span() == (0, len(ids)):
                        valid_input = True
                if valid_input:
                    self.modWindow.update("%s is a valid intput" % ids)
                    fist_id, last_id = ids.split("-")
                    id_list = [
                        str(x) for x in list(range(int(fist_id), int(last_id) + 1))
                    ]
                    self.process_list_of_modification(self.modWindow, id_list)
                else:
                    self.modWindow.update("%s is a invalid intput" % ids)
            elif ret_val == "3":
                ids = self.modWindow.draw("Enter ids as XXX,YYY,..")
                ids = ids.replace(" ", "")
                res = re.search("([0-9],)+[0-9]", ids)
                valid_input = False
                if res is not None:
                    if res.span() == (0, len(ids)):
                        valid_input = True
                if valid_input:
                    id_list = ids.split(",")
                    self.process_list_of_modification(self.modWindow, id_list)
                else:
                    self.modWindow.update("%s is a invalid intput" % ids)
            else:
                if ret_val != "0":
                    self.modWindow.update(
                        "Please enter value present in %s" % self.modWindow.validOptions
                    )
        if fromMain:
            self.run_main_window(None)
        if fromList:
            self.run_list_window(None)

    def process_list_of_modification(self, window, id_list):
        """
        Function prevalidating the ids set in the ModWindows for bulk updating of
        Entries
        """
        id_list = sorted(id_list, key=lambda x: int(x))
        _validIDs = []
        _rmIDs = []
        for ID in id_list:
            if int(ID) > len(self.database.entries) - 1:
                _rmIDs.append(ID)
            else:
                _validIDs.append(ID)
        if len(_rmIDs) > 0:
            window.update(
                "ids %s are larger than max (%s)"
                % (_rmIDs, len(self.database.entries) - 1)
            )
        if len(_validIDs) > 0:
            window.update("id_list : %s" % _validIDs)
            self.mod_list_of_items(self.modWindow, _validIDs)

    def run_multi_mod_window(self, startVal, ID, isNewWindow, fromMain, fromList):
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
                thisWindow.headerTextSecondary[name] = self.get_print_item_values(
                    ID, name, joinFull=True
                )
        ret_val = startVal
        while ret_val != "0":
            ret_val = thisWindow.draw("Enter Value: ")
            if ret_val == "0":
                pass
            elif ret_val in thisWindow.validOptions:
                if ret_val == str(self.mulitModExecVal):
                    thisWindow.update("Silent Execute triggered")  # TEMP
                    self.execute(ID, thisWindow, silent=True)
                else:
                    for elem in thisWindow.headerOptions:
                        modID, name, comment = elem
                        if modID == ret_val:
                            thisWindow.update("%s, %s" % (modID, name))  # TEMP
                            if name in self.database.model.items.keys():
                                thisWindow.update("%s is a Item" % name)  # TEMP
                                self.mod_single_item(
                                    thisWindow, [ID], name, fromMultiMod=True
                                )
                            elif name in self.database.model.listitems.keys():
                                thisWindow.update("%s is a ListItem" % name)  # TEMP
                                self.mod_list_item(
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
        self.run_mod_window(None, fromMain, fromList)

    def mod_list_item(self, window, ids, name, verbose=True, fromMultiMod=False):
        """
        Wrapper for the different modification options and how they are called in the
        database

        Args:
            windows (Window or ListWindows) : Current window
            ids (list) : List of ids to be modified
            name (str) : Item name to be modified
        """
        method = window.draw("Choose Method (Append/App/A | Replace/RP | Remove/RM)")
        if method.lower() in ["append", "app", "a"]:
            newValue = window.draw("New Value")
            for ID in ids:
                self.make_list_modifications(ID, name, "Append", None, newValue)
                if verbose:
                    window.update("Appended %s" % newValue)
        elif method.lower() in ["remove", "rm"]:
            oldValue = window.draw("Remove Value")
            for ID in ids:
                sucess = self.make_list_modifications(
                    ID, name, "Remove", oldValue, None
                )
                if sucess:
                    if verbose:
                        window.update("Removed %s from entry" % oldValue)
                else:
                    window.update("Value %s no in entry" % oldValue)
        elif method.lower() in ["replace", "rp"]:
            oldValue = window.draw("Value to replace")
            newValue = window.draw("New Value")
            for ID in ids:
                sucess = self.make_list_modifications(
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
            window.headerTextSecondary[name] = self.get_print_item_values(
                ids[0], name, joinFull=True
            )

    def mod_list_of_items(self, window, ids):
        """
        Multiple modification of a single Item
        """
        item = window.draw("Change item ({0})".format(" | ".join(self.config.modItems)))
        if item in self.modSingleItems:
            newValue = window.draw("New Value for %s" % item)
            for ID in ids:
                self.database.modifySingleEntry(ID, item, newValue, byID=True)
        elif item in self.modListItems:
            self.mod_list_item(window, ids, item, verbose=False)
        else:
            window.update("Input is no valid item")

    def mod_single_item(self, window, ids, name=None, fromMultiMod=False):
        """
        Wrapper for modifying a Single Item
        """
        if name is None:
            name = window.draw(
                "Change item ({0})".format(" | ".join(self.modSingleItems))
            )
        if name in self.modSingleItems:
            newValue = window.draw("New Value for %s" % name)
            for ID in ids:
                self.database.modifySingleEntry(ID, name, newValue, byID=True)
            if fromMultiMod:
                window.headerTextSecondary[name] = self.get_print_item_values(
                    ids[0], name, joinFull=True
                )

    def make_list_modifications(self, ID, name, method, oldValue, newValue):
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
            self.database.last_executed_ids.append(ID)
            if not silent:
                self.database.modifyListEntry(
                    ID,
                    "Opened",
                    mimir.backend.helper.getTimeFormatted("Full"),
                    byID=True,
                )

    def execute_random(self, window, fromList=False, silent=False, weighted=True):
        """
        Function for getting a random entry from the last printed List of entries
        (if none printed from all)
        """
        if not self.lastIDList:
            window.print("No entries to choose from. Maybe requery?")
        else:
            randID = self.database.getRandomEntry(
                choose_from=self.lastIDList, weighted=weighted
            )
            _listIDList = self.lastIDList
            if fromList:
                tableElements = self.generate_list([randID])
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

    def generate_list(self, get="All"):
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
                    value = self.get_print_item_values(id, item)
                entryElements.append(value)
            tableElements.append(tuple(entryElements))
        return tableElements

    def get_print_item_values(self, ID, item, joinWith=", ", joinFull=False):
        retValue = None
        thisEntry = self.database.getEntryByItemName("ID", ID)[0]
        if item in self.database.model.items:
            value = thisEntry.getItem(item).value
            self.mod_disaply(item, value)
            if len(value) > self.config.itemInfo[item]["maxLen"] and not joinFull:
                retValue = value[: self.config.itemInfo[item]["maxLen"]] + ".."
            else:
                retValue = value
        elif item in self.database.model.listitems:
            retValue = self.join_item_values(thisEntry, item, joinWith, joinFull)
        else:
            raise KeyError("Item %s no listitem or singelitem")

        return retValue

    def join_item_values(self, entry, item, joinWith=", ", joinFull=False):
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
                    thisValue.append(self.mod_disaply(item, val))
            if len(thisValue) > self.config.itemInfo[item]["nDisplay"]:
                if item not in ["Opened", "Changed"]:
                    thisValue.append("..")
                break
        return joinWith.join(thisValue)

    def mod_disaply(self, item, value):
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

    def modif_item_display(self, item, value):
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

    def __init__(self, config) -> None:
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


def init_database(basedir, config=None):
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
