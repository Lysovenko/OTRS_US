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
"Settings"

import atexit
from os import makedirs, name
from os.path import isdir, expanduser, join
from hashlib import md5
from sys import version
from base64 import b64encode, b64decode


class Config(dict):
    def __init__(self, filename):
        if name == 'posix':
            self.path = expanduser("~/.config/otrs_us")
        elif name == 'nt':
            if isdir(expanduser("~/Application Data")):
                self.path = expanduser("~/Application Data/otrs_us")
            else:
                self.path = expanduser("~/otrs_us")
        else:
            self.path = expanduser("~/otrs_us")
        if not isdir(self.path):
            makedirs(self.path)
        self.path = join(self.path, filename)
        cfgl = []
        try:
            with open(self.path) as fp:
                for line in iter(fp.readline, ''):
                    if not line.isspace() and not line.startswith('#'):
                        nam, val = line.strip().split('=', 1)
                        cfgl.append((nam, eval(val)))
        except Exception:
            pass
        dict.__init__(self, cfgl)
        self.hash = md5(repr(self).encode()).digest()
        atexit.register(self.save)

    def save(self):
        if self.hash == md5(repr(self).encode()).digest():
            return
        with open(self.path, 'w') as fp:
            for n, v in self.items():
                fp.write("%s=%s\n" % (n, repr(v)))
        self.hash = md5(repr(self).encode()).digest()


class Password(str):
    def __new__(self, enc_pwd, encoded=True):
        if not encoded:
            return str.__new__(self, enc_pwd)
        try:
            lep = list(b64decode(enc_pwd, b"@$"))
        except ValueError:
            return str.__new__(self, enc_pwd)
        k = list(md5(version.encode()).digest())
        lk = len(k)
        rb = [j ^ k[i % lk] for i, j in enumerate(lep)]
        return str.__new__(self, bytes(rb).decode())

    def __repr__(self):
        k = list(md5(version.encode()).digest())
        lk = len(k)
        lep = list(self.encode())
        rb = [j ^ k[i % lk] for i, j in enumerate(lep)]
        return repr(b64encode(bytes(rb), b"@$").decode())
