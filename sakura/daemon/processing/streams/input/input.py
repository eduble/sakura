class InputStream(object):
    def __init__(self, label):
        self.source_stream = None
        self.columns = None
        self.label = label
    def connect(self, output_stream):
        self.source_stream = output_stream
        self.columns = self.source_stream.columns
    def disconnect(self):
        self.source_stream = None
        self.columns = None
    def connected(self):
        return self.source_stream != None
    def columns(self):
        return self.columns
    def get_info_serializable(self):
        info = dict(label = self.label)
        if self.connected():
            info.update(
                connected = True,
                columns = [ col.get_info_serializable() for col in self.columns ],
                length = self.source_stream.length
            )
        else:
            info.update(
                connected = False
            )
        return info
    def __iter__(self):
        if self.connected():
            return self.source_stream.__iter__()
        else:
            return None
    def get_range(self, *args):
        if self.connected():
            return self.source_stream.get_range(*args)
        else:
            return None
