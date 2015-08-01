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
from urllib.parse import urlparse, parse_qsl, urlencode
from urllib.request import Request, urlopen
from ..parse.dashboard import DashboardParser
from ..parse.tickets import TicketsParser

_REQUESTS = {}


class Page:
    def __init__(self, core):
        self.core_cfg = core.call("core cfg")
        self.runt_cfg = core.call("runtime cfg")

    def parse(self, data):
        "Dummy method to be replaced"
        print(data)

    def load(self, location):
        try:
            session = self.runt_cfg["Session"]
        except KeyError:
            raise RuntimeError()
        r = Request("%s?%s" % (location, urlencode([("Session", session)])))
        try:
            pg = urlopen(r)
        except Exception:
            return
        pd = pg.read()
        if not self.check_login(pd.decode()):
            raise RuntimeError()
        return self.parse(pd.decode())

    def login(self, who, req=""):
        if who is None:
            who = self.runt_cfg
        user = who["user"]
        passwd = who["password"]
        site = who["site"]
        r = Request(
            site, urlencode(
                [("Action", "Login"), ("RequestedURL", req), ("Lang", "en"),
                 ("TimeOffset", ""), ("User", user), ("Password", passwd),
                 ("login", "Login")]).encode())
        pg = urlopen(r)
        url = pg.geturl()
        qpl = parse_qsl(urlparse(url).query)
        dpl = dict(qpl)
        if "Session" not in dpl:
            raise RuntimeError()
        self.runt_cfg["Session"] = dpl["Session"]

    def check_login(self, pd):
        for i in pd.splitlines():
            if "<title>" in i and "Login" in i:
                return False
        return True


class DashboardPage(Page):
    def parse(self, data):
        parser = DashboardParser()
        parser.feed(data)
        parser.close()
        return parser.tickets


class TicketsPage(Page):
    def parse(self, data):
        parser = TicketsParser()
        parser.feed(data)
        parser.close()
        return parser.articles
