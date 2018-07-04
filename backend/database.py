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
    def __init__(self, root, status, modelConf = None):
        logging.info("Initializing DataBase")
        self.databaseRoot = root
        self.entries = []
        self.entrydict = {}
        self.mimirdir = root+"/.mimir"
        self.savepath = root+"/.mimir/mainDB.json"
        self.maxID = 0
        if status == "new":
            self.model = Model(modelConf)
            if os.path.exists(self.mimirdir):
                raise RuntimeError(".mimir directory exiting in ROOT dir. Currently not supported!")
            else:
                logging.info("Creating .mimir folder in {0}".format(root))
                os.makedirs(self.mimirdir)
                logging.debug("Saving model in .mimir dir")
                with open(self.mimirdir+"/model.json", 'w') as outfile:
                    json.dump(self.model.initDict, outfile, sort_keys=True, indent=4, separators=(',', ': '))
            #New database always runs a search of the filesystem starting from self.root
            filesFound = self.getAllFilesMatchingModel()
            for path2file in filesFound:
                logging.debug("Adding file {0}".format(path2file))
                e = self.createNewEntry(path2file, self.maxID)
                self.maxID += 1
            self.maxID = self.maxID - 1
        elif status == "load":
            if not os.path.exists(self.mimirdir):
                raise RuntimeError("No .mimir dir existant in {0}".format(root))
            if modelConf is None:
                self.model = Model(self.mimirdir+"/model.json")
            else:
                self.model = Model(modelConf)
            self.loadMain()
            
        else:
            raise RuntimeError("Unsupported status: {0}".format(status))

    def getAllFilesMatchingModel(self, startdir = ""):
        """
        Returns all files matching the file extentions defined in model starting
        from database root dir.
        Returns list with all matching file w/o database root dir
        """
        if not startdir.endswith("/") and not startdir == "":
            startdir = startdir+"/"
        allfiles = glob(self.databaseRoot+"/"+startdir+"**/*.*", recursive=True)

        matchingfiles = []
        for f in allfiles:
            try:
                ext = f.split("/")[-1].split(".")[1]
            except IndexError:
                logging.warning("Found file not matching expected structure: {0}".format(f))
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
        status = False
        output = {}
        for entry in self.entries:
            output[entry.Path] = entry.getDictRepr()
        with open(self.savepath, "w") as outfile:
            json.dump(output, outfile, indent=4)
            status = True
        return status

    def loadMain(self):
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

    def findNewFiles(self, startdir = ""):
        """
        Find new files in starting from the root directory.

        Args:
            startdir (str) : Specifiy a subdirectory to start from
        """
        startingfrom = self.databaseRoot+"/"+startdir
        newFiles = []
        allfiles = self.getAllFilesMatchingModel(startdir)
        IDs = []
        existingFiles = []
        missingIDs = []
        for nEntry, entry in enumerate(self.entries):
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
                missingIDs[1:]
            else:
                self.maxID += 1
                cID = self.maxID
            self.createNewEntry(newFile, cID)
        return toret

    def getAllValuebyItemName(self, ItemName):
        """ Return a set of all values of name ItemName """
        if ItemName not in self.model.allItems:
            raise KeyError("Arg {0} not in model items".format(ItemName))
        retlist = []
        for entry in self.entries:
            retlist.append(getattr(entry, ItemName))
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
        return(machtingEntries)
            
    def remove(self, value, byID = False, byName = False, byPath = False):
        """
        Remove a entry from the databse by specifing value. Value can be ID, Name\n
        or Path (vector). When calling the function only one can be set to True otherwise a\n
        exception will be raised 
        
        Args:
            value (int, string) : Value by with the entry will be removed. For can be of\n
                                  type string for all vectors and also int for ID vector
            byID (bool) : Switch for using the ID vector
            byName (bool) : Switch for using the Name vector
            byPath (bool) : Switch for using the Path vector

        Raises:
            RuntimeError : If more than one vector or no vector was turned on
            TypeError : If value has a not supported type
            KeyError : If value is no valid Name, Path or ID
        """
        #Exceptions:
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

        #Now the actual function
        if byID:
            removetype = "ID"
        if byName:
            removetype = "Name"
        if byPath:
            removetype = "Path"
        entry2remove = self.getEntryByItemName(removetype, str(value))[0]
        self.entries.remove(entry2remove)
        self.entrydict.pop(entry2remove.Path, None)
        
    """
    def __repr__(self):
        pass
    """
    def __eq__(self, other):
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
        
    
    def getStats(self):
        """ Check if current status of the database is saved """
        pass

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
        logging.debug("Loading model from {0}".format(config))
        self.fileName = config
        modelDict = None
        with open(config) as f:
            modelDict = json.load(f)
        self.initDict = modelDict
        self.modelName = modelDict["General"]["Name"]
        self.modelDesc = modelDict["General"]["Description"]
        self.extentions = modelDict["General"]["Types"]
        self.items = {}
        self.listitems = {}
        for key in modelDict:
            if key != "General":
                logging.debug("Found item {0} in model".format(key))
                newitem = {}
                for itemKey in modelDict[key]:
                    if itemKey != "Type":
                        newitem[itemKey] = modelDict[key][itemKey]
                if modelDict[key]["Type"] == "ListItem":
                    self.listitems.update({key : newitem})
                elif modelDict[key]["Type"] == "Item":
                    self.items.update({key : newitem})
                else:
                    raise TypeError("Invalid item type in model definition")
        self.allItems = set(self.items.keys()).union(set(self.listitems.keys()))       
        #TODO Check if required items are in model

    def updateModel(self):
        pass

def validateDatabaseJSON(database, jsonfile):
    """ Function for validating a saved database. This comparison requires the 
    lastest version of the database to check in memory.
    
    Args:
        databse (DataBase) : Reference database (in Runtime)
        json (str) : Path to json file to be checked
    """
    checkDB = Database(database.databaseRoot, "load" ,database.model.fileName, jsonfile) 
    
