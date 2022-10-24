import numpy as np
from matplotlib.figure import Figure
import matplotlib as mpl
from matplotlib.backends.backend_webagg_core import (
    FigureManagerWebAgg,
    new_figure_manager_given_figure,
)

import argparse
import signal
import socket
import io
import json
import mimetypes
from pathlib import Path
import asyncio

import tornado
import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.ioloop

from figure_handler import FigureHandler

def create_figure1():
    """
    Creates a simple example figure.
    """
    fig = Figure()
    ax = fig.add_subplot()
    t = np.arange(0.0, 3.0, 0.01)
    s = np.sin(2 * np.pi * t)
    ax.plot(t, s)
    return fig

def create_figure2():
    """
    Creates another simple example figure.
    """
    fig = Figure()
    ax = fig.add_subplot()
    t = np.arange(-1.0, 1.0, 0.01)
    s = np.sin(t**2)
    ax.plot(t, s)
    return fig

class MainPage(tornado.web.RequestHandler):
    """
    Serves the main HTML page.
    """
    def get(self):
        self.render("template.html")

class MplJs(tornado.web.RequestHandler):
    """
    Serves the generated matplotlib javascript file.  The content
    is dynamically generated based on which toolbar functions the
    user has defined.  Call `FigureManagerWebAgg` to get its
    content.
    """
    def get(self):
        self.set_header('Content-Type', 'application/javascript')
        js_content = FigureManagerWebAgg.get_javascript()

        self.write(js_content)

class FigureJs(tornado.web.RequestHandler):
    """
    Serves the JavaScript necessary to load the figure and set up
    the associated WebSocket on the client side.
    """
    def initialize(self, figure_handlers):
        self.js_block = "".join(handler.js for handler in figure_handlers)
        
    def get(self):
        self.render("mpl_figure.js", js_block=self.js_block)

def make_app():
    figure1 = create_figure1()
    figure2 = create_figure2()
    
    handler1 = FigureHandler(
        figure1,
        fig_id=1,
        sock_uri="ws://localhost:8080/ws1",
        elt_id="figure1",
    )
    
    handler2 = FigureHandler(
        figure2,
        fig_id=2,
        sock_uri="ws://localhost:8080/ws2",
        elt_id="figure2",
    )
    
    application = tornado.web.Application([
        # Static files for the CSS and JS
        (r'/_static/(.*)',
            tornado.web.StaticFileHandler,
            {'path': FigureManagerWebAgg.get_static_file_path()}),

        # Static images for the toolbar
        (r'/_images/(.*)',
            tornado.web.StaticFileHandler,
            {'path': Path(mpl.get_data_path(), 'images')}),

        # The page that contains all of the pieces
        ('/', MainPage),

        ('/mpl.js', MplJs),
        ('/mpl_figure.js', FigureJs, {'figure_handlers': [handler1, handler2]}),

        # Sends images and events to the browser, and receives
        # events from the browser
        ('/ws1', handler1.socket),
        ('/ws2', handler2.socket),

        # Handles the downloading (i.e., saving) of static images
        (r'/download.([a-z0-9.]+)', handler1.downloader),
    ])
    return application

async def launch_app(port):
    app = make_app()
    app.listen(port)
    shutdown_event = asyncio.Event()
    await shutdown_event.wait()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=8080,
                        help='Port to listen on.')
    args = parser.parse_args()
    
    print(f"Listening on port {args.port}")
    print("Press Ctrl+C to quit")
    asyncio.run(launch_app(args.port))
