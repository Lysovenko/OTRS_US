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
"Making the multipart form"

from hashlib import sha1
from base64 import b64encode


def dump_multipart_text(data):
    bsum = sha1()
    for item in data:
        bsum.update(str(item[1]).encode())
    boundary = b64encode(bsum.digest())[:-1]
    result = []
    for name, content in data:
        result.append(b"--" + boundary)
        if type(content) is str:
            result.append((
                'Content-Disposition: form-data; name="%s"' % name).encode())
            result.append(b'')
            result.append(content.encode())
        elif type(content) is tuple:
            result.append((
                'Content-Disposition: form-data; name="%s";'
                ' filename="%s"' % (name, content[0])).encode())
            result.append(b'')
            result.append(content[1])
    result.append(b'--' + boundary + b'--')
    result.append(b'')
    contentType = "multipart/form-data; boundary=%s" % (boundary.decode())
    try:
        result = b'\r\n'.join(result)
    except TypeError as err:
        print(data)
        raise TypeError(err)
    headers = {'Content-type': contentType}
    return result, headers
