import logging
import json
from glob import glob

from backend.entry import DataBaseEntry
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
    """
    def __init__(self,root, status, modelConf):
        logging.info("Initializing DataBase")
        self.model = Model(modelConf)
        self.databaseRoot = root
        self.entries = []
        self.entrydict = {}
        maxID = 0
        if status == "new":
            #New database always runs a search of the filesystem starting from self.root
            filesFound = self.getAllFilesMatchingModel()
            for path2file in filesFound:
                e = self.createEntry(path2file, maxID)
                self.entries.append(e)
                self.entrydict[str(maxID)] = e
                maxID += 1
        elif status == "load":
            pass
        else:
            raise RuntimeError("Unsupported status: {0}".format(status))

    def getAllFilesMatchingModel(self):
        """ 
        Returns all files matching the file extentions defined in model starting
        from database root dir. 
        Returns list with all matching file w/o database root dir
        """
        allfiles = glob(self.databaseRoot+"/**/*.*", recursive=True)

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

    def createEntry(self, path, cID):
        """ Called for each file that is found on filesystem """
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
            entryinit.append((listitem, "List", self.model.items[item]["default"]))

        return DataBaseEntry(entryinit)
    
    def __repr__(self):
        pass

    def getStats(self):
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

        #TODO Check if required items are in model
        
    def updateModel(self):
        pass
    
