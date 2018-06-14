import sys
import os
sys.path.insert(0, os.path.abspath('..'))
from backend.entry import DataBaseEntry, Item, ListItem
import unittest
import pytest
import coverage


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
    Items = [("Item1", "Single", "DefaultForItem1"),
             ("Item2", "Single", "DefaultForItem2"),
             ("ListItem1", "List", ["DefaultListItem1"]),
             ("ListItem2", "List", ["DefaultListItem2"]),
        ]
        
    newEntry = DataBaseEntry(Items)
    return Items, newEntry


class TestEntry(unittest.TestCase):
    ###########################################################
    ################## Initialization #########################
    ###########################################################
    def test_initialize_entry(self):
        Items, newEntry = getEntry()
        assert check_items_in_entry(Items, newEntry) is True

    def test_initialize_raise_expception_type_list(self):
        with self.assertRaises(TypeError):
            newEntry = DataBaseEntry("blubb")

    def test_initialize_raise_exception_type_tuple(self):
        with self.assertRaises(TypeError):
            newEntry = DataBaseEntry(["blubb"])
            
    def test_initialize_raise_exceptions_tuple_objects(self):
        with self.assertRaises(RuntimeError):
            newEntry = DataBaseEntry([("Name","Value")])
        #Exeption if name is not type str
        with self.assertRaises(TypeError):
            newEntry = DataBaseEntry([(2.5,"Single","Value")])
        #Exception if type is not "Single" or "List"
        with self.assertRaises(TypeError):
            newEntry = DataBaseEntry([("Name","Blubb","Value")])
        with self.assertRaises(RuntimeError):
            newEntry = DataBaseEntry([("Name","Single",{})])
        with self.assertRaises(RuntimeError):
            newEntry = DataBaseEntry([("Name","List",{})])

            
    def test_entry_invalid_name_exception_runtime(self):
        newEntry = DataBaseEntry([("Item1", "Single", "DefaultForItem1")])
        with self.assertRaises(RuntimeError):
            newEntry.getItem("Blubb")

    ###########################################################
    ##################### Getting entries #####################
    ###########################################################
    def test_entry_get_item(self):
        Items, newEntry = getEntry()
        newEntry.getItem("Item1")
        isItemType = isinstance(newEntry.getItem("Item1"), Item)
        isListItemType = isinstance(newEntry.getItem("ListItem1"), ListItem)
        assert isItemType or isListItemType
            
    ###########################################################
    #################### Modification #########################
    ###########################################################
    ########### Add new item to DatabaseEntry #################
    def test_entry_add_new_item(self):
        Items, newEntry = getEntry()
        newTupleSingle = ("AddedItem","Single","AddedItemValue")
        newTupleList = ("AddedListItem","List",["AddedItemValue"])
        newName, newType, newValue = newTupleSingle
        newEntry.addItem(newName, newType, newValue)
        newName, newType, newValue = newTupleList
        newEntry.addItem(newName, newType, newValue)
        assert check_items_in_entry([newTupleSingle, newTupleList], newEntry)

    #Raise exception if non valid item type if passed
    def test_entry_add_new_item_raise_exception_passed_items(self):
        Items, newEntry = getEntry()
        with self.assertRaises(TypeError):
            newEntry.addItem(2.5, "Single", "newItem")
        with self.assertRaises(RuntimeError):
            newEntry.addItem("name", "Blubb", "newItem")
        with self.assertRaises(TypeError):
            newEntry.addItem("name", "Single", dict)

    #Raise exception if the new item already exists
    def test_entry_add_new_item_raise_exception_dublication(self):
        Items, newEntry = getEntry()
        with self.assertRaises(RuntimeError):
            newEntry.addItem("Item1","Single","AddedItemValue")
        
    ############## Modify existing items  ####################
    def test_entry_change_value_Item(self):
        assert False

    def test_entry_change_value_raise_valueError(self):
        assert False
    
    def test_entry_add_value_to_ListItem(self):
        assert False

    def test_entry_add_value_to_Item_raise_exception(self):
        assert False

    def test_entry_remove_value_to_ListItem(self):
        assert False

    def test_entry_remove_value_to_Item_raise_exception(self):
        assert False

    def test_entry_replace_value_to_ListItem(self):
        assert False
        
if __name__ == "__main__":
    unittest.main()
