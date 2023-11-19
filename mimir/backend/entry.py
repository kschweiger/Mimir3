"""
Entry Module. Includes definitons for DatabaseEnties and item of these entries
"""
import logging

logger = logging.getLogger(__name__)


class DataBaseEntry:
    """
    The Entry class describes all information stored in an database entry

    Args:
        initItems (list) : Each Item has to be a tuple of ItemName, ItemType ("Single"
                           or "List") and InitValues
    Attributes:
        names (list) : List of all item names in entry\n
        items (dict) : Dictionary with all Item/ListItem objects
    Raises:
        TypeError : If initItems is not of type list\n
        TypeError : If initItems is no list of tuples\n
        RuntimeError : If the tuple of initItems is invalid (not exactly three of type
                       str, typ, str/int/float
    """

    def __init__(self, init_items) -> None:
        if not isinstance(init_items, list):
            raise TypeError("Entry initialization need to be a list")
        for initial_item in init_items:
            if not isinstance(initial_item, tuple):
                raise TypeError(
                    "Every item in the initialization list needs to be a tuple"
                )
            else:
                if not len(initial_item) == 3:
                    raise RuntimeError(
                        "Tuple {0} has != 3 objects".format(initial_item)
                    )
                else:
                    name_, type_, value_ = initial_item
                    self.check_passed_items(name_, type_, value_)
        self.names = []
        self.items = {}
        for item_name, item_type, item_value in init_items:
            self.names.append(item_name)
            if item_type == "List":
                self.items[item_name] = ListItem(item_name, item_value)
            else:
                self.items[item_name] = Item(item_name, item_value)
        for item in self.names:
            setattr(self, item, self.items[item].value)

    def get_all_values_by_name(self, names, split=False):
        """
        Return all values matching items with name in names.
        Args:
            names (str/list) : Item names that values are returned
            split (bool) : If true values with be split by whitespace
        """
        if isinstance(names, str):
            names = [names]
        for name in names:
            if name not in self.names:
                raise KeyError("ItemName {0} not in DatabaseEntries names".format(name))

        result = []
        for name in names:
            value = self.items[name].value
            if isinstance(value, list):
                result += value
            else:
                result.append(value)

        if split:
            result_ = []
            for value in result:
                if " " in value:
                    result_ += value.split(" ")
                else:
                    result_.append(value)
            result = result_
        return set(result)

    def get_item(self, itemName):
        """Returns an item of the Database entry

        Raises:
            RuntimeError: If the passen itemName is not part of the database entry
        """
        if itemName not in self.names:
            raise RuntimeError("Entry has no item with name -- {0} --".format(itemName))
        return self.items[itemName]

    def has_item(self, itemName):
        """
        Check if a entry has an item with name itemName
        """
        return str(itemName) in self.names

    def add_item(self, newItem_name, newItem_type, newItem_value):
        """
        Add a new item to the DataBaseEntry
        """
        self.check_passed_items(newItem_name, newItem_type, newItem_value)
        if newItem_name in self.names:
            raise RuntimeError(
                "Entry already has item with name {0}".format(newItem_name)
            )
        self.names.append(newItem_name)
        if newItem_type == "List":
            self.items[newItem_name] = ListItem(newItem_name, newItem_value)
        else:
            self.items[newItem_name] = Item(newItem_name, newItem_value)

        setattr(self, newItem_name, self.items[newItem_name].value)

    def change_item_value(self, itemName, newValue):
        """
        Change value if a Item
        """
        self.check_passed_items(itemName)
        if not self.has_item(itemName):
            raise KeyError("Name {0} is not in names".format(itemName))
        if (
            not type(self.items[itemName]) == Item
        ):  # pylint: disable=unidiomatic-typecheck
            raise RuntimeError("Item {0} is not if type Item".format(itemName))
        self.items[itemName].replace(newValue)
        setattr(self, itemName, self.items[itemName].value)

    def add_item_value(self, itemName, newValue):
        """
        Add a value to a ListItem
        """
        self.check_passed_items(itemName)
        if not self.has_item(itemName):
            raise KeyError("Name {0} is not in names".format(itemName))
        if not isinstance(self.items[itemName], ListItem):
            raise RuntimeError("Item {0} is not if type ListItem".format(itemName))
        self.get_item(itemName).add(newValue)
        setattr(self, itemName, self.items[itemName].value)

    def remove_item_value(self, itemName, oldValue):
        """
        Remove a Value from a ListItem
        """
        self.check_passed_items(itemName)
        if not self.has_item(itemName):
            raise KeyError("Name {0} is not in names".format(itemName))
        if not isinstance(self.items[itemName], ListItem):
            raise RuntimeError("Item {0} is not if type ListItem".format(itemName))
        self.get_item(itemName).remove(oldValue)

    def replace_item_value(self, itemName, newValue, oldValue):
        """
        Replace value oldValue with new Value
        """
        self.check_passed_items(itemName)
        if not self.has_item(itemName):
            raise KeyError("Name {0} is not in names".format(itemName))
        if not isinstance(self.items[itemName], ListItem):
            raise RuntimeError("Item {0} is not if type ListItem".format(itemName))
        self.get_item(itemName).remove(oldValue)
        self.get_item(itemName).add(newValue)
        setattr(self, itemName, self.items[itemName].value)
        # self.removeItemValue(itemName, oldValue)
        # self.addItemValue(itemName, newValue)

    def get_dict_repr(self):
        """
        Convert Database entry to a dictionary representation
        """
        dictRepr = {}
        for name in self.names:
            dictRepr[name] = {}
            if isinstance(self.items[name], ListItem):
                dictRepr[name]["type"] = "List"
            else:
                dictRepr[name]["type"] = "Single"
            dictRepr[name]["value"] = self.items[name].value
        return dictRepr

    def __eq__(self, other):
        """
        Implementation of equalitiy relation for DataBaseEntry class
        """
        if isinstance(other, self.__class__):
            if self.names != other.names:
                return False
            for item in self.items:
                if self.items[item].getValue() != other.items[item].getValue():
                    return False
            return True
        else:
            return NotImplemented

    def __str__(self) -> str:
        repres = "=========================\n"
        for item in self.items:
            repres += "{0} | {1}\n".format(item, self.items[item].value)
        repres += "=========================\n"
        return repres

    @staticmethod
    def check_passed_items(passedName=None, passedType=None, passedValue=None):
        """
        Helper function for checking items passed to DataBaseEntry and raising
        exceptions
        """
        if not isinstance(passedName, str) and passedName is not None:
            msg = "New name {0} is type {1} not string".format(
                passedName, type(passedName)
            )
            raise TypeError(msg)
        if passedType not in ["Single", "List"] and passedType is not None:
            msg = "New item {0} has ivalid type: {1}".format(passedName, passedType)
            raise RuntimeError(msg)
        if not isinstance(passedValue, (str, list)) and passedValue is not None:
            msg = "New name {0} of type {1} has invalid value type {2}".format(
                passedName, passedType, type(passedValue)
            )
            raise TypeError(msg)


