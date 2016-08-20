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
"Ticket's text widget"

from tkinter import Text
from os import read, write, pipe, waitpid
import re
from subprocess import Popen
from time import sleep
from idlelib.Delegator import Delegator
from idlelib.ColorDelegator import ColorDelegator
from idlelib.Percolator import Percolator


def make_pat():
    kw = r"(?P<KEYWORD>&.*?;)"
    builtin = r"(?P<BUILTIN><[^!>].*?>)"
    comment = r"(?P<COMMENT><!--.*?-->)"
    return kw + "|" + builtin + "|" + comment


class HtmlColorDelegator(ColorDelegator):

    def __init__(self):
        Delegator.__init__(self)
        self.prog = re.compile(make_pat(), re.S)
        self.idprog = re.compile(r"\s+(\w+)", re.S)
        self.LoadTagDefs()


class TicText(Text):
    def __init__(self, parent, spell=None, **kw):
        Text.__init__(self, parent, wrap="word",
                      font="Times 14", takefocus=True, **kw)
        self.tg_regexp = re.compile("<[^>]*>")
        self.bind("<Control-c>", self.copy)
        self.bind("<Control-x>", self.cut)
        self.bind("<Return>", self.newline)
        self.tag_configure("h1", font="Times 16 bold", relief="raised")
        self.tag_configure("highlight", background="yellow", relief="raised")
        self.tag_configure("html_tag", foreground="blue")
        if spell:
            r, self.wd = pipe()
            self.rd, w = pipe()
            args = spell.split()
            self.sp = Popen(args, stdin=r, stdout=w)

            self.tag_configure("misspelled", foreground="red", underline=True)
            self.bind("<space>", self.Spellcheck)
        self.percolator = Percolator(self)
        self.percolator.insertfilter(HtmlColorDelegator())

    def copy(self, event=None):
        self.clipboard_clear()
        text = self.get("sel.first", "sel.last")
        self.clipboard_append(text)

    def cut(self, event):
        self.copy()
        self.delete("sel.first", "sel.last")

    def Spellcheck(self, event):
        """Spellcheck the word preceeding the insertion point"""
        index = self.search(r"\s", "insert", backwards=True, regexp=True)
        if index == "":
            index = "1.0"
        else:
            index = self.index("%s+1c" % index)
        word = self.get(index, "insert")
        write(self.wd, (word + "\n").encode())
        sleep(.01)
        spell = read(self.rd, 0x0fffffff)
        rm = len([None for i in spell.splitlines()
                  if i[:1] == b"#"])
        if not rm:
            self.tag_remove("misspelled", index, "%s+%dc" % (index, len(word)))
        else:
            self.tag_add("misspelled", index, "%s+%dc" % (index, len(word)))

    def highlight(self, regexp):
        text = self.get("1.0", "end")
        for m in re.finditer(regexp, text, re.I):
            self.tag_add("highlight", "1.0+%dc" % m.start(),
                         "1.0+%dc" % m.end())

    def newline(self, evt):
        self.insert("insert", "<br/>")
