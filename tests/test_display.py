# flake8: noqa
import copy
import json
import os
import shutil
import string
import sys
import unittest

import coverage
import pytest

import mimir.frontend.terminal.display as display
from mimir.frontend.terminal.display import ListWindow, Window  # , InteractionWindow


@pytest.fixture(scope="module")
def preCreatedWindowAndElements():
    headerElements = {
        "Title": "This is the Title",
        "Text": ["First line text", "Second line text"],
        "Options": [("FirstName", "FirstComment"), ("SecondName", "SecondComment")],
    }
    fixWindow = Window(20, 100, headerElements)
    fixWindow.setHeader()
    for i in range(15):
        fixWindow.update("This is line - " + str(i))
    return headerElements, fixWindow


@pytest.fixture(scope="module")
def preCreatedListWindow():
    headerElements = {
        "Title": "This is the Title",
        "Text": ["First line text", "Second line text"],
        "Options": [("FirstName", "FirstComment"), ("SecondName", "SecondComment")],
    }
    fixWindow = ListWindow(
        100, 100, headerElements, 3, ("Column1", "Column2", "Column3")
    )
    fixWindow.setHeader()
    entry1 = ("Entry1,1", "Entry1,2", "Entry1,3")
    entry2 = ("Entry2,1", "Entry2,2", "Entry2,3")
    entry3 = ("Entry3,1", "Entry3,2", "Entry3,3")
    fixWindow.update([entry1, entry2, entry3])
    return fixWindow


# @pytest.fixture(scope="module")
# def preCreatedInteractionWindow():
#     headerElements = {"Title" : "This is a IteractionWindow",
#                       "Options" : [("Some Input", "This will do something"),
#                                    ("Some other input", "This will do something else")]}
#     fixWindow = InteractionWindow(20, 100, headerElements)
#     fixWindow.setHeader()
#     for i in range(15):
#         fixWindow.update("This is line - "+str(i))
#     return fixWindow


def test_01_display_Window_init():
    thisWindow = Window(100, 100, {})
    assert (
        thisWindow.height == 100
        and thisWindow.width == 100
        and thisWindow.headerElements == {}
        and not thisWindow.headerSet
    )
    with pytest.raises(TypeError):
        Window("Height", 100, {})
    with pytest.raises(TypeError):
        Window(100, "Width", {})
    with pytest.raises(TypeError):
        Window(100, 100, "headerElements")


def test_02_display_Window_setHeader():
    # Test Text elements
    headerElements_text_str = {"Title": "Title", "Text": "Single line text"}
    window_text_str = Window(100, 100, headerElements_text_str)
    assert not window_text_str.headerSet
    window_text_str.setHeader()
    assert window_text_str.headerSet
    assert window_text_str.headerText == ["Single line text"]
    headerElements_text_str = {"Title": "Title", "Text": ["First line", "Second line"]}
    window_text_list = Window(100, 100, headerElements_text_str)
    window_text_list.setHeader()
    assert window_text_list.headerText == ["First line", "Second line"]
    with pytest.raises(TypeError):
        Window(100, 100, {"Title": "Title", "Text": 100}).setHeader()
    # Test Options elements
    headerElements_options = {
        "Title": "Title",
        "Text": "text",
        "Options": [("Option1", "Comment1"), ("Opt2", "LongerComment2")],
    }
    window_text_options = Window(100, 100, headerElements_options)
    window_text_options.setHeader()
    assert window_text_options.headerOptions == [
        ("0", "Option1", "Comment1"),
        ("1", "Opt2", "LongerComment2"),
    ]
    assert window_text_options.validOptions == ["0", "1"]
    assert (
        window_text_options.optionMaxId == 4
        and window_text_options.optionMaxName  # 4 because header is "code"
        == len("Option1")
        and window_text_options.optionMaxComment == len("LongerComment2")
    )

    # Test Errors
    with pytest.raises(TypeError):
        Window(
            100, 100, {"Title": "Title", "Text": "text", "Options": "NotAList"}
        ).setHeader()
    with pytest.raises(TypeError):
        Window(
            100, 100, {"Title": "Title", "Text": "text", "Options": ["NotATuple"]}
        ).setHeader()
    with pytest.raises(ValueError):
        Window(
            100, 100, {"Title": "Title", "Text": "text", "Options": [()]}
        ).setHeader()
    with pytest.raises(ValueError):
        Window(
            100, 100, {"Title": "Title", "Text": "text", "Options": [("A", "B", "C")]}
        ).setHeader()

    # Test weight overflow
    headerElements_text_str = {"Title": "Title", "Text": 46 * "A"}
    window_text_overflow = Window(20, 20, headerElements_text_str)
    window_text_overflow.setHeader()
    assert len(window_text_overflow.headerText) == 3
    for line in window_text_overflow.headerText:
        print(line)
    assert window_text_overflow.headerText[0] == 18 * "A"
    assert window_text_overflow.headerText[1] == 18 * "A"
    assert window_text_overflow.headerText[2] == 10 * "A"


