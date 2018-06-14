'''
Entry Module. Includes definitons for DatabaseEnties and item of these entries
'''
class DataBaseEntry(object):
    '''
    The Entry class describes all information stored in an database entry

    Args:
        initItems (list) : Each Item has to be a tuple of ItemName, ItemType ("Single" or "List") and InitValues
    Attributes:
        names (list) : List of all item names in entry
        items (dict) : Dictionary with all Item/ListItem objects
    Raises:
        TypeError : If initItems is not of type list
        TypeError : If initItems is no list of tuples
        RuntimeError : If the tuple of initItems is invalid (not exactly three of type str, typ, str/int/float
    '''
    def __init__(self, initItems):
        if not isinstance(initItems, list):
            raise TypeError("Entry initialization need to be a list")
        for initialItem in initItems:
            if not isinstance(initialItem, tuple):
                raise TypeError("Every item in the initialization list needs to be a tuple")
            else:
                if not len(initialItem) == 3:
                    raise RuntimeError("Tuple {0} has != 3 objects".format(initialItem))
                else:
                    name_, type_, value_ = initialItem
                    self.checkPassedItems(name_, type_, value_)
        self.names = []
        self.items = {}
        for itemName, itemType, itemValue in initItems:
            self.names.append(itemName)
            if itemType == "List":
                self.items[itemName] = ListItem(itemName, itemValue)
            else:
                self.items[itemName] = Item(itemName, itemValue)

    def getItem(self, itemName):
        """Returns an item of the Database entry

        Raises:
            RuntimeError: If the passen itemName is not part of the database entry
        """
        if itemName not in self.names:
            raise RuntimeError("Entry has no item with name -- {0} --".format(itemName))
        return self.items[itemName]

    def hasItem(self, itemName):
        """
        Check if a entry has an item with name itemName
        """
        return str(itemName) in self.names

    def addItem(self, newItem_name, newItem_type, newItem_value):
        """
        Add a new item to the DataBaseEntry
        """
        self.checkPassedItems(newItem_name, newItem_type, newItem_value)
        if newItem_name in self.names:
            raise RuntimeError("Entry already has item with name {0}".format(newItem_name))
        self.names.append(newItem_name)
        if newItem_type == "List":
            self.items[newItem_name] = ListItem(newItem_name, newItem_value)
        else:
            self.items[newItem_name] = Item(newItem_name, newItem_value)


    def changeItemValue(self, itemName, newValue):
        """
        Change value if a Item
        """
        self.checkPassedItems(itemName)
        if not self.hasItem(itemName):
            raise KeyError("Name {0} is not in names".format(itemName))
        if type(self.items[itemName]) is not Item:
            raise RuntimeError("Item {0} is not if type Item".format(itemName))
        self.items[itemName].replace(newValue)

    def addItemValue(self, itemName, newValue):
        """
        Add a value to a ListItem
        """
        self.checkPassedItems(itemName)
        if not self.hasItem(itemName):
            raise KeyError("Name {0} is not in names".format(itemName))
        if type(self.items[itemName]) is not ListItem:
            raise RuntimeError("Item {0} is not if type ListItem".format(itemName))
        self.getItem(itemName).add(newValue)

    def removeItemValue(self, itemName, oldValue):
        """
        Remove a Value from a ListItem
        """
        self.checkPassedItems(itemName)
        if not self.hasItem(itemName):
            raise KeyError("Name {0} is not in names".format(itemName))
        if type(self.items[itemName]) is not ListItem:
            raise RuntimeError("Item {0} is not if type ListItem".format(itemName))
        self.getItem(itemName).remove(oldValue)

    def replaceItemValue(self, itemName, newValue, oldValue):
        """
        Replace value oldValue with new Value
        """
        self.removeItemValue(itemName, oldValue)
        self.addItemValue(itemName, newValue)

    @staticmethod
    def checkPassedItems(passedName=None, passedType=None, passedValue=None):
        """
        Helper function for checking items passed to DataBaseEntry and raising exceptions
        """
        if not isinstance(passedName, str) and passedName is not None:
            msg = "New name {0} is type {1} not string".format(passedName, type(passedName))
            raise TypeError(msg)
        if not passedType in ["Single", "List"] and passedType is not None:
            msg = "New item {0} has ivalid type: {1}".format(passedName, passedType)
            raise RuntimeError(msg)
        if not isinstance(passedValue, (str, list))  and passedValue is not None:
            msg = "New name {0} of type {1} has invalid value type {2}".format(passedName, passedType, type(passedValue))
            raise TypeError(msg)

class Item(object):
    '''
    Entry that contains a list of specs

    Args:
        name (str) : Name of the Item
        values (str) : Initial value of the item
    Attributes:
        name (str) : This is the name of the Item
    '''
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def replace(self, newValue):
        """
        Replace value of Item

        Args:
            newValue (str) : Value that is save in value member
        """
        self.value = newValue

    def __repr__(self):
        return "{0} : {1}".format(self.name, self.value) #pragma: no cover

class ListItem(Item):
    '''
    Entry that contains a list of specs

    Args:
        name (str) : Name of the Item
        values (list, str) : Initial values of the item
    Attributes:
        name (str) : This is the name of the ListItem
        value (str or list) : Here are all value of the ListItem are saved

    Raises:
        TypError: Raises error when valies is not str or list
    '''
    def __init__(self, name, values):
        super().__init__(name, None)
        if not isinstance(values, (str, list)):
            raise TypeError
        if isinstance(values, str):
            values = [values]
        self.value = values

    def add(self, val2Add):
        """
        Add a value to the list of values in ListItem

        Args:
            val2Add (str or list) : Value or values to be added to

        Returns:
            bool : Is sucessful
        """
        if not isinstance(val2Add, (str, list)):
            raise TypeError("Value {0} is not str or list".format(val2Add))

        if isinstance(val2Add, str):
            val2Add = [val2Add]

        uniqueElem = []
        for newElem in val2Add:
            if newElem not in self.value:
                uniqueElem.append(newElem)

        if not uniqueElem: #apperently this is very pythonic
            return False
        else:
            self.value = self.value + uniqueElem
            return True

    def remove(self, toRemove):
        """
        Removes a value for the ListItem

        Args:
            toRemove (str, int) : Value or index to be removed

        Raises:
            TypError : If toRemove is not str or int
            IndexError : If index out of range
            ValueError : If value not in value list
        """
        if not isinstance(toRemove, (str, int)):
            raise TypeError
        #Remove by Value
        if isinstance(toRemove, str):
            if toRemove not in self.value:
                raise ValueError
            self.value.remove(toRemove)
        if isinstance(toRemove, int):
            if toRemove > len(self.value)-1:
                raise IndexError
            self.value.pop(toRemove)
    """
    #Obsolete. Can just remove and add.... I'll keep it for now
    def replace(self, oldValue, newValue):
        if not isinstance(oldValue, (str, int)):
            raise TypeError
        if not isinstance(newValue, (str, int, float)):
            raise TypeError
        #Replace by Value
        if isinstance(oldValue, str):
            if oldValue not in self.value:
                raise ValueError
            self.value[self.value.index(oldValue)] = newValue
        if isinstance(oldValue, int):
            if oldValue > len(self.value)-1:
                raise IndexError
            self.value[oldValue] = newValue
    """
