class OpInstanceMixin:
    @property
    def daemon_api(self):
        return self.op_class.daemon.api
    @property
    def remote_instance(self):
        # note: the following shortcut will become valid only after
        # the operator has been instanciated with function
        # instanciate_on_daemon() below.
        return self.daemon_api.op_instances[self.id]
    @property
    def instanciated(self):
        if not '_instanciated' in self.__dict__:
            self._instanciated = False
        return self._instanciated
    def __getattr__(self, attr):
        # if we cannot find the attr,
        # let's look at the real operator
        # instance on the daemon side.
        return getattr(self.remote_instance, attr)
    def pack(self):
        res = self.remote_instance.pack()
        res.update(
            cls_id = self.op_class.id,
            online = self.instanciated)
        return res
    def instanciate_on_daemon(self):
        self.daemon_api.create_operator_instance(self.op_class.name, self.id)
        self._instanciated = True
        return self.remote_instance
    def delete_on_daemon(self):
        self._instanciated = False
        self.daemon_api.delete_operator_instance(self.id)
    @classmethod
    def create_instance(cls, context, op_cls_id):
        op = cls(op_class = op_cls_id)      # create in local db
        context.db.commit()                 # refresh op id
        return op.instanciate_on_daemon()   # create remotely
    def delete_instance(self):
        # delete connected links
        for l in self.uplinks:
            l.delete_link()
        for l in self.downlinks:
            l.delete_link()
        # delete instance remotely
        self.delete_on_daemon()
        # delete instance in local db
        self.delete()