class Item:
    """
    Entry that contains a list of specs

    Args:
        name (str) : Name of the Item\n
        values (str) : Initial value of the item
    Attributes:
        name (str) : This is the name of the Item
    """

    def __init__(self, name, value) -> None:
        self.name = name
        self.value = value

    def replace(self, newValue):
        """
        Replace value of Item

        Args:
            newValue (str) : Value that is save in value member
        """
        self.value = newValue

    def get_value(self):
        """Returns the value of the entry"""
        return self.value

    def __repr__(self) -> str:
        return "{0} : {1}".format(self.name, self.value)  # pragma: no cover


class ListItem(Item):
    """
    Entry that contains a list of specs

    Args:
        name (str) : Name of the Item\n
        values (list, str) : Initial values of the item
    Attributes:
        name (str) : This is the name of the ListItem\n
        value (str or list) : Here are all value of the ListItem are saved

    Raises:
        TypError: Raises error when valies is not str or list
    """

    def __init__(self, name, values) -> None:
        super().__init__(name, None)
        if not isinstance(values, (str, list)):
            raise TypeError
        if isinstance(values, str):
            values = [values]
        self.value = values

    def add(self, val_2_add):
        """
        Add a value to the list of values in ListItem

        Args:
            val2Add (str or list) : Value or values to be added to

        Returns:
            bool : Is sucessful
        """
        if not isinstance(val_2_add, (str, list)):
            raise TypeError("Value {0} is not str or list".format(val_2_add))

        if isinstance(val_2_add, str):
            val_2_add = [val_2_add]

        unique_elem = []
        for new_elem in val_2_add:
            if new_elem not in self.value:
                unique_elem.append(new_elem)

        if not unique_elem:  # apperently this is very pythonic
            return False
        else:
            self.value = self.value + unique_elem
            return True

    def remove(self, to_remove):
        """
        Removes a value for the ListItem

        Args:
            toRemove (str, int) : Value or index to be removed

        Raises:
            TypError : If toRemove is not str or int\n
            IndexError : If index out of range\n
            ValueError : If value not in value list
        """
        if not isinstance(to_remove, (str, int)):
            raise TypeError
        # Remove by Value
        if isinstance(to_remove, str):
            if to_remove not in self.value:
                raise ValueError
            new_vals = []
            for val in self.value:
                if val != to_remove:
                    new_vals.append(val)
            # The python remove method for some reaseon also removes the
            # database.model._listitems[itemName]["default"] entry.. ¯\_(ツ)_/¯
            # self.value.remove(toRemove)
            self.value = new_vals
        if isinstance(to_remove, int):
            if to_remove > len(self.value) - 1:
                raise IndexError
            self.value.pop(to_remove)
