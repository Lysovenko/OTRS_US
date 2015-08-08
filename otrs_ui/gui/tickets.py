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
"Making the Tickets widget"

from tkinter import ttk, Text
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urllib.error import URLError
from ..core.pgload import TicketsPage, MessagePage


def autoscroll(sbar, first, last):
    """Hide and show scrollbar as needed."""
    first, last = float(first), float(last)
    if first <= 0 and last >= 1:
        sbar.grid_remove()
    else:
        sbar.grid()
    sbar.set(first, last)


class Tickets(ttk.Frame):
    def __init__(self, parent, appw):
        ttk.Frame.__init__(self, parent)
        self.app_widgets = appw
        self.echo = appw["core"].echo
        self.runt_cfg = appw["core"].call("runtime cfg")
        self.pw = pw = ttk.Panedwindow(self, orient="vertical")
        frame = self.make_tree()
        pw.add(frame)
        pw.pane(frame, weight=1)
        frame = self.make_text_field()
        pw.add(frame)
        pw.pane(frame, weight=2)
        pw.pack(fill="both")
        self.articles_range = []
        self.tree_data = {}
        self.url_begin = None

    def make_tree(self):
        frame = ttk.Frame(self.pw)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.tree = tree = ttk.Treeview(
            frame, selectmode="extended", columns=("from", "created", "mode"))
        tree.grid(column=0, row=0, sticky="nwes")
        vsb = ttk.Scrollbar(frame, command=tree.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        tree["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        hsb = ttk.Scrollbar(
            frame, command=tree.xview, orient="horizontal")
        hsb.grid(column=0, row=1, sticky="ew")
        tree["xscrollcommand"] = lambda f, l: autoscroll(hsb, f, l)
        tree.column("from", width=170, anchor="center")
        tree.column("created", width=70, anchor="center")
        tree.column("mode", width=70, anchor="center")
        tree.bind("<Double-Button-1>", self.enter_article)
        tree.bind("<Return>", self.enter_article)
        frame.bind_all("<Escape>", self.go_dasboard)
        return frame

    def go_dasboard(self, evt):
        self.app_widgets["notebook"].select(0)
        self.app_widgets["dashboard"].tree["New"].focus_set()

    def make_text_field(self):
        frame = ttk.Frame(self.pw)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        text = Text(frame, state="disabled", wrap="word",
                    font="Times 14")
        self.text = text
        text.grid(column=0, row=0, sticky="nwes")
        vsb = ttk.Scrollbar(frame, command=self.text.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        text["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        self.text_curinfo = None
        text.tag_configure("h1", font="Times 16 bold", relief="raised")
        return frame

    def load_ticket(self, url):
        self.echo("load ticket:", url)
        pg = TicketsPage(self.app_widgets["core"])
        felt_trees = None
        while True:
            try:
                lres = pg.load(url)
                text = self.text
                text["state"] = "normal"
                text.delete("1.0", "end")
                for i in lres.get("mail_header", ()):
                    text.insert("end", "%s\t%s\n" % i)
                text.insert("end", "\n")
                for i in lres.get("message_text", ()):
                    text.insert("end", i)
                text["state"] = "disabled"
                self.echo(lres["articles"])
                self.fill_tree(lres["articles"])
                break
            except RuntimeError:
                if self.app_widgets["dashboard"].login(pg):
                    continue
                break
            except ConnectionError:
                try:
                    self.echo("Login in Tickets.load_ticket")
                    pg.login(self.runt_cfg)
                except (RuntimeError, KeyError):
                    self.go_dasboard(None)

    def fill_tree(self, articles):
        if articles is None:
            raise ConnectionError()
        self.tree_data.clear()
        self.url_begin = (urlsplit(self.runt_cfg["site"])[:2] +
                          (urlsplit(articles[0]["article info"])[2],))
        tree = self.tree
        for i in reversed(self.articles_range):
            tree.delete(i)
        del self.articles_range[:]
        for item in articles:
            qd = dict(parse_qsl(urlsplit(item["article info"]).query))
            item["article info"] = qd
            no = qd["ArticleID"]
            self.tree_data[no] = item
            self.articles_range.append(no)
            tree.insert(
                "", "end", no, text=item["Subject"],
                values=(item["From"], item["Created"], item["Type"]))
        self.app_widgets["notebook"].select(self)
        self.tree.focus(item=self.articles_range[0])
        self.tree.focus_set()

    def enter_article(self, evt):
        iid = evt.widget.focus()
        if iid:
            params = [("Action", "AgentTicketZoom"),
                      ("Subaction", "ArticleUpdate")]
            for i in ("Count", "TicketID", "ArticleID"):
                params.append((i, self.tree_data[iid]["article info"][i]))
            params.append(("Session", self.runt_cfg["Session"]))
            url = urlunsplit(
                self.url_begin + (urlencode(params), ""))
            pg = TicketsPage(self.app_widgets["core"])
            lres = pg.load(url)
            mhead = lres["mail_header"]
            if "message_text" in lres:
                msg = lres["message_text"]
            else:
                params = [("Action", "AgentTicketAttachment"),
                          ("Subaction", "HTMLView"), ("FileID", "1")]
                for i in ("ArticleID",):
                    params.append((i, self.tree_data[iid]["article info"][i]))
                params.append(("Session", self.runt_cfg["Session"]))
                url = urlunsplit(
                    self.url_begin + (urlencode(params), ""))
                self.echo("enter article:", url)
                pg = MessagePage(self.app_widgets["core"])
                msg = pg.load(url)
            text = self.text
            text["state"] = "normal"
            text.delete("1.0", "end")
            for i in mhead:
                text.insert("end", "%s\t%s\n" % i)
            text.insert("end", "\n")
            for i in msg:
                text.insert("end", i)
            text["state"] = "disabled"
