from sakura.client.apiobject.base import APIObjectBase
from sakura.common.errors import APIRequestError

class APILink:
    _deleted = set()
    def __new__(cls, remote_api, link_info):
        link_id = link_info['link_id']
        remote_obj = remote_api.links[link_id]
        short_desc = "%s[%d]->%s[%d]" % (
                link_info['src_cls_name'],
                link_info['src_out_id'],
                link_info['dst_cls_name'],
                link_info['dst_in_id'])
        def get_remote_obj():
            if remote_obj in APILink._deleted:
                raise ReferenceError('This link was deleted!')
            else:
                return remote_obj
        class APILinkImpl(APIObjectBase):
            __doc__ = 'Sakura Link - ' + short_desc
            def _check_online(self):
                if not self.enabled:
                    raise APIRequestError('Link is disabled!')
            def __get_remote_info__(self):
                return get_remote_obj().info()
            def delete(self):
                """Delete this link"""
                self._check_online()
                get_remote_obj().delete()
                APILink._deleted.add(remote_obj)
            def monitor(self):
                """Include events about this object in api.stream_events()"""
                obj_id = 'links[%d]' % link_id
                get_remote_obj().monitor(obj_id)
            def unmonitor(self):
                """Stop including events about this object in api.stream_events()"""
                obj_id = 'links[%d]' % link_id
                remote_api.events.unmonitor(obj_id)
        return APILinkImpl()
