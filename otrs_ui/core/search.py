#!/usr/bin/env python3
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
"Searcher"
import re
from .ptime import TimeUnit, unix_time
from .pgload import QuerySender
from time import time


class Searcher:
    def __init__(self, core):
        self.__db = core.call("database")
        self.__core = core
        self.regexp = ""

    def db_search(self, query):
        if ":" in query:
            return self.db_by_time(query)
        if query.startswith(">"):
            return self.external_db_query(query[1:])
        return self.db_keywords(query)

    def db_by_time(self, query):
        try:
            totime, trange = query.split(":")
            t = time()
            st, en = [t - TimeUnit(i) for i in trange.split('-')]
        except ValueError:
            return ()
        totime = totime.strip()
        if totime not in ("mtime", "", "relevance"):
            return ()
        if not totime:
            totime = "relevance"
        result = []
        if st > en:
            st, en = en, st
        for tid, num, tit, mt in self.__db.execute(
                "SELECT id, number, title, mtime FROM tickets "
                "WHERE %s BETWEEN %d AND %d" % (
                    totime, st, en)):
            result.append({
                "number": num, "TicketID": tid, "title": tit,
                "mtime": mt, "articles": ()})
        return result

    def db_keywords(self, query):
        sql = self.__db.execute
        result = []
        sre = "%".join(query.replace("'", "''").split())
        self.regexp = pre = "\\W+".join(query.split())
        sql("CREATE TEMPORARY TABLE artsfound (id INT, ticket INT, msg TEXT)")
        sql("INSERT INTO artsfound SELECT id, ticket, message AS msg "
            "FROM articles WHERE message LIKE '%%%s%%'" % sre)
        for aid, in sql("SELECT id FROM artsfound", False):
            msg = sql("select msg from artsfound where id=%d" % aid)[0][0]
            m = re.search(pre, msg, re.I)
            if m is None:
                sql("DELETE FROM artsfound where id=%d" % aid)
        for tid, in sql("SELECT DISTINCT ticket FROM artsfound", False):
            arts = sql("SELECT id FROM artsfound WHERE ticket=%d" % tid, False)
            arts = set(list(zip(*arts))[0])
            num, tit, mt = sql(
                "SELECT number, title, mtime FROM tickets "
                "WHERE id=%d" % tid, False)[0]
            result.append({
                "number": num, "TicketID": tid, "title": tit,
                "mtime": mt, "articles": arts})
        sql("DROP TABLE artsfound")
        return result

    def external_db_query(self, query):
        result = []
        sre = "%".join(query.replace("'", "''").split())
        qs = QuerySender(self.__core)
        for tn, tid, title, mt in qs.send(
                "SELECT t.tn, t.id, t.title, t.change_time FROM ticket AS t "
                "WHERE t.title LIKE '%%%s%%' ORDER BY t.change_time DESC"
                % sre, 100)[1:]:
            print(tn, tid, title, mt)
            result.append({
                "number": int(tn), "TicketID": int(tid), "title": title,
                "mtime": unix_time(mt, "%Y-%m-%d %H:%M:%S"), "articles": ()})
        return result

    search = db_search