def test_03_display_Window_makeHeader(preCreatedWindowAndElements):
    with pytest.raises(RuntimeError):
        Window(100, 100, {"Title": "Title"}).makeheader()

    headerElements, preCreatedWindow = preCreatedWindowAndElements

    assert preCreatedWindow.header is None
    preCreatedWindow.makeheader()
    assert preCreatedWindow.header is not None
    foundTitle = False
    foundTextL1 = False
    foundTextL2 = False
    foundOptionsL1 = False
    foundOptionsL2 = False

    for line in preCreatedWindow.header:
        print(line)
        if headerElements["Title"] in line:
            foundTitle = True
        if headerElements["Text"][0] in line:
            foundTextL1 = True
        if headerElements["Text"][1] in line:
            foundTextL2 = True
        if (
            headerElements["Options"][0][0] in line
            and headerElements["Options"][0][1] in line
        ):
            foundOptionsL1 = True
        if (
            headerElements["Options"][1][0] in line
            and headerElements["Options"][1][1] in line
        ):
            foundOptionsL2 = True
    assert (
        foundTitle and foundTextL1 and foundTextL2 and foundOptionsL1 and foundOptionsL2
    )


def test_04_display_Window_expandAndCenterText():
    # Even len text
    centeredText = Window(100, 100, {"Title": "Title"}).expandAndCenterText(
        "SomeText", 20
    )
    expectedText = (6 * " ") + "SomeText" + (6 * " ")
    assert centeredText == expectedText
    # Odd len Text
    centeredText = Window(100, 100, {"Title": "Title"}).expandAndCenterText(
        "SomeText1", 20
    )
    expectedText = (5 * " ") + "SomeText1" + (6 * " ")
    assert centeredText == expectedText


def test_05_display_Window_makeTable():
    testWindow = Window(100, 100, {"Title": "Title"})
    table = testWindow.makeTable(
        ("FirtsColumn", "SecondColumn", "ThirdColumn"),
        [("0", "Name0", "Comment0"), ("1", "Name1", "Comment1")],
        (len("FirtsColumn"), len("SecondColumn"), len("ThirdColumn")),
    )
    for line in table:
        print(line)
    expectedTable = []
    expectedTable.append("FirtsColumn | SecondColumn | ThirdColumn")
    expectedTable.append("------------+--------------+------------")
    expectedTable.append("          0 | Name0        | Comment0   ")
    expectedTable.append("          1 | Name1        | Comment1   ")
    for iLine, expectedLine in enumerate(expectedTable):
        assert expectedLine == table[iLine]


def test_06_display_Window_draw(preCreatedWindowAndElements, capsys, monkeypatch):
    headerElements, preCreatedWindow = preCreatedWindowAndElements

    def mock_input(s):
        return s + " (mocked)"

    display.input = mock_input
    preCreatedWindow.draw("This is requesting some input")
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out != ""


def test_07_display_ListWindow_init():
    createdListWindow = ListWindow(
        100, 100, {"Title": "List"}, 3, ("Column1", "Column2", "Column3")
    )
    createdListWindow.setHeader()
    # Check inherited values:
    assert createdListWindow.boxWidth == createdListWindow.width - 2
    assert createdListWindow.headerTitle == "List"
    assert len(createdListWindow.headerText) == 0
    assert createdListWindow.headerOptions is None
    # Check ListWidow init options:
    assert createdListWindow.nColumns == 3
    assert createdListWindow.lines == []
    assert createdListWindow.tableMaxLen == [
        len("Column1"),
        len("Column2"),
        len("Column3"),
    ]
    with pytest.raises(ValueError):
        ListWindow(100, 100, {"Title": "List"}, 2, ("Column1", "Column2", "Column3"))


