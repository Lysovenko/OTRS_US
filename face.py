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
from os.path import isdir, join, dirname
from os import makedirs
from tickets import Tickets


class Face:
    def __init__(self, root):
        root.title(_("OTRS Client Side"))
        root.protocol("WM_DELETE_WINDOW", self.on_delete)
        self.root = root
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        self.ufid = []
        self.notebook = ttk.Notebook(root)
        # Dashboard, Tickets, -Customers, -Admin, -Forums, Search
        self.notebook.grid(column=0, row=0, sticky="senw")
        self.notebook.add(Tickets(self.notebook, self), text=_("Tickets"))
        self.sz = ttk.Sizegrip(root)
        self.sz.grid(column=1, row=1, sticky="se")
        self.status = StringVar()
        st_lab = ttk.Label(root, textvariable=self.status)
        st_lab.grid(column=0, row=1, sticky="we")
        self.add_menu()
        self.locked = False
        self.pages = {}
        root.tk.call("wm", "iconphoto", root._w,
                     PhotoImage(file=join(dirname(__file__), "icon.gif")))

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
        self.medit.add_command(label=_("Clear"), command=self.clear_list)

    def clear_list(self, evt=None):
        for i in self.pages:
            self.tree.delete(i)
        self.pages.clear()
        del self.ufid[:]

    def on_delete(self):
        self.root.destroy()


def start_face():
    try:
        import gettext
    except ImportError:
        __builtins__.__dict__["_"] = str
    else:
        localedir = join(dirname(__file__), "i18n", "locale")
        if isdir(localedir):
            gettext.install("jml", localedir=localedir)
        else:
            gettext.install("jml")
    root = Tk()
    f = Face(root)
    root.mainloop()


if __name__ == "__main__":
    start_face()
