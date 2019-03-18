import sys
import os
#sys.path.insert(0, os.path.abspath('..'))
#sys.path.insert(0, os.path.abspath('.'))
#print(sys.path)
import mimir.backend.helper
import unittest
import pytest
import coverage

import datetime

class TestItem(unittest.TestCase):
    def test_01_datetime(self):
        #Get all possible outputs from function
        dateFull = mimir.backend.helper.getTimeFormatted("Full")
        dateFallback = mimir.backend.helper.getTimeFormatted("UNDEFINEDARG")
        dateTime = mimir.backend.helper.getTimeFormatted("Time")
        dateDate = mimir.backend.helper.getTimeFormatted("Date")


        #Get current time
        currently = datetime.datetime.now()
        day = currently.day
        month = currently.month
        year = currently.year
        hour = currently.hour
        minutes = currently.minute
        sec = currently.second #not going to test seconds....

        splitoutput = dateFull.split("|")
        date = splitoutput[0]
        day2test = date.split(".")[0]
        month2test = date.split(".")[1]
        year2test = date.split(".")[2]
        time = splitoutput[1]
        hour2test = time.split(":")[0]
        minute2test = time.split(":")[1]
        second2test = time.split(":")[2]
        assert (len(splitoutput ) == 2
                and int(day2test) == day and int(month2test) == month and  int(year2test) == year-2000
                and int(hour2test) == hour and abs(int(minute2test)-minutes) <= 1 and abs(int(second2test)-sec) <= 3)

        assert dateFull == dateFallback

        assert dateTime == time
        assert dateDate == date
