# Copyright 2015-2016 Serhiy Lysovenko
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
"Making the Search widget"

from tkinter import ttk
from .dialogs import DlgDetails
from .tickets import autoscroll
from ..core.search import Searcher
from ..core.ptime import TimeConv
from ..core.pgload import QuerySender


class Search(ttk.Frame):
    def __init__(self, parent, appw):
        ttk.Frame.__init__(self, parent)
        self.app_widgets = appw
        self.echo = appw["core"].echo
        self.searcher = Searcher(appw["core"])
        self.tree_data = {}
        self.add_control()
        self.make_tree()
        self.ticket_range = []

    def add_control(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.control = ttk.Frame(self)
        self.control.grid_columnconfigure(1, weight=1)
        self.control.grid(column=0, row=0, sticky="ew")
        self.btn = ttk.Button(self.control, command=self.search,
                              text=_("Find"), width=8)
        self.btn.grid(column=0, row=0, sticky="w")
        self.entry = ttk.Entry(self.control, width=60)
        self.entry.grid(column=1, row=0, sticky="ew", padx=3)
        self.entry.bind("<KeyPress-Return>", self.search)

    def make_tree(self):
        self.tree = tree = ttk.Treeview(self, selectmode="extended",
                                        columns=("modified",))
        tree.grid(column=0, row=1, sticky="nwes")
        vsb = ttk.Scrollbar(self, command=tree.yview, orient="vertical")
        vsb.grid(column=1, row=1, sticky="ns")
        tree["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        hsb = ttk.Scrollbar(
            self, command=tree.xview, orient="horizontal")
        hsb.grid(column=0, row=1, sticky="ew")
        tree["xscrollcommand"] = lambda f, l: autoscroll(hsb, f, l)
        tree.bind("<Return>", self.enter_ticket)
        tree.bind("<Double-Button-1>", self.enter_ticket)

    def search(self, evt=None):
        self.__elapsed = 0
        sexpr = self.entry.get()
        if not sexpr:
            return
        self.searcher.search(sexpr)
        self.update()

    def update(self):
        sstatus = self.searcher.get_status()
        if sstatus == "Wait":
            self.app_widgets["core"].call(
                "print_status", _("Search... (%d)") % self.__elapsed)
            self.app_widgets["root"].after(1000, self.update)
            self.__elapsed += 1
            return
        if sstatus in ("LoginError", "URLError"):
            res = self.searcher.get_result()
            self.app_widgets["core"].call("print_status",
                                          _("Search failed: %s") % str(res))
        if sstatus == "Complete":
            self.app_widgets["core"].call("print_status", _("Search complete"))
            res = self.searcher.get_result()
            if res is not None:
                self.cur_sexpr = self.searcher.regexp
                self.fill_tree(res)

    def fill_tree(self, data):
        tshow = TimeConv(
            yday=_("yest."), mago=_("min."), dago=_("days"))
        self.tree_data.clear()
        tree = self.tree
        totw = sum(int(tree.column(i, "width")) for i in ("#0", "modified"))
        tree.column("#0", width=totw-80, anchor="center")
        tree.column("modified", width=80, anchor="center")
        old_focus = tree.focus()
        for i in reversed(self.ticket_range):
            tree.delete(i)
        data.sort(reverse=True, key=lambda x: x["mtime"])
        r_id = lambda x: "T%d" % x["TicketID"]
        self.tree_data.update(
            (r_id(i), (i["TicketID"], i["articles"], i["number"]))
            for i in data)
        self.ticket_range = tuple(r_id(i) for i in data)
        for item in data:
            tc = item.get("mtime", 0)
            if tc:
                tshow.set_modified(tc)
                tc = tshow.relative()
            tree.insert(
                "", "end", r_id(item), text=item["title"], values=(tc,))
        if old_focus in self.ticket_range:
            tree.focus(old_focus)
        else:
            try:
                tree.focus(self.ticket_range[0])
            except IndexError:
                pass

    def enter_ticket(self, evt):
        iid = evt.widget.focus()
        if iid:
            td = self.tree_data[iid]
            self.app_widgets["tickets"].load_ticket(
                td[0], prefered=td[1], sexpr=self.cur_sexpr)

    def main_tic_num(self, cfg):
        iid = self.tree.focus()
        if iid:
            td = self.tree_data[iid]
            cfg["MainTicketNumber"] = str(td[2])
