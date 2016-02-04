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
        results = self.__db.execute(
            "SELECT id, number, title, mtime FROM tickets WHERE id IN "
            "(SELECT DISTINCT ticket FROM articles WHERE message LIKE "
            "'%s')" % query, False)
        if not results:
            return
        result = []
        for i, num, tit, mt in results:
            result.append(
                {"number": num, "TicketID": i, "title": tit, "Changed": mt})
        return result

    search = db_search
