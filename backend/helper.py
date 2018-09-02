"""Helper functions for mimir modules"""
import datetime
import logging


def getTimeFormatted(retFormat):
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
    fulldate = "{0:02}.{1:02}.{2:02}".format(day, month, year-2000)
    fulltime = "{0:02}:{1:02}:{2:02}".format(hour, minutes, sec)
    if retFormat == "Full":
        return fulldate+"|"+fulltime
    elif retFormat == "Time":
        return fulltime
    elif retFormat == "Date":
        return fulldate
    else:
        logging.warning("Function was called with %s as argument. Falling back to Full output", retFormat)
        return fulldate+"|"+fulltime
