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
        self.tickets = {"New": [], "Open": [], "Reminder": []}
        self.cur_array = None
        self.cur_append = None
        self.importance = 0

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
            return
        if tag == "a" and dattrs.get("class") == "AsBlock MasterActionLink":
            self.cur_append = (dattrs["href"], dattrs["title"])
            self.data_handler = []
            return
        if tag == "span":
            cls = dattrs.get("class", "").split()
            if "UnreadArticles" in cls:
                self.importance = 3 if "Important" in cls else 1

    def handle_endtag(self, tag):
        if tag == "a" and self.cur_append is not None:
            self.cur_array.append(
                self.cur_append + ("".join(self.data_handler),
                                   self.importance))
            self.data_handler = None
            self.cur_append = None
            self.importance = 0
