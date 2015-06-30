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
"""
Making a face of the application
"""

from tkinter import Tk, Menu, PhotoImage, ttk, Text, StringVar, messagebox, \
    BooleanVar
from tkinter.filedialog import askdirectory
from os.path import isdir, join, dirname
from os import makedirs
from threading import Lock


def autoscroll(sbar, first, last):
    """Hide and show scrollbar as needed."""
    first, last = float(first), float(last)
    if first <= 0 and last >= 1:
        sbar.grid_remove()
    else:
        sbar.grid()
    sbar.set(first, last)


class Face:
    def __init__(self, root):
        root.title(_("OTRS Client Side"))
        root.protocol("WM_DELETE_WINDOW", self.on_delete)
        self.root = root
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self.ufid = []
        self.add_control(root)
        pw = ttk.Panedwindow(root, orient="vertical")
        self.pw = pw
        pw.add(self.make_tree())
        pw.add(self.make_text_field())
        pw.grid(column=0, row=1, columnspan=2, sticky="senw")
        self.sz = ttk.Sizegrip(root)
        self.sz.grid(column=1, row=2, sticky="se")
        self.status = StringVar()
        st_lab = ttk.Label(root, textvariable=self.status)
        st_lab.grid(column=0, row=2, sticky="we")
        self.add_menu()
        self.locked = False
        self.slock = Lock()
        self.pages = {}
        root.tk.call("wm", "iconphoto", root._w,
                     PhotoImage(file=join(dirname(__file__), "icon.gif")))

    def add_control(self, frame):
        self.control = ttk.Frame(frame)
        self.control.grid_columnconfigure(1, weight=1)
        self.control.grid(column=0, row=0, columnspan=2, sticky="ew")
        self.btn = ttk.Button(self.control, command=self.search,
                              text=_("Search"), width=8)
        self.btn.grid(column=0, row=0, sticky="w")
        self.entry = ttk.Entry(self.control, width=60)
        self.entry.grid(column=1, row=0, sticky="ew", padx=3)
        self.entry.bind("<KeyPress-Return>", self.search)
        self.dirname = StringVar()
        self.dirlab = ttk.Label(self.control, textvariable=self.dirname)
        self.dirlab.grid(row=1, column=1, sticky="ew")

    def make_tree(self):
        frame = ttk.Frame(self.pw)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.tree = tree = ttk.Treeview(frame, selectmode="extended")
        self.treef = frame
        tree.grid(column=0, row=0, sticky="nwes")
        vsb = ttk.Scrollbar(frame, command=tree.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        tree["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        hsb = ttk.Scrollbar(
            frame, command=tree.xview, orient="horizontal")
        hsb.grid(column=0, row=1, sticky="ew")
        tree["xscrollcommand"] = lambda f, l: autoscroll(hsb, f, l)
        tree.tag_bind("page", "<Insert>", self.remember_pg)
        tree.tag_configure("page", background="gray")
        tree.tag_configure("file", foreground="blue", font="Monospace 12")
        tree.tag_configure("bmk", foreground="red")
        tree.tag_configure("folder", font="Times 14 bold")
        return frame

    def make_text_field(self):
        frame = ttk.Frame(self.pw)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        text = Text(frame, state="disabled", wrap="word",
                    font="Times 14")
        self.text = text
        text.grid(column=0, row=0, sticky="nwes")
        vsb = ttk.Scrollbar(frame, command=self.text.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        text["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        self.text_curinfo = None
        text.tag_configure("h1", font="Times 16 bold", relief="raised")
        return frame

    def add_menu(self):
        top = self.tree.winfo_toplevel()
        top["menu"] = self.menubar = Menu(top)
        self.mfile = Menu(self.menubar)
        self.medit = Menu(self.menubar)
        self.msites = Menu(self.menubar)
        self.menubar.add_cascade(menu=self.mfile, label=_("File"))
        self.menubar.add_cascade(menu=self.medit, label=_("Edit"))
        self.menubar.add_cascade(menu=self.msites, label=_("Sites"))
        self.mfile.add_command(label=_("Search"), command=self.search)
        self.mfile.add_command(label=_("Quit"), command=self.on_delete,
                               accelerator="Ctrl+Q", underline=1)
        self.root.bind_all("<Control-q>", lambda x: self.on_delete())
        self.medit.add_command(label=_("Clear"), command=self.clear_list)

    def search(self, evt=None):
        self.sstatus(_("Wait..."))
        pages = self.pages
        sr = web_search(
            self.entry.get(), {i[0] for i in self.sites if i[2].get()})
        if sr is None:
            return
        for i in sr:
            h = i["hash"]
            if h not in pages:
                self.tree.insert("", "end", h, text=i["title"],
                                 tags=("page",))
                pages[h] = {"entered": False}
                pages[h]["site"] = i["site"]
                pages[h]["page"] = i["page"]
        self.sstatus(_("OK"))

    def remember_pg(self, evt=None):
        """Switch page remember"""
        iid = self.tree.focus()
        if iid in self.remember:
            self.tree.item(iid, tags=("page",))
            self.remember.pop(iid)
        else:
            self.tree.item(iid, tags=("page", "bmk"))
            pg = self.pages[iid]
            remember = dict()
            for name in ("site", "page", "folder"):
                if name in pg:
                    remember[name] = pg[name]
            remember["title"] = self.tree.item(iid)["text"]
            self.remember[iid] = remember

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