def test_08_display_ListWindow_update():
    createdListWindow = ListWindow(
        100, 100, {"Title": "List"}, 3, ("Column1", "Column2", "Column3")
    )
    createdListWindow.setHeader()
    with pytest.raises(TypeError):
        createdListWindow.update("NotATuple")
    with pytest.raises(TypeError):
        createdListWindow.update(["NotATuple"])
    with pytest.raises(ValueError):
        createdListWindow.update(("1", "2", "3", "4"))
    with pytest.raises(ValueError):
        createdListWindow.update(("1", "2"))
    createdListWindow.lines = []
    entry1 = ("Entry1,1", "Entry1,2", "Entry1,3")
    createdListWindow.update(entry1)
    assert entry1 == createdListWindow.lines[0]
    entry2 = ("Entry2,1", "Entry2,2", "Entry2,3")
    entry3 = ("Entry3,1", "Entry3,2", "Entry3,3")
    createdListWindow.update([entry2, entry3])
    assert entry2 == createdListWindow.lines[1]
    assert entry3 == createdListWindow.lines[2]


def test_09_display_ListWindow_draw(preCreatedListWindow, capsys):
    assert preCreatedListWindow.draw()
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out != ""


def test_10_display_ListWindow_splitOptionLine(preCreatedListWindow):
    nSplit, remainingElem = preCreatedListWindow.splitOptionLine(
        ["1 : Code1", "2 : Code2", "3 : Code3"], 30
    )
    assert nSplit == 2
    assert remainingElem == ["3 : Code3"]


def test_11_display_ListWindow_smallOptionTable(preCreatedListWindow):
    smallOptionTable, tableLen = preCreatedListWindow.makeSmallOptionTable()
    assert isinstance(smallOptionTable, list)
    expectedOptions = []
    for option in preCreatedListWindow.headerOptions:
        id, name, comment = option
        expectedOptions.append("{0} : {1}".format(id, name))
    foundExpectation = False
    for line in smallOptionTable:
        assert len(line) == preCreatedListWindow.width
        if " | ".join(expectedOptions) in line:
            foundExpectation = True
        print(line)
    assert foundExpectation


def test_12_display_ListWindow_smallOptionTable_MultiLine(preCreatedListWindow):
    orig = preCreatedListWindow.headerOptions
    preCreatedListWindow.headerOptions = [
        ("0", "FirstName_", "Comment"),
        ("1", "SecondName_", "Comment"),
        ("2", "ThirdName_", "Comment"),
        ("3", "FourthName_", "Comment"),
        ("4", "FifthName_", "Comment"),
        ("5", "FifthName_", "Comment"),
    ]
    smallOptionTable, tableLen = preCreatedListWindow.makeSmallOptionTable()
    print(smallOptionTable)
    assert isinstance(smallOptionTable, list)
    expectedOptions = []
    for option in preCreatedListWindow.headerOptions[:4]:
        id, name, comment = option
        expectedOptions.append("{0} : {1}".format(id, name))
    expectedLines = [" | ".join(expectedOptions)]
    expectedLines += [
        "{0} : {1}".format(
            preCreatedListWindow.headerOptions[5][0],
            preCreatedListWindow.headerOptions[5][1],
        )
    ]
    foundExpectation = [False, False]
    for line in smallOptionTable:
        assert len(line) == preCreatedListWindow.width
        if expectedLines[0] in line:
            foundExpectation[0] = True
        if expectedLines[1] in line:
            foundExpectation[1] = True
        print(line)
    assert all(foundExpectation)
    preCreatedListWindow.headerOptions = orig


def test_13_display_ListWindow_interact(preCreatedListWindow, capsys):
    def mock_input(s):
        return s + " (mocked)"

    display.input = mock_input
    preCreatedListWindow.interact("Requesting input", "Small")
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out != ""


