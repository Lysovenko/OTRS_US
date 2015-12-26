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
from .basic import BasicParser


class DashboardParser(BasicParser):
    def __init__(self):
        BasicParser.__init__(self)
        self.tickets = {"New": [], "Open": [], "Reminder": [], "inputs": {}}
        self.cur_array = None
        self.cur_append = {}
        self.importance = 0
        self.head_names = []
        self.cur_column = -1

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if tag == "div":
            div_id = dattrs.get("id")
            if div_id == "Dashboard0120-TicketNew":
                self.cur_array = self.tickets["New"]
            if div_id == "Dashboard0130-TicketOpen":
                self.cur_array = self.tickets["Open"]
            if div_id == "Dashboard0100-TicketPendingReminder":
                self.cur_array = self.tickets["Reminder"]
            if 0 <= self.cur_column < len(self.head_names):
                cn = self.head_names[self.cur_column]
                if cn is not None and "title" in dattrs:
                    self.cur_append[cn] = dattrs["title"]
            return
        if tag == "a" and dattrs.get("class") == "AsBlock MasterActionLink":
            self.cur_append.update((i, dattrs[i]) for i in ("href", "title"))
            self.data_handler = []
            return
        if tag == "span":
            cls = dattrs.get("class", "").split()
            if "UnreadArticles" in cls:
                self.importance = 3 if "Remarkable" in cls else 1
            return
        if tag == "input":
            self.tickets["inputs"][dattrs.get("name")] = dattrs.get("value")
        if tag == "tr":
            self.cur_column = -1
            self.cur_append = {}
            return
        if tag == "td":
            self.cur_column += 1
            return
        if tag == "th":
            self.head_names.append(dattrs.get("data-column"))
            return
        if tag == "thead":
            self.head_names = []
            return

    def handle_endtag(self, tag):
        if tag == "a" and self.data_handler:
            self.cur_append["number"] = "".join(self.data_handler)
            self.cur_append["marker"] = self.importance
            self.cur_array.append(self.cur_append)
            self.data_handler = None
            self.importance = 0
            return
        if tag == "tr":
            self.cur_append = None
