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
"Making the GUI of the application"

from tkinter import Tk, Menu, PhotoImage, ttk, StringVar, messagebox, \
    BooleanVar
from tkinter.filedialog import askdirectory
from os.path import isdir, join, dirname, pardir
from os import makedirs
from ..core.settings import Config
from ..core import get_core
from .tickets import Tickets
from .dashboard import Dashboard
from .search import Search
from .dialogs import DlgSettings


class Face:
    def __init__(self, root, core):
        root.title(_("OTRS Client Side"))
        root.protocol("WM_DELETE_WINDOW", self.on_delete)
        self.root = root
        self.core = core
        self.config = config = Config("face.cfg")
        root.geometry(config.get("geometry"))
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        self.notebook = ntbk = ttk.Notebook(root, takefocus=False)
        self.app_widgets = appw = {
            "core": core, "config": config, "root": root,
            "notebook": ntbk}
        # Dashboard, Tickets, -Customers, -Admin, -Forums, Search
        ntbk.grid(column=0, row=0, sticky="senw")
        appw["dashboard"] = Dashboard(ntbk, appw)
        ntbk.add(appw["dashboard"], text=_("Dashboard"))
        appw["tickets"] = Tickets(ntbk, appw)
        ntbk.add(appw["tickets"], text=_("Ticket"))
        ntbk.hide(appw["tickets"])
        appw["search"] = Search(ntbk, appw)
        ntbk.add(appw["search"], text=_("Search"))
        self.status = StringVar()
        st_lab = ttk.Label(root, textvariable=self.status)
        core.register("print_status", self.status.set)
        st_lab.grid(column=0, row=1, sticky="we")
        self.sz = ttk.Sizegrip(root)
        self.sz.grid(column=0, row=1, sticky="se")
        self.add_menu()
        self.locked = False
        root.tk.call("wm", "iconphoto", root._w,
                     PhotoImage(file=join(dirname(__file__), "icon.gif")))
        root.after(500, appw["dashboard"].update)

    def add_menu(self):
        top = self.root.winfo_toplevel()
        top["menu"] = menubar = Menu(top)
        mfile = Menu(menubar)
        medit = Menu(menubar)
        mticket = Menu(menubar)
        menubar.add_cascade(menu=mfile, label=_("File"))
        menubar.add_cascade(menu=medit, label=_("Edit"))
        menubar.add_cascade(
            menu=mticket, label=_("Ticket"), state="disabled")
        medit.add_command(label=_("Settings"), command=self.ask_settings)
        self.app_widgets["menubar"] = menubar
        self.app_widgets["menu_ticket"] = mticket
        tcts = self.app_widgets["tickets"]
        for lab, cmd, acc, ul in (
                (_("New email ticket"), tcts.menu_new_email, "Ctrl+N", 0),
                (_("New phone ticket"), tcts.menu_new_phone, "Ctrl+H", 1),
                (_("Go to ticket"), tcts.menu_goto_url, "Ctrl+U", 0),
                (_("Download..."), tcts.menu_download, None, 1),
                (_("Quit"), self.on_delete, "Ctrl+Q", 0)):
            mfile.add_command(label=lab, command=cmd,
                              accelerator=acc, underline=ul)
        self.root.bind_all("<Control-q>", lambda x: self.on_delete())
        self.root.bind_all("<Control-u>", tcts.menu_goto_url)
        add_cmd = mticket.add_command
        add_cmd(label=_("Lock"), command=tcts.menu_lock, accelerator="Ctrl+L")
        add_cmd(label=_("Move"), command=tcts.menu_move, accelerator="Ctrl+M")
        add_cmd(label=_("Answer"), command=tcts.menu_answer,
                accelerator="Ctrl+A")
        add_cmd(label=_("Forward"), command=tcts.menu_forward,
                accelerator="Ctrl+W")
        add_cmd(label=_("Note"), command=tcts.menu_note, accelerator="Ctrl+T")
        add_cmd(label=_("Owner"), command=tcts.menu_owner,
                accelerator="Ctrl+O")
        add_cmd(label=_("Close"), command=tcts.menu_close,
                accelerator="Ctrl+E")
        add_cmd(label=_("Information"), command=tcts.menu_info,
                accelerator="Ctrl+I")
        add_cmd(label=_("Reload"), command=tcts.menu_reload,
                accelerator="Ctrl+R")
        add_cmd(label=_("Send message"), command=tcts.menu_send,
                accelerator="Ctrl+S")
        add_cmd(label=_("Merge to ticket"), command=tcts.menu_ticket_merge,
                accelerator="Ctrl+J")
        add_cmd(label=_("Copy URL"), command=tcts.menu_copy_url)

    def on_delete(self):
        self.config["geometry"] = self.root.geometry()
        self.root.destroy()

    def ask_settings(self):
        core_cfg = self.core.call("core cfg")
        cfg = {}
        cfg["refresh_time"] = irt = core_cfg.get("refresh_time")
        cfg.update(core_cfg)
        DlgSettings(self.root, _("Settings"), cfg=cfg)
        if cfg["OK button"]:
            cfg.pop("OK button")
            core_cfg.update(cfg)
            if not irt and core_cfg["refresh_time"]:
                self.root.after(
                    int(core_cfg["refresh_time"] * 1e3),
                    self.app_widgets["dashboard"].update)


def start_gui():
    try:
        import gettext
    except ImportError:
        __builtins__.__dict__["_"] = str
    else:
        ldir = join(dirname(__file__), pardir, pardir, "i18n", "locale")
        if isdir(ldir):
            gettext.install("otrs_us", localedir=ldir)
        else:
            gettext.install("otrs_us")
    root = Tk()
    f = Face(root, get_core())
    root.mainloop()
