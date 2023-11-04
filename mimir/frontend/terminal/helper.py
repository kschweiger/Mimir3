"""
Module collection helper funktions only required for the terminal fromtend
"""


class FixedList:
    """
    Custom list that is initialized with a fixed leangth. If items are added after the
    maximum lengths is reached, the earlier elements will be removed.
    """

    def __init__(self, maxLen) -> None:
        self.maxLen = maxLen
        self.elements = []

    def __len__(self) -> int:
        return len(self.elements)

    def append(self, value):
        """
        Same as list append but overflow will be removed form the FixedList
        """
        self.elements.append(value)
        if len(self.elements) == self.maxLen + 1:
            self.elements = self.elements[1:]

    def __str__(self) -> str:
        return str(self.elements)

    def __getitem__(self, index):
        return self.elements[index]

    def __add__(self, other):
        raise NotImplementedError
