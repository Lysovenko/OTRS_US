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
import sqlite3 as sql


class Database:
    "Sqlite3 database class"
    def __init__(self, pth_to_db):
        self.connection = None
        try:
            self.connection = sql.connect(pth_to_db)
        except sql.Error, e:
            pass

    def __bool__(self):
        return self.connection is not None
