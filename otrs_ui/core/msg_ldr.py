# Copyright 2016 Serhiy Lysovenko
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
"Messages downloader"

from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urllib.error import URLError
import re
from .ptime import ticket_time
from .pgload import (
    TicketsPage, MessagePage, AnswerPage, AnswerSender, LoginError, FileLoader)


def article_by_url(url):
    sp = 0
    t_id = a_id = None
    while True:
        m = re.search(r"(TicketID=(\d+))|((ArticleID=|#)(\d+))", url[sp:])
        if m is None:
            break
        sp += m.end()
        if m.group(2) is not None:
            t_id = int(m.group(2))
        elif m.group(5) is not None:
            a_id = int(m.group(5))
    return t_id, a_id


class MessageLoader:
    def __init__(self, core):
        self.echo = core.echo
        self.core = core
        self.runtime = core.call("runtime cfg")

    def zoom_ticket(self, ticket_id):
        self.echo("Zoom ticket:", ticket_id)
        url_beg = urlsplit(self.runtime.get("site"))[:3]
        params = (("Action", "AgentTicketZoom"), ("TicketID", ticket_id))
        url = urlunsplit(url_beg + (urlencode(params), ""))
        pg = TicketsPage(self.core)
        lres = None
        try:
            lres = pg.load(url)
        except LoginError:
            lres = pg.login(self.runtime)
        except ConnectionError:
            try:
                self.echo("Login in Tickets.load_ticket")
                lres = pg.login(self.runtime)
            except (LoginError, KeyError):
                return
        except KeyError:
            return
        if lres is None:
            raise ConnectionError()
        return self.describe_articles(lres["articles"])

    def describe_articles(self, articles):
        description = {}
        for item in articles:
            qd = dict(parse_qsl(urlsplit(item["article info"]).query))
            ticket_id = int(qd["TicketID"])
            article_id = int(qd["ArticleID"])
            title = item["Subject"]
            sender = item["From"]
            mktime = ticket_time(item["Created"])
            #, item["Type"]
            tree_data[no] = item
        return description

    def zoom_article(self, ticket_id, article_id):
        self.echo("Zoom article:", ticket_id, article_id)
        url_beg = urlsplit(self.runtime.get("site"))[:3]
        params = (
            ("Action", "AgentTicketZoom"), ("Subaction", "ArticleUpdate"),
            ("TicketID", ticket_id), ("ArticleID", article_id))
        url = urlunsplit(url_beg + (urlencode(params), ""))
        page = TicketsPage(self.core)
        mail_text = ""
        if page is None:
            return
        if "info" in page:
            self.ticket_info = page["info"]
        mail_header = page.get("mail_header", [])
        try:
            mail_text = page["message_text"]
        except KeyError:
            pass
        self.detect_allowed_actions(page.get("action_hrefs", []) +
                                    page.get("art_act_hrefs", []))
        try:
            self.queues = page["queues"]
        except KeyError:
            pass
        try:
            self.answers = page["answers"]
        except (KeyError, IndexError):
            self.answers = None
        if "mail_src" in page:
            url = urlunsplit(url_beg[:2] + urlsplit(page["mail_src"])[2:])
            self.echo("Get message:", url)
            pg = MessagePage(self.app_widgets["core"])
            mail_text = pg.load(url)
        return mail_text, mail_header

    def extract_url(self, ticket_id, article_id):
        return "%s?Action=AgentTicketZoom;TicketID=%d#%d" % (
            self.runtime.get("site"), ticket_id, article_id)

    def detect_allowed_actions(self, act_hrefs):
        total = {}
        ac_sub = self.action_subaction
        ac_sub.clear()
        for href in act_hrefs:
            qd = dict(parse_qsl(urlsplit(href).query))
            total.update(qd)
            try:
                ac_sub[qd["Action"]] = qd.get("Subaction")
            except KeyError:
                pass
        self.actions_params = total
        except KeyError:
            pass
