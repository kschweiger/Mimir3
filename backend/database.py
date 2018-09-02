"""
Toplevel Database class for the Mimir database
"""
import logging
import json
import os
from glob import glob

from backend.entry import DataBaseEntry, Item, ListItem
import backend.helper

class DataBase(object):
    """
    Database class that contains Items and all methods for reading/manipulation them
    TODO: Document how it is loaded/saved if already exising

    Args:
        root (str) : Base path of the database. This can change between different session\n
                     for example if the data base is on a removable drive\n
        status (str) : Initializes a new Database or loads a existing database in root dir \n
        model (str) : Path to the model used for database initialization

    Members:
        maxID (int) : Highes ID in the Database
    """
    def __init__(self, root, status, modelConf=None, dummy=False):
        logging.info("Initializing DataBase")
        self.databaseRoot = root
        self.entries = []
        self.entrydict = {}
        self.mimirdir = root+"/.mimir"
        self.savepath = root+"/.mimir/mainDB.json"
        self.maxID = 0
        self.isdummy = False
        if status == "new":
            self._model = Model(modelConf)
            if os.path.exists(self.mimirdir) and not dummy:
                raise RuntimeError(".mimir directory exiting in ROOT dir. Currently not supported!")
            elif dummy:
                logging.warning("Initializing Database as dummy - Disabling saving")
                self.isdummy = True
            else:
                logging.info("Creating .mimir folder in %s", root)
                os.makedirs(self.mimirdir)
                logging.debug("Saving model in .mimir dir")
                with open(self.mimirdir+"/model.json", 'w') as outfile:
                    json.dump(self._model.initDict, outfile, sort_keys=True, indent=4, separators=(',', ': '))
            #New database always runs a search of the filesystem starting from self.root
            filesFound = self.getAllFilesMatchingModel()
            for path2file in filesFound:
                logging.debug("Adding file %s", path2file)
                self.createNewEntry(path2file, self.maxID)
                self.maxID += 1
            self.maxID = self.maxID - 1
        elif status == "load":
            if not os.path.exists(self.mimirdir) and not dummy:
                raise RuntimeError("No .mimir dir existant in {0}".format(root))
            if dummy:
                logging.warning("Loading Database from %s as dummy", root)
                self.isdummy = True
            if modelConf is None:
                self._model = Model(self.mimirdir+"/model.json")
            else:
                self._model = Model(modelConf)
            self.loadMain()

        else:
            raise RuntimeError("Unsupported status: {0}".format(status))

    @property
    def model(self):
        """ Returns the model variable """
        return self._model

    def getAllFilesMatchingModel(self, startdir=""):
        """
        Returns all files matching the file extentions defined in model starting
        from database root dir.
        Returns list with all matching file w/o database root dir
        """
        if not startdir.endswith("/") and startdir != "":
            startdir = startdir+"/"
        allfiles = glob(self.databaseRoot+"/"+startdir+"**/*.*", recursive=True)

        matchingfiles = []
        for f in allfiles:
            try:
                ext = f.split("/")[-1].split(".")[1]
            except IndexError:
                logging.warning("Found file not matching expected structure: %s", f)
                continue
            if ext in self.model.extentions:
                matchingfiles.append(f)

        return matchingfiles

    def createNewEntry(self, path, cID):
        """ Create an entry for a file with path and ID.
        Called for each file that is found on filesystem
        Args:
            path (str) : Path to file added to DB on filesystem\n
            cID (int) : ID that is used for this entry

        Returns new DataBaseEntry object
         """
        filename = path.split("/")[-1].split(".")[0]
        entryinit = []
        for item in self.model.items:
            if item == "Path":
                entryinit.append(("Path", "Single", path))
            elif item == "ID":
                entryinit.append(("ID", "Single", str(cID)))
            elif item == "Name":
                entryinit.append(("Name", "Single", filename))
            elif item == "Added":
                entryinit.append(("Added", "Single", backend.helper.getTimeFormatted("Full")))
            else:
                entryinit.append((item, "Single", self.model.items[item]["default"]))
        for listitem in self.model.listitems:
            entryinit.append((listitem, "List", self.model.listitems[listitem]["default"]))

        e = DataBaseEntry(entryinit)

        self.entries.append(e)
        self.entrydict[str(cID)] = e
        return e

    def saveMain(self):
        """ Save the main database (json file with all entries) as mainDB.json in the .mimir folder of the DB """
        if self.isdummy:
            logging.error("Database isDummy - Saving disabled")
            return False
        status = False
        output = {}
        for entry in self.entries:
            output[entry.Path] = entry.getDictRepr()
        with open(self.savepath, "w") as outfile:
            json.dump(output, outfile, indent=4)
            status = True
        return status

    def loadMain(self):
        """ Load the main DB from the .mimir folder """
        with open(self.savepath) as saveFile:
            savedDB = json.load(saveFile)
        for filepath in savedDB:
            savedEntry = savedDB[filepath]
            entryinit = []
            for item in savedEntry:
                if not (item in self.model.items or item in self.model.listitems):
                    logging.warning("Found item in saved json not in model. Item will be ignored")
                    logging.warning("Currently this will result in loss of data when saving")
                    continue
                entryinit.append((item, savedEntry[item]["type"], savedEntry[item]["value"]))
            e = DataBaseEntry(entryinit)
            self.entries.append(e)
            self.entrydict[savedEntry["ID"]["value"]] = e

    def findNewFiles(self, startdir=""):
        """
        Find new files in starting from the root directory.

        Args:
            startdir (str) : Specifiy a subdirectory to start from
        """
        newFiles = []
        allfiles = self.getAllFilesMatchingModel(startdir)
        IDs = []
        existingFiles = []
        missingIDs = []
        for entry in self.entries:
            existingFiles.append(entry.Path)
            IDs.append(int(entry.ID))

        print(IDs)
        #Find all IDs missing so new files can be inserted
        IDs = set(IDs)
        for i in range(len(self.entries)):
            if i not in IDs:
                missingIDs.append(i)

        existingFiles = set(existingFiles)
        for file_ in allfiles:
            if file_ not in existingFiles:
                newFiles.append(file_)

        toret = newFiles
        #Insert/Append new files
        for newFile in newFiles:
            if len(missingIDs) > 0:
                cID = missingIDs[0]
                missingIDs = missingIDs[1:]
            else:
                self.maxID += 1
                cID = self.maxID
            self.createNewEntry(newFile, cID)
        return toret

    def getAllValuebyItemName(self, itemName):
        """ Return a set of all values of name itemName """
        if itemName not in self.model.allItems:
            raise KeyError("Arg {0} not in model items".format(itemName))
        retlist = []
        for entry in self.entries:
            retlist.append(getattr(entry, itemName))
        return set(retlist)

    def getEntryByItemName(self, itemName, itemValue):
        """ Get all entries that have value itemValue in Item with itemName """
        if itemName not in self.model.allItems:
            raise KeyError("Arg {0} not in model items".format(itemName))
        machtingEntries = []
        for entry in self.entries:
            if isinstance(entry, Item):
                if entry.getItem(itemName).value == itemValue:
                    machtingEntries.append(entry)
            else:
                if itemValue in entry.getItem(itemName).value:
                    machtingEntries.append(entry)
        return machtingEntries

    def remove(self, identifier, byID=False, byName=False, byPath=False):
        """
        Remove a entry from the databse by specifing indentifier. Indentifier can be ID, Name\n
        or Path (vector). When calling the function only one can be set to True otherwise a\n
        exception will be raised

        Args:
            indentifier (int, string) : Indentifier by with the entry will be removed. For can be of\n
                                  type string for all vectors and also int for ID vector
            byID (bool) : Switch for using the ID vector
            byName (bool) : Switch for using the Name vector
            byPath (bool) : Switch for using the Path vector

        Raises:
            RuntimeError : If more than one vector or no vector was turned on
            TypeError : If indentifier has a not supported type
            KeyError : If indentifier is no valid Name, Path or ID
        """
        #Exceptions:
        self.checkModVector(identifier, byID, byName, byPath)

        #Now the actual function
        if byID:
            removetype = "ID"
        if byName:
            removetype = "Name"
        if byPath:
            removetype = "Path"
        entry2remove = self.getEntryByItemName(removetype, str(identifier))[0]
        self.entries.remove(entry2remove)
        self.entrydict.pop(entry2remove.Path, None)

    def modifySingleEntry(self, identifier, itemName, newValue, byID=False, byName=False, byPath=False):
        """
        Modify an entry of the Database
        Args:
            indentifier (int, string) : Indentifier by which the entry will selected. It can be of\n
                                        type string for all vectors and also int for ID vector
            itemName (str) : Name of Item to be modified
            newValue (str) : New value for the item
            byID (bool) : Switch for using the ID vector
            byName (bool) : Switch for using the Name vector
            byPath (bool) : Switch for using the Path vector
        """
        self.checkModVector(identifier, byID, byName, byPath)
        if byID:
            Idtype = "ID"
        if byName:
            Idtype = "Name"
        if byPath:
            Idtype = "Path"
        modEntry = self.getEntryByItemName(Idtype, str(identifier))[0]
        if not type(modEntry.items[itemName]) == Item: # pylint: disable=unidiomatic-typecheck
            raise TypeError("Called modifySingleEntry with a Entry of type {0}".format(type(modEntry.items[itemName])))
        modEntry.changeItemValue(itemName, newValue)

    def modifyListEntry(self, identifier, itemName, newValue, method="Append", oldValue=None, byID=False, byName=False, byPath=False):
        """
        Modify an entry of the Database
        Args:
            indentifier (int, string) : Indentifier by which the entry will selected. It can be of\n
                                        type string for all vectors and also int for ID vector
            itemName (str) : Name of Item to be modified
            newValue (str) : New value for the item
            byID (bool) : Switch for using the ID vector
            byName (bool) : Switch for using the Name vector
            byPath (bool) : Switch for using the Path vector
        """
        self.checkModVector(identifier, byID, byName, byPath)
        if byID:
            Idtype = "ID"
        if byName:
            Idtype = "Name"
        if byPath:
            Idtype = "Path"
        modEntry = self.getEntryByItemName(Idtype, str(identifier))[0]
        if not isinstance(modEntry.items[itemName], ListItem):
            raise TypeError("Called modifyListEntry with a Entry of type {0}".format(type(modEntry.items[itemName])))
        if method == "Append":
            if (len(modEntry.getItem(itemName).value) == 1 and modEntry.getItem(itemName).value[0] == self.model.getDefaultValue(itemName)):
                default = self.model.getDefaultValue(itemName)
                modEntry.replaceItemValue(itemName, newValue, default)
            else:
                modEntry.addItemValue(itemName, newValue)
        elif method == "Replace":
            modEntry.replaceItemValue(itemName, newValue, oldValue)
        elif method == "Remove":
            modEntry.removeItemValue(itemName, oldValue)
            if len(modEntry.getItem(itemName).value) == 0:
                modEntry.addItemValue(itemName, self.model.getDefaultValue(itemName))
        else:
            raise NotImplementedError

    def query(self, itemNames, itemValues, returnIDs=False):
        """
        Query database: Will get all values for items with names itemNames and searches\n
        for all values given in the itemValues parameter

        Args:
            itemNames (str, list) : itemNames used for the query
            itemValues (str, list) : itemValues used for the query
            returnIDs (bool) : If True function will return a list of IDs instead of entries

        Returns:
            result (list) : list of all entries (ids) matching the query
        """
        if isinstance(itemNames, str):
            itemNames = [itemNames]
        if isinstance(itemValues, str):
            itemValues = [itemValues]
        for name in itemNames:
            if name not in self.model.allItems:
                raise KeyError("Arg {0} not in model items".format(name))
        result = []
        for entry in self.entries:
            entryValues = entry.getAllValuesbyName(itemNames)
            hit = False
            for value in itemValues:
                if value in entryValues:
                    hit = True
                    break
            if hit:
                if returnIDs:
                    result.append(entry.ID)
                else:
                    result.append(entry)
        return result

    def getEntrybyID(self, retID):
        """ Faster method for getting entry by ID """
        return self.getEntryByItemName("ID", retID)[0]

    def __eq__(self, other):
        """ Implementation of the equality relation """
        if isinstance(other, self.__class__):
            if len(self.entries) != len(other.entries):
                return False
            for entry in self.entries:
                foundequivalent = False
                for otherentry in other.entries:
                    #print("comparing",entry, otherentry)
                    if entry == otherentry:
                        foundequivalent = True
                        break
                if not foundequivalent:
                    return False
            return True
        else:
            return NotImplemented

    def getStatus(self):
        """ Check if current status of the database is saved """
        if not os.path.exists(self.savepath):
            logging.info("No database saved yet")
            return False
        dummyDB = DataBase(self.databaseRoot, "load", dummy=True)
        if self == dummyDB: # pylint: disable=simplifiable-if-statement
            return True
        else:
            return False

    def checkModVector(self, value, byID, byName, byPath):
        """ Common function for modification methods input chekcing """
        nVectorsActive = 0
        for vector in [byID, byName, byPath]:
            if not isinstance(vector, bool):
                raise TypeError("Vectors are required to be a bool")
            if vector:
                nVectorsActive += 1
        if nVectorsActive == 0 or nVectorsActive > 1:
            raise RuntimeError
        if not isinstance(value, (str, int)) and byID:
            raise TypeError("byID vector supports str and int but value was type {0}".format(type(value)))
        if not isinstance(value, str) and (byName or byPath):
            raise TypeError("byName and byPath vector support str but value was type {0}".format(type(value)))
        if byID:
            if str(value) not in self.getAllValuebyItemName("ID"):
                raise IndexError("Index {0} is out of range of DB".format(value))
        else:
            if byName:
                query = "Name"
            if byPath:
                query = "Path"
            if value not in self.getAllValuebyItemName(query):
                raise KeyError("Value w/ {0} {1} not in Database".format(query, value))

