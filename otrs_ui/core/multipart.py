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
"Making the Tickets widget"
import mimetypes, http.client
from hashlib import sha1
from base64 import b64encode

def dump_multipart_text(data):
#boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T' # Randomly generated
    data = [(n, d.encode()) for n, d in data]
    bsum = sha1()
    for item in data:
        bsum.update(item[1])
    boundary = b64encode(bsum.digest())
    result = []
    for name, content in data:
        result.append(b"--" + boundary)
        result.append(b"Content-Disposition: form-data; name={" +
                      name.encode() + b"}")
        result.append(b'')
        result.append(content)
    result.append(b'--'+boundary+b'--')
    result.append(b'')
    contentType = "multipart/form-data; boundary={%s}" % (boundary.decode())
    result = b'\r\n'.join(result)
    headers = {'Content-type': contentType}
    return result, headers
