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
""" """
from tkinter.ttk import (
    Button, Checkbutton, Separator, Frame, Entry, Label, Combobox)
from tkinter.scrolledtext import ScrolledText
from tkinter import IntVar, StringVar, Toplevel


class Dialog(Toplevel):
    "Base class for custom dialogs"
    def __init__(self, parent, title=None, **user_params):
        self.had_focus = parent.focus_get() if parent is not None else None
        Toplevel.__init__(self, parent)
        if title:
            self.title(title)
        self.result = None
        body = Frame(self)
        self.initial_focus = self.body(body, **user_params)
        body.pack(padx=5, pady=5)
        self.btn_ok_text = _("OK")
        self.btn_cancel_text = _("Cancel")
        self.button_box()
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        # TOTDO: Make correct dialog displacement
        self.initial_focus.focus_set()
        self.grab_set()
        self.wait_window(self)

    def body(self, master):
        """
        Dummy method to create the dialog body.
        Returns the widget which should have initial focus or None.
        Also you can override here the members btn_ok_text="OK" and
        btn_cancel_text="Cancel" to change buttons titles in button box
        """
        return

    def button_box(self):
        separ = Separator(self, orient="horizontal")
        separ.pack(expand=1, fill="x")
        box = Frame(self)
        b = Button(box, text=self.btn_ok_text, width=10,
                   command=self.accept, default="active")
        b.pack(side="left", padx=5, pady=5)
        b = Button(box, text=self.btn_cancel_text, width=10,
                   command=self.destroy)
        b.pack(side="right", padx=5, pady=5)
        self.bind("<Return>", self.accept)
        self.bind("<Escape>", self.destroy)
        box.pack()

    def accept(self, event=None):
        "Event for OK button"
        errorneous = self.validate()
        if errorneous is not None:
            errorneous.focus_set()
            return
        self.withdraw()
        self.update_idletasks()
        try:
            self.apply()
        finally:
            self.destroy()

    def destroy(self, event=None):
        "Put the focus back to the parent window and destroy the dialod"
        if self.had_focus is not None:
            self.had_focus.focus_set()
        Toplevel.destroy(self)

    def validate(self):
        """
        Dummy method to validate the data.
        Returns the widget which contain errorneous data or None.
        """
        return None

    def apply(self):
        """process the data
        This method is called automatically to process the data, *after*
        the dialog is destroyed. By default, it does nothing.
        """
        pass


class DlgLogin(Dialog):
    def body(self, master, cfg={}):
        "place user dialog widgets"
        self.config = cfg
        self.config["OK button"] = False
        self.site = StringVar()
        self.site.set(cfg.get("site", ""))
        self.login = StringVar()
        self.login.set(cfg.get("user", ""))
        self.password = StringVar()
        self.password.set(cfg.get("password", ""))
        site = Entry(master, width=15, textvariable=self.site)
        site.grid(column=1, row=0, sticky="e")
        Label(master, text=_("Site:")).grid(column=0, row=0, sticky="w")
        loge = Entry(master, width=15, textvariable=self.login)
        loge.grid(column=1, row=1, sticky="e")
        Label(master, text=_("Username:")).grid(column=0, row=1, sticky="w")
        pase = Entry(master, width=15, textvariable=self.password, show="*")
        pase.grid(column=1, row=2, sticky="e")
        Label(master, text=_("Password:")).grid(column=0, row=2, sticky="w")
        self.to_remember = IntVar()
        self.to_remember.set(cfg.get("remember_passwd", 1))
        chk1 = Checkbutton(master, text="Remember",
                           variable=self.to_remember)
        chk1.grid(column=0, row=3, sticky="w", columnspan=2)
        self.resizable(width=0, height=0)
        return loge

    def apply(self):
        "On ok button pressed"
        self.config["remember_passwd"] = self.to_remember.get()
        self.config["site"] = self.site.get()
        self.config["user"] = self.login.get()
        self.config["password"] = self.password.get()
        self.config["OK button"] = True


