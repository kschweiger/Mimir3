"""
Classes for displaying information in ther terminal.
"""
import logging

from mimir.frontend.terminal.helper import FixedList

logger = logging.getLogger(__name__)

class Window:
    """
    Object defining the window to be displayed

    Args:
        height (int) : Window height
        width (int) ; Window Width
        headerElements (dict) ; Head elements. See setHeader description
    """
    def __init__(self, height, width, headerElements, setHeader=False):
        tests = [(height, "height", int),
                 (width, "width", int),
                 (headerElements, "headerElements", dict)]
        for testArg in tests:
            var, name, expectedType = testArg
            if not isinstance(var, expectedType):
                raise TypeError("%s is required to be of type %s"%(name, expectedType))
        self.debug = False
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
        self.headerTextSecondary = None
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
        self.headerTextSecondary = {}
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

    def makeheader(self, skipTitle=False, skipText=False, skipOptions=False):
        """
        Sets the header
        """
        self.header, self.boxHeight = self.createHeader(skipTitle, skipText, skipOptions)

    def createHeader(self, skipTitle=False, skipText=False, skipOptions=False):
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
            if self.headerTextSecondary is not None:
                for key in self.headerTextSecondary:
                    text = "{0}: {1}".format(key, self.headerTextSecondary[key])
                    header.append("| "+text+(boxWidth-len(text)-1)*" "+"|")
                #self.headerTextSecondary = []
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
        maxLines = self.height-self.boxHeight
        if len(self.lines) > (maxLines):
            lines2print = self.lines[-maxLines:]
        #Prepend empty lines so the window looks constant
        if len(lines2print) < maxLines:
            for emptyline in range(maxLines-len(lines2print)):
                print("")
        for line in lines2print:
            print(line)
        answer = input(inputString+": ")
        self.lines.append(inputString+": "+answer)
        return answer

    @staticmethod
    def expandAndCenterText(text, width, symbol=" "):
        """
        Misc function for expanding the passes string text to width width by adding symbole before and after text
        """
        text = str(text)
        total_exp = width - len(text)
        if total_exp < 0:
            logger.warning("Text is longer than width")
            return text
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
        self.printedLines = FixedList(self.height)
        self.nLinesPrinted = 0
        self.nLinesPrintedGlobal = 0
        self.tableAdded = False


    def print(self, printStatement):
        """
        Is used to print the lines. This functions only intention is to also keep track of the printed lines in additon to actiually printing them.
        """
        logger.debug("Added: %s", printStatement[0:20])
        self.printedLines.append(printStatement)
        self.nLinesPrinted += 1
        self.nLinesPrintedGlobal += 1
        print(printStatement)#,self.nLinesPrinted)

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
        logger.debug("Running update in %s", self)
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
        self.tableAdded = True
        return True

    def draw(self, skipHeader=False, skipTable=False, fillWindow=False):
        """
        Draw the current state of the window
        """
        logger.debug("skipHeader=%s skipTable=%s fillWindow=%s", skipHeader, skipTable, fillWindow)
        #print("kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
        logger.debug("Running draw in %s", self)
        self.nLinesPrinted = 0
        self.makeheader()
        if self.nLinesPrintedGlobal > self.height:
            skipHeader = True
            fillWindow = False

        if not skipHeader:
            for line in self.header:
                self.print(line)
        tableLines = self.makeTable(self.tableHeaderElements, self.lines, self.tableMaxLen)
        if fillWindow and self.nLinesPrinted < self.height:
            logger.info("Drawing overflow lines - self.nLinesPrinted=%s", len(self.printedLines))
            self.drawBeforeOverflow(newTableLines=len(tableLines), skipTable=skipTable)
        else:
            logger.info("Skipping overflow - %s and %s < %s", fillWindow, len(self.printedLines), self.height)
        #print(tableLines)
        if not skipTable:
            for line in tableLines:
                lineLen = len(line)
                if self.alignment == "left":
                    if len(line) > self.width:
                        logger.error("Table line is wider than defined width. Consider extenting the width to %s", len(line)+2)
                        self.print(" "+line+" ")
                    else:
                        self.print(" "+line+" "+(self.boxWidth-lineLen)*" ")
                if self.alignment == "center":
                    self.print(self.expandAndCenterText(line, self.width))
        return True

    def drawBeforeOverflow(self, newTableLines, skipTable):
        """
        Function for (re)drawing the current state while the maximum height of the windows is not reached.
        Will add empty lines unter the header so the previously draw lines are at the bottom the window.

        Args:
            newTableLines (int) : Number of lines expected form the next table to be drawn
            skipTable (bool) : Required of the next updated should not draw a table. This is required to correclty calculate the number of empty lines required
        """
        logger.info("Entering function")
        if skipTable:
            newTableLines = 0

        postFillLines = []
        for iline, line in enumerate(self.printedLines):
            if line not in self.header:
                postFillLines.append(line)

        logger.info("print Empty: %s - print printed %s - newTable %s",
                     self.height-len(postFillLines)-newTableLines-len(self.header),
                     len(postFillLines), newTableLines)
        for i in range(self.height-len(postFillLines)-newTableLines-len(self.header)):
            if i == 0 and self.debug:
                print("print Empty:", self.height-len(postFillLines)-newTableLines-len(self.header),
                      " - print printed:", len(postFillLines), "- newTable:", newTableLines)
            else:
                print(self.width * " ")

        for iline, line in enumerate(postFillLines):
            print(line)




    def interact(self, interaction, printOptions=None, rePrintInitial=False, onlyInteraction=False):
        """
        Interaction with window, but the new lines will just be append (unlike the main windows draw method).
        Can also invoce the next draw method. So draw does not have to be called after each interaction.

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
                self.print(line)
        #print(self.nLinesPrinted, self.height)
        if not onlyInteraction:
            logger.info("self.nLinesPrinted=%s/%s", self.nLinesPrinted, self.height)
            #print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
            self.draw(skipHeader=(self.nLinesPrinted > self.height),
                      skipTable=(not self.tableAdded),
                      fillWindow=(self.nLinesPrinted < self.height))
            #print("ooooooooooooooooooooooooooooooooo")

        answer = input(interaction+": ")
        logger.info("Input: %s - Answer: %s", interaction, answer)
        toPrint = ""+interaction+": "+answer
        self.printedLines.append(toPrint+" "*(self.width-len(toPrint)))
        self.nLinesPrinted += 1
        self.nLinesPrintedGlobal += 1
        return answer

    def makeSmallOptionTable(self):
        """
        Make a small version of the option table. Intendet to be used once the window reach maximum height and new lines will only be appended.
        """
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
