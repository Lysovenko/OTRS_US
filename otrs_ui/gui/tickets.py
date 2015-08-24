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
from ..core.pgload import TicketsPage, MessagePage, AnswerPage, AnswerSender
from .dialogs import AboutBox, DlgDropBox


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
        frame.bind_all("<Control-Escape>", self.go_dasboard)
        frame.bind_all("<Control-i>", self.menu_info)
        frame.bind_all("<Control-r>", self.menu_reload)
        frame.bind_all("<Control-l>", self.menu_lock)
        frame.bind_all("<Control-m>", self.menu_move)
        frame.bind_all("<Control-a>", self.menu_answer)
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
                    font="Times 14")
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
        pg = TicketsPage(self.app_widgets["core"])
        lres = None
        while True:
            try:
                lres = pg.load(url)
                self.echo(lres["articles"])
                self.fill_tree(lres["articles"])
                break
            except RuntimeError:
                if self.app_widgets["dashboard"].login(pg):
                    continue
                lres = None
                break
            except ConnectionError:
                try:
                    self.echo("Login in Tickets.load_ticket")
                    pg.login(self.runt_cfg)
                except (RuntimeError, KeyError):
                    self.go_dasboard(None)
                    lres = None
        self.get_tickets_page(lres)
        self.set_menu_active()

    def get_tickets_page(self, page):
        if page is None:
            return
        if "info" in page:
            self.ticket_info = page["info"]
        try:
            mail_header = page["mail_header"]
            mail_text = page["message_text"]
        except KeyError:
            pass
        self.detect_allowed_actions(page.get("action_hrefs", []) +
                                    page.get("art_act_hrefs", []))
        try:
            self.queues = page["queues"]
            self.queues.pop("0")
        except KeyError:
            pass
        try:
            self.answers = page["answers"]
            self.answers.pop(0)
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
        self.show_email(mail_header, mail_text)
        self.cur_article["article text"] = mail_text
        self.cur_article["article header"] = mail_header

    def show_email(self, header, message):
        text = self.text
        text["state"] = "normal"
        text.delete("1.0", "end")
        for i in header:
            text.insert("end", "%s\t%s\n" % i)
        text.insert("end", "\n")
        for i in message:
            text.insert("end", i)
        text["state"] = "disabled"

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
        if allowed["AgentTicketLock"]:
            econ(_("Lock"), state="normal")
        else:
            econ(_("Lock"), state="disabled")
        # sometimes rises KeyError: 'ArticleID'
        self.cur_article = self.tree_data[total["ArticleID"]]
        self.tree.focus(item=total["ArticleID"])

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
        iid = evt.widget.focus()
        if iid:
            self.cur_article = ca = self.tree_data[iid]
            if "article text" in ca:
                self.show_email(ca["article header"], ca["article text"])
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
        for i in ("TicketID", "ChallengeToken", "Session"):
            params.append((i, self.actions_params[i]))
        url = urlunsplit(self.url_begin + (urlencode(params), ""))
        self.echo("######## url=", url)
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
        self.echo("######## Lock the ticket ;-),", subact)

    def menu_move(self, evt=None):
        if not self.queues:
            return
        selections = []
        for i in sorted(self.queues):
            if i != "-":
                selections.append(self.queues[i])
        tv = StringVar()
        tv.set(self.queues["-"])
        cfg = {"values": selections,
               "textvariable": tv, "state": "readonly"}
        DlgDropBox(self, title=_("Change queue"), cfg=cfg)
        if cfg["OK button"]:
            rv = tv.get()
            for i, v in self.queues.items():
                if v == rv:
                    break
            params = [
                ("Action", "AgentTicketMove"), ("QueueID", ""),
                ("DestQueueID", i)]
            for i in ("TicketID", "ChallengeToken", "Session"):
                params.append((i, self.actions_params[i]))
            url = urlunsplit(self.url_begin + ("", ""))
            pg = TicketsPage(self.app_widgets["core"])
            try:
                lres = pg.load(url, urlencode(params).encode())
                self.get_tickets_page(lres)
            except RuntimeError:
                pass

    def menu_answer(self, evt=None):
        if not self.answers:
            return
        selections = [i[1] for i in self.answers]
        tv = StringVar()
        cfg = {"values": selections,
               "textvariable": tv, "state": "readonly"}
        DlgDropBox(self, title=_("Answer type"), cfg=cfg)
        if cfg["OK button"]:
            ans = tv.get()
            for k, v in self.answers:
                if v == ans:
                    ans = k
                    break
            params = [("Action", "AgentTicketCompose"),
                      ("ReplyAll", ""), ("ResponseID", ans)]
            i = "ArticleID"
            self.actions_params[i] = self.cur_article["article info"][i]
            for i in ("Session", "TicketID", "ArticleID", "ChallengeToken"):
                params.append((i, self.actions_params[i]))
            url = urlunsplit(self.url_begin + (urlencode(params), ""))
            pg = AnswerPage(self.app_widgets["core"])
            inputs = pg.load(url)
            for i in inputs:
                self.echo(*i)
            pg = AnswerSender(self.app_widgets["core"])
            url = urlunsplit(self.url_begin + ("", ""))
            try:
                pg.send(url, [i[1:] for i in inputs if None not in i])
            except RuntimeError as err:
                self.echo("login failed {0}".format(err))
            self.echo("Answer the ticket ;-)")

    def menu_note(self):
        self.echo("Note the ticket ;-)")

    def menu_owner(self):
        self.echo("Change the ticket's owner ;-)")

    def menu_close(self):
        self.echo("Close the ticket ;-)")

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

    def menu_forward(self):
        self.echo("Forward the ticket ;-)")

    def menu_reload(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        if self.my_url:
            self.load_ticket(self.my_url)
