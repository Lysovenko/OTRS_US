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
"Page loader parrent"
import os
import re
from time import strftime
from urllib.parse import urlparse, parse_qsl, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.client import BadStatusLine
from gzip import decompress
from .parse.dashboard import DashboardParser
from .parse.tickets import TicketsParser
from .parse.messages import MessageParser, AnswerParser
from .multipart import dump_multipart_text


class LoginError(RuntimeError):
    pass


class Page:
    def __init__(self, core):
        self.core_cfg = core.call("core cfg")
        self.runt_cfg = core.call("runtime cfg")
        self.echo = core.echo
        self.last_url = ""

    def parse(self, data):
        "Dummy method to be replaced"
        print(data)

    def load(self, location, data=None, headers={}):
        if not location:
            raise LoginError()
        self.last_url = re.sub(r"https?:\/\/[^/]+", r"", location)
        heads = {"Accept-Encoding": "gzip, deflate"}
        if "Cookies" in self.runt_cfg:
            heads["Cookie"] = self.runt_cfg["Cookies"]
        heads.update(headers)
        r = Request(location, data, headers=heads)
        try:
            pg = urlopen(r)
        except HTTPError as err:
            self.echo("HTTP Error:", err.getcode())
            return
        except Exception as err:
            self.echo(repr(err))
            return
        pd = pg.read()
        if pg.getheader("Content-Encoding") == "gzip":
            pd = decompress(pd)
        self.dump_data(pg, pd)
        if not self.check_login(pd.decode(errors="ignore")):
            raise LoginError(r.get_full_url())
        return self.parse(pd)

    def login(self, who=None, req=None):
        "login and load"
        if who is None:
            who = self.runt_cfg
        if req is None:
            req = self.last_url
        user = who["user"]
        passwd = who["password"]
        site = who["site"]
        r = Request(
            site, urlencode(
                [("Action", "Login"), ("RequestedURL", req), ("Lang", "en"),
                 ("TimeOffset", ""), ("User", user), ("Password", passwd),
                 ("login", "Login")]).encode())
        try:
            pg = urlopen(r)
        except BadStatusLine:
            raise LoginError("BadStatusLine")
        pd = pg.read()
        if pg.getheader("Content-Encoding") == "gzip":
            pd = decompress(pd)
        m = re.search(r"OTRSAgentInterface=[^;&]+", pg.geturl())
        if m.group(0):
            self.runt_cfg["Cookies"] = m.group(0)
        else:
            self.runt_cfg.pop("Cookies", None)
        self.dump_data(pg, pd)
        return self.parse(pd)

    def check_login(self, pd):
        for i in pd.splitlines():
            if "<title>" in i and "Login" in i:
                return False
        return True

    def dump_data(self, page, data):
        if "pg_dum_to" not in self.core_cfg:
            return
        try:
            path = self.core_cfg["pg_dum_to"][0]
        except Exception as err:
            print("Exception: {0}".format(err))
            return
        classes = self.core_cfg["pg_dum_to"][1:]
        cl_name = str(self.__hash__).split()[3]
        if cl_name not in classes:
            return
        tdate = strftime("%b_%d_%H-%M-%S")
        fname = "%s-%s.html" % (cl_name, tdate)
        fname = os.path.join(path, fname)
        try:
            with open(fname, "wb") as fp:
                fp.write(("URL:\t%s\n" % page.geturl()).encode())
                fp.write(("CODE:\t%d\n" % page.getcode()).encode())
                for header in page.getheaders():
                    fp.write(("%s:\t%s\n" % header).encode())
                fp.write(b"\n")
                fp.write(data)
        except OSError as err:
            print("OSError: {0}".format(err))


class DashboardPage(Page):
    def parse(self, data):
        parser = DashboardParser()
        parser.feed(data.decode(errors="ignore"))
        parser.close()
        return parser.tickets


class TicketsPage(Page):
    def parse(self, data):
        parser = TicketsParser()
        parser.feed(data.decode(errors="ignore"))
        parser.close()
        res = {}
        for i in ("message_text", "articles", "info", "mail_header",
                  "action_hrefs", "queues", "mail_src", "art_act_hrefs",
                  "answers"):
            attr = getattr(parser, i)
            if attr:
                res[i] = attr
        for i in ("queues", "answers"):
            if not res[i][1]:
                del res[i]
        try:
            anss = res["answers"][1]
            hl = len(anss) // 2
            if anss[hl][0] == anss[0][0]:
                del anss[hl:]
        except (KeyError, IndexError):
            pass
        try:
            res["message_text"] = [(i,) for i in res["message_text"]]
        except KeyError:
            pass
        return res


class MessagePage(Page):
    def parse(self, data):
        parser = MessageParser()
        parser.feed(data.decode(errors="ignore"))
        parser.close()
        if parser.message_text:
            return parser.message_text
        else:
            return [(i,) for i in parser.data_handler]


class AnswerPage(Page):
    def parse(self, data):
        parser = AnswerParser()
        parser.feed(data.decode(errors="ignore"))
        parser.close()
        return parser.inputs, parser.error_msg


class AnswerSender(Page):
    def parse(self, data):
        return

    def send(self, location, data_list):
        da, di = dump_multipart_text(data_list)
        self.load(location, da, di)
