# flake8: noqa
import unittest

import pytest

# sys.path.insert(0, os.path.abspath('..'))
from mimir.backend.entry import DataBaseEntry, Item, ListItem


def check_items_in_entry(InputItems, entry):
    for itemName, itemType, itemValue in InputItems:
        if not entry.hasItem(itemName):
            return False
        if itemType == "Single":
            if not isinstance(entry.getItem(itemName).value, str):
                return False
        elif itemType == "List":
            if not isinstance(entry.getItem(itemName).value, list):
                return False
        if not entry.getItem(itemName).value == itemValue:
            return False
    return True


def getEntry():
    Items = [
        ("Item1", "Single", "DefaultForItem1"),
        ("Item2", "Single", "DefaultForItem2"),
        ("ListItem1", "List", ["DefaultListItem1"]),
        ("ListItem2", "List", ["DefaultListItem2"]),
    ]

    newEntry = DataBaseEntry(Items)
    return Items, newEntry


@pytest.fixture(scope="module")
def preCreatedEntry():
    Items = [
        ("Item1", "Single", "DefaultForItem1"),
        ("ListItem1", "List", ["DefaultListItem1"]),
        ("ListItem2", "List", ["DefaultListItem2 DefaultListItem3"]),
    ]

    newEntry = DataBaseEntry(Items)
    return newEntry


###########################################################
################## Initialization #########################
###########################################################
def test_initialize_entry():
    Items, newEntry = getEntry()
    assert check_items_in_entry(Items, newEntry) is True


def test_initialize_raise_expception_type_list():
    with pytest.raises(TypeError):
        newEntry = DataBaseEntry("blubb")


def test_initialize_raise_exception_type_tuple():
    with pytest.raises(TypeError):
        newEntry = DataBaseEntry(["blubb"])


def test_initialize_raise_exceptions_tuple_objects():
    with pytest.raises(RuntimeError):
        newEntry = DataBaseEntry([("Name", "Value")])
    # Exeption if name is not type str
    with pytest.raises(TypeError):
        newEntry = DataBaseEntry([(2.5, "Single", "Value")])
    # Exception if type is not "Single" or "List"
    with pytest.raises(RuntimeError):
        newEntry = DataBaseEntry([("Name", "Blubb", "Value")])
    with pytest.raises(TypeError):
        newEntry = DataBaseEntry([("Name", "Single", {})])
    with pytest.raises(TypeError):
        newEntry = DataBaseEntry([("Name", "List", {})])


def test_entry_invalid_name_exception_runtime():
    newEntry = DataBaseEntry([("Item1", "Single", "DefaultForItem1")])
    with pytest.raises(RuntimeError):
        newEntry.get_item("Blubb")


###########################################################
##################### Getting entries #####################
###########################################################
def test_entry_get_item():
    Items, newEntry = getEntry()
    newEntry.get_item("Item1")
    isItemType = isinstance(newEntry.get_item("Item1"), Item)
    isListItemType = isinstance(newEntry.get_item("ListItem1"), ListItem)
    assert isItemType or isListItemType


###########################################################
#################### Modification #########################
###########################################################
########### Add new item to DatabaseEntry #################
def test_entry_add_new_item():
    Items, newEntry = getEntry()
    newTupleSingle = ("AddedItem", "Single", "AddedItemValue")
    newTupleList = ("AddedListItem", "List", ["AddedItemValue"])
    newName, newType, newValue = newTupleSingle
    newEntry.add_item(newName, newType, newValue)
    newName, newType, newValue = newTupleList
    newEntry.add_item(newName, newType, newValue)
    assert check_items_in_entry([newTupleSingle, newTupleList], newEntry)


# Raise exception if non valid item type if passed
def test_entry_add_new_item_raise_exception_passed_items():
    Items, newEntry = getEntry()
    with pytest.raises(TypeError):
        newEntry.add_item(2.5, "Single", "newItem")
    with pytest.raises(RuntimeError):
        newEntry.add_item("name", "Blubb", "newItem")
    with pytest.raises(TypeError):
        newEntry.add_item("name", "Single", dict)


# Raise exception if the new item already exists
def test_entry_add_new_item_raise_exception_dublication():
    Items, newEntry = getEntry()
    with pytest.raises(RuntimeError):
        newEntry.add_item("Item1", "Single", "AddedItemValue")


