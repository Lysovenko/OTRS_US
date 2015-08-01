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
from urllib.parse import urlsplit, urlunsplit, parse_qsl
from urllib.error import URLError
from ..core.pgload import TicketsPage


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
        self.url_path = ""

    def make_tree(self):
        frame = ttk.Frame(self.pw)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.tree = tree = ttk.Treeview(frame, selectmode="extended")
        tree.grid(column=0, row=0, sticky="nwes")
        vsb = ttk.Scrollbar(frame, command=tree.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        tree["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        hsb = ttk.Scrollbar(
            frame, command=tree.xview, orient="horizontal")
        hsb.grid(column=0, row=1, sticky="ew")
        tree["xscrollcommand"] = lambda f, l: autoscroll(hsb, f, l)
        tree.tag_configure("page", background="gray")
        tree.tag_configure("file", foreground="blue", font="Monospace 12")
        tree.tag_configure("bmk", foreground="red")
        tree.tag_configure("folder", font="Times 14 bold")
        return frame

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
        self.echo("loading", url, "...")
        core = self.app_widgets["core"]
        core_cfg = core.call("core cfg")
        runt_cfg = core.call("runtime cfg")
        pg = TicketsPage(core)
        felt_trees = None
        while True:
            try:
                pgl = pg.load(url)
                self.echo(pgl)
                self.fill_tree(pgl)
                break
            except RuntimeError:
                if self.app_widgets["dashboard"].login(pg):
                    continue
                break
            except ConnectionError:
                try:
                    pg.login(runt_cfg)
                except (RuntimeError, KeyError):
                    continue

    def fill_tree(self, articles):
        if articles is None:
            raise ConnectionError()
        self.tree_data.clear()
        self.url_path = urlsplit(articles[0]["article info"]).path
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
            tree.insert("", "end", no, text=item["From"])