@pytest.mark.parametrize("height", [(15)])
def test_14_display_ListWindow_fillEmpty(preCreatedListWindow, capsys, height):
    createdListWindow = ListWindow(
        height, 100, {"Title": "List"}, 3, ("Column1", "Column2", "Column3")
    )
    createdListWindow.setHeader()
    createdListWindow.makeheader()
    tableLines = createdListWindow.makeTable(
        createdListWindow.tableHeaderElements,
        createdListWindow.lines,
        createdListWindow.tableMaxLen,
    )
    leftAlignTableLines = []
    for line in tableLines:
        lineLen = len(line)
        leftAlignTableLines.append(
            " " + line + " " + (createdListWindow.boxWidth - lineLen) * " "
        )
    headerLines = createdListWindow.header
    createdListWindow.draw(fillWindow=True)
    captured = capsys.readouterr()
    lineIdentifiers = list(string.ascii_lowercase) + list(string.ascii_uppercase)
    blankLines = (height - len(headerLines) - len(tableLines)) * [100 * " "]
    expectedLines = []
    for iline, line in enumerate(headerLines + blankLines + leftAlignTableLines):
        expectedLines.append(line.replace(" ", lineIdentifiers[iline]))
    modCapturedLines = []
    for iline, line in enumerate(captured.out.split("\n")):
        if line != "":
            modCapturedLines.append(line.replace(" ", lineIdentifiers[iline]))
    #####################################################################################
    print(
        "/////////////////////////////// EXPECTATION /////////////////////////////////////"
    )
    for line in expectedLines:
        print(line)
    print(
        "///////////////////////////////// RETURN ////////////////////////////////////////"
    )
    for line in modCapturedLines:
        print(line)
    #####################################################################################
    assert len(expectedLines) == len(modCapturedLines)
    for iline in range(len(modCapturedLines)):
        assert modCapturedLines[iline] == expectedLines[iline]


@pytest.mark.parametrize("height", [(15)])
def test_15_display_ListWindow_fillEmpty_skipTable(
    preCreatedListWindow, capsys, height
):
    createdListWindow = ListWindow(
        height, 100, {"Title": "List"}, 3, ("Column1", "Column2", "Column3")
    )
    createdListWindow.setHeader()
    createdListWindow.makeheader()
    headerLines = createdListWindow.header
    createdListWindow.draw(fillWindow=True, skipTable=True)
    captured = capsys.readouterr()
    lineIdentifiers = list(string.ascii_lowercase) + list(string.ascii_uppercase)
    blankLines = (height - len(headerLines)) * [100 * " "]
    expectedLines = []
    for iline, line in enumerate(headerLines + blankLines):
        expectedLines.append(line.replace(" ", lineIdentifiers[iline]))
    modCapturedLines = []
    for iline, line in enumerate(captured.out.split("\n")):
        if line != "":
            modCapturedLines.append(line.replace(" ", lineIdentifiers[iline]))
    #####################################################################################
    print(
        "/////////////////////////////// EXPECTATION /////////////////////////////////////"
    )
    for line in expectedLines:
        print(line)
    print(
        "///////////////////////////////// RETURN ////////////////////////////////////////"
    )
    for line in modCapturedLines:
        print(line)
    #####################################################################################
    assert len(expectedLines) == len(modCapturedLines)
    for iline in range(len(modCapturedLines)):
        assert modCapturedLines[iline] == expectedLines[iline]


