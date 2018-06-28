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
from sqlite3 import connect, Error, sqlite_version_info
from time import time
ART_SEEN = 1 << 8
ART_TEXT = 1 << 5
ART_TYPE_MASK = 0xf
TIC_SEEN = 1 << 8
TIC_UPD = 1
# TODO: escape more accurately sql datatypes


def sql_repr(x):
    if x is None:
        return "NULL"
    return repr(x).replace("\\'", "''").replace("\\\\", "\\")


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
            self.connection = connect(path)
        except Error as e:
            return
        tables = {
            "tickets": "id INT, number INT, mtime INT, flags INT, "
            "title VARCHAR, allow INT, info TEXT, relevance INT",
            "articles": "id INT, ticket INT, ctime INT, title VARCHAR, "
            "sender VARCHAR, reciever VARCHAR, flags INT, message TEXT",
            "allows": "id INT, value VARCHAR"}
        for table in tables:
            self.execute("CREATE TABLE IF NOT EXISTS %s (%s)" % (
                table, tables[table]))
        if autoclose:
            atexit.register(self.close)

    def __bool__(self):
        return self.connection is not None

    def execute(self, command, commit=True):
        cursor = self.connection.cursor()
        try:
            cursor.execute(command)
        except Error:
            raise Error(command)
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
            if flags is None and mtime is not None and dmtime < mtime:
                flags = dflags & (~TIC_UPD)
            for i, j, k in ((number, dnum, "number"), (mtime, dmtime, "mtime"),
                            (flags, dflags, "flags"), (title, dtitle, "title"),
                            (info, dinfo, "info"),
                            (int(time()), 0, "relevance")):
                if i is not None and i != j:
                    updict[k] = sql_repr(i)
            if updict:
                upstr = ", ".join("%s=%s" % (i, updict[i]) for i in updict)
                self.execute("UPDATE tickets SET %s "
                             "WHERE id=%d" % (upstr, id))
            return None if mtime is None else dmtime < mtime
        instup = tuple(j if i is None else sql_repr(i) for i, j in (
            (id, id), (number, '0'), (mtime, '0'), (flags, '0'),
            (title, "'No subj'"), (-1, 0), (info, "'()'"), (int(time()), 0)))
        self.execute("INSERT INTO tickets "
                     "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)" % instup)
        return True

    def update_tickets(self, updlist):
        sql = self.execute
        sql("CREATE TEMPORARY TABLE IF NOT EXISTS "
            "tmp_tickets(id INT, number INT, mtime INT, title VARCHAR)", False)
        if sqlite_version_info >= (3, 7, 11):
            rearr = ",".join(
                "(%s)" % ",".join(map(sql_repr, i)) for i in updlist)
            sql("INSERT INTO tmp_tickets VALUES %s" % rearr, False)
        else:
            for s in updlist:
                sql("INSERT INTO tmp_tickets VALUES (%s)" %
                    ",".join(map(sql_repr, s)), False)
        updated = sql("SELECT t.id FROM tmp_tickets AS t LEFT JOIN tickets"
                      " AS o ON t.id = o.id "
                      "WHERE t.mtime > o.mtime OR o.mtime IS NULL", False)
        sql("CREATE TEMPORARY TABLE IF NOT EXISTS "
            "upd_tickets (id INT, number INT, mtime INT, flags INT, "
            "title VARCHAR, allow INT, info TEXT, relevance INT)", False)
        sql("INSERT INTO upd_tickets SELECT t.id, t.number, t.mtime, CASE WHEN"
            " o.flags IS NULL THEN 0 WHEN o.mtime < t.mtime THEN o.flags & ~%d"
            " ELSE o.flags END, t.title, o.allow, o.info, %d FROM tmp_tickets "
            "AS t LEFT JOIN tickets AS o ON t.id = o.id "
            % (TIC_UPD, int(time())), False)
        sql("DROP TABLE tmp_tickets", False)
        sql("DELETE FROM tickets WHERE id in (SELECT id FROM upd_tickets)",
            False)
        sql("INSERT INTO tickets SELECT * FROM upd_tickets", False)
        sql("DROP TABLE upd_tickets")
        return [i for i, in updated]

    def ticket_fields(self, id, *fields):
        rval = self.execute("SELECT %s FROM tickets WHERE id=%d" %
                            (", ".join(fields), id), False)
        if rval:
            return rval[0]

    def ticket_allows(self, id, allows=None):
        if allows is None:
            rv = self.execute(
                "SELECT value FROM allows WHERE id IN "
                "(SELECT allow FROM tickets WHERE id=%d)" % id, False)
            if rv:
                return rv[0][0]
            return
        rv = self.execute("SELECT id FROM allows WHERE value=%s" %
                          sql_repr(allows), False)
        if rv:
            rv = rv[0][0]
        else:
            rv = self.execute("SELECT COUNT() FROM allows", False)
            rv = rv[0][0]
            self.execute("INSERT INTO allows "
                         "VALUES(%d, %s)" % (rv, sql_repr(allows)))
        self.execute("UPDATE tickets SET allow=%d WHERE id=%d" % (rv, id))
        return rv

    def article_description(self, id, ticket=None, ctime=None,
                            title=None, sender=None, flags=None):
        arts = self.execute("SELECT ticket, ctime, title, sender, flags "
                            "FROM articles WHERE id=%d" % id)
        if arts:
            dticket, dctime, dtitle, dsender, dflags = arts[0]
            updates = {}
            if ticket is not None and ticket != dticket:
                dticket = ticket
                updates["ticket"] = dticket
            if flags is not None and (flags & ART_SEEN) > (dflags & ART_SEEN):
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
            "VALUES(%d, %d, %d, %s, %s, '', %d, '')" % (
                id, ticket, ctime, sql_repr(title), sql_repr(sender), flags))
        return ticket, ctime, title, sender, flags

    def articles_description(self, ticket):
        rval = self.execute("SELECT id, ticket, ctime, title, sender, flags "
                            "FROM articles WHERE ticket=%d" % ticket, False)
        if rval:
            return rval
        return ()

    def article_message(self, id, message=None):
        if message is None:
            arts = self.execute("SELECT message FROM articles "
                                "WHERE id = %d" % id)
            if not arts:
                return
            return arts[0][0]
        self.execute("UPDATE articles SET message = %s, flags = flags | %d "
                     "WHERE id = %d" % (sql_repr(message), ART_TEXT, id))

    def close(self):
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, tp, val, tb):
        self.close()

    def delete_irrelevant(self, still_relevant):
        min_relevance = int(time() - still_relevant)
        self.execute(
            "DELETE FROM articles WHERE ticket in (SELECT id FROM tickets "
            "WHERE relevance < %d)" % min_relevance)
        self.execute("DELETE FROM tickets WHERE relevance<%d" % min_relevance)
