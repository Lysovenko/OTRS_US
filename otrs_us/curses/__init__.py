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
"Making the cue of the application"

from curses import wrapper, newwin
from curses.textpad import Textbox, rectangle


def main(scr):
    scr.addstr(0, 0, "Enter IM message: (hit q to exit)")
    y, x = scr.getmaxyx()
    ph = "Hello world! %d, %d" % (x, y)
    scr.move(y - 1, x - len(ph))
    for i in reversed(ph):
        scr.insch(i)
    ch = 0
    while chr(ch) != 'q':
        ch = scr.getch()
        scr.addstr(11, 10, repr(ch))
        scr.move(10, 10)
        scr.insch(ch)


def start_cue():
    wrapper(main)
