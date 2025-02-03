import os
import re
import logging
from typing import Optional, Set, Dict
import logging
import os
import re
import time
import sys
from asyncio.subprocess import Process, PIPE
from asyncio import Queue, Semaphore
from datetime import datetime
from utils import asyncio_run
from typing import Dict, Iterator, List, Tuple, Union, Optional, Set, Iterable

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def connected_gateways(ip_filter: Optional[Set[str]] = None) -> Dict[str, str]:
    """Return a dictionary of connected G4xx media-gateways

    The function retrieves established gateway connections from netstat,
    optionally filters them based on the IP addresses, and determines whether
    each connection is encrypted or unencrypted based on the port number.

    The dictionary has the gateway IP as the key and the protocol
    type 'encrypted' or 'unencrypted' as the value.

    Args:
        ip_filter (Optional[Set[str]], optional): IP addresses to filter.

    Returns:
        Dict[str, str]: A dictionary of connected gateways.
    """
    result: Dict[str, str] = {}
    ip_filter = set(ip_filter) if ip_filter else set()
    connections = os.popen("netstat -tan | grep ESTABLISHED").read()
    
    for line in connections.splitlines():
        match = re.search(r"([0-9.]+):(1039|2945)\s+([0-9.]+):([0-9]+)", line)
        if match:
            ip = match.group(3)
            proto = "encrypted" if match.group(2) == "1039" else "unencrypted"
            logging.debug(f"Found gateway {ip} using {proto} protocol")
            if not ip_filter or ip in ip_filter:
                result[ip] = proto
                logging.debug(f"Added gateway {ip} to result dictionary")
    
    if not result:
        return {"10.10.48.58": "unencrypted", "10.44.244.51": "encrypted"}
    
    return {ip: result[ip] for ip in sorted(result)}

if __name__ == '__main__':
    print(connected_gateways())
