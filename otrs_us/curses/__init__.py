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

from curses import (
    wrapper, ALL_MOUSE_EVENTS, KEY_MOUSE, mousemask, getmouse, echo, A_BOLD,
    newwin, doupdate, def_prog_mode, endwin, reset_prog_mode)
from curses.panel import new_panel, update_panels
from curses.textpad import Textbox, rectangle


def main(scr):
    h, w = scr.getmaxyx()
    hghts = [h // 3 + (1 if 3 - h % 3 <= i else 0) for i in range(3)]
    pr = 0
    wins = []
    for i in hghts:
        wins.append(newwin(i, w, pr, 0))
        pr += i
    for i in range(3):
        wins[i].box(0, 0)
    panels = [new_panel(i) for i in wins]
    update_panels()
    doupdate()
    x = 0
    while x != ord('q'):
        x = scr.getch()
        wn = wins[0]
        wn.addstr(1, 1, "%x" % x)
        wn.addstr(2, 1, repr([
            i for i in dir(wn) if not i.startswith('__')])[:w-3])
        def_prog_mode()
        endwin()
        print(dir(wn))
        reset_prog_mode()
        wins[0].refresh()


def start_cue():
    wrapper(main)
