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
"Thread for dashboard's update"
from threading import Thread, Lock
from urllib.error import URLError
from .pgload import DashboardPage, LoginError


class DashboardUpdater:
    def __init__(self, core):
        self.__st_lock = Lock()
        self.__status = "Ready"
        self.__result = None
        self.__page = DashboardPage(core)

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
        t = Thread(target=self.__loader)
        t.daemon = True
        t.start()

    def __loader(self):
        try:
            pgl = self.__page.load(self.__site)
        except LoginError:
            self.__set_status("LoginError")
            return
        except URLError as err:
            self.__result = err
            self.__set_status("URLError")
            return
        self.__result = pgl
        if pgl is None:
            self.__set_status("Empty")
        else:
            self.__set_status("Complete")

    def get_result(self):
        if self.get_status() in ("Complete", "URLError"):
            self.__set_status = "Ready"
            return self.__result

    def login(self, who):
        self.__who = who
        self.__status = "Wait"
        t = Thread(target=self.__login)
        t.daemon = True
        t.start()

    def __login(self):
        try:
            self.__page.login(self.__who)
        except LoginError:
            self.__set_status("LoginError")
            return
        except URLError as err:
            self.__result = err
            self.__set_status("URLError")
            return
        self.__site = self.__who.get("site", "")
        self.__loader()
