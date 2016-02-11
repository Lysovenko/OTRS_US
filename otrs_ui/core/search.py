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
"Search request sender"


class Searcher:
    def __init__(self, core):
        self.__db = core.call("database")

    def db_search(self, query):
        sql = self.__db.execute
        result = []
        sql("CREATE TEMPORARY TABLE artsfound (id INT, ticket INT)")
        sql("INSERT INTO artsfound SELECT id, ticket FROM articles "
            "WHERE message LIKE '%%%s%%'" %
            '%'.join(query.replace("'", "''").split()))
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

    search = db_search
