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
    def __init__(self):
        di = {}
        if hexversion >= 0x030200f0:
            di["strict"] = False
        HTMLParser.__init__(self, **di)
        self.row = None
        self.td_class = None
        self.in_table = False
        self.in_tbody = False
        self.WidgetSimple = 0
        self.ArticleMailHeader = 0
        self.ArticleBody = 0
        self.str_to_info = False
        self.label = None
        self.message_text = []
        self.articles = []
        self.info = []
        self.mail_header = []

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if tag == "input":
            cls = dattrs.get("class")
            if cls == "ArticleInfo" and self.row is not None:
                self.row["article info"] = dattrs["value"]
            if cls == "SortData" and self.row is not None:
                self.row[self.td_class] = dattrs["value"]
            return
        if tag == "td":
            self.td_class = dattrs.get("class")
            return
        if tag == "tr" and self.in_tbody:
            self.row = {"row": dattrs.get("class")}
            return
        if tag == "table":
            if dattrs.get("id") == "FixedTable":
                self.in_table = True
            return
        if tag == "tbody" and self.in_table:
            self.in_tbody = True
            return
        if tag == "div":
            cls = dattrs.get("class")
            if cls == "WidgetSimple":
                self.WidgetSimple += 1
            elif self.WidgetSimple:
                self.WidgetSimple += 1
            if cls == "ArticleMailHeader":
                self.ArticleMailHeader += 1
            elif self.ArticleMailHeader:
                self.ArticleMailHeader += 1
            if cls == "ArticleBody":
                self.ArticleBody += 1
            elif self.ArticleBody:
                self.ArticleBody += 1
            return
        if tag == "h2" and self.WidgetSimple:
            self.str_to_info = True
            return
        if tag == "label":
            self.label = True
            return
        if tag == "p":
            if dattrs.get("class") == "Value":
                if self.WidgetSimple:
                    self.info.append((self.label, dattrs.get("title")))
                if self.ArticleMailHeader:
                    self.mail_header.append((self.label, dattrs.get("title")))
                self.label = None

    def handle_data(self, data):
        if self.str_to_info:
            self.info.append(data)
            return
        if self.label is not None:
            self.label = data
            return
        if self.ArticleBody:
            self.message_text.append(data)
            return

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
            return
        if tag == "tbody":
            self.in_tbody = False
            return
        if tag == "tr" and self.row is not None:
            self.articles.append(self.row)
            self.row = None
            return
        if tag == "td":
            self.td_class = None
            return
        if tag == "div":
            if self.WidgetSimple:
                self.WidgetSimple -= 1
            if self.ArticleMailHeader:
                self.ArticleMailHeader -= 1
            if self.ArticleBody:
                self.ArticleBody -= 1
            return
        if tag == "h2":
            self.str_to_info = False
            return


class MessageParser(HTMLParser):
    def __init__(self):
        di = {}
        if hexversion >= 0x030200f0:
            di["strict"] = False
        HTMLParser.__init__(self, **di)
        self.message_text = []

    def handle_data(self, data):
        self.message_text.append(data)
