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
"Provide database operations"

import atexit
from os import makedirs, name
from os.path import isdir, expanduser, join
import sqlite3 as sql
ART_SEEN = 1 << 8
ART_TEXT = 1 << 5
ART_TYPE_MASK = 0xf


class Database:
    "Sqlite3 database class"
    def __init__(self, filename, autoclose=True):
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
            return
        tables = {
            "tickets": "id INT, number INT, mtime INT, flags INT, "
            "title VARCHAR, info TEXT",
            "articles": "id INT, ticket INT, ctime INT, title VARCHAR, "
            "sender VARCHAR, reciever VARCHAR, flags INT, message TEXT"}
        for table in tables:
            self.execute("CREATE TABLE IF NOT EXISTS %s (%s)" % (
                table, tables[table]))
        if autoclose:
            atexit.register(self.close)

    def __bool__(self):
        return self.connection is not None

    def execute(self, command, commit=True):
        cursor = self.connection.cursor()
        cursor.execute(command)
        if commit:
            self.connection.commit()
        return cursor.fetchall()

    def update_ticket(
            self, id, number=None, mtime=None, flags=None, title=None,
            info=None):
        tcts = self.execute("SELECT number, mtime, flags, title, info "
                            "FROM tickets WHERE id=%d" % id, False)
        if tcts:
            updict = {}
            dnum, dmtime, dflags, dtitle, dinfo = tcts[0]
            for i, j, k in ((number, dnum, "number"), (mtime, dmtime, "mtime"),
                            (flags, dflags, "flags"), (title, dtitle, "title"),
                            (info, dinfo, "info")):
                if i is not None and i != j:
                    updict[k] = repr(j)
            if updict:
                upstr = ", ".join("%s=%s" % (i, updict[i]) for i in updict)
                self.execute("UPDATE tickets SET %s "
                             "WHERE id=%d" % (upstr, id))
            return dmtime < mtime
        instup = tuple(j if i is None else repr(i) for i, j in (
            (id, id), (number, '0'), (mtime, '0'), (flags, '0'),
            (title, "'No subj'"), (info, "'None'")))
        self.execute("INSERT INTO tickets "
                     "VALUES(%s, %s, %s, %s, %s, %s)" % instup)
        return True

    def ticket_fields(self, id, *fields):
        rval = self.execute("SELECT %s FROM tickets WHERE id=%d" %
                            (", ".join(fields), id), False)
        if rval:
            return rval[0]

    def article_description(self, id, ticket=None, ctime=None,
                            title=None, sender=None, flags=None):
        arts = self.execute("SELECT ticket, ctime, title, seder, flags "
                            "FROM articles WHERE id=%d" % id)
        if arts:
            dticket, dctime, dtitle, dsender, dflags = arts[0]
            updates = {}
            if ticket is not None and ticket != dticket:
                dticket = ticket
                updates["ticket"] = dticket
            if flags is not None and flags & ART_SEEN:
                dflags |= ART_SEEN
                updates["flags"] = dflags
            if updates:
                us = ", ".join("%s=%s" % i for i in updates.items())
                self.execute("UPDATE articles SET %s WHERE id=%d" % (us, id))
            return dticket, dctime, dtitle, dsender, dflags
        if any(i is None for i in (ticket, ctime, title, sender, flags)):
            return
        self.execute(
            "INSERT INTO articles "
            "VALUES(%d, %d, %d, '%s', '%s', '', %d, '')" % (
                id, ticket, ctime, title, sender, flags))
        return ticket, ctime, title, sender, flags

    def articles_description(self, ticket):
        rval = self.execute("SELECT id, ticket, ctime, title, seder, flags "
                            "FROM articles WHERE ticket=%d" % ticket, False)
        if rval:
            return rval
        return ()

    def article_message(self, id, message=None):
        if message is None:
            arts = self.execute("SELECT message FROM articles "
                                "WHERE id=%d" % id)
            if arts is None:
                return
            return arts[0][0]
        self.execute("UPDATE articles SET message=%s, flags=flags | %d "
                     "WHERE id=%d" % (repr(message), ART_TEXT, id))

    def close(self):
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, tp, val, tb):
        self.close()
