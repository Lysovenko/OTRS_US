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
"Making the Search widget"

from tkinter import ttk, Text, StringVar
from os.path import isdir, join, dirname
from .tickets import autoscroll


class Search(ttk.Frame):
    def __init__(self, parent, appw):
        ttk.Frame.__init__(self, parent)
        self.app_widgets = appw
        self.echo = appw["core"].echo
        self.runt_cfg = appw["core"].call("runtime cfg")
        self.tree_data = {}
        self.add_control()
        self.make_tree()

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
        self.tree = tree = ttk.Treeview(self, selectmode="extended")
        tree.grid(column=0, row=1, sticky="nwes")
        vsb = ttk.Scrollbar(self, command=tree.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        tree["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        hsb = ttk.Scrollbar(
            self, command=tree.xview, orient="horizontal")
        hsb.grid(column=0, row=1, sticky="ew")
        tree["xscrollcommand"] = lambda f, l: autoscroll(hsb, f, l)
        tree.tag_bind("page", "<Return>", self.enter_ticket)
        tree.tag_bind("page", "<Double-Button-1>", self.enter_ticket)

    def search(self, evt=None):
        sexpr = self.entry.get()
        if not sexpr:
            return
        res = None
        if res is not None:
            self.fill_tree(res)
            runt_cfg["dash_inputs"] = res[0].pop("inputs", {})
        self.echo("Serch: %s" % sexpr)
        self.echo(self.runt_cfg["dash_inputs"])

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
        if data and "Changed" in data[0]:
            data.sort(reverse=True, key=dashb_time)
        new = tuple(i["number"] for i in data)
        self.tree_data.update(
            (i["number"], (i["TicketID"], i["title"])) for i in data)
        self.ticket_range = new
        for item in data:
            tags = ("new",) if item["marker"] & 1 else ()
            tc = item.get("Changed", 0)
            if tc:
                tshow.set_modified(tc)
                tc = tshow.relative()
            tree.insert(
                "", "end", item["number"], text=item["title"],
                tags=tags, values=(tc,))
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
            self.app_widgets["tickets"].load_ticket(
                self.tree_data[int(iid)][0])
