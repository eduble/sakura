import numpy as np
from sakura.common.chunk import NumpyChunk
from sakura.daemon.processing.tools import Registry
from sakura.daemon.processing.cache import Cache
from sakura.daemon.processing.column import Column
from time import time

# We measure the delay <d> it took to compute iterator
# values, and ensure iterator is kept in cache for
# at least a delay <d>*<factor>.
CACHE_VALUE_FACTOR = 10.0

class OutputStreamBase(Registry):
    def __init__(self, label):
        self.columns = []
        self.label = label
        self.length = None
        self.range_iter_cache = Cache(10)
    def add_column(self, col_label, col_type, col_tags=()):
        return self.register(self.columns, Column,
                    col_label, col_type, tuple(col_tags),
                    self, len(self.columns))
    def pack(self):
        return dict(label = self.label,
                    columns = self.columns,
                    length = self.length)
    def get_range(self, row_start, row_end, columns=None, filters=()):
        startup_time = time()
        chunk_len = row_end-row_start
        # try to reuse the last iterator
        it, compute_delay = self.range_iter_cache.get(key=(row_start, row_end, columns, filters))
        in_cache = it is not None
        # otherwise, create a new iterator
        if not in_cache:
            stream = self
            if columns is not None:
                stream = stream.select_columns(*columns)
            for condition in filters:
                stream = stream.filter(condition)
            it = stream.chunks(chunk_len, row_start)
            compute_delay = 0
        # read next chunk and return it
        for chunk in it:
            if chunk.size < chunk_len:
                # end of iterator, remove from cache if present
                if in_cache:
                    self.range_iter_cache.forget(it)
            else:
                # update info about last iterator
                new_row_start = row_start + chunk.size
                compute_delay += time()- startup_time
                expiry_delay = compute_delay * CACHE_VALUE_FACTOR
                self.range_iter_cache.save(it, expiry_delay,
                    key=(new_row_start, new_row_start + chunk_len, columns, filters),
                    context_info=compute_delay
                )
            return chunk
        # if we are here, stream has ended, forget about iterator and
        # return empty chunk
        if in_cache:
            self.range_iter_cache.forget(it)
        return NumpyChunk.empty(self.get_dtype())
    def get_dtype(self):
        return np.dtype(list(col.get_dtype() for col in self.columns))
    def select_columns(self, *columns):
        # verify that at least 1 column is specified
        if len(columns) == 0:
            return self
        # column objects or indices are accepted
        if isinstance(columns[0], int):
            col_indexes = tuple(columns)
        else:
            col_indexes = tuple(col.index for col in columns)
        # if all columns are selected in the same order, return self...
        if col_indexes == tuple(range(len(self.columns))):
            return self
        # compute a substream
        return self.__select_columns__(*col_indexes)
    def filter(self, cond):
        col, comp_op, other = cond
        # column object or index are accepted
        if isinstance(col, int):
            col_index = col
        else:
            col_index = col.index
        # compute a substream
        return self.__filter__(col_index, comp_op, other)
