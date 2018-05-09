import collections, json, numpy as np
from contextlib import contextmanager
from sakura.common.io import LocalAPIHandler, pack
from sakura.common.errors import APIRequestError
from sakura.hub.web.api import GuiToHubAPI
from sakura.hub.db import db_session_wrapper
from sakura.hub.context import greenlet_env

# caution: the object should be sent all at once,
# otherwise it will be received as several messages
# on the websocket. Thus we buffer possibly several
# writes, and send the whole buffer when we get a
# flush() call.
class FileWSock(object):
    def __init__(self, wsock):
        self.wsock = wsock
        self.msg = ''
    def write(self, s):
        self.msg += s
    def read(self):
        msg = self.wsock.receive()
        if msg == None:
            msg = ''
        return msg
    def flush(self):
        self.wsock.send(self.msg)
        self.msg = ''

class ResultWrapper:
    @staticmethod
    def on_success(result):
        return (True, pack(result))
    @staticmethod
    def on_exception(exc):
        if isinstance(exc, APIRequestError):
            return (False, str(exc))
        else:
            raise exc

def get_web_session_wrapper(session_id):
    @contextmanager
    def web_session_wrapper():
        # record session id --
        # We cannot simply record the session object itself,
        # because it is a pony db object
        # thus its scope is limited to a db session.
        # And for each call, we get a different db session.
        greenlet_env.session_id = session_id
        # call db session wrapper
        with db_session_wrapper():
            yield
    return web_session_wrapper

def gui_fallback_handler(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return { k: gui_fallback_handler(v) for k, v in obj.items() }
    elif isinstance(obj, type) and hasattr(obj, 'select'):    # for pony entities
        return tuple(gui_fallback_handler(o) for o in obj.select())
    elif hasattr(obj, 'pack'):
        return gui_fallback_handler(obj.pack())
    elif hasattr(obj, '_asdict'):
        return gui_fallback_handler(obj._asdict())
    elif isinstance(obj, list) or isinstance(obj, tuple) or \
                hasattr(obj, '__iter__'):
        return tuple(gui_fallback_handler(o) for o in obj)
    else:
        return obj

class GUISerializationProtocol:
    def load(self, f):
        return json.load(f)
    def dump(self, obj, f):
        return json.dump(obj, f,
                separators=(',', ':'),
                default=gui_fallback_handler)

gui_protocol = GUISerializationProtocol()

def rpc_manager(context, wsock, session):
    print('New GUI RPC connection.')
    # make wsock a file-like object
    f = FileWSock(wsock)
    # manage api requests
    local_api = GuiToHubAPI(context)
    web_session_wrapper = get_web_session_wrapper(session.id)
    handler = LocalAPIHandler(f, gui_protocol, local_api,
                session_wrapper = web_session_wrapper,
                result_wrapper = ResultWrapper)
    session.num_ws += 1
    handler.loop()
    session.num_ws -= 1
    print('GUI RPC disconnected.')

