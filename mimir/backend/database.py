"""
Toplevel Database class for the Mimir database
"""
import logging
import random
import json
import os
import copy
from shutil import copy2
from glob import glob
from collections import OrderedDict

from mimir.backend.entry import DataBaseEntry, Item, ListItem
import mimir.backend.helper
import mimir.backend.plugin

class DataBase:
    """
    Database class that contains entries which are organized by an unique ID. The class contains methods for operating on the Database (save, load, queries, random entries) and modifing/reading/removing Entries. When a new database is created, a root directory (which contains all files) and a model are required. The Model can be created with makeModelDefinition.py and modified for specific needs. During initialization a .mimir directory will be created in the passed root directory. There the database and all affiliated files (backup, secondary databases) will be saved. The model passed in this process will alse be saved there for future reference.

    Args:
        root (str) : Base path of the database. This can change between different session for example if the data base is on a removable drive
        status (str) : Initializes a new Database or loads a existing database in root dir
        model (str) : Path to the model used for database initialization

    Raises:
        RuntimeError : Raised if .mimir folder already existis and a new database is being created
        RuntimeError : Raised if a database is being loaded from a folder that has no initialized database
        RuntimeError : Raised for invalid status argument

    Attributes:
        maxID (int) : Highes ID in the Database
        databaseRoot (str) : Points to the root of the database
        mimirdir (str) : Points to the .mimir dir of the DB
        savepath (str) : Points to the path where the database is saved
        entries (list) : List of all Entry Object in the database
        entrydict (dict) : Dict of all entries with IDs as key
        _model (Model) : General information of the database model
        isdummy (bool) : Flag used for dummy databases --> Currently only disables saveing
        cachedValue (dict - list) : Saved all present Values for item (key)
        valuesChanged (dict - bool) : Flag if cachedValues are still valid
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
        self.cachedValues = {}
        self.cachedValuesChanged = {}
    
        if status == "new":
            self._model = Model(modelConf)
            self.initCaching() #initialize cache so self.createEntry works
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

        self.initCaching() #Set intiial cache with new entries
        
    def initCaching(self):
        for item in self.model.allItems:
            self.cachedValuesChanged[item] = True
            self.cachedValues[item] = self.getAllValuebyItemName(item)

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
        logging.debug("All files from glob: %s", len(allfiles))
        matchingfiles = []
        for f in allfiles:
            for ext in self.model.extentions:
                if f.endswith(ext):
                    matchingfiles.append(f.replace(self.databaseRoot+"/", ""))
                    continue
        logging.debug("Matching files: %s", len(matchingfiles))
        return matchingfiles

    def createNewEntry(self, path, cID):
        """ Create an entry for a file with path and ID.
        Called for each file that is found on filesystem
        Args:
            path (str) : Path to file added to DB on filesystem\n
            cID (int) : ID that is used for this entry

        Return:
            new DataBaseEntry object
        """
        logging.info("Initializing file with path: %s", path)
        filename = path.split("/")[-1]
        for ext in self.model.extentions:
            if filename.endswith(ext):
                filename = filename.replace("."+ext, "")
        logging.info("Initializing file with name: %s", filename)
        entryinit = {}
        for item in self.model.items:
            if item == "Path":
                entryinit["Path"] = ("Single", path)
            elif item == "ID":
                entryinit["ID"] = ("Single", str(cID))
            elif item == "Name":
                entryinit["Name"] = ("Single", filename)
            elif item == "Added":
                entryinit["Added"] = ("Single", mimir.backend.helper.getTimeFormatted("Full"))
            else:
                entryinit[item] = ("Single", self.model.items[item]["default"])
        for listitem in self.model.listitems:
            entryinit[listitem] = ("List", self.model.listitems[listitem]["default"])

        #If items with for plugins are degined run the pluging functions
        if self.model.pluginDefinitions:
            pluginValues = mimir.backend.plugin.getPluginValues(self.databaseRoot+"/"+path, self.model.pluginDefinitions)
            for plugin in pluginValues:
                eType, eValue = entryinit[self.model.pluginMap[plugin]]
                entryinit[self.model.pluginMap[plugin]] = (eType, pluginValues[plugin])

        _entryinit = []
        for entry in entryinit:
            _entryinit.append((entry, entryinit[entry][0], entryinit[entry][1]))

        e = DataBaseEntry(_entryinit)
        self.cachedValuesChanged["ID"] = True
        self.entries.append(e)
        self.entrydict[str(cID)] = e
        return e

    def saveMain(self):
        """
        Save the main database (json file with all entries)
        as mainDB.json in the .mimir folder of the DB.
        Before saving it will create a backup of the current
        state. Backups are save for days. Will overwrite if already
        present.
        """
        if self.isdummy:
            logging.error("Database isDummy - Saving disabled")
            return False
        status = False
        # Copy current DBfile and save it as backup
        if os.path.exists(self.savepath):
            logging.debug("Making backup")
            backupDate = mimir.backend.helper.getTimeFormatted("Date", "-", inverted=True)
            copy2(self.savepath, self.savepath.replace(".json", ".{0}.backup".format(backupDate)))
        # Convert database to dict so json save can be used
        output = OrderedDict()
        for entry in self.entries:
            output.update({entry.Path : entry.getDictRepr()})
        logging.debug("Saving database at %s", self.savepath)
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
            self.maxID += 1
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

        logging.debug("Found %s files in FS. Entries in database: %s", len(allfiles), len(existingFiles))
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
        pairs = []
        #Insert/Append new files
        for newFile in newFiles:
            if len(missingIDs) > 0:
                cID = missingIDs[0]
                missingIDs = missingIDs[1:]
            else:
                self.maxID += 1
                cID = self.maxID
            self.createNewEntry(newFile, cID)
            pairs.append((newFile, cID))

        return toret, pairs

    def getAllValuebyItemName(self, itemName):
        """ Return a set of all values of name itemName """
        if itemName not in self.model.allItems:
            raise KeyError("Arg {0} not in model items".format(itemName))
        if self.cachedValuesChanged[itemName]:
            self.cacheAllValuebyItemName(itemName)
        return self.cachedValues[itemName]

    def cacheAllValuebyItemName(self, itemName):
        """
        Function for filling the cached Value objects of the database
        """
        retlist = []
        for entry in self.entries:
            toAdd = getattr(entry, itemName)
            if isinstance(toAdd, list):
                retlist += toAdd
            else:
                retlist.append(toAdd)
        logging.info(retlist)
        self.cachedValuesChanged[itemName] = False
        self.cachedValues[itemName] = set(retlist)


    def getSortedIDs(self, sortBy, reverseOrder=True):
        """
        Returns a list of database IDs sorted by itemName sortBy.

        Args:
            sortBy (str) : itemName that will be used for sorting. The exact sorting \n
                           depends on the type set in the model (str, int, datetime)
        Return:
            sortedEntries (list[str]) : List of all id sorted by sortBy newValue

        Raises:
            KeyError : Will be raise if sortBy is no valid itemName for the model
        """
        if sortBy not in self.model.allItems:
            raise KeyError("Arg {0} not in model items".format(sortBy))
        allIDs = self.getAllValuebyItemName("ID")
        map_id_sortby = {}
        for ID in allIDs:
            map_id_sortby[ID] = self.getEntrybyID(ID).getItem(sortBy).value
        itemType = self.model.getItemType(sortBy)
        #If sortBy is a ListItem we need to figure out the value to sort by
        if sortBy in self.model.listitems:
            for ID in map_id_sortby:
                if itemType == "datetime":
                    map_id_sortby[ID] = mimir.backend.helper.sortDateTime(map_id_sortby[ID])[0]
                else:
                    #TODO: Think about a way to sort ListItems of type str/int
                    raise NotImplementedError("Sorting for none datetime listitems not implemented")

        pairs = []
        for ID in map_id_sortby:
            pairs.append((ID, map_id_sortby[ID]))

        if itemType == "datetime":
            sortedPairs = sorted(pairs,
                                 key=lambda x: (mimir.backend.helper.convertToDateTime(x[1]),
                                                -int(x[0]) if reverseOrder else int(x[0])),
                                 reverse=reverseOrder)
        elif itemType == "int":
            sortedPairs = sorted(pairs,
                                 key=lambda x: (int(x[1]),
                                                -int(x[0]) if reverseOrder else int(x[0])),
                                 reverse=reverseOrder)
        elif itemType == "float":
            sortedPairs = sorted(pairs,
                                 key=lambda x: (float(x[1]),
                                                -int(x[0]) if reverseOrder else int(x[0])),
                                 reverse=reverseOrder)
        else:
            sortedPairs = sorted(pairs,
                                 key=lambda x: (x[1],
                                                -int(x[0]) if reverseOrder else int(x[0])),
                                 reverse=reverseOrder)


        return [x[0] for x in sortedPairs]

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
        self.cachedValuesChanged[itemName] = True
        #Update the Changed date of the entry
        self.modifyListEntry(identifier, "Changed", mimir.backend.helper.getTimeFormatted("Full"),
                             byID=byID, byName=byName, byPath=byPath)

    def modifyListEntry(self, identifier, itemName, newValue, method="Append", oldValue=None, byID=False, byName=False, byPath=False):
        """
        Modify an entry of the Database.

        Args:
            indentifier (int, string) : Indentifier by which the entry will selected. It can be of type string for all vectors and also int for ID vector
            itemName (str) : Name of Item to be modified
            newValue (str) : New value for the item
            oldValue (str) : Required for replacement
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
        self.cachedValuesChanged[itemName] = True
        #Update the Changed date of the entry
        if itemName not in ("Changed", "Opened"):
            # Exclude changed item since this would lead to inf. loop
            # Exclude opened since it is not considered a "change" to the entry
            self.modifyListEntry(identifier, "Changed", mimir.backend.helper.getTimeFormatted("Full"),
                                 byID=byID, byName=byName, byPath=byPath)

    def getCount(self, identifier, itemName, byID=False, byName=False, byPath=False):
        """
        Method for counting the number of values in a ListItem. This need to be a database operation, because the Entry is not aware of it's default value which is not counted

        Args:
            indentifier (int, string) : Indentifier by which the entry will selected. It can be of type string for all vectors and also int for ID vector
            itemName (str) : ListItem that will be counted
            byID (bool) : Switch for using the ID vector
            byName (bool) : Switch for using the Name vector
            byPath (bool) : Switch for using the Path vector

        Raises:
            TypeError : If not ListItem is passed for itemName

        Returns:
            count (int) : Number of values for ListItem. Excluding the defaultvalue
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
        if ((len(modEntry.getItem(itemName).value) == 1 and
             modEntry.getItem(itemName).value[0] == self.model.getDefaultValue(itemName))):
            return 0
        else:
            return len(modEntry.getItem(itemName).value)




    def updateOpened(self, identifier, byID=False, byName=False, byPath=False):
        """
        Wrapper for modifyListEntry that is supposed to be called after a file has been openend.
        For this function the byID is enable on default when none of the arguments is set to true.

        Args:
            indentifier (int, string) : Indentifier by which the entry will selected. It can be of\n
                                        type string for all vectors and also int for ID vector
            byID (bool) : Switch for using the ID vector
            byName (bool) : Switch for using the Name vector
            byPath (bool) : Switch for using the Path vector
        """
        if not byID and not byName and not byPath:
            byID = True
        self.modifyListEntry(identifier, "Opened", mimir.backend.helper.getTimeFormatted("Full"),
                             byID=byID, byName=byName, byPath=byPath)


    def query(self, itemNames, itemValues, returnIDs=False):
        """
        Query database: Will get all values for items with names itemNames and searches\n
        for all values given in the itemValues parameter. Leading ! on a value will be used as a veto.

        Args:
            itemNames (str, list) : itemNames used for the query
            itemValues (str, list) : itemValues used for the query
            returnIDs (bool) : If True function will return a list of IDs instead of entries

        Return:
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
        hitValues = []
        vetoValues = []
        for value in itemValues:
            if value.startswith("!"):
                vetoValues.append(value.replace("!", ""))
            else:
                hitValues.append(value)
        logging.debug("Processing Query with:")
        logging.debug("  hitValues: %s", hitValues)
        logging.debug("  vetoValues: %s", vetoValues)
        for entry in self.entries:
            entryValues = entry.getAllValuesbyName(itemNames, split=True)
            hit = 0
            veto = False
            for value in hitValues:
                if value in entryValues:
                    hit += 1
            for value in vetoValues:
                if value in entryValues:
                    veto = True
            addEntry = False
            # Decide if entry will be returned. Options:
            # No vetoValue and hit: Return Entry
            # No vetoValue and no hit: Not Retrun Entry
            if len(vetoValues) == 0:
                if hit == len(itemValues):
                    addEntry = True
            # Set vetoValue and No hitValue and veto: Not return Entry
            # Set vetoValue and No hitValue and not veto: Return Entry
            elif len(vetoValues) >= 1 and len(hitValues) == 0:
                if not veto:
                    addEntry = True
            # Set vetoValue and Set hitValue and veto: Not return Entry
            # Set vetoValue and Set hitValue and not veto and not hit: Not return Entry
            # Set vetoValue and Set hitValue and not veto and hit: Return Entry
            else:
                if not veto and hit == len(hitValues):
                    addEntry = True
            if addEntry:
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

    @staticmethod
    def getRandomEntry(chooseFrom, weighted=False):
        """
        Get a random entry from the database out of the ID passed in the chooseFrom variable

        Args:
            chooseFrom (list, set) : List of ID to choose a random ID from
            weighted (bool) : Weighted random function (to be implemented)
        Return:
            retID (str) : Random ID
        """
        if isinstance(chooseFrom, set):
            chooseFrom = list(chooseFrom)
        if not weighted:
            retID = random.choice(chooseFrom)
        else:
            raise NotImplementedError
        return retID

    def getRandomEntryAll(self, weighted=False):
        """
        Get a random entry from the database out of all IDs. This is just a wrapper for getRandomEntry

        Args:
            chooseFrom (list, set) : List of ID to choose a random ID from
        Returns:
            retID (str) : Random ID
        """
        return self.getRandomEntry(list(self.getAllValuebyItemName("ID")), weighted)

    def getItemsPyPath(self, fullFileName, fast=False, whitespaceMatch=True):
        """
        Function will parse the filename for values pesent in the Items defined in SecondaryDBs.
        The passed file name will be split by separators define in model. Implemented as a two stage process.
        1. Split at / and try to identify full know values
        2.

        Args:
            fullFileName (str) : Expects full file name starting from the mimir base dictRepr

        Returns:
            foundOptions (dict) : List of values that could be matched to the path by Item
        """
        foundOptions = {}
        items2Check = self._model.secondaryDBs
        values = {}
        values_orig = {}
        for item in items2Check:
            values_orig[item] = list(self.getAllValuebyItemName(item))
            values[item] = set([x.lower() for x in self.getAllValuebyItemName(item)])
            foundOptions[item] = []
        whiteSpaceMatches = {}
        if whitespaceMatch:
            #Add all values that have a whitespace with all possible sparators to list
            #so exact matches can be found
            for item in items2Check:
                origVals = list(values[item])
                for value in origVals:
                    if " " in value:
                        for sep in self._model.separators:
                            values[item].add(value.replace(" ", sep)) # Add since set
                            whiteSpaceMatches[value.replace(" ", sep)] = value
        #Remove file endings from model
        for fileType in self._model.extentions:
            if fullFileName.endswith(fileType):
                fullFileName = fullFileName.replace("."+fileType, "")
                break
        fullFileName = fullFileName.lower()
        pathElements = fullFileName.split("/")
        remUnsplitElements = copy.copy(pathElements)
        for elem in pathElements:
            for item in items2Check:
                if elem in values[item]:
                    if whitespaceMatch:
                        if elem in whiteSpaceMatches.keys():
                            foundOptions[item].append(whiteSpaceMatches[elem])
                        else:
                            foundOptions[item].append(elem)
                    else:
                        foundOptions[item].append(elem)
                    remUnsplitElements.remove(elem)
        if whitespaceMatch:
            #For partial matched this is not needed.
            for item in items2Check:
                values[item] = set([x.lower() for x in self.getAllValuebyItemName(item)])
        #Now we need to split elements with whitespace into two element to match partial matches
        partialWhiteSpaces = {}
        for item in items2Check:
            newValueList = []
            for value in values[item]:
                if " " in value:
                    splitValues = value.split(" ")
                    newValueList += splitValues
                    for val in splitValues:
                        if not val in partialWhiteSpaces.keys():
                            partialWhiteSpaces[val] = [value]
                        else:
                            partialWhiteSpaces[val].append(value)
                else:
                    newValueList.append(value)
            values[item] = set(newValueList)
        remSplitElements = []
        for elem in remUnsplitElements:
            remSplitElements = list(self.splitStr(elem))
        if not fast:
            for element in remSplitElements:
                for item in items2Check:
                    for value in values[item]:
                        #If a single character is in whitespace name it will be skipped.
                        if len(value) == 1:
                            continue
                        if value in element:
                            if value in partialWhiteSpaces.keys():
                                foundOptions[item] += partialWhiteSpaces[value]
                                logging.debug("Adding %s for %s because %s in %s",
                                              partialWhiteSpaces[value],
                                              item, value, element)
                            else:
                                foundOptions[item].append(value)
                                logging.debug("Adding %s for %s because %s in %s",
                                              value, item, value, element)

        #Replace the lowercase versions of the options with the original case sensitive ones
        for item in items2Check:
            for ioption, option in enumerate(foundOptions[item]):
                for iorigOption, origOption in enumerate(values_orig[item]):
                    if option == origOption.lower():
                        foundOptions[item][ioption] = values_orig[item][iorigOption]
        for item in items2Check:
            foundOptions[item] = set(foundOptions[item])
        return foundOptions

    def splitStr(self, inputStr):
        """
        Splits a passed sting by all separators defined in the model

        Args:
            inputStr (str) : Some string

        Returns:
            foundElements (set) : Set of all elements possible by splitting
        """
        separateBy = self._model.separators
        foundElements = [inputStr]
        for separator in separateBy:
            foundElements = self.splitBySep(separator, foundElements)

        return set(foundElements)

    @staticmethod
    def splitBySep(separator, elementList):
        """ Helper function to make splitStr nicer """
        retList = []
        for elem in elementList:
            retList += elem.split(separator)

        return retList

