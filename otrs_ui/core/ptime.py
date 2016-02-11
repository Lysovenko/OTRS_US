#!/usr/bin/env python3
# Copyright 2015-2016 Serhiy Lysovenko
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

from time import strptime, mktime, localtime, strftime, time
import re


def unix_time(expr, fmt):
    try:
        return int(mktime(strptime(expr, fmt)))
    except ValueError:
        return int(time())


class TimeConv:
    "Time converter"
    def __init__(self, yday="yest.", mago="min. ago", dago="days ago"):
        self.cur = localtime()
        self.curs = mktime(self.cur)
        self.yday = yday
        self.mago = mago
        self.dago = dago

    def set_modified(self, modified):
        self.time = localtime(modified)

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


class TimeUnit(float):
    "time units parser"
    def __new__(self, value):
        m = re.search(r"^\s*(\d*[,.]?\d*)\s*(s|m|h|ms|d|w)?\s*$", value)
        if m is None:
            raise ValueError("Bad time %s" % value)
        return float.__new__(self, float(m.group(1).replace(',', '.')) * {
            "w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1,
            None: 1, "ms": 1e-3}[m.group(2)])

    def __repr__(self):
        return "'%s'" % self.__str__()

    def __str__(self):
        secs = self.real
        for d, l in ((604800, 'w'), (86400, 'd'), (3600, 'h'), (60, 'm')):
            if not secs % d:
                return "%d %s" % (secs // d, l)
        if secs < 1:
            return "%g ms" % secs * 1000
        return "%g s" % secs
