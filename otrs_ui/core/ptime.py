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


class TimeConv:
    "Time converter"
    def __init__(self, yday="yest.", mago="min. ago"):
        self.cur = localtime()
        self.curs = mktime(self.cur)
        self.yday = yday
        self.mago = mago

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
        return strftime("%d/%m/%y", self.time)
