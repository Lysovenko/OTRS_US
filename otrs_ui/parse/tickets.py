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
"parse tickets page"
from html.parser import HTMLParser
from sys import hexversion


SPEC_ENTS = {
    "quot": "\u0022", "apos": "\u0027", "nbsp": "\u00A0", "iexcl": "\u00A1",
    "cent": "\u00A2", "pound": "\u00A3", "curren": "\u00A4", "yen": "\u00A5",
    "brvbar": "\u00A6", "sect": "\u00A7", "uml": "\u00A8", "copy": "\u00A9",
    "ordf": "\u00AA", "laquo": "\u00AB", "not": "\u00AC", "shy": "\u00AD",
    "reg": "\u00AE", "macr": "\u00AF", "deg": "\u00B0", "plusmn": "\u00B1",
    "sup2": "\u00B2", "sup3": "\u00B3", "acute": "\u00B4", "micro": "\u00B5",
    "para": "\u00B6", "middot": "\u00B7", "cedil": "\u00B8", "sup1": "\u00B9",
    "ordm": "\u00BA", "raquo": "\u00BB", "frac14": "\u00BC", "frac12":
    "\u00BD", "frac34": "\u00BE", "iquest": "\u00BF", "Agrave": "\u00C0",
    "Aacute": "\u00C1", "Acirc": "\u00C2", "Atilde": "\u00C3", "Auml":
    "\u00C4", "Aring": "\u00C5", "AElig": "\u00C6", "Ccedil": "\u00C7",
    "Egrave": "\u00C8", "Eacute": "\u00C9", "Ecirc": "\u00CA", "Euml":
    "\u00CB", "Igrave": "\u00CC", "Iacute": "\u00CD", "Icirc": "\u00CE",
    "Iuml": "\u00CF", "ETH": "\u00D0", "Ntilde": "\u00D1", "Ograve": "\u00D2",
    "Oacute": "\u00D3", "Ocirc": "\u00D4", "Otilde": "\u00D5", "Ouml":
    "\u00D6", "times": "\u00D7", "Oslash": "\u00D8", "Ugrave": "\u00D9",
    "Uacute": "\u00DA", "Ucirc": "\u00DB", "Uuml": "\u00DC", "Yacute":
    "\u00DD", "THORN": "\u00DE", "szlig": "\u00DF", "agrave": "\u00E0",
    "aacute": "\u00E1", "acirc": "\u00E2", "atilde": "\u00E3", "auml":
    "\u00E4", "aring": "\u00E5", "aelig": "\u00E6", "ccedil": "\u00E7",
    "egrave": "\u00E8", "eacute": "\u00E9", "ecirc": "\u00EA", "euml":
    "\u00EB", "igrave": "\u00EC", "iacute": "\u00ED", "icirc": "\u00EE",
    "iuml": "\u00EF", "eth": "\u00F0", "ntilde": "\u00F1", "ograve":
    "\u00F2", "oacute": "\u00F3", "ocirc": "\u00F4", "otilde": "\u00F5",
    "ouml": "\u00F6", "divide": "\u00F7", "oslash": "\u00F8", "ugrave":
    "\u00F9", "uacute": "\u00FA", "ucirc": "\u00FB", "uuml": "\u00FC",
    "yacute": "\u00FD", "thorn": "\u00FE", "yuml": "\u00FF", "OElig": "\u0152",
    "oelig": "\u0153", "Scaron": "\u0160", "scaron": "\u0161", "Yuml":
    "\u0178", "fnof": "\u0192", "circ": "\u02C6", "tilde": "\u02DC", "Alpha":
    "\u0391", "Beta": "\u0392", "Gamma": "\u0393", "Delta": "\u0394",
    "Epsilon": "\u0395", "Zeta": "\u0396", "Eta": "\u0397", "Theta": "\u0398",
    "Iota": "\u0399", "Kappa": "\u039A", "Lambda": "\u039B", "Mu": "\u039C",
    "Nu": "\u039D", "Xi": "\u039E", "Omicron": "\u039F", "Pi": "\u03A0", "Rho":
    "\u03A1", "Sigma": "\u03A3", "Tau": "\u03A4", "Upsilon": "\u03A5", "Phi":
    "\u03A6", "Chi": "\u03A7", "Psi": "\u03A8", "Omega": "\u03A9", "alpha":
    "\u03B1", "beta": "\u03B2", "gamma": "\u03B3", "delta": "\u03B4",
    "epsilon": "\u03B5", "zeta": "\u03B6", "eta": "\u03B7", "theta": "\u03B8",
    "iota": "\u03B9", "kappa": "\u03BA", "lambda": "\u03BB", "mu": "\u03BC",
    "nu": "\u03BD", "xi": "\u03BE", "omicron": "\u03BF", "pi": "\u03C0", "rho":
    "\u03C1", "sigmaf": "\u03C2", "sigma": "\u03C3", "tau": "\u03C4",
    "upsilon": "\u03C5", "phi": "\u03C6", "chi": "\u03C7", "psi": "\u03C8",
    "omega": "\u03C9", "thetasym": "\u03D1", "upsih": "\u03D2", "piv":
    "\u03D6", "ensp": "\u2002", "emsp": "\u2003", "thinsp": "\u2009", "zwnj":
    "\u200C", "zwj": "\u200D", "lrm": "\u200E", "rlm": "\u200F", "ndash":
    "\u2013", "mdash": "\u2014", "lsquo": "\u2018", "rsquo": "\u2019", "sbquo":
    "\u201A", "ldquo": "\u201C", "rdquo": "\u201D", "bdquo": "\u201E",
    "dagger": "\u2020", "Dagger": "\u2021", "bull": "\u2022", "hellip":
    "\u2026", "permil": "\u2030", "prime": "\u2032", "Prime": "\u2033",
    "lsaquo": "\u2039", "rsaquo": "\u203A", "oline": "\u203E", "frasl":
    "\u2044", "euro": "\u20AC", "image": "\u2111", "weierp": "\u2118", "real":
    "\u211C", "trade": "\u2122", "alefsym": "\u2135", "larr": "\u2190", "uarr":
    "\u2191", "rarr": "\u2192", "darr": "\u2193", "harr": "\u2194", "crarr":
    "\u21B5", "lArr": "\u21D0", "uArr": "\u21D1", "rArr": "\u21D2", "dArr":
    "\u21D3", "hArr": "\u21D4", "forall": "\u2200", "part": "\u2202", "exist":
    "\u2203", "empty": "\u2205", "nabla": "\u2207", "isin": "\u2208", "notin":
    "\u2209", "ni": "\u220B", "prod": "\u220F", "sum": "\u2211", "minus":
    "\u2212", "lowast": "\u2217", "radic": "\u221A", "prop": "\u221D",
    "infin": "\u221E", "ang": "\u2220", "and": "\u2227", "or": "\u2228",
    "cap": "\u2229", "cup": "\u222A", "int": "\u222B", "there4": "\u2234",
    "sim": "\u223C", "cong": "\u2245", "asymp": "\u2248", "ne": "\u2260",
    "equiv": "\u2261", "le": "\u2264", "ge": "\u2265", "sub": "\u2282", "sup":
    "\u2283", "nsub": "\u2284", "sube": "\u2286", "supe": "\u2287", "oplus":
    "\u2295", "otimes": "\u2297", "perp": "\u22A5", "sdot": "\u22C5", "vellip":
    "\u22EE", "lceil": "\u2308", "rceil": "\u2309", "lfloor": "\u230A",
    "rfloor": "\u230B", "lang": "\u2329", "rang": "\u232A", "loz": "\u25CA",
    "spades": "\u2660", "clubs": "\u2663", "hearts": "\u2665",
    "diams": "\u2666", "lt": "<", "gt": ">", "amp": "&"}


