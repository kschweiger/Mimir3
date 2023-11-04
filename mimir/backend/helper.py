"""Helper functions for mimir modules"""
import datetime
import logging

logger = logging.getLogger(__name__)


class IdQueue:
    def __init__(self, max_len: int) -> None:
        self.container = []
        self.max_len = max_len

    def append(self, elem) -> None:
        self.container.append(elem)
        if len(self.container) > self.max_len:
            self.container.pop(0)

    def containes(self, elem) -> bool:
        return elem in self.container


def getTimeFormatted(retFormat, delimDate=".", inverted=False):
    """
    Helper function to get the the current time/date

    Options for retFormat:
        Full : Returns date + time
        Time : Returns time
        Date : Returns date
    """
    currently = datetime.datetime.now()
    day = currently.day
    month = currently.month
    year = currently.year
    hour = currently.hour
    minutes = currently.minute
    sec = currently.second
    if inverted:
        fulldate = "{2:02}{3}{1:02}{3}{0:02}".format(day, month, year - 2000, delimDate)
    else:
        fulldate = "{0:02}{3}{1:02}{3}{2:02}".format(day, month, year - 2000, delimDate)
    fulltime = "{0:02}:{1:02}:{2:02}".format(hour, minutes, sec)
    if retFormat == "Full":
        return fulldate + "|" + fulltime
    elif retFormat == "Time":
        return fulltime
    elif retFormat == "Date":
        return fulldate
    else:
        logger.warning(
            "Function was called with %s as argument. Falling back to Full output",
            retFormat,
        )
        return fulldate + "|" + fulltime


def sortDateTime(list2Sort):
    """
    Helper function to convert the datetime values from getTimeFormatted() back
    to datetime objects and return them in a sorted list
    """
    datetimeObj = []
    for elem in list2Sort:
        try:
            datetimeObj.append(convertToDateTime(elem))
        except TypeError:
            logger.debug("Converting %s to 01.01.00|00:00:00" % elem)
            datetimeObj.append(convertToDateTime("01.01.00|00:00:00"))
    datetimeObj = sorted(datetimeObj, reverse=True)
    retList = []
    for elem in datetimeObj:
        retList.append(
            "{0:02}.{1:02}.{2:02}|{3:02}:{4:02}:{5:02}".format(
                elem.day,
                elem.month,
                elem.year - 2000,
                elem.hour,
                elem.minute,
                elem.second,
            )
        )

    return retList


def convertToDateTime(internalString):
    """
    Helper function to convert an internal datestring back to a datetime object
    """
    if len(internalString.split("|")) != 2:
        raise TypeError(
            "Element is expected to be of form DD.MM.YY|HH:MM:SS but is %s"
            % internalString
        )
    date, time = internalString.split("|")
    if len(date.split(".")) != 3:
        raise RuntimeError("Date is expected as  DD.MM.YY with '.' as delimiter")
    if len(time.split(":")) != 3:
        raise RuntimeError("Date is expected as  HH:MM:SS with ':' as delimiter")
    day, month, year = date.split(".")
    hour, minute, sec = time.split(":")
    return datetime.datetime(
        2000 + int(year), int(month), int(day), int(hour), int(minute), int(sec)
    )
