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
"Provide database operations"

import atexit
from os import makedirs, name
from os.path import isdir, expanduser, join
import sqlite3 as sql


class Database:
    "Sqlite3 database class"
    def __init__(self, filename):
        if name == 'posix':
            path = expanduser("~/.config/otrs_us")
        elif name == 'nt':
            if isdir(expanduser("~/Application Data")):
                path = expanduser("~/Application Data/otrs_us")
            else:
                path = expanduser("~/otrs_us")
        else:
            path = expanduser("~/otrs_us")
        if not isdir(path):
            makedirs(path)
        path = join(path, filename)
        self.connection = None
        try:
            self.connection = sql.connect(path)
        except sql.Error as e:
            pass
        atexit.register(self.close)

    def __bool__(self):
        return self.connection is not None

    def close(self):
        if self.connection.close()
