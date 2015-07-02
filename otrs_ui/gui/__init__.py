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
"Making the face of the application"

from tkinter import Tk, Menu, PhotoImage, ttk, StringVar, messagebox, \
    BooleanVar
from tkinter.filedialog import askdirectory
from os.path import isdir, join, dirname, pardir
from os import makedirs
from ..settings import Config
from .tickets import Tickets
from .dashboard import Dashboard


class Face:
    def __init__(self, root):
        root.title(_("OTRS Client Side"))
        root.protocol("WM_DELETE_WINDOW", self.on_delete)
        self.root = root
        self.config = Config("face.cfg")
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        self.ufid = []
        self.notebook = ntbk = ttk.Notebook(root)
        # Dashboard, Tickets, -Customers, -Admin, -Forums, Search
        ntbk.grid(column=0, row=0, sticky="senw")
        ntbk.add(Dashboard(ntbk, self), text=_("Dashboard"))
        ntbk.add(Tickets(ntbk, self), text=_("Tickets"))
        self.sz = ttk.Sizegrip(root)
        self.sz.grid(column=1, row=1, sticky="se")
        self.status = StringVar()
        st_lab = ttk.Label(root, textvariable=self.status)
        st_lab.grid(column=0, row=1, sticky="we")
        self.add_menu()
        self.locked = False
        root.tk.call("wm", "iconphoto", root._w,
                     PhotoImage(file=join(dirname(__file__), "icon.gif")))
        root.geometry(self.config.get("geometry"))

    def add_menu(self):
        top = self.root.winfo_toplevel()
        top["menu"] = self.menubar = Menu(top)
        self.mfile = Menu(self.menubar)
        self.medit = Menu(self.menubar)
        self.msites = Menu(self.menubar)
        self.menubar.add_cascade(menu=self.mfile, label=_("File"))
        self.menubar.add_cascade(menu=self.medit, label=_("Edit"))
        self.menubar.add_cascade(menu=self.msites, label=_("Sites"))
        self.mfile.add_command(label=_("Search"))
        self.mfile.add_command(label=_("Quit"), command=self.on_delete,
                               accelerator="Ctrl+Q", underline=1)
        self.root.bind_all("<Control-q>", lambda x: self.on_delete())

    def on_delete(self):
        self.config["geometry"] = self.root.geometry()
        del self.config
        self.root.destroy()


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
    f = Face(root)
    root.mainloop()


if __name__ == "__main__":
    start_face()
