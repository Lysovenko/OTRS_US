# Copyright 2016 Serhiy Lysovenko
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
"Ticket's callbacks"
EDITABLE = -1
from .dialogs import AboutBox, DlgDetails
from tkinter.messagebox import showerror, showinfo
from time import ctime
from traceback import format_exc
import os
from ..core import version
from ..core.msg_ldr import MessageLoader, article_by_url, article_type
from ..core.pgload import LoginError
from ..core.pgload import QuerySender


class Callbacks:
    def __init__(self, appw):
        self.app_widgets = appw
        self.echo = appw["core"].echo
        self.runtime = appw["core"].call("runtime cfg")
        self.core_cfg = appw["core"].call("core cfg")
        self.loader = MessageLoader(appw["core"])
        self.articles_range = []
        self.tree_data = {}
        self.cur_article = -2
        self.my_tab = None
        self.ticket_id = None
        self.ticket_info = None
        self.actions_params = {}
        self.queues = {}
        self.sexpr = None

    def go_dasboard(self, evt):
        self.app_widgets["notebook"].select(0)
        self.app_widgets["dashboard"].tree["New"].focus_set()

    def load_ticket(self, ticket_id, force=False, prefered=None, sexpr=None):
        articles, info, allowed = self.loader.zoom_ticket(ticket_id, force)
        if articles is None:
            showerror(_("Error"), _("Ticket load was failed"))
            return
        self.ticket_id = ticket_id
        self.app_widgets["menu_ticket"].entryconfig(
            _("Send message"), state="disabled")
        self.sexpr = sexpr
        self.__update_tick_face(prefered, articles, info, allowed)

    def __update_tick_face(self, prefered, articles, info, allowed):
        if isinstance(prefered, set):
            self.fill_tree(articles, prefered)
        else:
            self.fill_tree(articles)
        self.ticket_info = info
        self.detect_allowed_actions(allowed)
        self.queues = self.core_cfg.get("queues")
        self.answers = self.core_cfg.get("answers")
        if prefered in self.articles_range:
            show = prefered
        else:
            for show in reversed(self.articles_range):
                if show in prefered if isinstance(prefered, set) else \
                   "system" not in article_type(articles[show]["Flags"]):
                    break
        self.runtime["now editing"] = None
        self.enter_article(show)
        self.tree.focus(show)

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
        if self.sexpr:
            text.highlight(self.sexpr)
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

    def fill_tree(self, articles, selected=()):
        tree = self.tree
        for i in reversed(self.articles_range):
            tree.delete(i)
        self.articles_range = list(articles)
        self.articles_range.sort(key=lambda x: articles[x]["ctime"])
        for art_id in self.articles_range:
            item = articles[art_id]
            item[EDITABLE] = False
            tags = (article_type(item["Flags"]),)
            tags += ("hightlighted",) if art_id in selected else ()
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
            try:
                mail_text = self.loader.zoom_article(ca["TicketID"], iid)
            except Exception:
                showerror(_("Error"), _("Can't download article %d") % iid)
                mail_text = [(format_exc(),)]
            ca.update(((EDITABLE, False), ("article header", ()),
                       ("article text", mail_text)))
            self.show_email(ca)

    def set_menu_active(self, evt):
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
            subact = self.actions_params["AgentTicketLock"]
        except KeyError:
            showerror(title, _("You are late. Sorry."))
            return
        lres = self.loader.lock_ticket(self.ticket_id, subact)
        if lres is None:
            showerror(title, _("The operation was failed"))
            return
        if subact == "Lock":
            showinfo(title, _("The ticket was successfully locked"))
        else:
            showinfo(title, _("The ticket was successfully unlocked"))
        self.__update_tick_face(int(self.tree.focus()), *lres)

    def menu_move(self, evt=None):
        if not self.queues or \
           self.my_tab != self.app_widgets["notebook"].select():
            return
        cfg = {"queue": self.queues}
        DlgDetails(self, _("Change queue"), cfg=cfg, selects=(
            ("queue", _("Queue:")),))
        if cfg["OK button"]:
            try:
                rv = self.loader.move_ticket(self.ticket_id, cfg["queue"])
            except KeyError:
                showerror(_("Error"), _("Unexpected error"))
                return
            if rv is None:
                return
        else:
            return
        self.__update_tick_face(int(self.tree.focus()), *rv)

    def menu_answer(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        if EDITABLE in self.tree_data or not self.answers:
            return
        cfg = {"type": self.answers}
        DlgDetails(self, _("Answer type"), cfg=cfg, selects=(
            ("type", _("Answer type:")),))
        if cfg["OK button"]:
            inputs, error = self.loader.load_article_pattern(
                self.ticket_id, self.cur_article, cfg["type"])
            if inputs:
                txt = dict(inputs).get("Body", "")
                ca = {EDITABLE: True, "article text": (), "inputs": inputs,
                      "snapshot": txt}
                self.articles_range.append(EDITABLE)
                self.tree.insert("", "end", EDITABLE, text=_("Edit"))
                self.tree_data[EDITABLE] = ca
                self.enter_article(EDITABLE)
                self.tree.focus(EDITABLE)
                self.runtime["now editing"] = self.ticket_id
            else:
                showerror(_("Answer"), (error if error else "Can't answer"))

    def menu_note(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        inputs, error = self.loader.load_note_pattern(self.ticket_id)
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
            self.loader.send_form(cfg, inputs)

    def menu_owner(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        inputs, error = self.loader.load_owners_pattern(self.ticket_id)
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
            self.loader.send_form(cfg, inputs)

    def menu_customer(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        inputs, error = self.loader.load_customers_pattern(self.ticket_id)
        if not inputs:
            showerror(_("Change owner"), error)
        cfg = dict(inputs)
        DlgDetails(
            self, _("Customer"), cfg=cfg, focus_on="CustomerID", inputs=(
                ("CustomerUserID", _("Customer:")),
                ("CustomerID", _("Customer ID:"))))
        if cfg["OK button"] and cfg.get("CustomerID"):
            self.loader.send_form(cfg, inputs)

    def menu_close(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select():
            return
        inputs, error = self.loader.load_close_pattern(self.ticket_id)
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
            self.loader.send_form(cfg, inputs)

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
        inputs, error = self.loader.load_forward_pattern(
            self.ticket_id, self.cur_article)
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
        self.runtime["now editing"] = self.ticket_id

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
            ticket_id, prefered = article_by_url(cfg["url"])
            if ticket_id is None:
                showerror(_("Error"), _("Wrong URL"))
                return
            self.load_ticket(ticket_id, True, prefered)

    def menu_copy_url(self, evt=None):
        self.text.clipboard_clear()
        self.text.clipboard_append(
            self.loader.extract_url(self.ticket_id, self.cur_article))

    def menu_send(self, evt=None):
        if self.my_tab != self.app_widgets["notebook"].select() or \
           self.tree.focus() != str(EDITABLE):
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
            # DODO: move form formation logic into core
            cfg["Body"] = self.text.get("1.0", "end")
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
            for i in range(len(inputs)):
                if inputs[i][0] == "CustomerTicketText":
                    pos = i + 1
                    break
            add = (
                ("CustomerInitialValue_1", email), ("CustomerKey_1", ""),
                ("CustomerQueue_1", email), ("CustomerTicketText_1", email))
            cfg.update(add)
            for i in reversed(add):
                inputs.insert(pos, i)
            try:
                self.loader.send_form(cfg, inputs)
            except LoginError:
                showerror(_("Send"), _("The ticket was logged off"))
                return
            self.app_widgets["menu_ticket"].entryconfig(
                _("Send message"), state="disabled")
            self.tree.delete(EDITABLE)
            self.tree_data.pop(EDITABLE)
            self.articles_range.pop(self.articles_range.index(EDITABLE))
            self.runtime["now editing"] = None
            self.tree.focus(item=self.articles_range[-1])
            self.menu_reload()

    def menu_new_email(self, evt=None):
        self.my_url = None
        self.app_widgets["menu_ticket"].entryconfig(
            _("Send message"), state="normal")
        if EDITABLE in self.tree_data:
            return
        inputs, error = self.loader.load_new_mail_pattern()
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
        inputs, error = self.loader.load_merge_pattern(self.ticket_id)
        cfg = dict(inputs)
        self.app_widgets["search"].main_tic_num(cfg)
        DlgDetails(self, _("Merge"), cfg=cfg, inputs=(
            ("MainTicketNumber", _("Ticket number:")),
            ("InformSender", _("Inform user")), ("To", _("To:")),
            ("Subject", _("Subject:")), ("Body", _("Message:"))), selects=(
            ("ArticleTypeID", _("Type of note:")),
            ("NewStateID", _("Next state:")), ("Month", _("Month:")),
            ("Day", _("Day:")), ("Year", _("Year:")),
            ("Hour", _("Hour:")), ("Minute", _("Minute:"))))
        if cfg["OK button"]:
            self.loader.send_form(cfg, inputs)
            self.menu_reload()

    def menu_download(self, evt=None):
        self.download_file("", self.core_cfg.get("dld_fldr", ""))

    def menu_download_eml(self, evt):
        art_id = int(evt.widget.focus())
        if art_id <= 0 or not self.ticket_id:
            return
        url = self.loader.extract_eml_url(self.ticket_id, art_id)
        pth = os.path.join(
            self.core_cfg.get("dld_fldr", ""),
            "Tickest-%d_Article-%d.eml" % (self.ticket_id, art_id))
        self.download_file(url, pth)

    def download_file(self, url, fldr):
        cfg = {"URL": url, "path": fldr}
        DlgDetails(self, _("Download"), cfg=cfg, inputs=(
            ("URL", _("Address:")), ("path", _("Path:"))))
        if cfg["OK button"]:
            self.loader.download_file(cfg["URL"], cfg["path"])

    def dbg_send_request(self, req=None):
        cfg = {"query": "", "items": "40"}
        DlgDetails(self, _("Send SQL request"), cfg=cfg,
                   inputs=(("query", _("QUERY:")), ("items", _("Items:"))))
        if cfg["OK button"]:
            pg = QuerySender(self.app_widgets["core"])
            otab = pg.send(cfg["query"], int(cfg["items"]))
            text = self.text
            text["state"] = "normal"
            text.delete("1.0", "end")
            for i in otab:
                text.insert("end", "\t".join(map(str, i)) + "\n")
            text["state"] = "disabled"
