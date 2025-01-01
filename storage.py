#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import asyncio
from asyncio import Lock
from abc import ABC, abstractmethod
from bisect import insort_left
from collections import deque
from collections.abc import MutableMapping
from itertools import islice
from typing import AsyncIterator, Iterable, Iterator, Optional, Tuple, Union, TypeVar, Any, Dict, List


class AbstractRepository(ABC):

    # Defining an abstract method called add that takes one argument, 'sessions'
    @abstractmethod
    async def put(self, sessions):
        # This method will be implemented by the concrete repositories        
        pass

    # Defining an abstract method called get that takes one argument, 'ids's
    @abstractmethod
    async def get(self, ids):
        # This method will be implemented by the concrete repositories
        pass

    # Defining an abstract method called clear that takes no arguments
    @abstractmethod
    def clear(self):
        # This method will be implemented by the concrete repositories
        pass

class SlicableOrderedDict(MutableMapping):
    """
    A mutable mapping that stores items in memory and supports a maximum
    length, discarding the oldest items if the maximum length is exceeded.
    Items are always stored ordered by keys. A key can also be integer or slice.
    """
    def __init__(self, items: Optional[Dict] = None, maxlen: Optional[int] = None) -> None:
        """
        Initialize the MemoryStorage object.

        Parameters
        ----------
        items : dict, optional
            Items to initialize the MemoryStorage with.
        maxlen : int, optional
            Maximum length of the MemoryStorage. If exceeded, oldest items are
            discarded. If not provided, the MemoryStorage has no maximum length.
        """
        self._items = dict(items) if items else dict()
        self._keys = deque(sorted(self._items.keys()) if items else [])
        self.maxlen = maxlen

    def __len__(self) -> int:
        """Return the number of items stored in the MemoryStorage."""
        return len(self._items)

    def __iter__(self) -> Iterator[Any]:
        """Return an iterator over the keys of the MemoryStorage."""
        yield from self._keys

    def __getitem__(self, key: Union[int, slice, Any]) -> Union[Any, List[Any]]:
        """
        Retrieve item(s) from the MemoryStorage using a key or slice.

        Parameters
        ----------
        key : int | slice | Any
            If an integer, returns the item at that index in the ordered keys.
            If a slice, returns a list of items corresponding to the slice.
            Otherwise, retrieves the item associated with the key.

        Returns
        -------
        item : Any | List[Any]
            The item associated with the key or a list of items if the key is a slice.

        Raises
        ------
        KeyError
            If the key is an integer and out of bounds, or if the key does not exist.
        """
        if isinstance(key, slice):
            return [self._items[self._keys[k]] for k in
                    range(len(self._items)).__getitem__(key)]
        if isinstance(key, tuple):
            return [self._items[self._keys[k]] for k in
                    range(len(self._items)).__getitem__(slice(*key))]
        if isinstance(key, int):
            if self._items and len(self._items) > key:
                return self._items[self._keys[key]]
            else: 
                raise KeyError
        return self._items[key]

    def get(self, key: Any, default: Any = None) -> Any:
        """
        Return the item associated with the key if it exists, otherwise return
        the default if given.

        Parameters
        ----------
        key : Any
            The key of the item to retrieve.
        default : Any, optional
            The default value to return if the key does not exist.

        Returns
        -------
        The item associated with the key, or the default if the key does not exist.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key: Any, item: Any) -> None:
        """
        Add or update an item in the MemoryStorage.

        If the key does not exist, it is added to the MemoryStorage. If the
        MemoryStorage has a maximum length and the addition of this item would
        exceed that length, the oldest key is discarded before adding the new
        key. The order of keys is preserved based on the insertion value.

        Parameters
        ----------
        key : Any
            The key to associate with the item.
        item : Any
            The item to store in the MemoryStorage.

        Returns
        -------
        None
        """
        if key in self._items:
            self._items[key] = item
        else:
            if self.maxlen and len(self._items) == self.maxlen:
                first_key = self._keys.popleft()
                del self._items[first_key]
            insort_left(self._keys, key)
            self._items[key] = item

    def __delitem__(self, key: Any) -> None:
        """
        Remove the item associated with the key from the MemoryStorage.

        Parameters
        ----------
        key : Any
            The key of the item to remove.

        Raises
        ------
        KeyError
            If the key does not exist in the MemoryStorage.
        """
        if key in self._items:
            del self._items[key]
            self._keys.remove(key)
        else:
            raise KeyError

    def __contains__(self, key: Any) -> bool:
        """
        Check if the specified key exists in the MemoryStorage.

        Parameters
        ----------
        key : Any
            The key to check for existence in the MemoryStorage.

        Returns
        -------
        bool
            True if the key exists in the MemoryStorage, False otherwise.
        """
        return key in self._items

    def index(self, key: Any) -> int:
        """
        Return the index of the key in the MemoryStorage.

        Parameters
        ----------
        key : Any
            The key to return the index of.

        Returns
        -------
        int
            The index of the key in the MemoryStorage.

        Raises
        ------
        ValueError
            If the key does not exist in the MemoryStorage.
        """
        if key in self._keys:
            return self._keys.index(key)
        raise ValueError
    
    def keys(self) -> Iterator[Any]:
        """
        Generate an iterator over the keys in the MemoryStorage.

        Returns
        -------
        Generator[Any]
            An iterator over the keys in the order they were inserted.
        """
        return (key for key in self._keys)

    def values(self) -> Iterator[Any]:
        """
        Generate an iterator over the values in the MemoryStorage.

        Returns
        -------
        Generator[Any]
            An iterator over the values in the order they were inserted.
        """
        return (self._items[key] for key in self._keys)

    def items(self) -> Iterator[Tuple]:
        """
        Generate an iterator over the (key, value) pairs in the MemoryStorage.
        The order of iteration is sorted by keys.

        Returns
        -------
        Generator[Tuple]
            An iterator over the (key, value) pairs in the MemoryStorage.
        """
        return ((key, self._items[key]) for key in self._keys)
    
    def clear(self) -> None:
        """
        Remove all items from the MemoryStorage.

        This method clears the storage by removing all key-value pairs and 
        resetting the internal key storage.
        """
        self._items.clear()
        self._keys.clear()

    def __repr__(self) -> str:
        """
        Return a string representation of the MemoryStorage instance.

        The string includes the name of the class, the items currently stored,
        and the maximum length of the storage if applicable.
        """
        return f"{type(self).__name__}=({self._items}, maxlen={self.maxlen})"

    def __eq__(self, other) -> bool:
        """
        Check if two MemoryStorage instances are equal.

        The comparison is done by checking if the items are equal and the maximum
        length is the same. If the other object is not of the same class, it returns
        NotImplemented.
        """
        if not isinstance(other, self.__class__):
            return NotImplemented
        return list(self.items()) == list(other.items()) and self.maxlen == other.maxlen

    def __len__(self):
        return len(self._items)

class AsyncMemoryStorage(SlicableOrderedDict, AbstractRepository):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the AsyncMemoryStorage object.

        Parameters
        ----------
        *args : Any
            Arguments to be passed to the superclass SlicableOrderedDict initialization.
        **kwargs : Any
            Keyword arguments to be passed to the superclass SlicableOrderedDict initialization.

        Attributes
        ----------
        _lock : Lock
            A lock object used to protect against concurrent access to the storage.
        """
        super().__init__(*args, **kwargs)
        self._lock: Lock = Lock()

    async def put(self, itemdict: Dict[Any, Any]) -> None:
        """
        Asynchronously put items into the AsyncMemoryStorage.

        This method puts each item in the given itemdict dictionary to the
        AsyncMemoryStorage, overwriting any existing item with the same key.

        Parameters
        ----------
        itemdict : Dict[Any, Any]
            A dictionary of items to add to the AsyncMemoryStorage.

        Returns
        -------
        None

        Notes
        -----
        This coroutine does not block the event loop, it yields control back to the
        event loop after each item is added.
        """
        async with self._lock:
            for k, v in itemdict.items():
                self[k] = v

    async def get(self, key: Union[slice, Tuple[int, int], int, Any] = None) -> AsyncIterator[Any]:
        """
        Configure the iteration range in the AsyncMemoryStorage.

        Parameters
        ----------
        key : Union[slice, Tuple[int, int], int, Any], optional
            The key or slice of keys to iterate over. If None, the entire
            AsyncMemoryStorage is iterated.

        Yields
        ------
        item : Any
            The next item in the iteration.
        """
        async with self._lock:
            if not key:
                key = slice(None, None)
            for item in self[key]:
                yield item

    async def clear(self) -> None:
        """
        Clear all items from the AsyncMemoryStorage.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        async with self._lock:
            super().clear()

if __name__ == "__main__":
    from utils import asyncio_run

    async def main():
        loop = asyncio.get_event_loop()
        storage = AsyncMemoryStorage()
        tasks = [loop.create_task(storage.put({'1': 'one', '2': 'two'})),
                 loop.create_task(storage.put({'3': 'three', '1': 'ONE'}))]
        await asyncio.gather(*tasks)
        async for value in storage.get():
            print(value)
        print(len(storage))
        await storage.clear()
        print(len(storage))

    asyncio_run(main())
