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
try:
    from Crypto.Cipher import AES
except ImportError:
    AES = None
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


class Password:
    def __init__(self, epasswd):
        self.__passphrased = epasswd.startswith("*")
        self.__plain = None
        if not self.__passphrased:
            self.__epassword = b64decode(epasswd, b"@$")
            self.__hash = md5(version.encode()).digest()
            ds = self.decrypt_xor(self.__epassword)
            try:
                self.__plain = ds.decode()
            except (UnicodeDecodeError):
                pass
        else:
            self.__epassword = b64decode(epasswd[1:], b"@$")
            self.__hash = None

    def encrypt_xor(self):
        k = list(self.__hash)
        lk = len(k)
        lep = list(self.__plain.encode())
        return bytes(j ^ k[i % lk] for i, j in enumerate(lep))

    def decrypt_xor(self, crypted):
        if self.__hash is None:
            return None
        k = list(self.__hash)
        lk = len(k)
        return bytes(j ^ k[i % lk] for i, j in enumerate(crypted))

    def encrypt_AES(self):
        lep = self.__plain.encode()
        lp = len(lep)
        lep = eval("b'\\x%02x'" % lp) + lep + self.__hash[(lp + 1) % 16:]
        coder = AES.new(self.__hash)
        return coder.encrypt(lep)

    def decrypt_AES(self, crypted):
        coder = AES.new(self.__hash)
        lep = coder.decrypt(crypted)
        lp = lep[0]
        if lp >= len(crypted):
            return None
        if self.__hash.endswith(lep[1 + lp:]):
            return lep[1:1 + lp]
        return None

    def require_passphrse(self):
        return self.__passphrased and self.__plain is None

    def try_passphrase(self, passphrase):
        self.__hash = md5(passphrase.encode()).digest()
        if AES is None:
            ds = self.decrypt_xor(self.__epassword)
        else:
            ds = self.decrypt_AES(self.__epassword)
        try:
            self.__plain = ds.decode()
        except (UnicodeDecodeError, AttributeError):
            self.__plain = None

    def set_passphrase(self, passphrase):
        self.__hash = md5(passphrase.encode()).digest()
        self.__passphrased = True

    def __str__(self):
        if self.__plain:
            return self.__plain
        else:
            return ""

    def __repr__(self):
        if self.__passphrased:
            cryptor = self.encrypt_xor if AES is None else self.encrypt_AES
            return repr("*" + b64encode(cryptor(), b"@$").decode())
        else:
            return repr(b64encode(self.encrypt_xor(), b"@$").decode())

    def clear(self):
        self.__hash = None
        self.__plain = None
        self.__passphrased = None