class DlgSettings(Dialog):
    def body(self, master, cfg={}):
        "place user dialog widgets"
        self.config = cfg
        self.config["OK button"] = False
        self.site = StringVar()
        self.site.set(cfg.get("site", ""))
        self.login = StringVar()
        self.login.set(cfg.get("user", ""))
        self.password = StringVar()
        self.password.set(cfg.get("password", ""))
        site = Entry(master, width=15, textvariable=self.site)
        site.grid(column=1, row=0, sticky="e")
        Label(master, text=_("Site:")).grid(column=0, row=0, sticky="w")
        loge = Entry(master, width=15, textvariable=self.login)
        loge.grid(column=1, row=1, sticky="e")
        Label(master, text=_("Username:")).grid(column=0, row=1, sticky="w")
        pase = Entry(master, width=15, textvariable=self.password, show="?")
        pase.grid(column=1, row=2, sticky="e")
        Label(master, text=_("Password:")).grid(column=0, row=2, sticky="w")
        self.time = StringVar()
        self.snd_cmd = StringVar()
        self.time.set(str(cfg.get("refresh_time", 0)))
        self.snd_cmd.set(str(cfg.get("snd_cmd", "")))
        self.etime = Entry(master, width=15, textvariable=self.time)
        self.etime.grid(column=1, row=3, sticky="e")
        self.esnd_cmd = Entry(master, width=15, textvariable=self.snd_cmd)
        self.esnd_cmd.grid(column=1, row=4, sticky="e")
        self.snd_err = StringVar()
        self.snd_err.set(str(cfg.get("snd_err", "")))
        self.esnd_err = Entry(master, width=15, textvariable=self.snd_err)
        self.esnd_err.grid(column=1, row=5, sticky="e")
        lab = Label(master, text=_("Refresh time:"))
        lab.grid(column=0, row=3, sticky="w")
        lab = Label(master, text=_("Sound command:"))
        lab.grid(column=0, row=4, sticky="w")
        lab = Label(master, text=_("Error sound command:"))
        lab.grid(column=0, row=5, sticky="w")
        return self.etime

    def apply(self):
        "On ok button pressed"
        self.config["refresh_time"] = int(self.time.get())
        self.config["snd_cmd"] = self.snd_cmd.get()
        self.config["snd_err"] = self.snd_err.get()
        self.config["site"] = self.site.get()
        self.config["user"] = self.login.get()
        self.config["password"] = self.password.get()
        self.config["OK button"] = True

    def validate(self):
        try:
            int(self.time.get())
        except ValueError:
            return self.etime
        return None


class DlgDropBox(Dialog):
    def body(self, master, cfg={}):
        "place user dialog widgets"
        self.config = cfg
        self.cb = Combobox(master, **cfg)
        self.cb.pack()
        self.config["OK button"] = False
        return self.cb

    def apply(self):
        "On ok button pressed"
        self.config["OK button"] = True


class DlgMsgDetails(Dialog):
    def body(self, master, cfg={}, inputs=(), selects=()):
        """place user dialog widgets
        inputs - aliases for input forms,
        selects - aliasses for dropbox names"""
        self.config = cfg
        self.config["OK button"] = False
        self.entries = entries = {}
        self.comboboxes = combos = {}
        self.stringvars = svars = {}
        for pos, (nam, lab) in enumerate(inputs):
            try:
                val = cfg[nam]
            except KeyError:
                continue
            svars[nam] = sv = StringVar()
            sv.set(val)
            entries[nam] = en = Entry(master, width=30, textvariable=sv)
            en.grid(column=1, row=pos, sticky="e")
            Label(master, text=lab).grid(column=0, row=pos, sticky="w")
        start_pos = len(inputs)
        for pos, (nam, lab) in enumerate(selects, start_pos):
            try:
                sel, itms = cfg[nam]
            except KeyError:
                continue
            itms, names = zip(*itms)
            combos[nam] = cb = Combobox(
                master, width=30, state="readonly", values=names,
                exportselection=0)
            cb.grid(column=1, row=pos, sticky="e")
            cb.current(itms.index(sel) if sel else 0)
            Label(master, text=lab).grid(column=0, row=pos, sticky="w")

    def apply(self):
        cfg = self.config
        self.config["OK button"] = True
        for nam, val in self.stringvars.items():
            cfg[nam] = val.get()
        for nam, val in self.comboboxes.items():
            cfg[nam] = cfg[nam][1][val.current()][0]


class AboutBox(Toplevel):
    "an AboutBox emmulation in tkinter"
    def __init__(self, parent, title=None, text=None):
        self.had_focus = parent.focus_get()
        Toplevel.__init__(self, parent)
        if title:
            self.title(title)
        stext = ScrolledText(self, background="gray")
        stext.pack(padx=5, pady=5)
        if text is not None:
            stext.insert("end", text)
        stext["state"] = "disabled"
        separ = Separator(self, orient="horizontal")
        separ.pack(expand=1, fill="x")
        b = Button(self, text=_("OK"), width=10,
                   command=self.destroy, default="active")
        self.bind("<Escape>", self.destroy)
        b.pack()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        b.focus_set()
        self.grab_set()
        self.wait_window()

    def destroy(self, event=None):
        "Put the focus back to the parent window and destroy the dialod"
        if self.had_focus is not None:
            self.had_focus.focus_set()
        Toplevel.destroy(self)


if __name__ == "__main__":
    from tkinter import Tk, Button
    _ = str
    root = Tk()
    cfg = dict((
        ("ToCustomer", "To"), ("CcCustomer", "Copy"),
        ("BccCustomer", "Hidden copy"), ("Subject", "Subject"),
        ("TimeUnits", "Time units"),
        ("StateID", ("x", (("c", "h"), ("x", "y")))),
        ("Month", ("x", (("c", "h"), ("x", "y")))),
        ("Day", ("x", (("c", "h"), ("x", "y")))),
        ("Year", ("x", (("c", "h"), ("x", "y")))),
        ("Hour", ("x", (("c", "h"), ("x", "y")))),
        ("Minute", ("x", (("c", "h"), ("x", "y")))),
        ("DynamicField_TicketFreeText15", ("x", (("c", "h"), ("x", "y"))))
    ))
    DlgMsgDetails(root, title="about drop", cfg=cfg)
    print(cfg)
