class FixedList:
    """
    Custom list that is initialized with a fixed leangth. If items are added after the maximum leangths is reached, the earlier elements will be removed.
    """
    def __init__(self, maxLen):
        self.maxLen = maxLen
        self.elements =[]

    def __len__(self):
        return len(self.elements)

    def append(self, value):
        self.elements.append(value)
        if len(self.elements) == self.maxLen+1:
            self.elements = self.elements[1:]

    def __str__(self):
        return str(self.elements)

    def __getitem__(self, index):
        return self.elements[index]

    def __add__(self, other):
        raise NotImplementedError
