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
"interactor"
from .settings import Config


class Interactor(dict):
    def register(self, name, function, data=None):
        if name in self:
            raise KeyError("function `%s' already registred")
        self[name] = (function, data)

    def call(self, name, *args, **dargs):
        func, data = self[name]
        if data is None:
            return func(*args, **dargs)
        else:
            return func(data, *args, **dargs)

    def echo(self, *args, **dargs):
        try:
            if self["core cfg"][1].get("echo"):
                print(*args, **dargs)
        except Exception:
            return


def get_core():
    actor = Interactor()
    actor.register("core cfg", lambda x: x, Config("core.cfg"))
    actor.register("runtime cfg", lambda x: x, dict())
    return actor
