#!/usr/bin/env python3
# Copyright 2015-2016 Serhiy Lysovenko
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
"Thread for dashboard's update"
from traceback import print_exc
from threading import Thread, Lock, active_count
from urllib.error import URLError
from urllib.parse import urlsplit, parse_qs
from .pgload import DashboardPage, LoginError
from .ptime import dashb_time


class DashboardUpdater:
    def __init__(self, core):
        self.__st_lock = Lock()
        self.__status = "Ready"
        self.__result = None
        self.__page = DashboardPage(core)
        self.__db = core.call("database")
        rtm = core.call("runtime cfg")
        rtm["changed tickets"] = self.ts_changed = \
            rtm.get("changed tickets", set())

    def get_status(self):
        self.__st_lock.acquire()
        status = self.__status
        self.__st_lock.release()
        return status

    def __set_status(self, status):
        self.__st_lock.acquire()
        self.__status = status
        self.__st_lock.release()

    def start_loader(self, site):
        self.__site = site
        self.__set_status("Wait")
        self.__result = None
        t = Thread(target=self.__thr_loader)
        t.daemon = True
        t.start()

    def __thr_loader(self):
        try:
            if self.__site is None:
                pgl = self.__page.login(self.__who)
            else:
                pgl = self.__page.load(self.__site)
        except LoginError:
            self.__set_status("LoginError")
            return
        except URLError as err:
            self.__result = err
            self.__set_status("URLError")
            return
        except Exception as err:
            self.__result = "%s: %s" % (str(type(err)), str(err))
            print_exc()
            self.__set_status("URLError")
            return
        self.__result = pgl
        if pgl is None:
            self.__set_status("Empty")
        else:
            self.__set_status("Complete")

    def get_result(self):
        if self.get_status() != "Wait":
            self.__set_status("Ready")
            result = self.__result
            self.__result = None
            if not isinstance(result, dict):
                return result
            pgl = result
            result = {}
            summary = {"Important": 0}
            for name in ("Reminder", "New", "Open"):
                summary[name] = False
                tarr = []
                for item in pgl[name]:
                    tid, = parse_qs(urlsplit(item["href"]).query)["TicketID"]
                    if self.__db.update_ticket(
                            int(tid), int(item["number"]), dashb_time(item),
                            title=item["title"]):
                        self.ts_changed.add(int(tid))
                        summary[name] = True
                        if item["marker"] & 2:
                            summary["Important"] += 1
                        item["marker"] |= 4
                    ritem = dict(item)
                    ritem["TicketID"] = int(tid)
                    tarr.append(ritem)
                result[name] = tarr
            return result, summary

    def login(self, who):
        self.__who = who
        self.__site = None
        self.__set_status("Wait")
        t = Thread(target=self.__thr_loader)
        t.daemon = True
        t.start()

    def get_info(self):
        return "currently %d threads" % active_count()
