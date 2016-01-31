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
from tkinter.messagebox import showerror, showinfo
from time import ctime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import re
from ..core import version
from ..core.msg_ldr import MessageLoader, article_by_url, article_type
from ..core.pgload import (
    TicketsPage, MessagePage, AnswerPage, AnswerSender, LoginError, FileLoader)
from .dialogs import AboutBox, DlgDetails
from .ttext import TicText
EDITABLE = -1


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
        self.core_cfg = appw["core"].call("core cfg")
        self.loader = MessageLoader(appw["core"])
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
        self.cur_article = -2
        self.my_tab = None
        self.ticket_id = None
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
                ("h", self.menu_new_phone), ("j", self.menu_ticket_merge)):
            frame.bind_all("<Control-%s>" % k, f)
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
        text = TicText(frame, spell=self.core_cfg.get("spell"),
                       state="disabled")
        self.text = text
        text.grid(column=0, row=0, sticky="nwes")
        vsb = ttk.Scrollbar(frame, command=self.text.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        text["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        self.text_curinfo = None
        return frame

    def load_ticket(self, ticket_id, force=False):
        self.ticket_id = ticket_id
        articles, info, allowed = self.loader.zoom_ticket(ticket_id, force)
        self.app_widgets["menu_ticket"].entryconfig(
            _("Send message"), state="disabled")
        self.fill_tree(articles)
        self.ticket_info = info
        self.detect_allowed_actions(allowed)
        self.queues = self.core_cfg.get("queues")
        self.answers = self.core_cfg.get("answers")
        for show in reversed(self.articles_range):
            if "system" not in article_type(articles[show]["Flags"]):
                break
        self.enter_article(show)
        self.tree.focus(show)
        self.set_menu_active()

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
        text["state"] = "normal" if article[EDITABLE] else "disabled"

    def detect_allowed_actions(self, allowed):
        allowed = dict(allowed)
        self.actions_params = allowed
        econ = self.app_widgets["menu_ticket"].entryconfig
        state = "normal" if allowed.get("AgentTicketLock") else "disabled"
        for l in (_("Lock"), _("Answer"), _("Close")):
            econ(l, state=state)

    def change_cur_article(self, article):
        if self.cur_article == article:
            return self.tree_data[article]
        try:
            ca = self.tree_data[self.cur_article]
            if ca.get(EDITABLE):
                ca["snapshot"] = self.text.get("1.0", "end")
        except KeyError:
            pass
        self.cur_article = article
        return self.tree_data[article]

    def fill_tree(self, articles):
        tree = self.tree
        for i in reversed(self.articles_range):
            tree.delete(i)
        self.articles_range = list(articles)
        self.articles_range.sort(key=lambda x: articles[x]["ctime"])
        for art_id in self.articles_range:
            item = articles[art_id]
            item[EDITABLE] = False
            tags = (article_type(item["Flags"]),)
            tree.insert(
                "", "end", art_id, text=item["Title"],
                values=(item["Sender"], ctime(item["ctime"]),
                        "%x" % item["Flags"]), tags=tags)
        self.tree_data = articles
        self.app_widgets["notebook"].select(self)
        self.my_tab = self.app_widgets["notebook"].select()
        self.tree.focus(item=self.articles_range[0])
        self.tree.focus_set()

    def enter_article(self, evt):
        iid = (int(evt) if isinstance(evt, (str, int, float))
               else int(evt.widget.focus()))
        if iid:
            self.app_widgets["menu_ticket"].entryconfig(
                _("Send message"), state="normal"
                if iid == EDITABLE else "disabled")
            ca = self.change_cur_article(iid)
            if "article text" in ca:
                self.show_email(ca)
                return
            mail_text = self.loader.zoom_article(ca["TicketID"], iid)
            ca.update(((EDITABLE, False), ("article header", ()),
                       ("article text", mail_text)))
            self.show_email(ca)

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
        url = self.extract_url(params, "menu_lock", (
            "TicketID", "ChallengeToken", "OTRSAgentInterface"))
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
            self.loader.move_ticket(self.ticket_id, cfg["queue"])

    def menu_answer(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        if EDITABLE in self.tree_data or not self.answers:
            return
        cfg = {"type": self.answers}
        DlgDetails(self, _("Answer type"), cfg=cfg, selects=(
            ("type", _("Answer type:")),))
        if cfg["OK button"]:
            params = [("Action", "AgentTicketCompose"),
                      ("ReplyAll", ""), ("ResponseID", cfg["type"])]
            i = "ArticleID"
            self.actions_params[i] = self.cur_article["article info"][i]
            url = self.extract_url(params, "menu_answer", (
                "TicketID", "ArticleID", "ChallengeToken"))
            pg = AnswerPage(self.app_widgets["core"])
            inputs, error = pg.load(url)
            if inputs:
                txt = dict(inputs).get("Body", "")
                ca = {EDITABLE: True, "article text": (), "inputs": inputs,
                      "snapshot": txt}
                self.articles_range.append(EDITABLE)
                self.tree.insert("", "end", EDITABLE, text=_("Edit"))
                self.tree_data[EDITABLE] = ca
                self.enter_article(EDITABLE)
                self.tree.focus(EDITABLE)
            else:
                showerror(_("Answer"), (error if error else "Can't answer"))

    def menu_note(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        params = [("Action", "AgentTicketNote")]
        url = self.extract_url(
            params, "menu_note", ("TicketID", "OTRSAgentInterface"))
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
            self.send_multiprat(cfg, inputs)

    def menu_owner(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        params = [("Action", "AgentTicketOwner")]
        url = self.extract_url(
            params, "menu_note", ("TicketID", "OTRSAgentInterface"))
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
            ("ArticleTypeID", _("Type of note:")),
            ("NewStateID", _("Next state:")), ("Month", _("Month:")),
            ("Day", _("Day:")), ("Year", _("Year:")),
            ("Hour", _("Hour:")), ("Minute", _("Minute:"))))
        if cfg["OK button"] and cfg.get("NewOwnerID"):
            if not cfg["Body"]:
                cfg["Body"] = "Owner was changed using OTRS_US %s" % version
            self.send_multiprat(cfg, inputs)

    def menu_close(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        params = [("Action", "AgentTicketClose")]
        url = self.extract_url(
            params, "menu_close", ("TicketID",))
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
                cfg["Body"] = "Closed using OTRS_US %s" % version
            self.send_multiprat(cfg, inputs)

    def menu_info(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        res = []
        for item in self.ticket_info:
            if isinstance(item, str):
                res.append(item.strip() + "\n")
            else:
                res.append("%s\t%s\n" % tuple(i.strip() for i in item[:2]))
        AboutBox(self, title=_("Ticket Info"), text="".join(res))

    def menu_forward(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        if EDITABLE in self.tree_data or not self.answers:
            return
        params = [("Action", "AgentTicketForward")]
        url = self.extract_url(params, "menu_note", (
            "TicketID", "ArticleID"))
        pg = AnswerPage(self.app_widgets["core"])
        inputs, error = pg.load(url)
        if not inputs:
            showerror(_("Forward"), error)
            return
        cfg = dict(inputs)
        txt = cfg.get("Body", "")
        ca = {EDITABLE: True, "article text": (), "inputs": inputs,
              "snapshot": txt}
        self.articles_range.append(EDITABLE)
        self.tree.insert("", "end", EDITABLE, text=_("Edit"))
        self.tree_data[EDITABLE] = ca
        self.enter_article(EDITABLE)
        self.tree.focus(EDITABLE)

    def menu_reload(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        if self.ticket_id:
            self.load_ticket(self.ticket_id, True)

    def menu_goto_url(self, evt=None):
        cfg = {"url": ""}
        DlgDetails(self, _("Go to ticket"),
                   cfg=cfg, inputs=(("url", _("URL:")),))
        if cfg["OK button"]:
            url = cfg["url"]
            if self.my_url is not None:
                m = re.search(r"TicketID=(\d+)", url)
                url = re.sub(r"TicketID=(\d+)", m.group(0), self.my_url)
            self.load_ticket(url)

    def menu_copy_url(self, evt=None):
        self.text.clipboard_clear()
        self.text.clipboard_append(re.sub(
            '(;OTRSAgentInterface=[0-9a-f]+)*', '', self.my_url))

    def menu_send(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select() or \
           self.tree.focus() != EDITABLE:
            return
        inputs = self.tree_data[EDITABLE]["inputs"]
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
                email = email[email.find("<") + 1:email.find(">")]
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
            try:
                pg.send(url, form)
            except LoginError:
                showerror(_("Send"), _("The ticket was logged off"))
                return
            self.app_widgets["menu_ticket"].entryconfig(
                _("Send message"), state="disabled")
            self.tree.delete(EDITABLE)
            self.tree_data.pop(EDITABLE)
            self.articles_range.pop(self.articles_range.index(EDITABLE))
            self.tree.focus(item=self.articles_range[-1])
            self.menu_reload()

    def extract_url(self, params, where, keys):
        self.actions_params["ArticleID"] = self.tree.focus()
        for i in keys:
            try:
                params.append((i, self.actions_params[i]))
            except KeyError as err:
                self.echo("In %s KeyError: %s" % (where, err))
        return urlunsplit(self.url_begin + (urlencode(params), ""))

    def menu_new_email(self, evt=None):
        self.my_url = None
        self.app_widgets["menu_ticket"].entryconfig(
            _("Send message"), state="normal")
        self.set_menu_active()
        if EDITABLE in self.tree_data:
            return
        params = [("Action", "AgentTicketEmail")]
        url = self.extract_url(
            params, "menu_new_email", ("OTRSAgentInterface",))
        pg = AnswerPage(self.app_widgets["core"])
        inputs, error = pg.load(url)
        if not inputs:
            showerror(_("New email"), error)
            return
        self.tree_data.clear()
        for i in reversed(self.articles_range):
            self.tree.delete(i)
        self.articles_range = [EDITABLE]
        cfg = dict(inputs)
        txt = cfg.get("Body", "")
        ca = {EDITABLE: True, "article text": (), "inputs": inputs,
              "snapshot": txt}
        self.tree.insert("", "end", EDITABLE, text=_("Edit"))
        self.tree_data[EDITABLE] = ca
        self.enter_article(EDITABLE)
        self.tree.focus(EDITABLE)
        self.echo('New email ticket')

    def menu_new_phone(self, evt=None):
        self.echo('New phone ticket')

    def menu_ticket_merge(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        params = [("Action", "AgentTicketMerge")]
        url = self.extract_url(
            params, "ticket_merge", ("TicketID", "OTRSAgentInterface"))
        pg = AnswerPage(self.app_widgets["core"])
        inputs, error = pg.load(url)
        cfg = dict(inputs)
        DlgDetails(self, _("Merge"), cfg=cfg, inputs=(
            ("MainTicketNumber", _("Ticket number:")),
            ("InformSender", _("Inform user")), ("To", _("To:")),
            ("Subject", _("Subject:")), ("Body", _("Message:"))), selects=(
            ("ArticleTypeID", _("Type of note:")),
            ("NewStateID", _("Next state:")), ("Month", _("Month:")),
            ("Day", _("Day:")), ("Year", _("Year:")),
            ("Hour", _("Hour:")), ("Minute", _("Minute:"))))
        if cfg["OK button"]:
            self.send_multiprat(cfg, inputs)

    def send_multiprat(self, cfg, inputs):
        pg = AnswerSender(self.app_widgets["core"])
        url = urlunsplit(self.url_begin + ("", ""))
        pg.send(url, [(i[0], cfg.get(i[0], ("", b""))) for i in inputs])
        self.menu_reload()

    def menu_download(self, evt=None):
        cfg = {"URL": "", "path": self.core_cfg.get("dld_fldr", "")}
        DlgDetails(self, _("Download"), cfg=cfg, inputs=(
            ("URL", _("Address:")), ("path", _("Path:"))))
        if cfg["OK button"]:
            fl = FileLoader(self.app_widgets["core"])
            fl.set_save_path(cfg["path"])
            url = cfg["URL"]
            if url.startswith("/"):
                m = re.search(r"^https?://[^/]+", self.runt_cfg["site"])
                url = m.group(0) + url
            fl.load(url)
