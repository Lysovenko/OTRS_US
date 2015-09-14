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
from time import strftime
from urllib.parse import urlparse, parse_qsl, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
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

    def parse(self, data):
        "Dummy method to be replaced"
        print(data)

    def load(self, location, data=None, headers={}):
        try:
            session = self.runt_cfg["Session"]
        except KeyError:
            raise LoginError()
        heads = {"Accept-Encoding": "gzip, deflate"}
        heads.update(headers)
        if "?" in location or data is not None:
            r = Request(location, data, headers=heads)
        else:
            r = Request(
                "%s?%s" % (location, urlencode([("Session", session)])),
                data, headers=heads)
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
            raise LoginError()
        self.runt_cfg["Session"] = dpl["Session"]

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
                print(repr(page.geturl()))
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
        try:
            anss = res["answers"]
            hl = len(anss) // 2
            if anss[hl][0] == anss[0][0]:
                del anss[hl:]
        except (KeyError, IndexError):
            pass
        return res


class MessagePage(Page):
    def parse(self, data):
        parser = MessageParser()
        parser.feed(data.decode(errors="ignore"))
        parser.close()
        return parser.message_text


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
