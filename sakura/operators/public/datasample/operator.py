#!/usr/bin/env python
from sakura.daemon.processing.operator import Operator
from . import datasets

class DataSampleOperator(Operator):
    NAME = "Data Sample"
    SHORT_DESC = "Data Sample."
    TAGS = [ "testing", "datasource" ]

    def construct(self):
        # no inputs
        pass
        # outputs:
        streams = []
        for ds in datasets.load():
            if hasattr(ds, 'STREAM'):
                # statically defined stream
                stream = ds.STREAM
            else:
                # dynamically generated stream
                stream = ds.load_stream(self)
            streams.append(stream)
        for stream in sorted(streams, key=lambda s: s.label):
            self.register_output(stream)
        # no parameters
        pass
