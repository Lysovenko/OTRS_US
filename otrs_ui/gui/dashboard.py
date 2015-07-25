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
        self.tree_data = {}
        self.ticket_range = {}
        self.pw = pw = ttk.Panedwindow(self, orient="vertical")
        pw.add(self.make_tree("Reminder"))
        pw.add(self.make_tree("New"))
        pw.add(self.make_tree("Open"))
        pw.pack(fill="both")
        pw.bind("<Expose>", self.pw_expose)
        s0, s1 = appw["config"].get("dashboard_sashes", (None, None))
        pw.sashpos(0, s0)
        pw.sashpos(1, s1)
        self.update()

    def pw_expose(self, evt):
        s0 = self.pw.sashpos(0)
        s1 = self.pw.sashpos(1)
        self.app_widgets["config"]["dashboard_sashes"] = (s0, s1)

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
        return frame

    def update(self):
        from ..core.pgload import DashboardPage
        from .dialogs import DlgLogin
        core = self.app_widgets["core"]
        core_cfg = core.call("core cfg")
        runt_cfg = core.call("runtime cfg")
        pg = DashboardPage(core)
        while True:
            try:
                pgl = pg.load(runt_cfg.get("site", ""))
                self.fill_trees(pgl)
                break
            except RuntimeError:
                cfg = {"user": core_cfg.get("user", ""),
                       "password": core_cfg.get("password", ""),
                       "site": core_cfg.get("site", "")}
                dl = DlgLogin(self,  _("Login"), cfg=cfg)
                if cfg["OK button"]:
                    runt_cfg["site"] = cfg["site"]
                    if cfg["remember_passwd"]:
                        core_cfg["user"] = cfg["user"]
                        core_cfg["site"] = cfg["site"]
                        core_cfg["password"] = cfg["password"]
                    pg.login(cfg)
                else:
                    break

    def fill_trees(self, pgl):
        result = {}
        for name in ("Reminder", "New", "Open"):
            data = pgl[name]
            tree = self.tree[name]
            try:
                result[name] = data[0][2] \
                               not in self.ticket_range.get(name, ())
            except IndexError:
                result[name] = False
            self.tree_data[name] = dict(((i[2], i[:2]) for i in data))
            self.ticket_range[name] = [i[2] for i in data]
            for item in data:
                tree.insert("", "end", item[2], text=item[1])
        return result
