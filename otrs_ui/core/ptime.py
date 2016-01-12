#!/usr/bin/env python3
# Copyright 2015 Serhiy Lysovenko
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"Parse some timestamps"

from time import strptime, mktime, localtime, strftime
import re


class TimeConv:
    "Time converter"
    def __init__(self, yday="yest.", mago="min. ago", dago="days ago"):
        self.cur = localtime()
        self.curs = mktime(self.cur)
        self.yday = yday
        self.mago = mago
        self.dago = dago

    def set_modified(self, modified):
        self.time = strptime(modified, "%m/%d/%Y %H:%M")

    def relative(self):
        cur = self.cur
        secs = 3600 * cur.tm_hour + 60 * cur.tm_min + cur.tm_sec
        delta = self.curs - mktime(self.time)
        if delta < 3600:
            return "%d %s" % (delta // 60, self.mago)
        if delta < secs:
            return strftime("%H:%M", self.time)
        if delta <= secs + 86400:
            return self.yday + " " + strftime("%H:%M", self.time)
        if delta < secs + 864000:
            return "%d %s" % ((delta - secs) // 86400 + 1, self.dago)
        return strftime("%d/%m/%y", self.time)


class TimeUnit:
    "time units parser"
    def __init__(self, value):
        print(value)
        m = re.search(r"(\d+([,.])?\d*)\s*((s)|(m)|(h)|(ms))?$", value)
        if m in None:
            raise ValueError("Bad time %s" % value)
        mantisa, dec_sep, units = (m.group(i) for i in range(1, 4))
        if dec_sep == ",":
            mantisa = mantisa.replace(',', '.')
        if units == "s":
            self.__seconds = float(mantisa)
        elif units == "m":
            self.__seconds = float(mantisa) * 60
        elif units == "h":
            self.__seconds = float(mantisa) * 3600
        elif units == "ms":
            self.__seconds = float(mantisa) * 1e-3
        else:
            raise ValueError("Bad time units %s" % units)

    def __repr__(self):
        return "%g s" % self.__seconds

    def seconds(self):
        return self.__seconds

    def miliseconds(self):
        return self.__seconds / 1000
