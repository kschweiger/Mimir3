'''
Entry Module. Includes definitons for DatabaseEnties and item of these entries
'''
class DataBaseEntry(object):
    '''
    The Entry class describes all information stored in an database entry

    Args:

    Attributes:
        someAtribute
    '''
    def __init__(self, args):
        pass

    def setValues(self, WhichValue, ):
        '''
        Set Values for the entry

        Args:
            WhichValue (str) : Defines which value will be set
            newValue : New value stored
        '''
        pass

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
        return "{0} : {1}".format(self.name, self.value)

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
        if isinstance(val2Add, str):
            self.value.append(val2Add)
        elif isinstance(val2Add, list):
            self.value = self.value + val2Add
        else:
            raise TypeError
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
        pass

    def replace(self, oldValue, newValue):
        """
        Replaces value of ListItem either by value or index

        """
        pass
