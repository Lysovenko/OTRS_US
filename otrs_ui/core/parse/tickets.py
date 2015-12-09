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


class TicketsParser(BasicParser):
    def __init__(self):
        BasicParser.__init__(self)
        self.row = None
        self.td_class = None
        self.p_title = None
        self.in_table = False
        self.in_tbody = False
        self.p_value = False
        self.div_classes = dict()
        self.art_ctrl_cls = tuple(sorted(("LightRow", "Bottom")))
        self.opt_val = None
        self.on_div_end = {"ArticleBody": self.stop_data_handling}
        self.label = ""
        self.message_text = []
        self.articles = []
        self.info = []
        self.mail_header = []
        self.action_hrefs = []
        self.art_act_hrefs = []
        self.queues = [None, []]
        self.answers = [None, []]
        self.mail_src = None

    def stop_data_handling(self):
        self.data_handler = None

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        div_cls = self.div_classes
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
            if dattrs.get("id") == "ArticleTable":
                self.in_table = True
            return
        if tag == "tbody" and self.in_table:
            self.in_tbody = True
            return
        if tag == "div":
            cls = dattrs.get("class")
            for k in div_cls:
                div_cls[k] += 1
            if cls:
                scls = cls.split()
                try:
                    hcls, = scls
                except ValueError:
                    hcls = tuple(sorted(scls))
                if hcls not in div_cls:
                    div_cls[hcls] = 1
            if cls == "ArticleBody":
                self.data_handler = self.message_text
            return
        if tag == "title" or (tag == "h2" and "WidgetSimple" in div_cls):
            self.data_handler = []
            return
        if tag == "label":
            self.label = ""
            self.data_handler = []
            return
        if tag == "p":
            if "Value" in dattrs.get("class", "").split():
                self.p_value = True
                self.data_handler = []
                self.p_title = dattrs.get("title")
            return
        if tag == "a":
            if "ActionRow" in div_cls and "Scroller" not in div_cls:
                try:
                    self.action_hrefs.append(dattrs["href"])
                except KeyError:
                    pass
            if self.art_ctrl_cls in div_cls:
                try:
                    self.art_act_hrefs.append(dattrs["href"])
                except KeyError:
                    pass
            if self.p_value and dattrs.get("href"):
                self.data_handler.append("[%s]\n" % dattrs["href"])
            return
        if tag == "option":
            if "selected" in dattrs:
                if "ActionRow" in div_cls:
                    self.selected[0] = dattrs["value"]
                if self.art_ctrl_cls in div_cls:
                    self.answers[0] = dattrs["value"]
            self.opt_val = dattrs.get("value")
            self.data_handler = []
            return
        if tag == "iframe" and "ArticleMailContent" in div_cls:
            self.mail_src = dattrs.get("src")
            return

    def handle_endtag(self, tag):
        div_cls = self.div_classes
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
            for k in list(div_cls):
                div_cls[k] -= 1
                if div_cls[k] == 0:
                    del div_cls[k]
                    try:
                        self.on_div_end[k]()
                    except KeyError:
                        pass
            return
        if tag == "title" or (tag == "h2" and "WidgetSimple" in div_cls):
            self.info.append("".join(self.data_handler))
            self.data_handler = None
            return
        if tag == "label":
            self.label = "".join(self.data_handler)
            return
        if tag == "p" and self.p_value:
            self.p_value = False
            if self.p_title is None:
                title = "".join(self.data_handler)
            else:
                title = self.p_title
            self.data_handler = None
            if "WidgetSimple" in div_cls:
                self.info.append((self.label, title))
            if "ArticleMailHeader" in div_cls:
                self.mail_header.append((self.label, title))
        if tag == "option":
            if "ActionRow" in div_cls or any(
                    ["ActionRow" in i for i in div_cls]):
                self.queues[1].append(
                    (self.opt_val, "".join(self.data_handler)))
            if self.art_ctrl_cls in div_cls:
                self.answers[1].append(
                    (self.opt_val, "".join(self.data_handler)))
            self.data_handler = None
            return
