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
"Page loader"
from urllib.parse import urlparse, parse_qsl, urlencode
from urllib.request import Request, urlopen


_REQUESTS = {}
class Page:
    def load(self, location):
        r = Request(location)
        try:
            pg = urlopen(r)
        except Exception:
            return
        pd = pg.read()
        
    def login(self):
        r = Request(
            "https://otrs.hvosting.ua/otrs/index.pl",
            urlencode(
                [("Action", "Login"), ("RequestedURL", ""), ("Lang", "en"),
                 ("TimeOffset", ""), ("User", user), ("Password", passwd),
                 ("login", "Login")]).encode())
        pg = urlopen(r)
