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
"Making the Dashboard widget"

from os import system
from os.path import dirname, join
from time import strftime
from tkinter import ttk, PhotoImage
from tkinter.messagebox import showerror
from .tickets import autoscroll
from ..core.dash_upd import DashboardUpdater
from ..core.ptime import TimeConv
from .dialogs import DlgLogin


class Dashboard(ttk.Frame):
    def __init__(self, parent, appw):
        ttk.Frame.__init__(self, parent)
        self.app_widgets = appw
        self.root = appw["root"]
        self.echo = appw["core"].echo
        self.config = config = appw["config"]
        config.setdefault("dashboard_seq", ("Reminder", "New", "Open"))
        self.runtime = appw["core"].call("runtime cfg")
        self.tree = {}
        self.tree_data = {}
        self.ticket_range = {}
        self.pw = pw = ttk.Panedwindow(
            self, orient="vertical", takefocus=False)
        for i in config["dashboard_seq"]:
            frame = self.make_tree(i)
            pw.add(frame)
            pw.pane(frame, weight=1)
        pw.pack(fill="both")
        self.important = PhotoImage(
            file=join(dirname(__file__), "important.gif"))
        self.updater = DashboardUpdater(appw["core"])
        self.login_escaped = False
        self.login_failed = 0

    def make_tree(self, name):
        frame = ttk.Frame(self.pw, takefocus=False)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.tree[name] = tree = ttk.Treeview(
            frame, selectmode="extended", columns=("modified",))
        tree.grid(column=0, row=0, sticky="nwes")
        vsb = ttk.Scrollbar(frame, command=tree.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        tree["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        hsb = ttk.Scrollbar(
            frame, command=tree.xview, orient="horizontal")
        hsb.grid(column=0, row=1, sticky="ew")
        tree["xscrollcommand"] = lambda f, l: autoscroll(hsb, f, l)
        tree.column("modified", width=70, anchor="center")
        tree.heading("#0", text=_("Title"))
        tree.heading("modified", text=_("Modified"))
        tree.tag_configure("new", foreground="blue", background="gray")
        tree.bind("<FocusIn>", self.activate)
        tree.bind("<Return>", self.enter_ticket)
        tree.bind("<Double-Button-1>", self.enter_ticket)
        return frame

    def update(self):
        core = self.app_widgets["core"]
        core_cfg = core.call("core cfg")
        runt_cfg = core.call("runtime cfg")
        status = self.updater.get_status()
        self.echo("\033[0;7m%s\033[0m>>> %s: %s" % (
            strftime("%H:%M:%S"), status, self.updater.get_info()))
        if status == "Wait":
            self.root.after(1000, self.update)
            return
        if status == "Ready":
            self.updater.start_loader(runt_cfg.get("site", ""))
            self.root.after(1000, self.update)
            return
        if status == "LoginError" and not self.login_escaped:
            self.login()
            self.root.after(1000, self.update)
            self.login_failed += 1
            return
        if status == "Complete":
            res = self.updater.get_result()
            if res is not None:
                self.fill_trees(res[0])
                self.show_status(res[1])
            self.login_failed = 0
        if status in ("URLError", "Empty"):
            self.on_url_error(self.updater.get_result())
        refresh = core_cfg.get("refresh_time")
        if refresh > 10:
            self.root.after(int(refresh * 1e3), self.update)

    def show_status(self, summary):
        ding = " ".join(i for i in ("Reminder", "New", "Open") if summary[i])
        if ding:
            message = "%s: %s" % (
                strftime("%H:%M:%S"), ding)
        else:
            message = strftime("%H:%M:%S")
        self.app_widgets["core"].call("print_status", message)
        if ding:
            snd_cmd = self.app_widgets["core"].call("core cfg").get("snd_cmd")
            imp_cmd = self.app_widgets["core"].call("core cfg").get("snd_imp")
            if snd_cmd:
                system(snd_cmd)
            if imp_cmd:
                summary["Important"].discard(self.runtime.get("now editing"))
                if summary["Important"]:
                    system(imp_cmd)

    def fill_trees(self, pgl):
        tshow = TimeConv(
            yday=_("yest."), mago=_("min."), dago=_("days"))
        self.tree_data.clear()
        for name in ("Reminder", "New", "Open"):
            tree = self.tree[name]
            totw = sum(int(tree.column(i, "width"))
                       for i in ("#0", "modified"))
            tree.column("#0", width=totw-80, anchor="center")
            tree.column("modified", width=80, anchor="center")
            old_focus = tree.focus()
            for i in reversed(self.ticket_range.get(name, ())):
                tree.delete(i)
            data = pgl[name]
            if data and "mtime" in data[0]:
                data.sort(reverse=True, key=lambda x: x["mtime"])
            r_id = lambda x: "T%d" % x["TicketID"]
            self.tree_data.update(
                (r_id(i), (i["TicketID"], i["title"])) for i in data)
            self.ticket_range[name] = tuple(r_id(i) for i in data)
            for item in data:
                if item["marker"] & 2:
                    image = self.important
                else:
                    image = ""
                tags = ("new",) if item["marker"] & 1 else ()
                tc = item.get("mtime", 0)
                if tc:
                    tshow.set_modified(tc)
                    tc = tshow.relative()
                tree.insert(
                    "", "end", r_id(item), text=item["title"], image=image,
                    tags=tags, values=(tc,))
            if old_focus in self.ticket_range[name]:
                tree.focus(old_focus)
            else:
                try:
                    tree.focus(self.ticket_range[name][0])
                except IndexError:
                    pass

    def activate(self, evt):
        "make selection jumps between trees"
        selt = evt.widget
        for opt in self.tree.values():
            if opt is not selt:
                sel = opt.selection()
                if sel:
                    opt.selection_remove(*sel)
        selt.selection_add(selt.focus())

    def enter_ticket(self, evt):
        iid = evt.widget.focus()
        if iid:
            self.app_widgets["tickets"].load_ticket(self.tree_data[iid][0])

    def login(self, dialog=False):
        core = self.app_widgets["core"]
        core_cfg = core.call("core cfg")
        runt_cfg = core.call("runtime cfg")
        cfg = {}
        if 2 < self.login_failed:
            dialog = True
        for i in ("site", "user", "password"):
            cfg[i] = runt_cfg.get(i, core_cfg.get(i, ""))
        if not all(cfg.values()):
            dialog = True
        if dialog:
            DlgLogin(self,  _("Login"), cfg=cfg)
        else:
            cfg["OK button"] = True
            cfg["remember_passwd"] = False
        if cfg["OK button"]:
            for i in ("site", "user", "password"):
                runt_cfg[i] = cfg[i]
                if cfg["remember_passwd"]:
                    core_cfg[i] = cfg[i]
            self.echo("Login in Dashboard.login")
            self.updater.login(cfg)
        else:
            self.login_escaped = True

    def on_url_error(self, error):
        message = "%s: %s" % (strftime("%H:%M:%S"),
                              "URLError: {0}".format(error))
        self.app_widgets["core"].call("print_status", message)
        snd_cmd = self.app_widgets["core"].call("core cfg").get("snd_err")
        if snd_cmd:
            system(snd_cmd)
