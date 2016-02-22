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
"Making the Tickets widget"

from tkinter import ttk, StringVar
from .ttext import TicText
from .ticket_cb import Callbacks


def autoscroll(sbar, first, last):
    """Hide and show scrollbar as needed."""
    first, last = float(first), float(last)
    if first <= 0 and last >= 1:
        sbar.grid_remove()
    else:
        sbar.grid()
    sbar.set(first, last)


class Tickets(ttk.Frame, Callbacks):
    def __init__(self, parent, appw):
        ttk.Frame.__init__(self, parent)
        Callbacks.__init__(self, appw)
        self.pw = pw = ttk.Panedwindow(self, orient="vertical")
        frame = self.make_tree()
        self.make_binds(frame)
        pw.add(frame)
        pw.pane(frame, weight=1)
        frame = self.make_text_field(appw["config"].get("spell"))
        self.make_binds(frame)
        pw.add(frame)
        pw.pane(frame, weight=2)
        pw.pack(fill="both")

    def make_binds(self, frame):
        binds = (
            ("Escape", self.go_dasboard), ("Control-i", self.menu_info),
            ("Control-r", self.menu_reload), ("Control-l", self.menu_lock),
            ("Control-m", self.menu_move), ("Control-a", self.menu_answer),
            ("Control-s", self.menu_send), ("Control-t", self.menu_note),
            ("Control-e", self.menu_close), ("Control-w", self.menu_forward),
            ("Control-o", self.menu_owner), ("Control-n", self.menu_new_email),
            ("Control-h", self.menu_new_phone),
            ("Control-j", self.menu_ticket_merge))
        for i in frame.winfo_children():
            for k, f in binds:
                i.bind("<%s>" % k, f)

    def make_tree(self):
        frame = ttk.Frame(self.pw)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.tree = tree = ttk.Treeview(
            frame, selectmode="extended", columns=("from", "created", "mode"))
        tree.grid(column=0, row=0, sticky="nwes")
        vsb = ttk.Scrollbar(frame, command=tree.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        tree["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        hsb = ttk.Scrollbar(
            frame, command=tree.xview, orient="horizontal")
        hsb.grid(column=0, row=1, sticky="ew")
        tree["xscrollcommand"] = lambda f, l: autoscroll(hsb, f, l)
        tree.column("from", width=170, anchor="center")
        tree.column("created", width=70, anchor="center")
        tree.column("mode", width=70, anchor="center")
        tree.bind("<Double-Button-1>", self.enter_article)
        tree.bind("<Return>", self.enter_article)
        tree.bind("<Control-Return>", self.menu_download_eml)
        tag_clrs = {
            "agent-email-external": "#D3E5B5",
            "agent-email-internal": "#ffd1d1",
            "agent-note-external": "#d1d1d1",
            "agent-note-internal": "#FFCCCC",
            "agent-phone": "#d1e8d1",
            "customer-email-external": "#D4DEFC",
            "customer-note-external": "#D4DEFC",
            "customer-phone": "#FCB24B",
            "customer-webrequest": "#FCB24B",
            "system-email-external": "#ffffd1",
            "system-email-internal": "#ffffd1",
            "system-email-notification-ext": "#ffffd1",
            "system-email-notification-int": "#ffffd1",
            "system-note-external": "#ffffd1",
            "system-note-internal": "#ffffd1",
            "system-note-report": "#ffffd1"}
        tag_clrs.update(self.app_widgets["config"].get("art_type_clrs", ()))
        for nam, clr in tag_clrs.items():
            tree.tag_configure(nam, background=clr)
        tree.tag_configure("hightlighted", foreground="red")
        return frame

    def make_text_field(self, spell):
        frame = ttk.Frame(self.pw)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        text = TicText(frame, spell=spell, state="disabled")
        self.text = text
        text.grid(column=0, row=0, sticky="nwes")
        vsb = ttk.Scrollbar(frame, command=self.text.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        text["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        self.text_curinfo = None
        return frame