class TicketsParser(HTMLParser):
    def __init__(self):
        di = {}
        if hexversion >= 0x030200f0:
            di["strict"] = False
        HTMLParser.__init__(self, **di)
        self.row = None
        self.td_class = None
        self.p_title = None
        self.in_table = False
        self.in_tbody = False
        self.p_value = False
        self.div_classes = dict()
        self.data_handler = None
        self.label = ""
        self.message_text = []
        self.articles = []
        self.info = []
        self.mail_header = []
        self.action_hrefs = []
        self.queues = {}
        self.mail_src = None

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        div_cls = self.div_classes
        if tag == "input":
            cls = dattrs.get("class")
            if cls == "ArticleInfo" and self.row is not None:
                self.row["article info"] = dattrs["value"]
            if cls == "SortData" and self.row is not None:
                self.row[self.td_class] = dattrs["value"]
            return
        if tag == "td":
            self.td_class = dattrs.get("class")
            return
        if tag == "tr" and self.in_tbody:
            self.row = {"row": dattrs.get("class")}
            return
        if tag == "table":
            if dattrs.get("id") == "FixedTable":
                self.in_table = True
            return
        if tag == "tbody" and self.in_table:
            self.in_tbody = True
            return
        if tag == "div":
            cls = dattrs.get("class")
            for k in div_cls:
                div_cls[k] += 1
            if cls:
                scls = cls.split()
                try:
                    hcls, = scls
                except ValueError:
                    hcls = tuple(sorted(scls))
                if hcls not in div_cls:
                    div_cls[hcls] = 1
            if cls == "ArticleBody":
                self.data_handler = self.message_text
            return
        if tag == "h2" and "WidgetSimple" in div_cls:
            self.data_handler = []
            return
        if tag == "label":
            self.label = ""
            self.data_handler = []
            return
        if tag == "p":
            if "Value" in dattrs.get("class", "").split():
                self.p_value = True
                self.data_handler = []
                self.p_title = dattrs.get("title")
            return
        if tag == "a" and "ActionRow" in div_cls and "Scroller" not in div_cls:
            try:
                self.action_hrefs.append(dattrs["href"])
            except KeyError:
                pass
            return
        if tag == "option" and "ActionRow" in div_cls:
            self.queues[None] = dattrs.get("value")
            self.data_handler = []
            return
        if tag == "iframe" and "ArticleMailContent" in div_cls:
            self.mail_src = dattrs.get("src")
            return

    def handle_data(self, data):
        if self.data_handler is not None:
            self.data_handler.append(data)

    def handle_endtag(self, tag):
        div_cls = self.div_classes
        if tag == "table":
            self.in_table = False
            return
        if tag == "tbody":
            self.in_tbody = False
            return
        if tag == "tr" and self.row is not None:
            self.articles.append(self.row)
            self.row = None
            return
        if tag == "td":
            self.td_class = None
            return
        if tag == "div":
            for k in list(div_cls):
                div_cls[k] -= 1
                if div_cls[k] == 0:
                    del div_cls[k]
            return
        if tag == "h2" and "WidgetSimple" in div_cls:
            self.info.append("".join(self.data_handler))
            self.data_handler = None
            return
        if tag == "label":
            self.label = "".join(self.data_handler)
            return
        if tag == "p" and self.p_value:
            self.p_value = False
            if self.p_title is None:
                title = "".join(self.data_handler)
            else:
                title = self.p_title
            self.data_handler = None
            if "WidgetSimple" in div_cls:
                self.info.append((self.label, title))
            if "ArticleMailHeader" in div_cls:
                self.mail_header.append((self.label, title))
        if tag == "option" and "ActionRow" in div_cls:
            self.queues[self.queues.pop(None)] = "".join(self.data_handler)
            self.data_handler = None
            return

    def handle_entityref(self, name):
        if self.data_handler is not None:
            if name in SPEC_ENTS:
                self.data_handler.append(SPEC_ENTS[name])
            else:
                self.data_handler.append('&%s;' % name)

    def handle_charref(self, name):
        if self.data_handler is not None:
            self.data_handler.append(chr(int(name)))


class MessageParser(HTMLParser):
    def __init__(self):
        di = {}
        if hexversion >= 0x030200f0:
            di["strict"] = False
        HTMLParser.__init__(self, **di)
        self.message_text = []

    def handle_data(self, data):
        self.message_text.append(data)
