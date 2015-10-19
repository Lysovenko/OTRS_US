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

from tkinter import ttk, Text, StringVar
from tkinter.messagebox import showerror, showinfo
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urllib.error import URLError
from ..core.pgload import (
    TicketsPage, MessagePage, AnswerPage, AnswerSender, LoginError)
from .dialogs import AboutBox, DlgDetails


def autoscroll(sbar, first, last):
    """Hide and show scrollbar as needed."""
    first, last = float(first), float(last)
    if first <= 0 and last >= 1:
        sbar.grid_remove()
    else:
        sbar.grid()
    sbar.set(first, last)


class Tickets(ttk.Frame):
    def __init__(self, parent, appw):
        ttk.Frame.__init__(self, parent)
        self.app_widgets = appw
        self.echo = appw["core"].echo
        self.runt_cfg = appw["core"].call("runtime cfg")
        self.pw = pw = ttk.Panedwindow(self, orient="vertical")
        frame = self.make_tree()
        pw.add(frame)
        pw.pane(frame, weight=1)
        frame = self.make_text_field()
        pw.add(frame)
        pw.pane(frame, weight=2)
        pw.pack(fill="both")
        self.articles_range = []
        self.tree_data = {}
        self.url_begin = None
        self.cur_article = {}
        self.my_tab = None
        self.my_url = None
        self.ticket_info = None
        self.action_subaction = {}
        self.actions_params = {}
        self.queues = {}

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
        for k, f in (
                ("Escape", self.go_dasboard), ("i", self.menu_info),
                ("r", self.menu_reload), ("l", self.menu_lock),
                ("m", self.menu_move), ("a", self.menu_answer),
                ("s", self.menu_send), ("t", self.menu_note),
                ("e", self.menu_close), ("w", self.menu_forward),
                ("o", self.menu_owner), ("n", self.menu_new_email),
                ("h", self.menu_new_phone)):
            frame.bind_all("<Control-%s>" % k, f)
        return frame

    def go_dasboard(self, evt):
        self.app_widgets["notebook"].select(0)
        self.app_widgets["notebook"].hide(self)
        self.app_widgets["dashboard"].tree["New"].focus_set()
        self.set_menu_active()

    def make_text_field(self):
        frame = ttk.Frame(self.pw)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        text = Text(frame, state="disabled", wrap="word",
                    font="Times 14", takefocus=True)
        self.text = text
        text.grid(column=0, row=0, sticky="nwes")
        vsb = ttk.Scrollbar(frame, command=self.text.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        text["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        self.text_curinfo = None
        text.tag_configure("h1", font="Times 16 bold", relief="raised")
        return frame

    def load_ticket(self, url):
        self.echo("load ticket:", url)
        self.my_url = url
        self.app_widgets["menu_ticket"].entryconfig(
            _("Send message"), state="disabled")
        pg = TicketsPage(self.app_widgets["core"])
        lres = None
        while True:
            try:
                lres = pg.load(url)
                self.fill_tree(lres["articles"])
                break
            except LoginError:
                if self.app_widgets["dashboard"].login(pg):
                    continue
                lres = None
                break
            except ConnectionError:
                try:
                    self.echo("Login in Tickets.load_ticket")
                    pg.login(self.runt_cfg)
                except (LoginError, KeyError):
                    self.go_dasboard(None)
                    lres = None
            except KeyError:
                showerror(_("Error"), _("Wrong Ticket"))
                return
        self.get_tickets_page(lres)
        self.set_menu_active()

    def get_tickets_page(self, page):
        if page is None:
            return
        if "info" in page:
            self.ticket_info = page["info"]
        mail_header = page.get("mail_header", [])
        try:
            mail_text = page["message_text"]
        except KeyError:
            pass
        self.detect_allowed_actions(page.get("action_hrefs", []) +
                                    page.get("art_act_hrefs", []))
        try:
            self.queues = page["queues"]
        except KeyError:
            pass
        try:
            self.answers = page["answers"]
        except (KeyError, IndexError):
            self.answers = None
        if "article text" in self.cur_article:
            mail_text = self.cur_article["article text"]
        elif "mail_src" in page:
            url = urlunsplit(
                self.url_begin[:2] + urlsplit(page["mail_src"])[2:])
            self.echo("Get message:", url)
            pg = MessagePage(self.app_widgets["core"])
            mail_text = pg.load(url)
        self.cur_article["article text"] = mail_text
        self.cur_article["article header"] = mail_header
        self.show_email(self.cur_article)

    def show_email(self, article):
        snapshot = article.get("snapshot")
        text = self.text
        text["state"] = "normal"
        text.delete("1.0", "end")
        if snapshot is None:
            for i in article["article header"]:
                text.insert("end", "%s\t%s\n" % i)
            text.insert("end", "\n")
            for i in article["article text"]:
                text.insert("end", *i)
        else:
            text.insert("1.0", snapshot)
        text["state"] = "normal" if article["editable"] else "disabled"

    def detect_allowed_actions(self, act_hrefs):
        total = {}
        allowed = {"AgentTicketLock": False}
        ac_sub = self.action_subaction
        ac_sub.clear()
        for href in act_hrefs:
            qd = dict(parse_qsl(urlsplit(href).query))
            total.update(qd)
            try:
                ac_sub[qd["Action"]] = qd.get("Subaction")
            except KeyError:
                pass
            if qd.get("Action") in allowed:
                allowed[qd["Action"]] = True
        self.actions_params = total
        econ = self.app_widgets["menu_ticket"].entryconfig
        state = "normal" if allowed["AgentTicketLock"] else "disabled"
        for l in (_("Lock"), _("Answer"), _("Close")):
            econ(l, state=state)
        try:
            self.change_cur_article(self.tree_data[total["ArticleID"]])
            self.tree.focus(item=total["ArticleID"])
        except KeyError:
            pass

    def change_cur_article(self, article):
        ca = self.cur_article
        if ca is article:
            return
        if ca.get("editable"):
            ca["snapshot"] = self.text.get("1.0", "end")
        self.cur_article = article

    def fill_tree(self, articles):
        if articles is None:
            raise ConnectionError()
        tree_data = {}
        self.url_begin = (urlsplit(self.runt_cfg["site"])[:2] +
                          (urlsplit(articles[0]["article info"])[2],))
        tree = self.tree
        for i in reversed(self.articles_range):
            tree.delete(i)
        del self.articles_range[:]
        for item in articles:
            qd = dict(parse_qsl(urlsplit(item["article info"]).query))
            item["article info"] = qd
            item["editable"] = False
            no = qd["ArticleID"]
            tree_data[no] = item
            self.articles_range.append(no)
            tree.insert(
                "", "end", no, text=item["Subject"],
                values=(item["From"], item["Created"], item["Type"]))
        for i in list(self.tree_data.keys()):
            if i not in tree_data:
                del self.tree_data[i]
        for i in tree_data:
            if i not in self.tree_data:
                self.tree_data[i] = tree_data[i]
        self.app_widgets["notebook"].select(self)
        self.my_tab = self.app_widgets["notebook"].select()
        self.tree.focus(item=self.articles_range[0])
        self.tree.focus_set()

    def enter_article(self, evt):
        iid = evt if type(evt) == str else evt.widget.focus()
        if iid:
            self.app_widgets["menu_ticket"].entryconfig(
                _("Send message"), state="normal"
                if iid == "editable" else "disabled")
            ca = self.tree_data[iid]
            self.change_cur_article(ca)
            if "article text" in ca:
                self.show_email(ca)
                return
            params = [("Action", "AgentTicketZoom"),
                      ("Subaction", "ArticleUpdate")]
            for i in ("Count", "TicketID", "ArticleID"):
                params.append((i, ca["article info"][i]))
            params.append(("Session", self.runt_cfg["Session"]))
            url = urlunsplit(self.url_begin + (urlencode(params), ""))
            pg = TicketsPage(self.app_widgets["core"])
            self.get_tickets_page(pg.load(url))

    def set_menu_active(self):
        econ = self.app_widgets["menubar"].entryconfig
        if self.my_tab == self.app_widgets["notebook"].select():
            econ(_("Ticket"), state="normal")
        else:
            econ(_("Ticket"), state="disabled")

    def menu_lock(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        title = _("Ticket Lock")
        try:
            subact = self.action_subaction["AgentTicketLock"]
        except KeyError:
            showerror(title, _("You are late. Sorry."))
            return
        params = [("Action", "AgentTicketLock"), ("Subaction", subact)]
        self.append_params(params, "menu_lock", (
            "TicketID", "ChallengeToken", "Session"))
        url = urlunsplit(self.url_begin + (urlencode(params), ""))
        pg = TicketsPage(self.app_widgets["core"])
        lres = pg.load(url)
        self.get_tickets_page(lres)
        if lres:
            if subact == "Lock":
                showinfo(title, _("The ticket was successfully locked"))
            else:
                showinfo(title, _("The ticket was successfully unlocked"))
        else:
            showerror(title, _("The operation was failed"))

    def menu_move(self, evt=None):
        if not self.queues or \
           self.my_tab != self.app_widgets["notebook"].select():
            return
        cfg = {"queue": self.queues}
        DlgDetails(self, _("Change queue"), cfg=cfg, selects=(
            ("queue", _("Queue:")),))
        if cfg["OK button"]:
            params = [
                ("Action", "AgentTicketMove"), ("QueueID", ""),
                ("DestQueueID", cfg["queue"])]
            self.append_params(params, "menu_move", (
                "TicketID", "ChallengeToken", "Session"))
            url = urlunsplit(self.url_begin + ("", ""))
            pg = TicketsPage(self.app_widgets["core"])
            try:
                lres = pg.load(url, urlencode(params).encode())
                self.get_tickets_page(lres)
            except LoginError:
                pass

    def menu_answer(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        if "editable" in self.tree_data or not self.answers:
            return
        cfg = {"type": self.answers}
        DlgDetails(self, _("Answer type"), cfg=cfg, selects=(
            ("type", _("Answer type:")),))
        if cfg["OK button"]:
            params = [("Action", "AgentTicketCompose"),
                      ("ReplyAll", ""), ("ResponseID", cfg["type"])]
            i = "ArticleID"
            self.actions_params[i] = self.cur_article["article info"][i]
            self.append_params(params, "menu_answer", (
                "Session", "TicketID", "ArticleID", "ChallengeToken"))
            url = urlunsplit(self.url_begin + (urlencode(params), ""))
            pg = AnswerPage(self.app_widgets["core"])
            inputs, error = pg.load(url)
            if inputs:
                txt = dict(inputs).get("Body", "")
                ca = {"editable": True, "article text": (), "inputs": inputs,
                      "snapshot": txt}
                self.articles_range.append("editable")
                self.tree.insert("", "end", "editable", text=_("Edit"))
                self.tree_data["editable"] = ca
                self.enter_article("editable")
                self.tree.focus("editable")
            else:
                showerror(_("Answer"), (error if error else "Can't answer"))

    def menu_note(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        params = [("Action", "AgentTicketNote")]
        self.append_params(params, "menu_note", ("TicketID", "Session"))
        url = urlunsplit(self.url_begin + (urlencode(params), ""))
        pg = AnswerPage(self.app_widgets["core"])
        inputs, error = pg.load(url)
        cfg = dict(inputs)
        cfg.pop("FileUpload")
        DlgDetails(self, _("Note"), cfg=cfg, focus_on="Body", inputs=(
            ("Subject", _("Subject:")), ("Body", _("Message:")),
            ("TimeUnits", _("Time units:"))), selects=(
            ("ArticleTypeID", _("Type of note:")),
            ("NewStateID", _("Next state:")), ("Month", _("Month:")),
            ("Day", _("Day:")), ("Year", _("Year:")),
            ("Hour", _("Hour:")), ("Minute", _("Minute:"))))
        if cfg["OK button"]:
            pg = AnswerSender(self.app_widgets["core"])
            url = urlunsplit(self.url_begin + ("", ""))
            pg.send(url, [(i[0], cfg.get(i[0], ("", b""))) for i in inputs])
            self.menu_reload()

    def menu_owner(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        params = [("Action", "AgentTicketOwner")]
        self.append_params(params, "menu_note", ("TicketID", "Session"))
        url = urlunsplit(self.url_begin + (urlencode(params), ""))
        pg = AnswerPage(self.app_widgets["core"])
        inputs, error = pg.load(url)
        if not inputs:
            showerror(_("Change owner"), error)
        cfg = dict(inputs)
        cfg.pop("FileUpload")
        cfg["NewOwnerType"] = "New"
        DlgDetails(self, _("Owner"), cfg=cfg, focus_on="NewOwnerID", inputs=(
            ("Subject", _("Subject:")), ("Body", _("Comment:"))), selects=(
            ("NewOwnerID", _("Owner:")), ("OldOwnerID", _("Old owner:")),
            ("ArticleTypeID", _("Article type:"))))
        if cfg["OK button"] and cfg.get("NewOwnerID"):
            if not cfg["Body"]:
                cfg["Body"] = "Owner was changed using OTRS_US"
            pg = AnswerSender(self.app_widgets["core"])
            url = urlunsplit(self.url_begin + ("", ""))
            pg.send(url, [(i[0], cfg.get(i[0], ("", b""))) for i in inputs])
            self.menu_reload()

    def menu_close(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        params = [("Action", "AgentTicketClose")]
        self.append_params(params, "menu_note", ("TicketID", "Session"))
        url = urlunsplit(self.url_begin + (urlencode(params), ""))
        pg = AnswerPage(self.app_widgets["core"])
        inputs, error = pg.load(url)
        if not inputs:
            showerror(_("Close"), error)
            return
        cfg = dict(inputs)
        cfg.pop("FileUpload")
        DlgDetails(self, _("Close"), cfg=cfg, focus_on="Body", inputs=(
            ("Subject", _("Subject:")), ("Body", _("Message:")),
            ("TimeUnits", _("Time units:"))), selects=(
            ("ArticleTypeID", _("Type of note:")),
            ("NewStateID", _("Next state:")),
            ("DynamicField_TicketFreeText15", _("Requires review:"))))
        if cfg["OK button"]:
            if not cfg["Body"]:
                cfg["Body"] = "Closed using OTRS_US"
            pg = AnswerSender(self.app_widgets["core"])
            url = urlunsplit(self.url_begin + ("", ""))
            pg.send(url, [(i[0], cfg.get(i[0], ("", b""))) for i in inputs])
            self.menu_reload()

    def menu_info(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        res = []
        for item in self.ticket_info:
            if type(item) == str:
                res.append(item.strip() + "\n")
            else:
                res.append("%s\t%s\n" % tuple(i.strip() for i in item[:2]))
        AboutBox(self, title=_("Ticket Info"), text="".join(res))

    def menu_forward(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        if "editable" in self.tree_data or not self.answers:
            return
        params = [("Action", "AgentTicketForward")]
        self.append_params(params, "menu_note", (
            "TicketID", "ArticleID", "Session"))
        url = urlunsplit(self.url_begin + (urlencode(params), ""))
        pg = AnswerPage(self.app_widgets["core"])
        inputs, error = pg.load(url)
        if not inputs:
            showerror(_("Forward"), error)
            return
        cfg = dict(inputs)
        txt = cfg.get("Body", "")
        ca = {"editable": True, "article text": (), "inputs": inputs,
              "snapshot": txt}
        self.articles_range.append("editable")
        self.tree.insert("", "end", "editable", text=_("Edit"))
        self.tree_data["editable"] = ca
        self.enter_article("editable")
        self.tree.focus("editable")

    def menu_reload(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        if self.my_url:
            self.load_ticket(self.my_url)

    def menu_send(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select() or \
           self.tree.focus() != "editable":
            return
        inputs = self.tree_data["editable"]["inputs"]
        cfg = dict(inputs)
        cfg.pop("FileUpload")
        cfg["CustomerTicketCounterToCustomer"] = "1"
        DlgDetails(self, _("Send"), cfg=cfg, inputs=(
            ("ToCustomer", _("To:")), ("CcCustomer", _("Copy:")),
            ("BccCustomer", _("Hidden copy:")), ("To", _("To:")),
            ("Cc", _("Copy:")), ("Bcc", _("Hidden copy:")),
            ("Subject", _("Subject:")),
            ("TimeUnits", _("Time units:"))), selects=(
            ("StateID", _("Next state:")),
            ("ComposeStateID", _("Next state:")), ("Month", _("Month:")),
            ("Day", _("Day:")), ("Year", _("Year:")),
            ("Hour", _("Hour:")), ("Minute", _("Minute:")),
            ("DynamicField_TicketFreeText15", _("Requires review:")),
            ("ArticleTypeID", _("Article type:"))))
        if cfg["OK button"]:
            cfg["Body"] = self.text.get("1.0", "end")
            pg = AnswerSender(self.app_widgets["core"])
            url = urlunsplit(self.url_begin + ("", ""))
            form = [(i[0], cfg.get(i[0], ("", b""))) for i in inputs]
            email = None
            for i in ("ToCustomer", "To", "CustomerInitialValue"):
                if i in cfg and cfg[i]:
                    email = cfg[i]
                    break
            if email is None:
                showerror(_("Error"), _("Receiver was not found"))
                return
            if '<' in email:
                email = email[email.find("<")+1:email.find(">")]
            pos = 0
            for i in range(len(form)):
                if form[i][0] == "CustomerTicketText":
                    pos = i + 1
                    break
            for i in reversed((
                    ("CustomerInitialValue_1", email),
                    ("CustomerKey_1", ""),
                    ("CustomerQueue_1", email),
                    ("CustomerTicketText_1", email))):
                form.insert(pos, i)
            pg.send(url, form)
            self.app_widgets["menu_ticket"].entryconfig(
                _("Send message"), state="disabled")
            self.tree.delete("editable")
            self.tree_data.pop("editable")
            self.articles_range.pop(self.articles_range.index("editable"))
            self.tree.focus(item=self.articles_range[-1])
            self.menu_reload()

    def append_params(self, params, where, keys):
        self.actions_params["ArticleID"] = self.tree.focus()
        for i in keys:
            try:
                params.append((i, self.actions_params[i]))
            except KeyError as err:
                self.echo("In %s KeyError: %s" % (where, err))

    def menu_new_email(self, evt=None):
        self.my_url = None
        self.app_widgets["menu_ticket"].entryconfig(
            _("Send message"), state="normal")
        self.set_menu_active()
        if "editable" in self.tree_data:
            return
        params = [("Action", "AgentTicketEmail")]
        self.append_params(params, "menu_new_email", ("Session",))
        url = urlunsplit(self.url_begin + (urlencode(params), ""))
        pg = AnswerPage(self.app_widgets["core"])
        inputs, error = pg.load(url)
        if not inputs:
            showerror(_("New email"), error)
            return
        self.tree_data.clear()
        for i in reversed(self.articles_range):
            self.tree.delete(i)
        self.articles_range = ["editable"]
        cfg = dict(inputs)
        txt = cfg.get("Body", "")
        ca = {"editable": True, "article text": (), "inputs": inputs,
              "snapshot": txt}
        self.tree.insert("", "end", "editable", text=_("Edit"))
        self.tree_data["editable"] = ca
        self.enter_article("editable")
        self.tree.focus("editable")
        self.echo('New email ticket')

    def menu_new_phone(self, evt=None):
        self.echo('New phone ticket')

    def menu_ticket_merge(self, evt=None):
        print('AgentTicketMerge')
