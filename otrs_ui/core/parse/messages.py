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
        self.data_handler = self.message_text


class AnswerParser(BasicParser):
    def __init__(self):
        BasicParser.__init__(self)
        self.inputs = []

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if tag == "input":
            self.inputs.append(tuple(
                dattrs.get(i) for i in ("name", "value")))
            return
        if tag == "textarea":
            self.tags_name = dattrs.get("name")
            self.data_handler = []

    def handle_endtag(self, tag):
        if tag == "textarea":
            self.inputs.append(
                (self.tags_name, "".join(self.data_handler)))
            self.data_handler = None
