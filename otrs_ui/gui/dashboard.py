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
"Making the Dashboard widget"

from tkinter import ttk
from .tickets import autoscroll


class Dashboard(ttk.Frame):
    def __init__(self, parent, appw):
        ttk.Frame.__init__(self, parent)
        self.app_widgets = appw
        self.tree = {}
        self.pw = pw = ttk.Panedwindow(self, orient="vertical")
        pw.add(self.make_tree("Reminder"))
        pw.add(self.make_tree("New"))
        pw.add(self.make_tree("Open"))
        pw.pack(fill="both")
        self.update()

    def make_tree(self, name):
        frame = ttk.Frame(self.pw)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.tree[name] = tree = ttk.Treeview(frame, selectmode="extended")
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

    def update(self):
        from ..core.pgload import Page
        from .dialogs import DlgLogin
        pg = Page(self.app_widgets["core"])
        while True:
            try:
                pg.load("https://otrs.hvosting.ua/otrs/index.pl")
            except RuntimeError:
                cfg = {"login": "user", "password": "qwerty"}
                dl = DlgLogin(self,  _("Login"), cfg=cfg)
        pass
