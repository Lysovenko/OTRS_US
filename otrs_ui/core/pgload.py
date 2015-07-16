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


_REQUESTS = {}


class Page:
    def __init__(self, core):
        self.core_cfg = core.call("core cfg")
        self.runt_cfg = core.call("runtime cfg")

    def load(self, location):
        r = Request(location)
        try:
            pg = urlopen(r)
        except Exception:
            return
        pd = pg.read()
        if not self.check_login(pd.decode()):
            raise RuntimeError()

    def login(self, who):
        user = who["user"]
        passwd = who["passwd"]
        site = who["site"]
        r = Request(site,
            urlencode(
                [("Action", "Login"), ("RequestedURL", ""), ("Lang", "en"),
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
                print (i)
                return False
        return True