@pytest.mark.parametrize("height", [(30)])
def test_16_display_ListWindow_fillEmpty_afterTableDraw(capsys, height):
    """
    This test is used to varify
    """

    def mock_input(s):
        return s + " (mocked)"

    createdListWindow = ListWindow(
        height, 100, {"Title": "List"}, 3, ("Column1", "Column2", "Column3")
    )
    createdListWindow.setHeader()
    createdListWindow.makeheader()
    headerLines = createdListWindow.header
    tableEntries = []
    tableEntries2 = []
    for i in range(5):
        tableEntries.append(
            ("Entry" + str(i) + ",1", "Entry" + str(i) + ",2", "Entry" + str(i) + ",3")
        )
        tableEntries2.append(
            (
                "SecEntry" + str(i) + ",1",
                "SecEntry" + str(i) + ",2",
                "SecEntry" + str(i) + ",3",
            )
        )
    createdListWindow.update(tableEntries)
    tableLines = createdListWindow.makeTable(
        createdListWindow.tableHeaderElements,
        createdListWindow.lines,
        createdListWindow.tableMaxLen,
    )
    createdListWindow.draw(fillWindow=True)
    captured = capsys.readouterr()
    # -1 because there is one empty element after the split
    assert len(captured.out.split("\n")) - 1 == height

    # for iline, line in enumerate(captured.out.split("\n")):
    #     print(iline, "a ",line)
    # captured = capsys.readouterr()
    display.input = mock_input
    createdListWindow.interact("Requesting input", None, onlyInteraction=True)
    createdListWindow.lines = []
    createdListWindow.update(tableEntries2)
    tableLines2 = createdListWindow.makeTable(
        createdListWindow.tableHeaderElements,
        createdListWindow.lines,
        createdListWindow.tableMaxLen,
    )
    createdListWindow.draw(fillWindow=True)

    captured = capsys.readouterr()
    assert len(captured.out.split("\n")) - 1 == height
    # for iline, line in enumerate(captured.out.split("\n")):
    #     print("{0:2}".format(iline), "b",line)

    # Build expectation
    lineIdentifiers = 3 * (
        list(string.ascii_lowercase) + list(string.ascii_uppercase) + list(range(10))
    )
    leftAlignTableLines = []
    for line in tableLines:
        lineLen = len(line)
        leftAlignTableLines.append(
            " " + line + " " + (createdListWindow.boxWidth - lineLen) * " "
        )
    leftAlignTableLines2 = []
    for line in tableLines2:
        lineLen = len(line)
        leftAlignTableLines2.append(
            " " + line + " " + (createdListWindow.boxWidth - lineLen) * " "
        )

    interactionStr = "" + mock_input("Requesting input: Requesting input: ")
    interaction = [interactionStr + " " * (100 - len(interactionStr))]

    blankLines = (
        height
        - len(headerLines)
        - len(leftAlignTableLines)
        - len(leftAlignTableLines2)
        - 1
    ) * [100 * " "]

    expectedLines = []
    for iline, line in enumerate(
        headerLines
        + blankLines
        + leftAlignTableLines
        + interaction
        + leftAlignTableLines2
    ):
        expectedLines.append(line.replace(" ", lineIdentifiers[iline]))

    modCapturedLines = []
    for iline, line in enumerate(captured.out.split("\n")):
        if line != "":
            modCapturedLines.append(line.replace(" ", str(lineIdentifiers[iline])))

    ####################################################################################
    print(
        "/////////////////////////////// EXPECTATION /////////////////////////////////////"
    )
    for line in expectedLines:
        print(line)
    print(
        "///////////////////////////////// RETURN ////////////////////////////////////////"
    )
    for line in modCapturedLines:
        print(line)
    ####################################################################################
    assert len(expectedLines) == len(modCapturedLines)
    for iline in range(len(modCapturedLines)):
        assert modCapturedLines[iline] == expectedLines[iline]


def test_17_display_Window_makeHeader_SecondaryText(preCreatedWindowAndElements):
    headerElements, preCreatedWindow = preCreatedWindowAndElements

    assert preCreatedWindow.headerTextSecondary == {}

    preCreatedWindow.headerTextSecondary["SomeStatement"] = "Some Information"
    preCreatedWindow.headerTextSecondary["SomeMoreStatement"] = "Some More Information"
    preCreatedWindow.makeheader()
    print(
        "///////////////////////////////// HEADER ////////////////////////////////////////"
    )
    for line in preCreatedWindow.header:
        print(line)
    print(
        "/////////////////////////////////////////////////////////////////////////////////"
    )
    for key in preCreatedWindow.headerTextSecondary.keys():
        expectedText = "{0}: {1}".format(key, preCreatedWindow.headerTextSecondary[key])
        foundLine = False
        for line in preCreatedWindow.header:
            if expectedText in line:
                foundLine = True
        assert foundLine
