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
"parse dashboard page"
from html.parser import HTMLParser
from sys import hexversion


class DashboardParser(HTMLParser):
    def __init__(self, rtcfg):
        di = {}
        if hexversion >= 0x030200f0:
            di["strict"] = False
        HTMLParser.__init__(self, **di)
        self.tickets = {"New": [], "Open": [], "Reminder": []}
        self.cur_array = None
        self.cur_append = None

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if tag == "div":
            if dattrs.get("id") == "Dashboard0120-TicketNew":
                self.cur_array = self.tickets["New"]
                del self.cur_array[:]
            if dattrs.get("id") == "Dashboard0130-TicketOpen":
                self.cur_array = self.tickets["Open"]
                del self.cur_array[:]
            if dattrs.get("id") == "Dashboard0100-TicketPendingReminder":
                self.cur_array = self.tickets["Reminder"]
                del self.cur_array[:]
        if tag == "a" and dattrs.get("class") == "AsBlock MasterActionLink":
            self.cur_append = (dattrs["href"], dattrs["title"])

    def handle_data(self, data):
        if self.cur_append is not None:
            self.cur_append += (data,)

    def handle_endtag(self, tag):
        if tag == "a" and self.cur_append is not None:
            self.cur_array.append(self.cur_append)
            self.cur_append = None
