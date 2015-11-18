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
"Ticket's text widget"

from tkinter import Text


class TicText(Text):
    def __init__(self, parent, **kw):
        Text.__init__(self, parent, wrap="word",
                      font="Times 14", takefocus=True, **kw)
        self.bind("<Control-c>", self.copy)
        self.bind("<Control-x>", self.cut)
        self.tag_configure("h1", font="Times 16 bold", relief="raised")

    def copy(self, event=None):
        self.clipboard_clear()
        text = self.get("sel.first", "sel.last")
        self.clipboard_append(text)

    def cut(self, event):
        self.copy()
        self.delete("sel.first", "sel.last")
