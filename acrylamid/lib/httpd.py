# -*- encoding: utf-8 -*-
#
# Copyright 2012 Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses -- see LICENSE.

"""
Internal Webserver
~~~~~~~~~~~~~~~~~~

Launch a dumb webserver as thread."""

import os
import time

from threading import Thread

from acrylamid.utils import force_unicode as u
from acrylamid.compat import PY2K
from acrylamid.helpers import joinurl

if PY2K:
    from SocketServer import TCPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
else:
    from socketserver import TCPServer
    from http.server import SimpleHTTPRequestHandler


class ReuseAddressServer(TCPServer):
    """avoids socket.error: [Errno 48] Address already in use"""
    allow_reuse_address = True

    def serve_forever(self):
        """Handle one request at a time until doomsday."""
        while not self.kill_received:
            if not self.wait:
                self.handle_request()
            else:
                time.sleep(0.1)


class RequestHandler(SimpleHTTPRequestHandler):
    """This is a modified version of python's -m SimpleHTTPServer to
    serve on a specific sub directory of :func:`os.getcwd`."""

    www_root = '.'
    log_error = lambda x, *y: None

    def translate_path(self, path):
        path = SimpleHTTPRequestHandler.translate_path(self, path)
        return joinurl(u(os.getcwd()), self.www_root, path[len(u(os.getcwd())):])

    def end_headers(self):
        self.send_header("Cache-Control", "max-age=0, must-revalidate")
        SimpleHTTPRequestHandler.end_headers(self)


class Webserver(Thread):
    """A single-threaded webserver to serve while generation.

    :param port: port to listen on
    :param root: serve this directory under /"""

    def __init__(self, port=8000, root='.', log_message=lambda x, *y: None):
        Thread.__init__(self)
        Handler = RequestHandler
        Handler.www_root = root
        Handler.log_message = log_message

        self.httpd = ReuseAddressServer(("", port), Handler)
        self.httpd.wait = False
        self.httpd.kill_received = False

    def setwait(self, value):
        self.httpd.wait = value
    wait = property(lambda self: self.httpd.wait, setwait)

    def run(self):
        self.httpd.serve_forever()
        self.join(1)

    def shutdown(self):
        """"Sets kill_recieved and closes the server socket."""
        self.httpd.kill_received = True
        self.httpd.socket.close()
