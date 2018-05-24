import sys, sakura.daemon.conf as conf
from sakura.daemon.processing.operator import Operator
from sakura.daemon.processing.parameter import ParameterException

class DaemonEngine(object):
    def __init__(self, op_classes, datastores):
        self.op_classes = op_classes
        self.datastores = {}
        for ds in datastores:
            ds = ds.adapter.adapt(ds)
            self.datastores[(ds.host, ds.driver_label)] = ds
        self.op_instances = {}
        self.hub = None
        self.fragment_sources = {}
        self.name = conf.daemon_desc
    def fire_data_issue(self, issue, should_fail=True):
        if should_fail:
            raise Exception(issue)
        else:
            sys.stderr.write(issue + '\n')
    def register_hub_api(self, hub_api):
        self.hub = hub_api
    def get_daemon_info_serializable(self):
        op_classes_desc = list(
            Operator.descriptor(op_cls) for op_cls in self.op_classes.values()
        )
        return dict(name=self.name,
                    datastores=tuple(ds.pack() for ds in self.datastores.values()),
                    op_classes=op_classes_desc)
    def create_operator_instance(self, cls_name, op_id):
        op_cls = self.op_classes[cls_name]
        op = op_cls(op_id)
        op.daemon = self
        op.construct()
        op.auto_fill_parameters(permissive=True)
        self.op_instances[op_id] = op
        print("created operator %s op_id=%d" % (cls_name, op_id))
    def delete_operator_instance(self, op_id):
        print("deleting operator %s op_id=%d" % (self.op_instances[op_id].NAME, op_id))
        del self.op_instances[op_id]
    def is_foreign_operator(self, op_id):
        return op_id not in self.op_instances
    def connect_operators(self, src_op_id, src_out_id, dst_op_id, dst_in_id,
                            auto_fill_params = True):
        if self.is_foreign_operator(src_op_id):
            # the source is a remote operator.
            src_label = 'remote(op_id=%d,out%d)' % (src_op_id, src_out_id)
            src_op = self.hub.context.op_instances[src_op_id]
        else:
            src_op = self.op_instances[src_op_id]
            src_label = '%s op_id=%d out%d' % (src_op.NAME, src_op_id, src_out_id)
        dst_op = self.op_instances[dst_op_id]
        dst_input_stream = dst_op.input_streams[dst_in_id]
        dst_input_stream.connect(src_op.output_streams[src_out_id])
        if auto_fill_params:
            # auto select unselected parameters
            dst_op.auto_fill_parameters(stream = dst_input_stream)
        print("connected %s -> %s op_id=%d in%d" % \
                (src_label, dst_op.NAME, dst_op_id, dst_in_id))
    def disconnect_operators(self, src_op_id, src_out_id, dst_op_id, dst_in_id):
        dst_op = self.op_instances[dst_op_id]
        dst_input_stream = dst_op.input_streams[dst_in_id]
        dst_op.unselect_parameters(stream = dst_input_stream)
        dst_input_stream.disconnect()
        #if self.is_foreign_operator(src_op_id):
        if False:
            # discard the fragment source operator
            del self.fragment_sources[(dst_op_id, dst_in_id)]
        print("disconnected [...] -> %s op_id=%d in%d" % \
                (dst_op.NAME, dst_op_id, dst_in_id))
    def get_possible_links(self, src_op_id, dst_op_id):
        dst_op = self.op_instances[dst_op_id]
        if self.is_foreign_operator(src_op_id):
            src_op = self.hub.context.op_instances[src_op_id]
        else:
            src_op = self.op_instances[src_op_id]
        # check all src_op.output -> dst_op.input combinations
        # and discard those which cause an exception.
        links = []
        for dst_in_id, dst_input_stream in enumerate(dst_op.input_streams):
            for src_out_id in range(len(src_op.output_streams)):
                if dst_input_stream.connected():
                    # this entry is already connected with something else
                    continue
                self.connect_operators(src_op_id, src_out_id, dst_op_id, dst_in_id,
                                        auto_fill_params = False)
                try:
                    # auto select parameters
                    dst_op.auto_fill_parameters(stream = dst_input_stream)
                    # if we are here, this link is possible
                    links.append((src_out_id, dst_in_id))
                except ParameterException:
                    pass
                self.disconnect_operators(src_op_id, src_out_id, dst_op_id, dst_in_id)
        return links
