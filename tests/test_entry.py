import sys
import os
sys.path.insert(0, os.path.abspath('..'))
from backend.entry import Item, ListItem
import unittest
import pytest
import coverage


class TestItem(unittest.TestCase):

    def test_initialization_single(self):
         newitem = Item("TestName", "TestValue")
         assert newitem.name == "TestName"
         assert newitem.value == "TestValue"
         
    def test_initialization_list(self):
        newitem = ListItem("TestName", ["TestValue"])
        assert newitem.name == "TestName"
        assert isinstance(newitem.value, list)
        assert newitem.value[0] == "TestValue"

    def test_initialization_list_fromString(self):
        newitem = ListItem("TestName", "TestValue")
        assert newitem.name == "TestName"
        assert isinstance(newitem.value, list)
        assert newitem.value[0] == "TestValue"

    def test_initialization_list_exeption_type(self):
        with self.assertRaises(TypeError):
             ListItem("TestName", {})
        
    def test_Item_replace_item(self):
        newitem = Item("TestName", "InitValue")
        newitem.replace("ReplacedValue")
        assert newitem.value == "ReplacedValue"
        
    def test_ListItem_add_item(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        addRet = newitem.add("newValue")
        assert addRet is True 
        assert "newValue" in newitem.value

    def test_ListItem_add_item_multiple(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        newValues = ["newValue1", "newValue2"]
        addRet = newitem.add(newValues)
        assert addRet is True
        assert all(elem in newitem.value for elem in newValues)

    def test_ListItem_add_item_dublicate(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        addRet = newitem.add("InitValue3")
        assert addRet is False

    def test_ListItem_add_item_dublicate_list(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        addRet = newitem.add(["InitValue3","InitValue2"])
        assert addRet is False

    def test_ListItem_add_item_dublicate_list_partial(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        newValues = ["InitValue3", "newValue1", "newValue2"]
        addRet = newitem.add(newValues)
        assert addRet is True
        assert all(elem in newitem.value for elem in newValues)
        assert newitem.value.count("InitValue3") == 1

    def test_ListItem_remove_item_Raise_TypError(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        with self.assertRaises(TypeError):
            newitem.remove(2.567)

    def test_ListItem_replace_item_Raise_TypError_old(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        newValue = "newValue"
        with self.assertRaises(TypeError):
            newitem.replace(2.567, newValue)
    def test_ListItem_replace_item_Raise_TypError_new(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        newValue = "newValue"
        with self.assertRaises(TypeError):
            newitem.replace("InitValue1", {})
        
    def test_ListItem_remove_item_byValue(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        newitem.remove("InitValue2")
        assert "InitValue2" not in newitem.value

    def test_ListItem_remove_item_byValue_fail(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        with self.assertRaises(ValueError):
            newitem.remove("InitValue5")

    def test_ListItem_replace_item_byValue_fail(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        newValue = "newValue"
        with self.assertRaises(ValueError):
            newitem.replace("InitValue5", newValue)
    
    def test_ListItem_replace_item_byValue(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        newValue = "newValue"
        val2replace = "InitValue2"
        oldindex = newitem.value.index(val2replace)
        assert newitem.value[oldindex] == val2replace

    def test_ListItem_remove_item_byIndex(self):
        values = ["InitValue1", "InitValue2", "InitValue3"]
        newitem = ListItem("TestName", values)
        oldValue = values[0]
        newitem.remove(0)
        assert oldValue not in newitem.value

    def test_ListItem_remove_item_byIndex_Raise_IndexError(self):
        values = ["InitValue1", "InitValue2", "InitValue3"]
        newitem = ListItem("TestName", values)
        with self.assertRaises(IndexError):
            newitem.remove(3)

    def test_ListItem_replace_item_byIndex(self):
        values = ["InitValue1", "InitValue2", "InitValue3"]
        newitem = ListItem("TestName", values)
        newitem.replace(0, "newValue")
        assert "newValue" == newitem.value[0]

    def test_ListItem_replace_item_byIndex_Raise_IndexError(self):
        values = ["InitValue1", "InitValue2", "InitValue3"]
        newitem = ListItem("TestName", values)
        with self.assertRaises(IndexError):
            newitem.replace(3, "newValue")
        
if __name__ == "__main__":
    unittest.main()
