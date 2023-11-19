"""
Toplevel Database class for the Mimir database
"""
import copy
import json
import logging
import os
import random
from collections import OrderedDict
from glob import glob
from shutil import copy2
from typing import List, Set, Union

import mimir.backend.helper
import mimir.backend.plugin
from mimir.backend.entry import DataBaseEntry, Item, ListItem
from mimir.backend.enums import RandomWeightingMethod

logger = logging.getLogger(__name__)


class DataBase:
    """
    Database class that contains entries which are organized by an unique ID. The class
    contains methods for operating on the Database (save, load, queries, random entries)
    and modifing/reading/removing Entries. When a new database is created, a root
    directory (which contains all files) and a model are required. The Model can be
    created with makeModelDefinition.py and modified for specific needs. During
    initialization a .mimir directory will be created in the passed root directory.
    There the database and all affiliated files (backup, secondary databases) will be
    saved. The model passed in this process will alse be saved there for future
    reference.

    Args:
        root (str) : Base path of the database. This can change between different
                     session for example if the data base is on a removable drive
        status (str) : Initializes a new Database or loads an existing database
                       in root dir
        model (str) : Path to the model used for database initialization

    Raises:
        RuntimeError : Raised if .mimir folder already existis and a new database is
                       being created
        RuntimeError : Raised if a database is being loaded from a folder that has no
                       initialized database
        RuntimeError : Raised for invalid status argument

    Attributes:
        maxID (int) : Highes ID in the Database
        databaseRoot (str) : Points to the root of the database
        mimirdir (str) : Points to the .mimir dir of the DB
        savepath (str) : Points to the path where the database is saved
        entries (list) : List of all Entry Object in the database
        entrydict (dict) : Dict of all entries with ids as key
        _model (Model) : General information of the database model
        isdummy (bool) : Flag used for dummy databases
                         --> Currently only disables saveing
        cachedValue (dict - list) : Saved all present Values for item (key)
        valuesChanged (dict - bool) : Flag if cachedValues are still valid
    """

    def __init__(self, root, status, model_conf=None, dummy=False) -> None:
        logger.info("Initializing DataBase")
        self.databaseRoot = root
        self.entries = []
        self.entrydict = {}
        self.mimirdir = root + "/.mimir"
        self.savepath = root + "/.mimir/mainDB.json"
        self.maxID = 0
        self.isdummy = False
        self.cachedValues = {}
        self.cachedValuesChanged = {}

        self.last_executed_ids = mimir.backend.helper.IdQueue(100)

        if status == "new":
            self._model = Model(model_conf)
            self.init_caching()  # initialize cache so self.createEntry works
            if os.path.exists(self.mimirdir) and not dummy:
                raise RuntimeError(
                    ".mimir directory exiting in ROOT dir. Currently not supported!"
                )
            elif dummy:
                logger.warning("Initializing Database as dummy - Disabling saving")
                self.isdummy = True
            else:
                logger.info("Creating .mimir folder in %s", root)
                os.makedirs(self.mimirdir)
                logger.debug("Saving model in .mimir dir")
                with open(self.mimirdir + "/model.json", "w") as outfile:
                    json.dump(
                        self._model.initDict,
                        outfile,
                        sort_keys=True,
                        indent=4,
                        separators=(",", ": "),
                    )
            # New database always runs a search of the filesystem starting from root
            files_found = self.get_all_files_matching_model()
            for path2file in files_found:
                logger.debug("Adding file %s", path2file)
                self.create_new_entry(path2file, self.maxID, skip_caching=True)
                self.maxID += 1
            self.maxID = self.maxID - 1
        elif status == "load":
            if not os.path.exists(self.mimirdir) and not dummy:
                raise RuntimeError("No .mimir dir existant in {0}".format(root))
            if dummy:
                logger.warning("Loading Database from %s as dummy", root)
                self.isdummy = True
            if model_conf is None:
                self._model = Model(self.mimirdir + "/model.json")
            else:
                self._model = Model(model_conf)
            self.load_main()

        else:
            raise RuntimeError("Unsupported status: {0}".format(status))

        self.init_caching()  # Set intiial cache with new entries

    def init_caching(self):
        for item in self.model.allItems:
            self.cachedValuesChanged[item] = True
            self.cachedValues[item] = self.get_all_value_by_item_name(item)

    @property
    def model(self):
        """Returns the model variable"""
        return self._model

    def get_all_files_matching_model(self, start_dir="") -> list[str]:
        """
        Returns all files matching the file extentions defined in model starting
        from database root dir.
        Returns list with all matching file w/o database root dir
        """
        if not start_dir.endswith("/") and start_dir != "":
            start_dir = start_dir + "/"
        allfiles = glob(self.databaseRoot + "/" + start_dir + "**/*.*", recursive=True)
        logger.debug("All files from glob: %s", len(allfiles))
        matchingfiles = []
        matchingfiles_full = []
        for f in allfiles:
            for ext in self.model.extentions:
                if f.endswith(ext):
                    matchingfiles.append(f.replace(self.databaseRoot + "/", ""))
                    logger.debug("Found file %s", f)
                    matchingfiles_full.append(f)
                    continue
        if len(allfiles) > len(matchingfiles_full):
            for f in set(allfiles).difference(set(matchingfiles_full)):
                logger.debug("Removed file %s", f)
        logger.debug("Matching files: %s", len(matchingfiles))
        return matchingfiles

    def create_new_entry(self, path, c_id, skip_caching=False):
        """Create an entry for a file with path and ID.
        Called for each file that is found on filesystem
        Args:
            path (str) : Path to file added to DB on filesystem\n
            cID (int) : ID that is used for this entry

        Return:
            new DataBaseEntry object
        """
        logger.info("Initializing file with path: %s", path)
        filename = path.split("/")[-1]
        for ext in self.model.extentions:
            if filename.endswith(ext):
                filename = filename.replace("." + ext, "")
        logger.info("Initializing file with name: %s", filename)
        entryinit = {}
        for item in self.model.items:
            if item == "Path":
                entryinit["Path"] = ("Single", path)
            elif item == "ID":
                entryinit["ID"] = ("Single", str(c_id))
            elif item == "Name":
                entryinit["Name"] = ("Single", filename)
            elif item == "Added":
                entryinit["Added"] = (
                    "Single",
                    mimir.backend.helper.getTimeFormatted("Full"),
                )
            else:
                entryinit[item] = ("Single", self.model.items[item]["default"])
        for listitem in self.model.listitems:
            entryinit[listitem] = ("List", self.model.listitems[listitem]["default"])

        # If items with for plugins are degined run the pluging functions
        if self.model.pluginDefinitions:
            plugin_values = mimir.backend.plugin.getPluginValues(
                self.databaseRoot + "/" + path, self.model.pluginDefinitions
            )
            for plugin in plugin_values:
                e_type, e_value = entryinit[self.model.pluginMap[plugin]]
                entryinit[self.model.pluginMap[plugin]] = (
                    e_type,
                    plugin_values[plugin],
                )

        _entryinit = []
        for entry in entryinit:
            _entryinit.append((entry, entryinit[entry][0], entryinit[entry][1]))

        e = DataBaseEntry(_entryinit)
        if not skip_caching:
            self.cachedValuesChanged["ID"] = True
        self.entries.append(e)
        self.entrydict[str(c_id)] = e
        return e

    def save_main(self):
        """
        Save the main database (json file with all entries)
        as mainDB.json in the .mimir folder of the DB.
        Before saving it will create a backup of the current
        state. Backups are save for days. Will overwrite if already
        present.
        """
        if self.isdummy:
            logger.error("Database isDummy - Saving disabled")
            return False
        status = False
        # Copy current DBfile and save it as backup
        if os.path.exists(self.savepath):
            logger.debug("Making backup")
            backup_date = mimir.backend.helper.getTimeFormatted(
                "Date", "-", inverted=True
            )
            copy2(
                self.savepath,
                self.savepath.replace(".json", ".{0}.backup".format(backup_date)),
            )
        # Convert database to dict so json save can be used
        output = OrderedDict()
        for entry in self.entries:
            output.update({entry.Path: entry.getDictRepr()})
        logger.debug("Saving database at %s", self.savepath)
        with open(self.savepath, "w") as outfile:
            json.dump(output, outfile, indent=4)
            status = True
        return status

    def load_main(self):
        """Load the main DB from the .mimir folder"""
        with open(self.savepath) as save_file:
            saved_db = json.load(save_file)
        for filepath in saved_db:
            saved_entry = saved_db[filepath]
            entryinit = []
            for item in saved_entry:
                if not (item in self.model.items or item in self.model.listitems):
                    logger.warning(
                        "Found item in saved json not in model. Item will be ignored"
                    )
                    logger.warning(
                        "Currently this will result in loss of data when saving"
                    )
                    continue
                entryinit.append(
                    (item, saved_entry[item]["type"], saved_entry[item]["value"])
                )
            e = DataBaseEntry(entryinit)
            self.entries.append(e)
            self.maxID += 1
            self.entrydict[saved_entry["ID"]["value"]] = e
        self.maxID -= 1

    def find_new_files(self, start_dir=""):
        """
        Find new files in starting from the root directory.

        Args:
            startdir (str) : Specifiy a subdirectory to start from
        """
        new_files = []
        allfiles = self.get_all_files_matching_model(start_dir)
        ids = []
        existing_files = []
        missing_ids = []
        for entry in self.entries:
            existing_files.append(entry.Path)
            ids.append(int(entry.ID))

        logger.debug(
            "Found %s files in FS. Entries in database: %s",
            len(allfiles),
            len(existing_files),
        )
        # Find all ids missing so new files can be inserted
        ids = set(ids)
        for i in range(len(self.entries)):
            if i not in ids:
                missing_ids.append(i)

        existing_files = set(existing_files)
        for file_ in allfiles:
            if file_ not in existing_files:
                new_files.append(file_)

        toret = new_files
        pairs = []
        # Insert/Append new files
        for new_file in new_files:
            if len(missing_ids) > 0:
                cid = missing_ids[0]
                missing_ids = missing_ids[1:]
            else:
                self.maxID += 1
                cid = self.maxID
            self.create_new_entry(new_file, cid)
            pairs.append((new_file, cid))

        return toret, pairs

    def check_changed_paths(self, start_dir=""):
        """
        Function that finds if files changed their path
        """
        existing_files = []
        existing_files_names = []
        allfiles = self.get_all_files_matching_model(start_dir)
        nameids = {}
        for entry in self.entries:
            existing_files.append(entry.Path)
            existing_files_names.append(entry.Path.split("/")[-1])
            nameids[entry.Path.split("/")[-1]] = entry.ID

        logger.debug(
            "Found %s files in FS. Entries in database: %s",
            len(allfiles),
            len(existing_files),
        )

        changed_files = []
        changed_file_paths = {}
        for file_ in allfiles:
            if file_ not in existing_files:
                changed_files.append(file_)
                changed_file_paths[file_.split("/")[-1]] = file_

        updated_files = []
        for file_ in changed_files:
            name_ = file_.split("/")[-1]
            if name_ in existing_files_names:
                this_id = nameids[name_]
                this_entry = self.get_entry_by_item_name("ID", this_id)[0]
                old_path = this_entry.Path
                logger.info(
                    "Updated path of entry %s to %s", this_id, changed_file_paths[name_]
                )
                this_entry.change_item_value("Path", changed_file_paths[name_])
                updated_files.append((this_id, old_path, changed_file_paths[name_]))

        return updated_files

    def get_missing_files(self, start_dir=""):
        allfiles = self.get_all_files_matching_model(start_dir)
        nameids = {}
        existing_files = []
        existing_files_names = []
        for entry in self.entries:
            existing_files.append(entry.Path)
            existing_files_names.append(entry.Path.split("/")[-1])
            nameids[entry.Path.split("/")[-1]] = entry.ID

        logger.debug(
            "Found %s files in FS. Entries in database: %s",
            len(allfiles),
            len(existing_files),
        )

        missing_files = []
        if len(allfiles) != len(existing_files):
            for file_ in existing_files:
                if file_ not in allfiles:
                    missing_files.append(file_)

        return missing_files

    def check_missing_files(self, start_dir="", mod_id=True):
        """
        This function compares the files on the filesystem (from the db rootdir) to the
        existing path in the database. If one is missing, the Entry is deleted and the
        last entry (with the highest ID) will be moved in its place.

        NOTE: This does not ask for permission! But the backup funcitonality on saving
        should help with accidents....
        """
        missing_files = self.get_missing_files(start_dir)
        logger.debug("Missing files: %s", missing_files)
        id_changes = []
        if missing_files:
            for missing_file in missing_files:
                missing_id = (
                    self.get_entry_by_item_name("Path", missing_file)[0]
                    .get_item("ID")
                    .value
                )
                self.remove(missing_id, by_id=True)
                if mod_id:
                    self.modify_single_entry(self.maxID, "ID", missing_id, by_id=True)
                    id_changes.append((self.maxID, missing_id))
                    logger.info("Change ID of entry %s to %s", self.maxID, missing_id)
                    self.maxID -= 1

        return id_changes

    def reset_entry_ids(self):
        i_id = 0
        for entry_id in [e.ID for e in self.entries]:
            logger.debug("Change ID of entry %s to %s", entry_id, i_id)
            self.modify_single_entry(entry_id, "ID", str(i_id), by_id=True)
            i_id += 1

    def get_all_value_by_item_name(self, item_name):
        """Return a set of all values of name itemName"""
        if item_name not in self.model.allItems:
            raise KeyError("Arg {0} not in model items".format(item_name))
        if self.cachedValuesChanged[item_name]:
            self.cache_all_value_by_item_name(item_name)
        return self.cachedValues[item_name]

    def cache_all_value_by_item_name(self, item_name):
        """
        Function for filling the cached Value objects of the database
        """
        retlist = []
        for entry in self.entries:
            to_add = getattr(entry, item_name)
            if isinstance(to_add, list):
                retlist += to_add
            else:
                retlist.append(to_add)
        self.cachedValuesChanged[item_name] = False
        self.cachedValues[item_name] = set(retlist)

    def get_sorted_ids(self, sort_by, reverse_order=True):
        """
        Returns a list of database ids sorted by itemName sortBy.

        Args:
            sortBy (str) : itemName that will be used for sorting. The exact sorting \n
                           depends on the type set in the model (str, int, datetime)
        Return:
            sortedEntries (list[str]) : List of all id sorted by sortBy newValue

        Raises:
            KeyError : Will be raise if sortBy is no valid itemName for the model
        """
        if sort_by not in self.model.allItems:
            raise KeyError("Arg {0} not in model items".format(sort_by))
        all_ids = self.get_all_value_by_item_name("ID")
        map_id_sortby = {}
        for this_id in all_ids:
            map_id_sortby[this_id] = (
                self.get_entry_by_id(this_id).get_item(sort_by).value
            )
        item_type = self.model.get_item_type(sort_by)
        # If sortBy is a ListItem we need to figure out the value to sort by
        if sort_by in self.model.listitems:
            for this_id in map_id_sortby:
                if item_type == "datetime":
                    map_id_sortby[this_id] = mimir.backend.helper.sortDateTime(
                        map_id_sortby[this_id]
                    )[0]
                else:
                    # TODO: Think about a way to sort ListItems of type str/int
                    raise NotImplementedError(
                        "Sorting for none datetime listitems not implemented"
                    )

        pairs = []
        for this_id in map_id_sortby:
            pairs.append((this_id, map_id_sortby[this_id]))

        if item_type == "datetime":
            sorted_pairs = sorted(
                pairs,
                key=lambda x: (
                    mimir.backend.helper.convertToDateTime(x[1]),
                    -int(x[0]) if reverse_order else int(x[0]),
                ),
                reverse=reverse_order,
            )
        elif item_type == "int":
            sorted_pairs = sorted(
                pairs,
                key=lambda x: (int(x[1]), -int(x[0]) if reverse_order else int(x[0])),
                reverse=reverse_order,
            )
        elif item_type == "float":
            sorted_pairs = sorted(
                pairs,
                key=lambda x: (float(x[1]), -int(x[0]) if reverse_order else int(x[0])),
                reverse=reverse_order,
            )
        else:
            sorted_pairs = sorted(
                pairs,
                key=lambda x: (x[1], -int(x[0]) if reverse_order else int(x[0])),
                reverse=reverse_order,
            )

        return [x[0] for x in sorted_pairs]

    def get_entry_by_item_name(
        self, item_name: str, item_value: str
    ) -> List[DataBaseEntry]:
        """Get all entries that have value itemValue in Item with itemName"""
        if item_name not in self.model.allItems:
            raise KeyError("Arg {0} not in model items".format(item_name))
        machting_entries = []
        for entry in self.entries:
            item = entry.getItem(item_name)
            if isinstance(item, Item):
                if item.value == item_value:
                    machting_entries.append(entry)
                    if item_name in "ID":
                        break
            else:
                if item_value in item.value:
                    machting_entries.append(entry)
        return machting_entries

    def remove(self, identifier, by_id=False, by_name=False, by_path=False):
        """
        Remove a entry from the databse by specifing indentifier. Indentifier can be ID,
        Name or Path (vector). When calling the function only one can be set to True
        otherwise a exception will be raised

        Args:
            identifier (int, string) : Indentifier by with the entry will be removed.
                                       For can be of type string for all vectors and
                                       also int for ID vector
            byID (bool) : Switch for using the ID vector
            byName (bool) : Switch for using the Name vector
            byPath (bool) : Switch for using the Path vector

        Raises:
            RuntimeError : If more than one vector or no vector was turned on
            TypeError : If indentifier has a not supported type
            KeyError : If indentifier is no valid Name, Path or ID
        """
        # Exceptions:
        self.check_mod_vector(identifier, by_id, by_name, by_path)

        # Now the actual function
        remove_type: None | str = None
        if by_id:
            remove_type = "ID"
        if by_name:
            remove_type = "Name"
        if by_path:
            remove_type = "Path"
        if remove_type is None:
            raise RuntimeError
        entry2remove = self.get_entry_by_item_name(remove_type, str(identifier))[0]
        self.entries.remove(entry2remove)
        self.entrydict.pop(entry2remove.Path, None)
        logger.debug("Removed entry:")
        for line in str(entry2remove).split("\n"):
            logger.debug("  %s", line)

    def modify_single_entry(
        self,
        identifier,
        item_name,
        new_value,
        by_id=False,
        by_name=False,
        by_path=False,
    ):
        """
        Modify an entry of the Database

        Args:
            identifier (int, string) : Indentifier by which the entry will selected.
                                        It can be of\n type string for all vectors and
                                        also int for ID vector
            itemName (str) : Name of Item to be modified
            newValue (str) : New value for the item
            byID (bool) : Switch for using the ID vector
            byName (bool) : Switch for using the Name vector
            byPath (bool) : Switch for using the Path vector
        """
        self.check_mod_vector(identifier, by_id, by_name, by_path)
        id_type: None | str = None
        if by_id:
            id_type = "ID"
        if by_name:
            id_type = "Name"
        if by_path:
            id_type = "Path"
        if id_type is None:
            raise RuntimeError
        mod_entry = self.get_entry_by_item_name(id_type, str(identifier))[0]
        if (
            not type(mod_entry.items[item_name]) == Item
        ):  # pylint: disable=unidiomatic-typecheck
            raise TypeError(
                "Called modifySingleEntry with a Entry of type {0}".format(
                    type(mod_entry.items[item_name])
                )
            )
        mod_entry.change_item_value(item_name, new_value)
        self.cachedValuesChanged[item_name] = True
        # Update the Changed date of the entry
        if (
            (by_id and item_name == "ID")
            or (by_name and item_name == "Name")
            or (by_path and item_name == "Path")
        ):
            logger.debug("Changed value not changed because item it changed by itself")
        else:
            self.modify_list_entry(
                identifier,
                "Changed",
                mimir.backend.helper.getTimeFormatted("Full"),
                by_id=by_id,
                by_name=by_name,
                by_path=by_path,
            )

    def modify_list_entry(
        self,
        identifier,
        item_name,
        new_value,
        method="Append",
        old_value=None,
        by_id=False,
        by_name=False,
        by_path=False,
    ):
        """
        Modify an entry of the Database.

        Args:
            identifier (int, string) : Indentifier by which the entry will selected.
                                        It can be of type string for all vectors and
                                        also int for ID vector
            itemName (str) : Name of Item to be modified
            newValue (str) : New value for the item
            oldValue (str) : Required for replacement
            byID (bool) : Switch for using the ID vector
            byName (bool) : Switch for using the Name vector
            byPath (bool) : Switch for using the Path vector
        """
        self.check_mod_vector(identifier, by_id, by_name, by_path)
        id_type: None | str = None
        if by_id:
            id_type = "ID"
        if by_name:
            id_type = "Name"
        if by_path:
            id_type = "Path"
        if id_type is None:
            raise RuntimeError
        mod_entry = self.get_entry_by_item_name(id_type, str(identifier))[0]
        if not isinstance(mod_entry.items[item_name], ListItem):
            raise TypeError(
                "Called modifyListEntry with a Entry of type {0}".format(
                    type(mod_entry.items[item_name])
                )
            )
        if method == "Append":
            if len(mod_entry.get_item(item_name).value) == 1 and mod_entry.get_item(
                item_name
            ).value[0] == self.model.get_default_value(item_name):
                default = self.model.get_default_value(item_name)
                mod_entry.replace_item_value(item_name, new_value, default)
            else:
                mod_entry.add_item_value(item_name, new_value)
        elif method == "Replace":
            mod_entry.replace_item_value(item_name, new_value, old_value)
        elif method == "Remove":
            mod_entry.remove_item_value(item_name, old_value)
            if len(mod_entry.get_item(item_name).value) == 0:
                mod_entry.add_item_value(
                    item_name, self.model.get_default_value(item_name)
                )
        else:
            raise NotImplementedError
        self.cachedValuesChanged[item_name] = True
        # Update the Changed date of the entry
        if item_name not in ("Changed", "Opened"):
            # Exclude changed item since this would lead to inf. loop
            # Exclude opened since it is not considered a "change" to the entry
            self.modify_list_entry(
                identifier,
                "Changed",
                mimir.backend.helper.getTimeFormatted("Full"),
                by_id=by_id,
                by_name=by_name,
                by_path=by_path,
            )

    def get_count(
        self, identifier, item_name, by_id=False, by_name=False, by_path=False
    ):
        """
        Method for counting the number of values in a ListItem. This need to be a
        database operation, because the Entry is not aware of it's default value which
        is not counted

        Args:
            identifier (int, string) : Indentifier by which the entry will selected.
                                        It can be of type string for all vectors and
                                        also int for ID vector
            itemName (str) : ListItem that will be counted
            byID (bool) : Switch for using the ID vector
            byName (bool) : Switch for using the Name vector
            byPath (bool) : Switch for using the Path vector

        Raises:
            TypeError : If not ListItem is passed for itemName

        Returns:
            count (int) : Number of values for ListItem. Excluding the defaultvalue
        """
        self.check_mod_vector(identifier, by_id, by_name, by_path)
        id_type: None | str = None
        if by_id:
            id_type = "ID"
        if by_name:
            id_type = "Name"
        if by_path:
            id_type = "Path"
        if id_type is None:
            raise RuntimeError
        mod_entry = self.get_entry_by_item_name(id_type, str(identifier))[0]
        if not isinstance(mod_entry.items[item_name], ListItem):
            raise TypeError(
                "Called modifyListEntry with a Entry of type {0}".format(
                    type(mod_entry.items[item_name])
                )
            )
        if len(mod_entry.get_item(item_name).value) == 1 and mod_entry.get_item(
            item_name
        ).value[0] == self.model.get_default_value(item_name):
            return 0
        else:
            return len(mod_entry.get_item(item_name).value)

    def update_opened(self, identifier, by_id=False, by_name=False, by_path=False):
        """
        Wrapper for modifyListEntry that is supposed to be called after a file has been
        openend. For this function the byID is enable on default when none of the
        arguments is set to true.

        Args:
            identifier (int, string) : Indentifier by which the entry will selected.
                                        It can be of type string for all vectors and
                                        also int for ID vector
            byID (bool) : Switch for using the ID vector
            byName (bool) : Switch for using the Name vector
            byPath (bool) : Switch for using the Path vector
        """
        if not by_id and not by_name and not by_path:
            by_id = True
        self.modify_list_entry(
            identifier,
            "Opened",
            mimir.backend.helper.getTimeFormatted("Full"),
            by_id=by_id,
            by_name=by_name,
            by_path=by_path,
        )

    def query(self, item_names, item_values, return_ids=False):
        """
        Query database: Will get all values for items with names itemNames and searches
        for all values given in the itemValues parameter. Leading ! on a value will be
        used as a veto.

        Args:
            itemNames (str, list) : itemNames used for the query
            itemValues (str, list) : itemValues used for the query
            returnIDs (bool) : If True function will return a list of ids instead of
                               entries

        Return:
            result (list) : list of all entries (ids) matching the query
        """
        if isinstance(item_names, str):
            item_names = [item_names]
        if isinstance(item_values, str):
            item_values = [item_values]
        for name in item_names:
            if name not in self.model.allItems:
                raise KeyError("Arg {0} not in model items".format(name))
        result = []
        hit_values = []
        veto_values = []
        for value in item_values:
            if value.startswith("!"):
                veto_values.append(value.replace("!", ""))
            else:
                hit_values.append(value)
        logger.debug("Processing Query with:")
        logger.debug("  hitValues: %s", hit_values)
        logger.debug("  vetoValues: %s", veto_values)
        for entry in self.entries:
            entry_values = entry.getAllValuesbyName(item_names, split=True)
            hit = 0
            veto = False
            for value in hit_values:
                if value in entry_values:
                    hit += 1
            for value in veto_values:
                if value in entry_values:
                    veto = True
            add_entry = False
            # Decide if entry will be returned. Options:
            # No vetoValue and hit: Return Entry
            # No vetoValue and no hit: Not Retrun Entry
            if len(veto_values) == 0:
                if hit == len(item_values):
                    add_entry = True
            # Set vetoValue and No hitValue and veto: Not return Entry
            # Set vetoValue and No hitValue and not veto: Return Entry
            elif len(veto_values) >= 1 and len(hit_values) == 0:
                if not veto:
                    add_entry = True
            # Set vetoValue and Set hitValue and veto: Not return Entry
            # Set vetoValue and Set hitValue and not veto and not hit: Not return Entry
            # Set vetoValue and Set hitValue and not veto and hit: Return Entry
            else:
                if not veto and hit == len(hit_values):
                    add_entry = True
            if add_entry:
                if return_ids:
                    result.append(entry.ID)
                else:
                    result.append(entry)
        return result

    def get_entry_by_id(self, ret_id):
        """Faster method for getting entry by ID"""
        return self.get_entry_by_item_name("ID", ret_id)[0]

    def __eq__(self, other):
        """Implementation of the equality relation"""
        if isinstance(other, self.__class__):
            if len(self.entries) != len(other.entries):
                return False
            for entry in self.entries:
                foundequivalent = False
                for otherentry in other.entries:
                    # print("comparing",entry, otherentry)
                    if entry == otherentry:
                        foundequivalent = True
                        break
                if not foundequivalent:
                    return False
            return True
        else:
            return NotImplemented

    def get_status(self):
        """Check if current status of the database is saved"""
        if not os.path.exists(self.savepath):
            logger.info("No database saved yet")
            return False
        dummy_db = DataBase(self.databaseRoot, "load", dummy=True)
        if self == dummy_db:  # pylint: disable=simplifiable-if-statement
            return True
        else:
            return False

    def check_mod_vector(self, value, by_id, by_name, by_path):
        """Common function for modification methods input chekcing"""
        n_vectors_active = 0
        for vector in [by_id, by_name, by_path]:
            if not isinstance(vector, bool):
                raise TypeError("Vectors are required to be a bool")
            if vector:
                n_vectors_active += 1
        if n_vectors_active == 0 or n_vectors_active > 1:
            raise RuntimeError
        if not isinstance(value, (str, int)) and by_id:
            raise TypeError(
                "byID vector supports str and int but value was type {0}".format(
                    type(value)
                )
            )
        if not isinstance(value, str) and (by_name or by_path):
            raise TypeError(
                "byName and byPath vector support str but value was type {0}".format(
                    type(value)
                )
            )
        if by_id:
            if str(value) not in self.get_all_value_by_item_name("ID"):
                raise IndexError("Index {0} is out of range of DB".format(value))
        else:
            if by_name:
                query = "Name"
            if by_path:
                query = "Path"
            if value not in self.get_all_value_by_item_name(query):
                print(value, self.get_all_value_by_item_name(query))
                raise KeyError("Value w/ {0} {1} not in Database".format(query, value))

    def get_random_entry(
        self,
        choose_from: Union[List[str], Set[str]],
        weighted: bool = False,
        method: RandomWeightingMethod = RandomWeightingMethod.TIMES_OPENED,
    ) -> str:
        """
        Get a random entry from the database out of the ID passed in the chooseFrom
        variable

        Args:
            choose_from (list, set) : List of ID to choose a random ID from
            weighted (bool) : Weighted random function (to be implemented)
            method (RandomWeightingMethod) : Method for the weighting
        Return: Random ID
        """
        if isinstance(choose_from, set):
            choose_from = list(choose_from)

        choose_from = [
            e for e in choose_from if not self.last_executed_ids.containes(e)
        ]

        if not weighted:
            return random.choice(choose_from)
        else:
            return self._get_weighted_random_entry(choose_from, method)

    def _get_weighted_random_entry(
        self, choose_from: List[str], method: RandomWeightingMethod
    ) -> str:
        entries = [self.get_entry_by_item_name("ID", i)[0] for i in choose_from]
        if method == RandomWeightingMethod.TIMES_OPENED:
            weights = [
                1 / (2 * len([elem for elem in entry.Opened if "|" in elem]) + 1)
                for entry in entries
            ]
            weights = [(5 if w == 1 else w) for w in weights]
            return random.choices(choose_from, weights)[0]
        else:
            raise NotImplementedError

    def get_random_rntry_all(self, weighted=False):
        """
        Get a random entry from the database out of all ids. This is just a wrapper for
        getRandomEntry

        Args:
            chooseFrom (list, set) : List of ID to choose a random ID from
        Returns:
            retID (str) : Random ID
        """
        return self.get_random_entry(
            list(self.get_all_value_by_item_name("ID")), weighted
        )

    def get_items_by_path(self, full_file_name, fast=False, whitespace_match=True):
        """
        Function will parse the filename for values pesent in the Items defined in
        SecondaryDBs. The passed file name will be split by separators define in model.
        Implemented as a two stage process.
        1. Split at / and try to identify full know values
        2.

        Args:
            fullFileName (str) : Expects full file name starting from the mimir
                                 base dictRepr

        Returns:
            foundOptions (dict) : List of values that could be matched to the path
                                  by Item
        """
        found_options = {}
        items_2_check = self._model.secondaryDBs
        values = {}
        values_orig = {}
        for item in items_2_check:
            values_orig[item] = list(self.get_all_value_by_item_name(item))
            values[item] = set(
                [x.lower() for x in self.get_all_value_by_item_name(item)]
            )
            found_options[item] = []
        whitewpace_matches = {}
        if whitespace_match:
            # Add all values that have a whitespace with all possible sparators to list
            # so exact matches can be found
            for item in items_2_check:
                orig_vals = list(values[item])
                for value in orig_vals:
                    if " " in value:
                        for sep in self._model.separators:
                            values[item].add(value.replace(" ", sep))  # Add since set
                            whitewpace_matches[value.replace(" ", sep)] = value
        # Remove file endings from model
        for file_type in self._model.extentions:
            if full_file_name.endswith(file_type):
                full_file_name = full_file_name.replace("." + file_type, "")
                break
        full_file_name = full_file_name.lower()
        path_elements = full_file_name.split("/")
        rem_unsplit_elements = copy.copy(path_elements)
        for elem in path_elements:
            for item in items_2_check:
                if elem in values[item]:
                    if whitespace_match:
                        if elem in whitewpace_matches.keys():
                            found_options[item].append(whitewpace_matches[elem])
                        else:
                            found_options[item].append(elem)
                    else:
                        found_options[item].append(elem)
                    rem_unsplit_elements.remove(elem)
        if whitespace_match:
            # For partial matched this is not needed.
            for item in items_2_check:
                values[item] = set(
                    [x.lower() for x in self.get_all_value_by_item_name(item)]
                )
        # Now we need to split elements with whitespace into
        # two element to match partial matches
        partial_whitespaces = {}
        for item in items_2_check:
            new_value_list = []
            for value in values[item]:
                if " " in value:
                    split_values = value.split(" ")
                    new_value_list += split_values
                    for val in split_values:
                        if val not in partial_whitespaces.keys():
                            partial_whitespaces[val] = [value]
                        else:
                            partial_whitespaces[val].append(value)
                else:
                    new_value_list.append(value)
            values[item] = set(new_value_list)
        rem_split_elements = []
        for elem in rem_unsplit_elements:
            rem_split_elements = list(self.split_str(elem))
        if not fast:
            for element in rem_split_elements:
                for item in items_2_check:
                    for value in values[item]:
                        # If a single character is in whitespace name
                        # it will be skipped.
                        if len(value) == 1:
                            continue
                        if value in element:
                            if value in partial_whitespaces.keys():
                                found_options[item] += partial_whitespaces[value]
                                logger.debug(
                                    "Adding %s for %s because %s in %s",
                                    partial_whitespaces[value],
                                    item,
                                    value,
                                    element,
                                )
                            else:
                                found_options[item].append(value)
                                logger.debug(
                                    "Adding %s for %s because %s in %s",
                                    value,
                                    item,
                                    value,
                                    element,
                                )

        # Replace the lowercase versions of the options with the original
        # case sensitive ones
        for item in items_2_check:
            for ioption, option in enumerate(found_options[item]):
                for i_orig_option, orig_option in enumerate(values_orig[item]):
                    if option == orig_option.lower():
                        found_options[item][ioption] = values_orig[item][i_orig_option]
        for item in items_2_check:
            found_options[item] = set(found_options[item])
        return found_options

    def split_str(self, inputStr):
        """
        Splits a passed sting by all separators defined in the model

        Args:
            inputStr (str) : Some string

        Returns:
            foundElements (set) : Set of all elements possible by splitting
        """
        separate_by = self._model.separators
        found_elements = [inputStr]
        for separator in separate_by:
            found_elements = self.split_by_eep(separator, found_elements)

        return set(found_elements)

    @staticmethod
    def split_by_eep(separator, elementList):
        """Helper function to make splitStr nicer"""
        ret_list = []
        for elem in elementList:
            ret_list += elem.split(separator)

        return ret_list


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

    def __init__(self, config) -> None:
        logger.debug("Loading model from %s", config)
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
                logger.debug("Found item %s in model", key)
                newitem = {}
                for itemKey in modelDict[key]:
                    if itemKey != "Type":
                        newitem[itemKey] = modelDict[key][itemKey]
                if modelDict[key]["Type"] == "ListItem":
                    self._listitems.update({key: newitem})
                elif modelDict[key]["Type"] == "Item":
                    self._items.update({key: newitem})
                else:
                    raise TypeError("Invalid item type in model definition")
        self.allItems = set(self._items.keys()).union(set(self._listitems.keys()))

        self.pluginDefinitions = []
        self.pluginMap = {}
        for item in self._listitems:
            thisPlugIn = self._listitems[item]["plugin"]
            if thisPlugIn != "":
                self.pluginDefinitions.append(thisPlugIn)
                if thisPlugIn not in self.pluginMap.keys():
                    self.pluginMap[thisPlugIn] = item
                else:
                    raise RuntimeError(
                        "There should only be on Item with any given plugin"
                    )
        for item in self._items:
            thisPlugIn = self._items[item]["plugin"]
            if thisPlugIn != "":
                self.pluginDefinitions.append(thisPlugIn)
                if thisPlugIn not in self.pluginMap.keys():
                    self.pluginMap[thisPlugIn] = item
                else:
                    raise RuntimeError(
                        "There should only be on Item with any given plugin"
                    )
        self.pluginDefinitions = set(self.pluginDefinitions)

        # TODO Check if required items are in model

    def update_model(self):
        """
        Function for updating the model

        TODO: Will beused if one wants to change the model of the database.
        TODO: If called a new model .json will be loaded and the changes will be
        TODO: propagated **savely** to the databse model
        """
        pass

    def get_default_value(self, itemName):
        """Returns the default item name of the modlue"""
        if itemName in self._items.keys():
            defVal = self._items[itemName]["default"]
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

    def get_item_type(self, itemName):
        """Returns the default item name of the modlue"""
        if itemName in self._items.keys():
            return self._items[itemName]["itemType"]
        elif itemName in self._listitems.keys():
            return self._listitems[itemName]["itemType"]
        else:
            raise KeyError

    @property
    def items(self):
        """Retruns all item demfinitons in the model"""
        return self._items

    @property
    def listitems(self):
        """Retruns all listitem demfinitons in the model"""
        return self._listitems
