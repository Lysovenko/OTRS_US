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
from .pgload import (
    TicketsPage, MessagePage, AnswerPage, AnswerSender, LoginError, FileLoader)


class MessageLoader:
    def __init__(self, core):
        self.echo = core.echo

    def load_ticket(self, url):
        self.echo("load ticket:", url)
        self.my_url = url
        pg = TicketsPage(self.app_widgets["core"])
        lres = None
        while True:
            try:
                lres = pg.load(url)
                if lres is None:
                    raise ConnectionError()
                self.fill_tree(lres["articles"])
                break
            except LoginError:
                lres = pg.login(self.runt_cfg)
                break
            except ConnectionError:
                try:
                    self.echo("Login in Tickets.load_ticket")
                    lres = pg.login(self.runt_cfg)
                except (LoginError, KeyError):
                    lres = None
            except KeyError:
                showerror(_("Error"), _("Wrong Ticket"))
                return

    def get_tickets_page(self, page):
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
        if "article text" in self.cur_article:
            mail_text = self.cur_article["article text"]
        elif "mail_src" in page:
            url = urlunsplit(
                self.url_begin[:2] + urlsplit(page["mail_src"])[2:])
            self.echo("Get message:", url)
            pg = MessagePage(self.app_widgets["core"])
            mail_text = pg.load(url)
        self.cur_article["article text"] = mail_text
        self.cur_article["article header"] = mail_header
        self.show_email(self.cur_article)
