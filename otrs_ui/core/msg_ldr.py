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
from threading import Thread, Lock
import re
from .ptime import ticket_time
from .pgload import (
    TicketsPage, MessagePage, AnswerPage, AnswerSender, LoginError, FileLoader)
from .database import ART_SEEN, ART_TEXT, TIC_UPD
TICKET_TYPES = (
    "agent-email-external", "agent-email-internal",
    "agent-note-external", "agent-note-internal",
    "agent-phone", "customer-email-external",
    "customer-note-external", "customer-phone",
    "customer-webrequest", "system-email-external",
    "system-email-internal", "system-email-notification-ext",
    "system-email-notification-int", "system-note-external",
    "system-note-internal", "system-note-report")


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
        self.__db = core.call("database")

    def zoom_ticket(self, ticket_id):
        info, flags = self.__db.ticket_fields(ticket_id, "info", "flags")
        if flags & TIC_UPD:
            return self.describe_articles(ticket_id), info
        arts = self.__update_ticket(ticket_id)
        info, = self.__db.ticket_fields(ticket_id, "info")
        return arts, info

    def __update_ticket(self, ticket_id):
        self.echo("Zoom ticket:", ticket_id)
        url_beg = urlsplit(self.runtime.get("site"))[:3]
        params = (("Action", "AgentTicketZoom"), ("TicketID", ticket_id))
        url = urlunsplit(url_beg + (urlencode(params), ""))
        pg = TicketsPage(self.core)
        page = None
        try:
            page = pg.load(url)
        except LoginError:
            page = pg.login(self.runtime)
        except ConnectionError:
            try:
                self.echo("Login in Tickets.load_ticket")
                page = pg.login(self.runtime)
            except (LoginError, KeyError):
                return
        except KeyError:
            return
        if page is None:
            raise ConnectionError()
        # ticket properties aka info
        if "info" in page:
            self.ticket_info = page["info"]
        allow = self.detect_allowed_actions(page.get("action_hrefs", []) +
                                            page.get("art_act_hrefs", []))
        info = ";;".join((repr(page.get("info", ())), repr(allow)))
        flags, = self.__db.ticket_fields(ticket_id, "flags")
        flags |= TIC_UPD
        self.__db.update_ticket(ticket_id, info=info, flags=flags)
        return self.describe_articles(page["articles"])

    def describe_articles(self, articles):
        if isinstance(articles, int):
            articles = self.__db.articles_description(articles)
        description = {}
        for item in articles:
            if isinstance(item, dict):
                qd = dict(parse_qsl(urlsplit(item["article info"]).query))
                ticket_id = int(qd["TicketID"])
                article_id = int(qd["ArticleID"])
                title = item["Subject"]
                sender = item["From"]
                ctime = ticket_time(item["Created"])
                rcs = item["row"].split()
                flags = TICKET_TYPES.index(rcs[0])
                if "UnreadArticles" not in rcs:
                    flags |= ART_SEEN
                flags = self.__db.article_description(
                    article_id, ticket_id, ctime, title, sender, flags)[4]
            else:
                article_id, ticket_id, ctime, title, sender, flags = item
            description[article_id] = {
                "TicketID": ticket_id, "ctime": ctime,
                "Title": title, "Sender": sender, "Flags": flags}
        return description

    def zoom_article(self, ticket_id, article_id):
        art_descr = self.__db.article_description(article_id)
        if art_descr[4] & ART_TEXT:
            return self.__db.article_message(article_id)
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
        mail_header = page.get("mail_header", [])
        try:
            mail_text = page["message_text"]
        except KeyError:
            pass
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
        if mail_header:
            mail_text.insert(0, (";;",))
        for i in mail_header:
            mail_text.insert(0, ("%s\t%s\n" % i,))
        self.__db.article_message(article_id, mail_text)
        return mail_text

    def extract_url(self, ticket_id, article_id):
        return "%s?Action=AgentTicketZoom;TicketID=%d#%d" % (
            self.runtime.get("site"), ticket_id, article_id)

    def detect_allowed_actions(self, act_hrefs):
        allowed = {"AgentTicketLock": False}
        for href in act_hrefs:
            qd = dict(parse_qsl(urlsplit(href).query))
            try:
                allowed[qd["Action"]] = qd.get("Subaction", True)
            except KeyError:
                pass
        return allowed
