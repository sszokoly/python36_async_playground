#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import asyncio
from abc import ABC, abstractmethod
from bisect import insort_left
from collections import deque
from collections.abc import MutableMapping
from itertools import islice
from typing import AsyncIterator, Iterator, Optional, Tuple, Union, TypeVar, Any, Dict, List


class AbstractRepository(ABC):

    # Defining an abstract method called add that takes one argument, 'sessions'
    @abstractmethod
    def add(self, sessions):
        # This method will be implemented by the concrete repositories        
        pass

    # Defining an abstract method called get that takes one argument, 'ids'
    @abstractmethod
    def get(self, ids):
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
    Items are always returned ordered by keys. A key can also be integer or slice.
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
        The item associated with the key or a list of items if the key is a slice.

        Raises
        ------
        KeyError
            If the key is an integer and out of bounds, or if the key does not exist.
        """
        if isinstance(key, slice):
            if key.start is None:
                start = 0
            elif key.start < 0:
                start = len(self._items) + key.start
            else:
                start = key.start
            if key.stop is None:
                stop = len(self._items)
            elif key.stop < 0:
                stop = len(self._items) + key.stop
            else:
                stop = key.stop
            return [self._items[key] for key in
                islice(self._keys, start, stop, key.step)]
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
        key.

        Parameters
        ----------
        key : Any
            The key to associate with the item.
        item : Any
            The item to store in the MemoryStorage.
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

class AsyncMemoryStorage(SlicableOrderedDict):

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
        start : int
            Starting index for iteration or slicing operations, initialized to 0.
        stop : int
            Stopping index for iteration or slicing operations, initialized to the current length of the storage.
        """
        super().__init__(*args, **kwargs)
        self.start: int = 0
        self.stop: int = len(self)

    async def add(self, sessions: Dict[Any, Any]) -> None:
        """
        Asynchronously add items to the AsyncMemoryStorage.

        This method adds each item in the given sessions dictionary to the
        AsyncMemoryStorage, overwriting any existing item with the same key.

        Parameters
        ----------
        sessions : Dict[Any, Any]
            A dictionary of items to add to the AsyncMemoryStorage.

        Returns
        -------
        None

        Notes
        -----
        This coroutine does not block the event loop, it yields control back to the
        event loop after each item is added.
        """
        for k, v in sessions.items():
            self[k] = v
        await asyncio.sleep(0)

    def get(self, *args: Union[slice, Tuple[int, int], int, Any]) -> AsyncIterator:
        """
        Configure the iteration range in the AsyncMemoryStorage.

        This method sets the `start` and `stop` attributes based on the provided
        arguments, allowing for iteration over a specified range of items in the
        storage. The arguments can be a slice, a tuple of two integers, a single
        integer, or a key present in the storage.

        Parameters
        ----------
        *args : Union[slice, Tuple[int, int], int, Any]
            - If no arguments are provided, the entire storage is selected for iteration.
            - If a slice is provided, the `start` and `stop` are set according to the slice.
            - If a tuple of two integers is provided, it is treated as a range.
            - If a single integer is provided, it specifies the starting index, and
            optionally the stopping index if a second integer is given.
            - If an object in the storage is provided, the `start` and `stop` are set
            to the index of this object in the storage.

        Returns
        -------
        AsyncIterator
            An asynchronous iterator over the specified range of items in the storage.
        """
        if not args:
            self.start = 0
            self.stop = len(self)
        elif isinstance(args[0], slice):
            if args[0].start is None:
                self.start = 0
            elif args[0].start < 0:
                self.start = len(self) + args[0].start
            else:
                self.start = args[0].start
            if args[0].stop is None:
                self.stop = len(self)
            elif args[0].stop < 0:
                self.stop = len(self) + args[0].stop
            else:
                self.stop = args[0].stop
        elif (isinstance(args[0], tuple) and
              isinstance(args[0][0], int) and
              isinstance(args[0][1], int)):
            self.start = args[0][0]
            self.stop = args[0][1]
        elif isinstance(args[0], int):
            self.start = args[0]
            if len(args) == 2:
                self.stop = args[1]
            else:
                self.stop = args[0] + 1
        elif args[0] in self:
            self.start = self.index(args[0])
            self.stop = self.start + 1
        return self.__aiter__()

    def clear(self) -> None:
        """
        Clear all items from the MemoryStorage.

        This method clears the storage by removing all key-value pairs and
        resetting the internal key storage.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        super(AsyncMemoryStorage, self).clear()

    def __aiter__(self) -> 'AsyncMemoryStorage':
        """Return an asynchronous iterator for the AsyncMemoryStorage instance.

        Returns
        -------
        AsyncMemoryStorage
            The instance itself as an asynchronous iterator.
        """
        return self

    async def __anext__(self) -> Tuple[Any, Dict[str, Any]]:
        """
        Return the next item from the asynchronous iterator.

        This method is a coroutine that returns the next item from the
        asynchronous iterator. It is intended to be used in an asynchronous
        for loop.

        Parameters
        ----------
        None

        Returns
        -------
        Tuple[Any, Dict[str, Any]]
            A tuple containing the key and value of the next item in the
            asynchronous iterator.

        Raises
        ------
        StopAsyncIteration
            When the end of the asynchronous iterator is reached.
        """
        await asyncio.sleep(0)
        if self.start >= self.stop:
            raise StopAsyncIteration
        element = self[self.start]
        self.start += 1
        return element

if __name__ == "__main__":
    from utils import asyncio_run
    from bgw_regex import stdout_to_cmds, cmds_to_rtpsessions
    from storage import AsyncMemoryStorage
    stdout = '''#BEGIN\nshow rtp-stat detailed 00002\r\n\r\nSession-ID: 1\r\nStatus: Terminated, QOS: Ok, EngineId: 10\r\nStart-Time: 2024-11-04,10:06:10, End-Time: 2024-11-04,10:07:10\r\nDuration: 00:00:00\r\nCName: gwp@10.10.48.58\r\nPhone: \r\nLocal-Address: 10.10.48.58:2052 SSRC 1653399062\r\nRemote-Address: 10.10.48.192:35000 SSRC 2704961869 (0)\r\nSamples: 0 (5 sec)\r\n\r\nCodec:\r\nG711U 200B 20mS srtpAesCm128HmacSha180, Silence-suppression(Tx/Rx) Disabled/Disabled, Play-Time 4.720sec, Loss 0.8% #0, Avg-Loss 0.8%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 22mS, Max-Jbuf-Delay 22mS\r\n\r\nReceived-RTP:\r\nPackets 245, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, Jitter 2mS #0, Avg-Jitter 2mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 0, Flow-Label 2\r\n\r\nTransmitted-RTP:\r\nVLAN 0, DSCP 46, L2Pri 0, RTCP 10, Flow-Label 0\r\n\r\nRemote-Statistics:\r\nLoss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS\r\n\r\nEcho-Cancellation:\r\nLoss 0dB #2, Len 0mS\r\n\r\nRSVP:\r\nStatus Unused, Failures 0\n#END'''
    stdout += '''#BEGIN\nshow rtp-stat detailed 00001\r\n\r\nSession-ID: 1\r\nStatus: Terminated, QOS: Ok, EngineId: 10\r\nStart-Time: 2024-11-04,10:06:07, End-Time: 2024-11-04,10:07:07\r\nDuration: 00:00:00\r\nCName: gwp@10.10.48.58\r\nPhone: \r\nLocal-Address: 10.10.48.58:2052 SSRC 1653399062\r\nRemote-Address: 10.10.48.192:35000 SSRC 2704961869 (0)\r\nSamples: 0 (5 sec)\r\n\r\nCodec:\r\nG711U 200B 20mS srtpAesCm128HmacSha180, Silence-suppression(Tx/Rx) Disabled/Disabled, Play-Time 4.720sec, Loss 0.8% #0, Avg-Loss 0.8%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 22mS, Max-Jbuf-Delay 22mS\r\n\r\nReceived-RTP:\r\nPackets 245, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, Jitter 2mS #0, Avg-Jitter 2mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 0, Flow-Label 2\r\n\r\nTransmitted-RTP:\r\nVLAN 0, DSCP 46, L2Pri 0, RTCP 10, Flow-Label 0\r\n\r\nRemote-Statistics:\r\nLoss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS\r\n\r\nEcho-Cancellation:\r\nLoss 0dB #2, Len 0mS\r\n\r\nRSVP:\r\nStatus Unused, Failures 0\n#END'''

    async def main():
        storage = AsyncMemoryStorage()
        rtpsessions = cmds_to_rtpsessions(stdout_to_cmds(stdout))
        await storage.add(rtpsessions)
        async for rtpsession in storage.get():
            print(rtpsession)
            print('----------------------')
        storage.clear()
        print(storage)

    asyncio_run(main())
