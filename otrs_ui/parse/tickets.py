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
        self.cur_array = None
        self.cur_append = None

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if tag == "input":
            if dattrs.get("class") == "ArticleInfo":
                self.articles.append(dattrs["value"])

    def handle_data(self, data):
        pass

    def handle_endtag(self, tag):
        pass
