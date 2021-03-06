#!/usr/bin/env python3
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


from argparse import ArgumentParser
parser = ArgumentParser(description="OTRS US")
from sys import argv
faces = "tk", "t", "curses", "c"
face = argv[1].lower() if len(argv) > 1 and argv[1].lower() in faces else None
if face in ("tk", "t", None):
    try:
        from otrs_us.tk import start_gui
        start_gui()
        exit()
    except (ImportError, RuntimeError):
        pass
if face in ("curses", "c", None):
    try:
        from otrs_us.curses import start_cue
        start_cue()
        exit()
    except ImportError:
        pass
