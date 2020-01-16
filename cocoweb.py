import asyncio
import functools
import inspect
import os
from urllib import parse

from aiohttp import web

def get(url):
    '''
    defined decorator @get('path')
    :根据参数url返回一个装饰器
    :param url:
    :return:
    '''

    def decorator(func):
        '''
        装饰器：根据函数返回一个装饰过的函数
        :param func:
        :return:
        '''
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.__url__=url
        wrapper.__method__='GET'
        return wrapper
    return decorator


def post(url):

    def decorator(func):
        '''
        functools.wraps 必填参数wrapped:表明包装的函数
        :param func:
        :return:
        '''
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.__url__ = url
        wrapper.__method__ = 'POST'
        return wrapper
    return decorator


class HandlerDecorator(object):


    def __init__(self, method: str, url) -> None:
        super().__init__()
        self._method = method.upper()
        self._url = url

    def __call__(self, fn):

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not asyncio.iscoroutinefunction(fn) and not inspect.iscoroutinefunction(fn):
                return asyncio.coroutine(fn)(*args, **kwargs)
            return fn(*args, **kwargs)
        wrapper.__url__ = self._url
        wrapper.__method__ = self._method
        return wrapper


class put(HandlerDecorator):

    def __init__(self, *args) -> None:
        super().__init__('PUT', *args)

class delete(HandlerDecorator):

    def __init__(self, *args) -> None:
        super().__init__('DELETE', *args)


class RequestHandler(object):
    '''
    接收一个协程 解析请求和相应
    '''
    def __init__(self, coro):
        self._coro = coro

    async def __call__(self, request: web.Request):
        # parse http request
        kwargs = None
        if request.method == 'POST':
            ct = request.content_type
            if not ct:
                raise web.HTTPBadRequest('Missing content-type')
            if ct.startswith('application/json'):
                params = await request.json()
                if not isinstance(params, dict):
                    raise web.HTTPBadRequest('json type must be object')
                kwargs = params

        if request.method == 'GET':
            qs = request.query_string
            if qs:
                kwargs = dict()
                for k, v in parse.parse_qs(qs):
                    kwargs[k] = v[0]

        if kwargs is None:
            kwargs = request.match_info
        else:
            for k, v in request.match_info.items():
                kwargs[k] = v

        result = await self._coro(**kwargs)
        # parse response
        return result


def add_route(app: web.Application, coro):
    '''
    接受一个协程
    :param app:
    :param coro:
    :return:
    '''
    app.router.add_route(coro.__method__, coro.__url__, RequestHandler(coro))


def add_routes(app: web.Application, model_name: str):
    n = model_name.rfind('.')
    if n == (-1):
        mod = __import__(model_name, globals(), locals())
    else:
        name = model_name[n+1:]
        mod = getattr(__import__(model_name[:n], globals(), locals(), [name]), name)
    for attr_name in dir(mod):
        if attr_name.startswith('_'):
            continue

        attr = getattr(mod, attr_name)
        if callable(attr):
            method = getattr(attr, '__method__')
            url = getattr(attr, '__url__')
            if method and url:
                add_route(app, attr)


def add_static(app: web.Application):
    path = os.path.join(os.path.abspath(__file__), 'static')
    app.router.add_static('/static/', path)


@get('/index/')
def index():
    pass


@delete('/hello')
def hello():
    pass


if __name__ == '__main__':
    print('url:%s method:%s' % (index.__url__, index.__method__))
    print('url:%s method:%s' % (hello.__url__, hello.__method__))
