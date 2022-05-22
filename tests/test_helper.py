# flake8: noqa
import datetime
import os
import sys
import unittest

import coverage
import pytest

# sys.path.insert(0, os.path.abspath('..'))
# sys.path.insert(0, os.path.abspath('.'))
# print(sys.path)
import mimir.backend.helper
import mimir.frontend.terminal.helper


def test_01_datetime():
    # Get all possible outputs from function
    dateFull = mimir.backend.helper.getTimeFormatted("Full")
    dateFallback = mimir.backend.helper.getTimeFormatted("UNDEFINEDARG")
    dateTime = mimir.backend.helper.getTimeFormatted("Time")
    dateDate = mimir.backend.helper.getTimeFormatted("Date")
    dateDateInvert = mimir.backend.helper.getTimeFormatted("Date", inverted=True)

    # Get current time
    currently = datetime.datetime.now()
    day = currently.day
    month = currently.month
    year = currently.year
    hour = currently.hour
    minutes = currently.minute
    sec = currently.second  # not going to test seconds....

    invertedDate = "{0:02}{3}{1:02}{3}{2:02}".format(year - 2000, month, day, ".")

    splitoutput = dateFull.split("|")
    date = splitoutput[0]
    day2test = date.split(".")[0]
    month2test = date.split(".")[1]
    year2test = date.split(".")[2]
    time = splitoutput[1]
    hour2test = time.split(":")[0]
    minute2test = time.split(":")[1]
    second2test = time.split(":")[2]
    assert (
        len(splitoutput) == 2
        and int(day2test) == day
        and int(month2test) == month
        and int(year2test) == year - 2000
        and int(hour2test) == hour
        and abs(int(minute2test) - minutes) <= 1
        and abs(int(second2test) - sec) <= 3
    )

    assert dateFull == dateFallback

    assert dateTime == time
    assert dateDate == date
    print(dateFull, dateDate, dateDateInvert, invertedDate)
    assert dateDateInvert == invertedDate


def test_02_convertInternalString():
    with pytest.raises(TypeError):
        mimir.backend.helper.convertToDateTime("Blubb")
    # Check error for invalid date
    with pytest.raises(RuntimeError):
        mimir.backend.helper.convertToDateTime("Blubb|00:00:00")
    # Check error for invalid time
    with pytest.raises(RuntimeError):
        mimir.backend.helper.convertToDateTime("01.01.01|Blubb")

    internalString = "01.01.19|00:00:00"
    datetimeObj = mimir.backend.helper.convertToDateTime(internalString)
    retConverted = "{0:02}.{1:02}.{2:02}|{3:02}:{4:02}:{5:02}".format(
        datetimeObj.day,
        datetimeObj.month,
        datetimeObj.year - 2000,
        datetimeObj.hour,
        datetimeObj.minute,
        datetimeObj.second,
    )
    assert retConverted == internalString


def test_03_sortDateTime():
    # Check sorted with same date
    sortedList = mimir.backend.helper.sortDateTime(
        [
            "01.01.19|00:00:00",
            "01.02.19|01:00:00",
            "01.01.19|01:01:00",
            "01.01.19|01:01:01",
        ]
    )
    expectedList = [
        "01.02.19|01:00:00",
        "01.01.19|01:01:01",
        "01.01.19|01:01:00",
        "01.01.19|00:00:00",
    ]
    assert len(sortedList) == len(expectedList)
    for iElem, elem in enumerate(sortedList):
        assert elem == expectedList[iElem]
    # Check sorted by date and time
    sortedList = mimir.backend.helper.sortDateTime(
        [
            "01.04.19|00:00:00",
            "01.02.19|01:00:00",
            "01.02.19|12:00:00",
            "01.01.19|01:01:01",
        ]
    )
    expectedList = [
        "01.04.19|00:00:00",
        "01.02.19|12:00:00",
        "01.02.19|01:00:00",
        "01.01.19|01:01:01",
    ]
    assert len(sortedList) == len(expectedList)
    for iElem, elem in enumerate(sortedList):
        assert elem == expectedList[iElem]


def test_04_fixedList():
    fixedList = mimir.frontend.terminal.helper.FixedList(5)
    assert fixedList.elements == []


def test_05_fixedList_len():
    fixedList = mimir.frontend.terminal.helper.FixedList(5)
    assert len(fixedList) == 0
    fixedList.append(1)
    assert len(fixedList) == 1
    assert fixedList.elements[0] == 1
    fixedList.append(2)
    fixedList.append(3)
    fixedList.append(4)
    fixedList.append(5)
    assert len(fixedList) == 5 and fixedList.elements == [1, 2, 3, 4, 5]
    fixedList.append(6)
    assert len(fixedList) == 5
    assert fixedList.elements == [2, 3, 4, 5, 6]
    fixedList.append(7)
    assert len(fixedList) == 5
    assert fixedList.elements == [3, 4, 5, 6, 7]


def test_06_fixedList_getItem():
    fixedList = mimir.frontend.terminal.helper.FixedList(5)
    fixedList.elements = [1, 2, 3, 4, 5]
    assert fixedList[0] == 1
    assert fixedList[4] == 5
    with pytest.raises(IndexError):
        fixedList[5]


def test_07_fixedList_loop():
    fixedList = mimir.frontend.terminal.helper.FixedList(5)
    fixedList.elements = [1, 2, 3, 4, 5]
    iElem = 0
    for elem in fixedList:
        print(elem)
        assert elem == fixedList.elements[iElem]
        iElem += 1
    assert iElem == 5
