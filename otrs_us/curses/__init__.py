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

from curses import wrapper, ALL_MOUSE_EVENTS, KEY_MOUSE, mousemask, getmouse
from curses.textpad import Textbox, rectangle


def get_param(prompt_string, screen):
    screen.clear()
    screen.border(0)
    screen.addstr(2, 2, prompt_string)
    screen.refresh()
    istr = screen.getstr(10, 10, 60)
    return str(istr)


def execute_cmd(cmd_string):
    # system("clear")
    a = 0
    print("")
    if a == 0:
        print("Command executed correctly")
    else:
        print("Command terminated with error")
    # input("Press enter")
    print("")


def main(scr):
    x = 0
    while x != ord('4'):
#        scr = curses.initscr()
        scr.clear()
        scr.border(0)
        scr.addstr(2, 2, "Please enter a number...")
        scr.addstr(4, 4, "1 - Add a user")
        scr.addstr(5, 4, "2 - Restart Apache")
        scr.addstr(6, 4, "3 - Show disk space")
        scr.addstr(7, 4, "4 - Exit")
        scr.refresh()
        x = scr.getch()
        if x == ord('1'):
            username = get_param("Enter the username", scr)
            homedir = get_param("Enter the home directory, eg /home/nate", scr)
            groups = get_param(
                "Enter comma-separated groups, eg adm,dialout,cdrom", scr)
            shell = get_param("Enter the shell, eg /bin/bash:", scr)
            # curses.endwin()
            execute_cmd("useradd -d " + homedir + " -g 1000 -G " + groups +
                        " -m -s " + shell + " " + username)
        if x == ord('2'):
            # curses.endwin()
            execute_cmd("df")
        if x == ord('3'):
            # curses.endwin()
            execute_cmd("df -h")


def start_cue():
    wrapper(main)