class Model:
    """
    Database model

    Args:
        config : Config file for the model
    Attributes:
        filename : Path to the model json
        modelName : name of the model
        modelDesc : Description of the model
        extentions : File extentions that are used as criterion for searching files
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
        self.separators = modelDict["General"]["Separators"]
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

        self.pluginDefinitions = []
        self.pluginMap = {}
        for item in self._listitems:
            thisPlugIn = self._listitems[item]["plugin"]
            if thisPlugIn != "":
                self.pluginDefinitions.append(thisPlugIn)
                if not thisPlugIn in self.pluginMap.keys():
                    self.pluginMap[thisPlugIn] = item
                else:
                    raise RuntimeError("There should only be on Item with any given plugin")
        for item in self._items:
            thisPlugIn = self._items[item]["plugin"]
            if  thisPlugIn != "":
                self.pluginDefinitions.append(thisPlugIn)
                if not thisPlugIn in self.pluginMap.keys():
                    self.pluginMap[thisPlugIn] = item
                else:
                    raise RuntimeError("There should only be on Item with any given plugin")
        self.pluginDefinitions = set(self.pluginDefinitions)





        #TODO Check if required items are in model

    def updateModel(self):
        """
        Function for updating the model

        TODO: Will beused if one wants to change the model of the database. If called a new model .json will be loaded and the changes will be propagated **savely** to the databse model
        """
        pass

    def getDefaultValue(self, itemName):
        """ Returns the default item name of the modlue """
        if itemName in self._items.keys():
            defVal = self._items[itemName]["default"][0]
        elif itemName in self._listitems.keys():
            defVal = self._listitems[itemName]["default"]
        else:
            raise KeyError
        if isinstance(defVal, list):
            return defVal[0]
        elif isinstance(defVal, str):
            return defVal
        else:
            raise TypeError

    def getItemType(self, itemName):
        """ Returns the default item name of the modlue """
        if itemName in self._items.keys():
            return self._items[itemName]["itemType"]
        elif itemName in self._listitems.keys():
            return self._listitems[itemName]["itemType"]
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
