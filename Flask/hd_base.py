import functools
from flask import request
import flask


def require(*required_args):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            for arg in required_args:
                if arg not in request.json:
                    return flask.jsonify(code=400, msg='参数不正确')
            return func(*args, **kw)
        return wrapper
    return decorator