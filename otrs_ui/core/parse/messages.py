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
from .basic import BasicParser


class MessageParser(BasicParser):
    def __init__(self):
        BasicParser.__init__(self)
        self.message_text = []
        self.data_handler = []
        self.curtags = []
        self.preformatted = 0

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            del self.data_handler[:]
            del self.message_text[:]
            del self.curtags[:]
            self.preformatted = 0
        self.append_msg_text()
        dattrs = dict(attrs)
        if tag == "h1":
            self.curtags.append(tag)
            return
        if tag == "p":
            self.message_text.append(("\n    ",))
            return
        if tag == "br":
            self.message_text.append(("\n",))
            return
        if tag == "div":
            self.message_text.append(("\n<div>\n",))
            return
        if tag == "img":
            self.message_text.append(("\n<img>\n", ("h1",)))
            return
        if tag == "pre":
            self.preformatted += 1
            return

    def handle_endtag(self, tag):
        self.append_msg_text()
        if self.curtags and tag == self.curtags[-1]:
            self.curtags.pop(-1)
        if tag == "div":
            self.message_text.append(("\n</div>\n",))
            return
        if tag == "pre":
            self.preformatted -= 1
            return

    def append_msg_text(self):
        if self.preformatted:
            self.message_text.append(
                ("".join(self.data_handler), tuple(self.curtags)))
        else:
            tspl = []
            for i in self.data_handler:
                tspl += i.split()
            if tspl:
                self.message_text.append((" ".join(tspl), tuple(self.curtags)))
        del self.data_handler[:]


class AnswerParser(BasicParser):
    def __init__(self):
        BasicParser.__init__(self)
        self.inputs = []
        self.cur_select = None
        self.cur_option = None
        self.error_msg = None

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if tag == "input":
            self.inputs.append(tuple(
                dattrs.get(i) for i in ("name", "value")))
            return
        if tag == "option":
            self.cur_option = dattrs["value"]
            if "selected" in dattrs:
                self.cur_select["selected"] = dattrs["value"]
            self.data_handler = []
            return
        if tag == "select":
            self.cur_select = dattrs
            dattrs["values"] = []
            return
        if tag == "textarea":
            self.tags_name = dattrs.get("name")
            self.data_handler = []
            return
        if tag == "span" and dattrs.get("class") == "Error":
            self.data_handler = []
            return

    def handle_endtag(self, tag):
        if tag == "option":
            self.cur_select["values"].append(
                (self.cur_option, "".join(self.data_handler)))
            self.data_handler = None
            return
        if tag == "select":
            cs = self.cur_select
            self.inputs.append(
                (cs["name"], (cs.get("selected"), cs["values"])))
            return
        if tag == "textarea":
            self.inputs.append(
                (self.tags_name, "".join(self.data_handler)))
            self.data_handler = None
            return
        if tag == "span":
            if self.data_handler:
                self.error_msg = "".join(self.data_handler)
                self.data_handler = None
            return