class Model(object):
    """
    Database model

    Args:
        config : Config file for the model
    Attributes:
        filename : Path to the model json\n
        modelName : name of the model\n
        modelDesc : Description of the model\n
        extentions : File extentions that are used as criterion for searching files\n
    """
    def __init__(self, config):
        logging.debug("Loading model from %s", config)
        self.fileName = config
        modelDict = None
        with open(config) as f:
            modelDict = json.load(f)
        self.initDict = modelDict
        self.modelName = modelDict["General"]["Name"]
        self.modelDesc = modelDict["General"]["Description"]
        self.extentions = modelDict["General"]["Types"]
        self.secondaryDBs = modelDict["General"]["SecondaryDBs"]
        self._items = {}
        self._listitems = {}
        for key in modelDict:
            if key != "General":
                logging.debug("Found item %s in model", key)
                newitem = {}
                for itemKey in modelDict[key]:
                    if itemKey != "Type":
                        newitem[itemKey] = modelDict[key][itemKey]
                if modelDict[key]["Type"] == "ListItem":
                    self._listitems.update({key : newitem})
                elif modelDict[key]["Type"] == "Item":
                    self._items.update({key : newitem})
                else:
                    raise TypeError("Invalid item type in model definition")
        self.allItems = set(self._items.keys()).union(set(self._listitems.keys()))
        #TODO Check if required items are in model

    def updateModel(self):
        """ Function for updating the model (not sure if needed) """
        pass

    def getDefaultValue(self, itemName):
        """ Returns the default item name of the modlue """
        if itemName in self._items.keys():
            return self._items[itemName]["default"][0]
        elif itemName in self._listitems.keys():
            return self._listitems[itemName]["default"][0]
        else:
            raise KeyError

    @property
    def items(self):
        """ Retruns all item demfinitons in the model """
        return self._items
    @property
    def listitems(self):
        """ Retruns all listitem demfinitons in the model """
        return self._listitems

#def validateDatabaseJSON(database, jsonfile):
#    """
#    Function for validating a saved database. This comparison requires the
#    lastest version of the database to check in memory.
#
#    Args:
#        databse (DataBase) : Reference database (in Runtime)
#        json (str) : Path to json file to be checked
#    """
#    checkDB = Database(database.databaseRoot, "load", database.model.fileName, jsonfile)
