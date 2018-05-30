import sys
import os
sys.path.insert(0, os.path.abspath('..'))
from backend.entry import Item, ListItem
import unittest
import pytest

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
        newitem = ListItem("TestName", "InitValue")
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
        addRet = newitem.add(["InitValue3", "newValue1", "newValue2"])
        assert addRet is True
        assert all(elem in newitem.value for elem in newValues)
        assert newitem.value.count("InitValue3") == 1
        
    def test_ListItem_remove_item_byValue(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])
        #newitem.remove

    def test_ListItem_replace_item_byValue(self):
        newitem = ListItem("TestName", ["InitValue1", "InitValue2", "InitValue3"])


indices = ( (0, True),
            (3, False) )
@pytest.mark.parametrize('n,expected', indices)
def test_ListItem_remove_item_byIndex(n, expected):
    values = ["InitValue1", "InitValue2", "InitValue3"]
    newitem = ListItem("TestName", values)
    remRet = newitem.remove(n)
    assert rmRet is expected
    if rmRet:
        assert values[n] not in newitem.value

@pytest.mark.parametrize('n,expected', indices)
def test_ListItem_replace_item_byIndex(n, expected):
    values = ["InitValue1", "InitValue2", "InitValue3"]
    newitem = ListItem("TestName", values)
    replRet = newitem.replace(n, "newValue")
    assert replRet is expected
    if replRet:
        assert "newValue" == newitem.value[n]

        
if __name__ == "__main__":
    unittest.main()
