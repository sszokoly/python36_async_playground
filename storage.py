from collections import deque
from abc import ABC, abstractmethod
from collections.abc import Sequence

class AbstractStorage(ABC, Sequence):
    @abstractmethod
    def clear(self):
        """Clears storage"""   
    @abstractmethod
    def append(self, x):
        """Add x to the right side"""
   
class Storage(AbstractStorage):
    def __init__(self, maxlen=None):
        self._items = deque([], maxlen)
    def append(self, x):
        self._items.append(x)
    def clear(self):
        self._items.clear()
    def __getitem__(self, i):
        return self._items[i]
    def __len__(self):
        return len(self._items)
    def __str__(self):
        return self._items.__repr__()

storage = Storage(3)
storage.append({'id': '00001', 'local_ip': '10.10.10.48.58'})
storage.append({'id': '00001', 'local_ip': '10.44.244.48.58'})
print(storage)