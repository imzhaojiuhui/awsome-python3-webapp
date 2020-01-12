#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging;logging.basicConfig(level=logging.INFO)

from aiohttp import web


def index(request):

    return web.Response(body=b'<h1>Awesome</h1>', headers={'content-type':'text/html'})

def init():
    app = web.Application()
    app.router.add_route('GET', '/', index)
    web.run_app(app, host='127.0.0.1', port=9000)
    logging.info('server starting')

if __name__=='__main__':
    init()