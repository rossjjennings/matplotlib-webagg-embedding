import io
import json
import mimetypes
from pathlib import Path

import tornado
import tornado.web
import tornado.websocket

import matplotlib as mpl
from matplotlib.backends.backend_webagg_core import (
    FigureManagerWebAgg, new_figure_manager_given_figure)

class FigureHandler:
    """
    A convenient way to encapsulate the pieces needed to add a figure to a 
    Tornado web application, those pieces being:
     - A WebSocket class ("socket") inheriting from 
       tornado.websocket.WebSocketHandler
     - A Downloader class ("downloader") inheriting from 
       tornado.web.RequestHandler
     - A bit of JavaScript ("js") to add to the webpage.
    """
    def __init__(handler, figure, fig_id):
        handler.figure = figure
        handler.manager = new_figure_manager_given_figure(fig_id, figure)
        handler.fig_id = fig_id
        
        class Downloader(tornado.web.RequestHandler):
            """
            Handles downloading of the figure in various file formats.
            """

            def get(self, fmt):
                manager = handler.manager
                self.set_header(
                    'Content-Type', mimetypes.types_map.get(fmt, 'binary'))
                buff = io.BytesIO()
                manager.canvas.figure.savefig(buff, format=fmt)
                self.write(buff.getvalue())
        handler.downloader = Downloader

        class WebSocket(tornado.websocket.WebSocketHandler):
            """
            A websocket for interactive communication between the plot in
            the browser and the server.

            In addition to the methods required by tornado, it is required to
            have two callback methods:

                - ``send_json(json_content)`` is called by matplotlib when
                it needs to send json to the browser.  `json_content` is
                a JSON tree (Python dictionary), and it is the responsibility
                of this implementation to encode it as a string to send over
                the socket.

                - ``send_binary(blob)`` is called to send binary image data
                to the browser.
            """
            supports_binary = True

            def open(self):
                # Register the websocket with the FigureManager.
                manager = handler.manager
                manager.add_web_socket(self)
                if hasattr(self, 'set_nodelay'):
                    self.set_nodelay(True)

            def on_close(self):
                # When the socket is closed, deregister the websocket with
                # the FigureManager.
                manager = handler.manager
                manager.remove_web_socket(self)

            def on_message(self, message):
                # The 'supports_binary' message is relevant to the
                # websocket itself.  The other messages get passed along
                # to matplotlib as-is.

                # Every message has a "type" and a "figure_id".
                message = json.loads(message)
                if message['type'] == 'supports_binary':
                    self.supports_binary = message['value']
                else:
                    manager = handler.manager
                    manager.handle_json(message)

            def send_json(self, content):
                self.write_message(json.dumps(content))

            def send_binary(self, blob):
                if self.supports_binary:
                    self.write_message(blob, binary=True)
                else:
                    data_uri = "data:image/png;base64,{0}".format(
                        blob.encode('base64').replace('\n', ''))
                    self.write_message(data_uri)
        handler.socket = WebSocket
