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
from .ptime import unix_time
from .pgload import (
    TicketsPage, MessagePage, AnswerPage, AnswerSender, LoginError, FileLoader)
from .database import ART_SEEN, ART_TEXT, TIC_UPD, ART_TYPE_MASK
ARTICLE_TYPES = (
    "agent-email-external", "agent-email-internal",
    "agent-note-external", "agent-note-internal",
    "agent-phone", "customer-email-external",
    "customer-note-external", "customer-phone",
    "customer-webrequest", "system-email-external",
    "system-email-internal", "system-email-notification-ext",
    "system-email-notification-int", "system-note-external",
    "system-note-internal", "system-note-report")
article_type = lambda flag: ARTICLE_TYPES[flag & ART_TYPE_MASK]


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
        self.cfg = core.call("core cfg")
        self.__db = core.call("database")

    def zoom_ticket(self, ticket_id, force_update=None):
        rv = self.__db.ticket_fields(ticket_id, "info", "flags")
        if rv:
            info, flags = rv
        else:
            flags = 0
        if flags & TIC_UPD and not force_update:
            info = eval(info)
            allowed = eval(self.__db.ticket_allows(ticket_id))
            return self.describe_articles(ticket_id), info, allowed
        arts = self.__update_ticket(ticket_id)
        info = eval(self.__db.ticket_fields(ticket_id, "info")[0])
        allowed = eval(self.__db.ticket_allows(ticket_id))
        return arts, info, allowed

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
        return self.__treat_ticket_page(ticket_id, page)

    def __treat_ticket_page(self, ticket_id, page):
        try:
            if page["answers"][1]:
                self.cfg["answers"] = page["answers"]
        except (KeyError, IndexError):
            pass
        try:
            self.cfg["queues"] = page["queues"]
        except KeyError:
            pass
        allow = self.detect_allowed_actions(page.get("action_hrefs", []) +
                                            page.get("art_act_hrefs", []))
        info = repr(page.get("info", ()))
        flags = self.__db.ticket_fields(ticket_id, "flags")
        flags = 0 if flags is None else flags[0]
        flags |= TIC_UPD
        self.__db.update_ticket(ticket_id, info=info, flags=flags)
        self.__db.ticket_allows(ticket_id, allow)
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
                ctime = unix_time(item["Created"], self.cfg["art_tm_fmt"])
                rcs = item["row"].split()
                flags = ARTICLE_TYPES.index(rcs[0])
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
            return eval(self.__db.article_message(article_id))
        self.echo("Zoom article:", ticket_id, article_id)
        url_beg = urlsplit(self.runtime.get("site"))[:3]
        params = (
            ("Action", "AgentTicketZoom"), ("Subaction", "ArticleUpdate"),
            ("TicketID", ticket_id), ("ArticleID", article_id),
            ("OTRSAgentInterface", self.runtime["OTRSAgentInterface"]))
        url = urlunsplit(url_beg + (urlencode(params), ""))
        pg = TicketsPage(self.core)
        page = pg.load(url)
        mail_text = ""
        if page is None:
            return
        mail_header = page.get("mail_header", [])
        try:
            mail_text = page["message_text"]
        except KeyError:
            pass
        if "mail_src" in page:
            url = urlunsplit(url_beg[:2] + urlsplit(page["mail_src"])[2:])
            self.echo("Get message:", url)
            pg = MessagePage(self.core)
            mail_text = pg.load(url)
        if mail_header:
            mail_text.insert(0, ("\n",))
        for i in mail_header:
            mail_text.insert(0, ("%s\t%s\n" % i,))
        self.__db.article_message(article_id, repr(mail_text))
        return mail_text

    def extract_url(self, ticket_id, article_id):
        return "%s?Action=AgentTicketZoom;TicketID=%d#%d" % (
            self.runtime.get("site"), ticket_id, article_id)

    def detect_allowed_actions(self, act_hrefs):
        allowed = {}
        for href in act_hrefs:
            qd = dict(parse_qsl(urlsplit(href).query))
            try:
                allowed[qd["Action"]] = qd.get("Subaction", True)
            except KeyError:
                pass
        allowed = tuple(sorted(allowed.items()))
        return repr(allowed)

    def move_ticket(self, ticket_id, where):
        params = [
            ("Action", "AgentTicketMove"), ("QueueID", ""),
            ("DestQueueID", where), ("TicketID", ticket_id),
            ("ChallengeToken", self.runtime["ChallengeToken"])]
        return self.__send_request_tp(ticket_id, params)

    def __send_request_tp(self, ticket_id, params):
        url = self.runtime["site"]
        pg = TicketsPage(self.core)
        page = None
        try:
            page = pg.load(url, urlencode(params).encode())
        except LoginError:
            return
        if page is None:
            return
        arts = self.__treat_ticket_page(ticket_id, page)
        info = eval(self.__db.ticket_fields(ticket_id, "info")[0])
        allowed = eval(self.__db.ticket_allows(ticket_id))
        return arts, info, allowed

    def lock_ticket(self, ticket_id, subact):
        params = [
            ("Action", "AgentTicketLock"), ("Subaction", subact),
            ("TicketID", ticket_id),
            ("ChallengeToken", self.runtime["ChallengeToken"])]
        return self.__send_request_tp(ticket_id, params)

    def load_article_pattern(self, ticket_id, article_id, ans_id):
        params = [("Action", "AgentTicketCompose"),
                  ("ReplyAll", ""), ("ResponseID", ans_id),
                  ("TicketID", ticket_id), ("ArticleID", article_id),
                  ("ChallengeToken", self.runtime["ChallengeToken"])]
        return self.__send_request_ap(params)

    def load_note_pattern(self, ticket_id):
        params = [
            ("Action", "AgentTicketNote"), ("TicketID", ticket_id),
            ("ChallengeToken", self.runtime["ChallengeToken"])]
        return self.__send_request_ap(params)

    def load_owners_pattern(self, ticket_id):
        params = [
            ("Action", "AgentTicketOwner"), ("TicketID", ticket_id)]
        return self.__send_request_ap(params)

    def load_close_pattern(self, ticket_id):
        params = [
            ("Action", "AgentTicketClose"), ("TicketID", ticket_id)]
        return self.__send_request_ap(params)

    def load_forward_pattern(self, ticket_id, article_id):
        params = [
            ("Action", "AgentTicketForward"), ("TicketID", ticket_id),
            ("ArticleID", article_id)]
        return self.__send_request_ap(params)

    def load_merge_pattern(self, ticket_id):
        params = [
            ("Action", "AgentTicketMerge"), ("TicketID", ticket_id)]
        return self.__send_request_ap(params)

    def load_new_mail_pattern(self):
        params = [("Action", "AgentTicketEmail")]
        return self.__send_request_ap(params)

    def __send_request_ap(self, params):
        url = "%s?%s" % (self.runtime["site"], urlencode(params))
        pg = AnswerPage(self.core)
        return pg.load(url)

    def send_multiprat(self, cfg, inputs):
        pg = AnswerSender(self.core)
        url = self.runtime["site"]
        pg.send(url, [(i[0], cfg.get(i[0], ("", b""))) for i in inputs])

    def download_file(self, url, downpath):
        if url.startswith("/"):
            m = re.search(r"^https?://[^/]+", self.runtime["site"])
            url = m.group(0) + url
        fl = FileLoader(self.core)
        fl.set_save_path(downpath)
        fl.load(url)