############## Modify existing items  ####################
def test_entry_change_value_Item():
    Items, newEntry = getEntry()
    newEntry.change_item_value("Item1", "ReplacedValue")
    assert newEntry.get_item("Item1").value == "ReplacedValue"
    assert newEntry.Item1 == "ReplacedValue"


def test_entry_change_value_exception_passedName():
    Items, newEntry = getEntry()
    with pytest.raises(TypeError):
        newEntry.change_item_value(2.5, "ReplacedValue")
    with pytest.raises(KeyError):
        newEntry.change_item_value("notExisting", "ReplacedValue")


def test_entry_change_value_raise_exception_notItem():
    Items, newEntry = getEntry()
    with pytest.raises(RuntimeError):
        newEntry.change_item_value("ListItem1", "ReplacedValue")


def test_entry_add_value_to_ListItem():
    Items, newEntry = getEntry()
    newEntry.add_item_value("ListItem1", "AddedListItem1")
    assert newEntry.get_item("ListItem1").value[-1] == "AddedListItem1"


def test_entry_add_value_to_Item_raise_exception():
    Items, newEntry = getEntry()
    with pytest.raises(TypeError):
        newEntry.add_item_value(2.5, "ReplacedValue")
    with pytest.raises(KeyError):
        newEntry.add_item_value("notExisting", "ReplacedValue")


def test_entry_change_value_raise_exception_notListItem():
    Items, newEntry = getEntry()
    with pytest.raises(RuntimeError):
        newEntry.add_item_value("Item1", "ReplacedValue")


def test_entry_remove_value_from_ListItem():
    Items, newEntry = getEntry()
    newEntry.remove_item_value("ListItem1", "DefaultListItem1")
    assert "DefaultListItem1" not in newEntry.get_item("ListItem1").value


def test_entry_remove_value_from_Item_raise_exception():
    Items, newEntry = getEntry()
    with pytest.raises(TypeError):
        newEntry.remove_item_value(2.5, "DefaultListItem1")
    with pytest.raises(KeyError):
        newEntry.remove_item_value("notExisting", "DefaultListItem1")
    with pytest.raises(ValueError):
        newEntry.remove_item_value("ListItem1", "SomeNonExistingName")


def test_entry_remove_value_from_ListItem_exception_notListItem():
    Items, newEntry = getEntry()
    with pytest.raises(RuntimeError):
        newEntry.remove_item_value("Item1", "DefaultListItem1")


def test_entry_replace_value_of_ListItem():
    Items, newEntry = getEntry()
    newEntry.replace_item_value("ListItem1", "ReplacedItem", "DefaultListItem1")
    assert (
        "ReplacedItem" in newEntry.get_item("ListItem1").value
        and "DefaultListItem1" not in newEntry.get_item("ListItem1").value
    )


################### Stuff  ########################
def test_entry_equal():
    Items, newEntry = getEntry()
    Items2, newEntry2 = getEntry()
    assert newEntry == newEntry2


def test_entry_notequal_sameNames():
    Items, newEntry = getEntry()
    Items2, newEntry2 = getEntry()
    newEntry2.change_item_value("Item1", "ReplacedValue")
    assert newEntry != newEntry2


def test_entry_notequal_differentNames():
    Items, newEntry = getEntry()
    Items2, newEntry2 = getEntry()
    newTupleSingle = ("AddedItem", "Single", "AddedItemValue")
    newName, newType, newValue = newTupleSingle
    newEntry2.add_item(newName, newType, newValue)
    assert newEntry != newEntry2


def test_entry_getAllValues_byName():
    Items, newEntry = getEntry()
    with pytest.raises(KeyError):
        allValues = newEntry.get_all_values_by_name(["Blubb"])
    allValues = newEntry.get_all_values_by_name(["Item1", "ListItem1"])
    assert list(allValues) == list(set(["DefaultForItem1", "DefaultListItem1"]))


def test_entry_getAllValues_byName_split(preCreatedEntry):
    allValues = preCreatedEntry.getAllValuesbyName(["ListItem2"], split=False)
    assert list(allValues) == list(set(["DefaultListItem2 DefaultListItem3"]))
    allValues = preCreatedEntry.getAllValuesbyName(["ListItem2"], split=True)
    assert list(allValues) == list(set(["DefaultListItem2", "DefaultListItem3"]))


if __name__ == "__main__":
    unittest.main()
