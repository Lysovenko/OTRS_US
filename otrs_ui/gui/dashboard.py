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
from os import system
from os.path import dirname, join
from time import strftime
from urllib.parse import urlsplit, urlunsplit
from urllib.error import URLError
from tkinter import ttk, PhotoImage
from tkinter.messagebox import showerror
from .tickets import autoscroll
from ..core.pgload import DashboardPage, LoginError
from .dialogs import DlgLogin


class Dashboard(ttk.Frame):
    def __init__(self, parent, appw):
        ttk.Frame.__init__(self, parent)
        self.app_widgets = appw
        self.root = appw["root"]
        self.echo = appw["core"].echo
        self.tree = {}
        self.tree_data = {}
        self.ticket_range = {}
        self.pw = pw = ttk.Panedwindow(
            self, orient="vertical", takefocus=False)
        for i in ("Reminder", "New", "Open"):
            frame = self.make_tree(i)
            pw.add(frame)
            pw.pane(frame, weight=1)
        pw.pack(fill="both")
        self.urlbegin = ("", "")
        self.important = PhotoImage(
            file=join(dirname(__file__), "important.gif"))

    def make_tree(self, name):
        frame = ttk.Frame(self.pw, takefocus=False)
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
        tree.bind("<FocusIn>", self.activate)
        tree.bind("<Return>", self.enter_ticket)
        tree.bind("<Double-Button-1>", self.enter_ticket)
        return frame

    def update(self):
        core = self.app_widgets["core"]
        core_cfg = core.call("core cfg")
        runt_cfg = core.call("runtime cfg")
        pg = DashboardPage(core)
        felt_trees = None
        show_dlg = False
        while True:
            try:
                pgl = pg.load(runt_cfg.get("site", ""))
                felt_trees = self.fill_trees(pgl)
                break
            except LoginError:
                if self.login(pg, show_dlg):
                    show_dlg = True
                    continue
                break
            except ConnectionError:
                if self.login(pg, False):
                    continue
                break
            except URLError as err:
                self.on_url_error(err)
                break
        refresh = core_cfg.get("refresh_time", 0)
        if refresh > 10000:
            self.root.after(refresh, self.update)
        self.show_status(felt_trees)

    def show_status(self, trees):
        if trees is None:
            return
        ding = any(trees.values())
        if ding:
            message = "%s: %s" % (
                strftime("%H:%M:%S"), " ".join(i for i in trees if trees[i]))
        else:
            message = strftime("%H:%M:%S")
        self.app_widgets["core"].call("print_status", message)
        if ding:
            snd_cmd = self.app_widgets["core"].call("core cfg").get("snd_cmd")
            if snd_cmd:
                system(snd_cmd)

    def fill_trees(self, pgl):
        if pgl is None:
            raise ConnectionError()
        result = {}
        self.tree_data.clear()
        for name in ("Reminder", "New", "Open"):
            data = pgl[name]
            tree = self.tree[name]
            old_focus = tree.focus()
            for i in reversed(self.ticket_range.get(name, ())):
                tree.delete(i)
            try:
                result[name] = (
                    data[0][2] not in self.ticket_range.get(name, ()))
            except IndexError:
                result[name] = False
            self.tree_data.update((i[2], i[:2]) for i in data)
            self.ticket_range[name] = [i[2] for i in data]
            for item in data:
                if item[3]:
                    result[name] = True
                    image = self.important
                else:
                    image = ""
                tree.insert("", "end", item[2], text=item[1], image=image)
            if old_focus in self.ticket_range[name]:
                tree.focus(old_focus)
            else:
                try:
                    tree.focus(self.ticket_range[name][0])
                except IndexError:
                    pass
        return result

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
            self.app_widgets["tickets"].load_ticket(
                urlunsplit(
                    self.urlbegin + urlsplit(self.tree_data[iid][0])[2:]))

    def login(self, page, dialog=True):
        core = self.app_widgets["core"]
        core_cfg = core.call("core cfg")
        runt_cfg = core.call("runtime cfg")
        cfg = {}
        for i in ("site", "user", "password"):
            cfg[i] = runt_cfg.get(i, core_cfg.get(i))
        if None in cfg.values():
            dialog = True
            for i, v in cfg.items():
                if v is None:
                    cfg[i] = ""
        if dialog:
            DlgLogin(self,  _("Login"), cfg=cfg)
        else:
            cfg["OK button"] = True
            cfg["remember_passwd"] = False
        if cfg["OK button"]:
            for i in ("site", "user", "password"):
                runt_cfg[i] = cfg[i]
            self.urlbegin = urlsplit(cfg["site"])[:2]
            if cfg["remember_passwd"]:
                for i in ("site", "user", "password"):
                    core_cfg[i] = cfg[i]
            try:
                self.echo("Login in Dashboard.login")
                page.login(cfg)
            except LoginError:
                if dialog:
                    showerror(_("Error"), _("Login attempt failed"))
            except URLError as err:
                self.on_url_error(err)
                return False
            return True
        return False

    def on_url_error(self, error):
        message = "%s: %s" % (strftime("%H:%M:%S"),
                              "URLError: {0}".format(error))
        self.app_widgets["core"].call("print_status", message)
        snd_cmd = self.app_widgets["core"].call("core cfg").get("snd_err")
        if snd_cmd:
            system(snd_cmd)
