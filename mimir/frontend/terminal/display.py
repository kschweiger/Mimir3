"""
Classes for displaying information in ther terminal.
"""
class Window:
    """
    Object defining the window to be displayed

    Args:
        height (int) : Window height
        width (int) ; Window Width
        headerElements (dict) ; Head elements. See setHeader description
    """
    def __init__(self, height, width, headerElements, setHeader = False):
        tests = [(height, "height", int),
                 (width, "width", int),
                 (headerElements, "headerElements", dict)]
        for testArg in tests:
            var, name, expectedType = testArg
            if not isinstance(var, expectedType):
                raise TypeError("%s is required to be of type %s"%(name, expectedType))
        self.height = height
        self.width = width
        self.boxWidth = width-2
        self.boxHeight = height
        self.headerElements = headerElements
        self.headerSet = False
        self.header = None
        self.optionsTableId = "Code"
        self.optionsTableName = "Name"
        self.optionsTableComment = "Comment"
        self.optionMaxId = len(self.optionsTableId)
        self.optionMaxName = len(self.optionsTableName)
        self.optionMaxComment = len(self.optionsTableComment)
        self.optionsTableTitleElements = (self.optionsTableId,
                                          self.optionsTableName,
                                          self.optionsTableComment)

        self.lines = []
        self.skipTitle = False
        self.skipText = False
        #Define attributes that are defined outside __init__
        self.headerTitle = None
        self.headerText = None
        self.headerOptions = None
        self.validOptions = None
        if setHeader:
            self.setHeader()

    def setHeader(self):
        """
        Method for setting more explicit members for the header from the passed headerElements:
        The headerElements passed to the class can have the following options:
        Title : Single String that will be displayed as Title
        Text : List of strings / one string that will be displayed under the Title
        Options : This is the list that displays the input options for the windows. It is expected to be a List of tuples, with each tuple consiting of two elements (name and comment). The options will be numbered (this is the input value) by the passed order
        """
        self.headerTitle = self.headerElements["Title"]
        self.headerText = []
        if "Text" in self.headerElements.keys():
            if isinstance(self.headerElements["Text"], str):
                self.headerText.append(self.headerElements["Text"])
            elif isinstance(self.headerElements["Text"], list):
                self.headerText += self.headerElements["Text"]
            else:
                raise TypeError("Only str and list are supported for text headerelements")
            _headerText = []
            for line in self.headerText:
                if len(line) > self.boxWidth:
                    firstChar = 0
                    lastChar = self.boxWidth
                    for nOverFlow in range(len(line)//self.boxWidth):
                        print(firstChar, lastChar, line[firstChar:lastChar])
                        _headerText.append(line[firstChar:lastChar])
                        firstChar = lastChar
                        lastChar = lastChar + self.boxWidth
                    _headerText.append(line[firstChar:])
                else:
                    _headerText.append(line)
            self.headerText = _headerText

        self.headerOptions = None
        self.validOptions = None
        if "Options" in self.headerElements.keys():
            if not isinstance(self.headerElements["Options"], list):
                raise TypeError("Options are required to be lists")
            for iOption in range(len(self.headerElements["Options"])):
                if not isinstance(self.headerElements["Options"][iOption], tuple):
                    raise TypeError("Each options is required to be of type tuple")
                name, comment = self.headerElements["Options"][iOption]
                if iOption == 0:
                    self.headerOptions = [(str(iOption), name, comment)]
                    self.validOptions = [str(iOption)]
                else:
                    self.headerOptions.append((str(iOption), name, comment))
                    self.validOptions.append(str(iOption))
                if len(str(iOption)) > self.optionMaxId:
                    self.optionMaxId = len(str(iOption))
                if len(name) > self.optionMaxName:
                    self.optionMaxName = len(name)
                if len(comment) > self.optionMaxComment:
                    self.optionMaxComment = len(comment)
        self.headerSet = True

    def makeheader(self, skipTitle = False, skipText = False, skipOptions = False):
        """
        Sets the header
        """
        self.header, self.boxHeight = self.createHeader(skipTitle, skipText, skipOptions)

    def createHeader(self, skipTitle = False, skipText = False, skipOptions = False):
        """
        Generates the lines of the header from set Title, Text and Options

        Returns:
            header (list) : List if lines of the header
            boxHeight (int) : Total height of the header
        """
        if not self.headerSet:
            raise RuntimeError("Header ist not set")

        boxWidth = self.boxWidth
        header = []
        header.append("+"+boxWidth*"-"+"+")
        header.append("|"+boxWidth*" "+"|")

        if not skipTitle:
            header.append("|"+self.expandAndCenterText(self.headerElements["Title"], boxWidth)+"|")
            header.append("|"+boxWidth*" "+"|")

        if not skipText:
            for text in self.headerText:
                header.append("| "+text+(boxWidth-len(text)-1)*" "+"|")
            if len(self.headerText) > 0:
                header.append("|"+boxWidth*" "+"|")

        if self.validOptions is not None and not skipOptions:
            table = self.makeTable(self.optionsTableTitleElements,
                                   self.headerOptions,
                                   (self.optionMaxId, self.optionMaxName, self.optionMaxComment))
            for tableLine in table:
                header.append("|"+self.expandAndCenterText(tableLine, boxWidth)+"|")
        header.append("|"+boxWidth*" "+"|")
        header.append("+"+boxWidth*"-"+"+")
        boxHeight = len(header)

        return header, boxHeight

    def update(self, newLine):
        """
        Update the internal lines in the window.
        """
        self.lines.append(newLine)

    def draw(self, inputString):
        """
        Draw the current state of the window. Will check if the lines exeed the height and will not print earlier lines if found.
        """
        self.makeheader()
        for line in self.header:
            print(line)
        lines2print = self.lines
        maxLines = self.height-self.boxHeight-2
        if len(self.lines) > (maxLines):
            lines2print = self.lines[-maxLines:]
        for line in lines2print:
            print(line)
        return input(inputString+": ")

    @staticmethod
    def expandAndCenterText(text, width, symbol=" "):
        """
        Misc function for expanding the passes string text to width width by adding symbole before and after text
        """
        text = str(text)
        total_exp = width - len(text)
        if total_exp%2 == 0:
            expandLeft, expandRight = total_exp//2, total_exp//2
        else:
            expandLeft, expandRight = total_exp//2, total_exp//2+1

        return (expandLeft*symbol)+text+(expandRight*symbol)

    @staticmethod
    def makeTable(headerElements, elements, maxLenElements):
        """
        Misc class for generating a table view of the massed arguments. Result will look like this:
             header[0] | header[1]      | header[2]
        ---------------+----------------+---------------
        elements[0][0] | elements[0][1] | elements[0][1]
        """
        tableLines = []
        headerLine = ""
        dividerLine = ""
        for ielement, element in enumerate(headerElements):
            headerLine += element + (maxLenElements[ielement]-len(element))*" "
            if ielement < len(maxLenElements)-1:
                headerLine += " | "
            if ielement == 0:
                dividerLine += (maxLenElements[ielement]+1)*"-"+"+"
            elif ielement == len(maxLenElements)-1:
                dividerLine += (maxLenElements[ielement]+1)*"-"
            else:
                dividerLine += (maxLenElements[ielement]+2)*"-"+"+"
        tableLines.append(headerLine)
        tableLines.append(dividerLine)
        for line in elements:
            thisLine = ""
            for ielement, element in enumerate(line):
                if ielement == 0:
                    thisLine += (maxLenElements[ielement]-len(element))*" "+element
                else:
                    thisLine += element+(maxLenElements[ielement]-len(element))*" "
                if ielement < len(maxLenElements)-1:
                    thisLine += " | "
            tableLines.append(thisLine)

        return tableLines

class ListWindow(Window):
    """
    Window class for displaying lists of database entries. No header will be displayed. The ListWindow class will figure out the fomatting of the lines. In the context of MTF each line will be split into fields for each Item requested for display in the config based in the maximum width. Generated List will be longer than the maxim height of the windows.

    Args:
        height (int) : Window height
        width (int) ; Window Width
        headerElements (dict) ; Head elements. See setHeader description
        nColumns (int) : Number of colums for each line
        tableHeaderElements (tuple) : Header for the table
    """
    def __init__(self, height, width, headerElements, nColumns, tableHeaderElements, alignment="left"):
        super().__init__(height, width, headerElements)
        self.lines = []
        self.nColumns = nColumns
        if len(tableHeaderElements) != self.nColumns:
            raise ValueError("Passed tableHeaderElements has not nColumns elements")
        self.tableHeaderElements = tableHeaderElements
        self.tableMaxLen = []
        for i in range(self.nColumns):
            self.tableMaxLen.append(len(self.tableHeaderElements[i]))
        if alignment not in ["left", "center"]:
            raise KeyError("%s not supported"%alignment)
        self.alignment = alignment

    def update(self, newContent, resetHeader=None):
        """
        Update the internal state of the window. For ListWindow object this are new lines of the list

        Args:
            newContent (tuple, list(tuple)) : tuble or list of tuples with nColumns elements
            resetHeader (str) : Pass a new Title

        Raises:
            TypeError : Raised if newContent is not tuple or list of tuples
            ValueError : Raised if len(tuple) != nColumns
        """
        if not isinstance(newContent, tuple) and not isinstance(newContent, list):
            raise TypeError("%s is required to be tuple or list"%newContent)
        if isinstance(newContent, list):
            for elem in newContent:
                self.update(elem)
            return True
        if len(newContent) != self.nColumns:
            raise ValueError("Passed content is not of len nColumns")

        if resetHeader is not None:
            self.headerTitle = resetHeader

        self.lines.append(newContent)
        for icontent, content in enumerate(newContent):
            if len(content) > self.tableMaxLen[icontent]:
                self.tableMaxLen[icontent] = len(content)

        return True
    def draw(self):
        """
        Draw the current state of the window
        """
        self.makeheader()
        for line in self.header:
            print(line)
        tableLines = self.makeTable(self.tableHeaderElements, self.lines, self.tableMaxLen)
        for line in tableLines:
            lineLen = len(line)
            if self.alignment == "left":
                print(" "+line+" "+(lineLen-2)*" ")
            if self.alignment == "center":
                print(self.expandAndCenterText(line, self.width))
        return True

    def interact(self, interaction, printOptions = None):
        """
        Interaction with window, but the new lines will just be append (unlike the main windows draw method)

        Args:
            interaction (str) : Text that will be displayedi n a sdtin statement
            printOptions : None/"Full"/"Small"
        """
        if printOptions is not None and printOptions not in ["Full", "Small"]:
            raise KeyError("Only None/Full/Small supperted for printOptions")
        if printOptions is not None:
            if printOptions == "Full":
                options, optionHeight = self.createHeader(True, True, False)
            else:
                options, optionsHeight = self.makeSmallOptionTable()

            #Print requestion option version
            for line in options:
                print(line)

        return input(interaction+": ")

    def makeSmallOptionTable(self):
        retList = []
        elements = []
        for option in self.headerOptions:
            code, name, comment = option
            elements.append("{0} : {1}".format(code, name))

        joinedString = " | ".join(elements)
        optionLines = []
        if len(joinedString) > self.boxWidth:
            thisElements = elements
            while len(joinedString) > self.boxWidth:
                split, remainingElem = self.splitOptionLine(thisElements, self.boxWidth)
                optionLines.append(" | ".join(thisElements[:split]))
                thisElements = remainingElem
                joinedString = " | ".join(remainingElem)
            optionLines.append(" | ".join(thisElements))
        else:
            optionLines.append(joinedString)
        retList.append("+"+self.boxWidth*"-"+"+")
        retList.append("|"+self.boxWidth*" "+"|")
        for line in optionLines:
            retList.append("|"+self.expandAndCenterText(line, self.boxWidth)+"|")
        retList.append("|"+self.boxWidth*" "+"|")
        retList.append("+"+self.boxWidth*"-"+"+")

        return retList, len(retList)

    @staticmethod
    def splitOptionLine(elements, maxlen):
        """
        Splits the passed elements so the joined string does not exceed maxlen

        Args:
            elements (list) : List of strings that should be joined with
            maxlen (int) : Maximum allowed length elements can be joined to

        Returns:
            nElements (int) : Index where the input elements have to be split so the joined fit into maxLen
            remainingElements (list) : Remaining elements that exceed the joined maxLen
        """
        nElements = len(elements)
        joinedString = " | ".join(elements)
        while len(joinedString) > maxlen:
            nElements -= 1
            joinedString = " | ".join(elements[:nElements])

        remainingElements = elements[nElements:]
        return nElements, remainingElements


# class InteractionWindow(Window):
#     """
#     Window class used when interacting with the database. The windows will render a header with interaction options and some sequence of interactions.
#     """
#     def __init__(self, height, width, headerElements):
#         super().__init__(height, width, headerElements)
#         self.lines = []
#
#     def update(self, newLine):
#         """
#         Update the internal lines in the Interaction window.
#         """
#         self.lines.append(newLine)
#
#     def draw(self, inputString):
#         """
#         Draw the current state of the window. Will check if the lines exeed the height and will not print earlier lines if found.
#         """
#         self.makeheader()
#         for line in self.header:
#             print(line)
#         lines2print = self.lines
#         maxLines = self.height-self.boxHeight-2
#         if len(self.lines) > (maxLines):
#             lines2print = self.lines[-maxLines:]
#         for line in lines2print:
#             print(line)
#         return input(inputString+": ")
