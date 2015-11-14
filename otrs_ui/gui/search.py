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

    def search(self):
        pass

    def enter_ticket(self, evt=None):
        pass
