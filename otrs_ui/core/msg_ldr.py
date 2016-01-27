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
from .pgload import (
    TicketsPage, MessagePage, AnswerPage, AnswerSender, LoginError, FileLoader)


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
        while True:
            try:
                lres = pg.load(url)
                if lres is None:
                    raise ConnectionError()
                break
            except LoginError:
                lres = pg.login(self.runtime)
                break
            except ConnectionError:
                try:
                    self.echo("Login in Tickets.load_ticket")
                    lres = pg.login(self.runtime)
                except (LoginError, KeyError):
                    lres = None
            except KeyError:
                return

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

    def menu_goto_url(self, evt=None):
        cfg = {"url": ""}
        DlgDetails(self, _("Go to ticket"),
                   cfg=cfg, inputs=(("url", _("URL:")),))
        if cfg["OK button"]:
            url = cfg["url"]
            if self.my_url is not None:
                m = re.search(r"TicketID=(\d+)", url)
                url = re.sub(r"TicketID=(\d+)", m.group(0), self.my_url)
            self.load_ticket(url)

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
