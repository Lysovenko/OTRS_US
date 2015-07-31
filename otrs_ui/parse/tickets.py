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
"parse tickets page"
from html.parser import HTMLParser
from sys import hexversion


class TicketsParser(HTMLParser):
    def __init__(self, rtcfg):
        di = {}
        if hexversion >= 0x030200f0:
            di["strict"] = False
        HTMLParser.__init__(self, **di)
        self.articles = []
        self.row = None
        self.td_class = None
        self.cur_append = None
        self.in_table = False
        self.in_tbody = False

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if tag == "table":
            if dattrs.get("id") == "FixedTable":
                self.in_table = True
        if tag == "tbody" and self.in_table:
            self.in_tbody = True
        if tag == "input":
            if dattrs.get("class") == "ArticleInfo" and self.row is not None:
                self.row += dattrs["value"]
        if tag == "tr" and self.in_tbody:
            self.row = ()
        if tag == "td":
            self.td_class = dattrs.get("class")

    def handle_data(self, data):
        pass

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.row is not None:
            self.articles.append(self.row)
            self.row = None
        if tag == "td":
            self.td_class = None
