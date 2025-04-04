
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import asyncio
import atexit
import base64
import _curses, curses, curses.ascii, curses.panel
import enum
import functools
import json
import logging
import os
import re
import sys
import textwrap
import time
import zlib
from abc import ABC, abstractmethod
from asyncio import coroutines
from asyncio import events
from asyncio import tasks
from asyncio import Lock, Queue, Semaphore
from bisect import insort_left
from collections import deque
from collections.abc import MutableMapping
from typing import Any, Callable, Coroutine, Optional, Tuple
from subprocess import CalledProcessError, call
from datetime import datetime
from typing import AsyncIterator, Iterable, Iterator, Optional, Tuple, Union, TypeVar, Any, Dict, List, Set

logger = logging.getLogger(__name__)

############################ CONSTATS, VARIABLES ############################
LOG_FORMAT = "%(asctime)s - %(levelname)8s - %(message)s [%(filename)s:%(lineno)s]"

script_template = '''
eJzdGWtv28jxu37FHE0f/GJsC7gPdZs+kOaQa5C74JwWKCSFoMmVxAtF0rvL2Aar/34z+yCXD0nOtU
2BEoLE3Z2d98zOjiZH31xWgl/epfkleyxZLCdH+x74wDZlFkkG/4h4Gt1lTMDeDZOJYBLWhZBQ0/dW
jSvBeB5tGNT2Tc+XkRAPCdT6V89xWYZCRrjfvun5LBIyDwWLBdTtu16Li80myhNcqaG2gy1szc5iFS
7TDKlrkUOc2E72C34ErxXsc+U2gst0w4pKwvWVlo8Xm1KCNz89Am8ScR49gctvqKfqGjltV5XcTIi0
yDsQtLbKirsoC1OUdZalQi4mJB1pFa4mk3SJkLM0XxbAHnFVNLIv4NtvwW80kTPwLhP2+TKvsszbbn
HbBPDRCBSIQdDsWbRQ9CiYhGUMfaOBUavIKX5Q1WGaS7J2BsHSoX11SPWk/fe8iFlS8YN6V6pHPccg
i/AXUeRKV5ZTrS7tj6uHUPkg/VabO9QYuRFqmuV9gwwtoLCRARQJr649NROVJcsTMzn3iM7cu4G55+
vXCxiFM6wY0Ga0B1ox7MCb8Y4djWBmhzPescMqgDZY4ZYFZ1G8xvEn9gSfo6xiqNmZVtFq4MYL1z16
6H3EYHhReFo+0FU6qp0JydN8Bfi94elqLcHXSHDDYsj5drtDINeEXyTU0Pb/I8G2W42IM1nxXENTZG
lv3zC+YmGmYrSu6fca6HvaOr/JNJjrWQKzuMhjzKq+BlU/00UDh4FWZRJziii4hKDK0/sKA9tuX3Q4
0cAtL3HGojzEvFdi6qtr/dLlo4wk5QKcmvN5Pg/mgXwqGdxj1MJ9lUooOIgyihmQWXAS2ZVpjgpFUH
hx/qe3Rp+crUR1B0GUZeBbrL6h7Xmg3xq6GXKPqVKUGdJowOa514quk3TI2ab4TIrKeJSvKKmprVeA
NgmuW3CDY/ZLkSLh3uYWs8sn+h5qw28UNKehHoVMxFHJkvC+KiQTA3sMnWZ0HxLmDukdZtrgUWuPx0
GO1JL0xfQ8M4OO6flmr57Th6kbG0Yb7lTjhxXnLJfWSXxzEuPw5K5aLhk/7WwxoWChu7sbSOMS9Hhn
1mGCALyvxkGrG9R+Z5bOP8vSOMOOk7/4uhwf5u0rMyQyxkq4/iImbanV4xNRCxAyYZyD90HDeL/vgJ
j48Lw+Widl2/jrpDYTe50ocyM0Y0tpww5ssCzaAMTjJYximX5moVPHjdQrFKllxAWzJ1EoKkTGn0JK
ShdtCdPw6xSENGVPOQK32W9GWD2xLh7ojAtUjW0POtBsUQrROcxVqy4KMaGhSfDt4+wq+N3inDIaoe
/VhX0F7hbDbO/sxEJFpKsmd1n+UE9o04jLMKG7iH4lB6DkrOfohWZ66LQLKu2gTjYosncsLuzHA99B
6zt42yILpxsmFjs8xmZcpNO1NmcxuXzH2nXtXmXq6dVWPV/kApAKxfN1uNLMT0d8grOlWlMCzdgji0
HJ6Z0f/zM43gTHycXxm5vjdzfHtx4E6Bs5ukYAvsMefTlH5b/rZYQZplf/b26mOPftkrpcBd6QX8uz
Rabt0nFLdMiGVINwMYoFPcBFRI7QNfjQRfwOZd8FH9LQQh2gMi7kfzf0eiE4MnxGcO7xl7pO8z3168
eT+e35KcDJ/Oxfc6FecHyhvufi3P6+OPMN/Y5ftyWrIgIhKgjuC7HH75R5uoo+IqSkXQXEiyzD2hML
UE6Vs1yTCz5KDPanbnC1LvoHV+PjkdX44Wjm0AnDNeE5XBNFz82RwDLB9iJ3MIwd8vaQpZxDFuyQ9J
oRSUEji9a+q/nFZAcznVLhNecFv4EflFWMvyYFVtZ5IQEH8frG2MypJrqVhG58aP8aBl9dqwmlSOeS
dgSvihwtJ5XdjP2pohCQ5mhNVhaYYUkQFHVTtjeEZuqaqpQi/gR4I0C/0lSCJuQGqX4xRDEdopgeRk
GsbzCQmGK9x6J2OIfJP0I7mnZdzqjxepehzPoVuGo+3EN6F+EN7TbmKV5JDveQjm7L6AHhb99QWZ5j
YYuZYSLUpBBrCO4hKOAWbRPLN4WQb9nTqzWLP6GpXuYFrf1dMP4Wz9CclsX3acZeNj028G3n88+qNY
T03mBxmLE+we6tyntPndGCJzfqUmOuYbpdiueniZSRUlj5dpAXOXtQSa1xc4V+WBezRzy7p9995yZO
Viz/kyh1U9AV7uw945tUpWBIWJ6y5Mx7DsV221/VrgNytNdS6zqvHyXHihdW6OgP0ROoviCaA8y5s8
QN9kLcFCQns49zsTg/DU7myfnpbH5CSXnkDkRdiEGvUbdmbatPlQhe94SxSxZm0gsEFwYTDsrRotRc
70BqjtKWlR2INZxGPTl6FZUYdKztkTZNeN0xPVBPLggFnUuo5Z8/vKczTWIOT7GmRLY5u68wE7DEyN
B0+tu0+LOqnG01bA5qqiac8rZfW8/GS26noDWJ6y/qtrMP+fCaNhu9vRmE76gbl+xDqPp1SQeh28Lz
R9geIeak1iFCVbu4Vwl6bI3ewMHIzt4Jbctj2zZr93oXWLOPlyqtC7VF2+Dct82zkUtCwmSUUh3jFH
1NS8vFQdAVqi+mQ1klxd+El6KA841YdSlo5Roa37yEq/ES91nJEJJK9Qbmz2HJ63UpBtnMPjvKqpZ5
o4xeOug/4/80nbTGPrX9jt9Ueask8gOWuuQmcs2LarWG5m8GT2VbXuVAzjmxTmqWm95J45lHAyNbkE
4r96BruLt6DnDA8F9o8IaQt/twGpjxOeYb/n14YmkNDdYzx08as770Un0Jf7v96UdT7U6UhDPzL9qC
/s+kYoN4pt7mr8uCdPY='''

script_template_test = '''
eJxtUcFugzAMvfMVVlSkdgMJWLsDU4+TtsNO22UaE2Lg0kiQIBJEJ5R/n0NoO03zAez3/PIcx1Oo4S
iVhsl+jWfrQWEvihZhOmcO7wqlxgom93dYr7tc6YL058zhTaG0yBWWCqZr7rhStm0hKmImmM6FAbMo
ZZ0feEPueOqw1DkBxnNm1CjbZ6Hhg7ie9FzotUXXG7iB7caYT+psEDtILmOQMwqrwBKqQiOwW/899N
vQrwL/KfVfUv+VkY4f6MDV1WO/h9gYwjyg6AatIBRS4NhwgaB0hX0P7HEe8o23KAfNHgBPXEOy23l0
nVnDpilj9ZiLof3CPmMpZCyK4owF4HDar0NX9gkc7rI/4OUyC/OrtvR5k5a1nuooR1DfSmPrBI0sC8
2lSGFxnzv6QQgu6rCU4sDrfzqNsb3z86JShF4ckijZhnES3kVBHKfRfRrvgnneIKK4rtIduqjhL2co
mPcDP4naQQ=='''

CONFIG = {
    "username": "root",
    "passwd": "cmb@Dm1n",
    "timeout": 15,
    "polling_secs": 5,
    "max_polling": 20,
    "lastn_secs": 30,
    "loglevel": "ERROR",
    "logfile": "bgw.log",
    "expect_log": "expect_log",
    "ip_filter": None,
    "storage": None,
    "color_scheme": "default",
    "storage_maxlen": None,
    "script_template": script_template,
    "discovery_commands": [
        "set utilization cpu",
        "show announcements files",
        "show running-config",
        "show system",
        "show faults",
        "show capture",
        "show temp",
        "show sla-monitor",
        "show lldp config",
        "show port",
        "show mg list",
    ],
    "query_commands": [
        "show voip-dsp",
        "show rtp-stat summary",
    ]
}

#System
#+---+-------------+---------------+------------+-------------+-----+--+--------+
#│BGW│    Name     |     LAN IP    │  LAN MAC   |   Uptime    |Model│HW│Firmware│
#+---+-------------+---------------+------------+-------------+-----+--+--------+
#|001|             |192.168.111.111|3475c764ef08|153d05h23m06s| g430│1A│43.11.12│
#+---+-------------+---------------+------------+-------------+-----+--+--------+

SYSTEM_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'normal',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'gw_name',
        'column_name': 'Name',
        'column_color': 'normal',
        'column_fmt_spec': '>13',
        'column_xpos': 5,
    },
    {
        'column_attr': 'host',
        'column_name': 'LAN IP',
        'column_color': 'normal',
        'column_fmt_spec': '>15',
        'column_xpos': 19,
    },
    {
        'column_attr': 'mac',
        'column_name': 'LAN MAC',
        'column_color': 'normal',
        'column_fmt_spec': '>12',
        'column_xpos': 35,
    },
    {
        'column_attr': 'uptime',
        'column_name': 'Uptime',
        'column_color': 'normal',
        'column_fmt_spec': '>13',
        'column_xpos': 48,
    },
    {
        'column_attr': 'model',
        'column_name': 'Model',
        'column_color': 'normal',
        'column_fmt_spec': '>5',
        'column_xpos': 62,
    },
    {
        'column_attr': 'hw',
        'column_name': 'HW',
        'column_color': 'normal',
        'column_fmt_spec': '>2',
        'column_xpos': 68,
    },
    {
        'column_attr': 'fw',
        'column_name': 'Firmware',
        'column_color': 'normal',
        'column_fmt_spec': '>8',
        'column_xpos': 71,
    },
]

#Hardware
#+---+----------+--------+------------+-----+----+------+---+----+-------+------+
#│BGW│ Location |  Temp  |   Serial   |Chass|Main|Memory│DSP│Anno|C.Flash|Faults|
#+---+----------+--------+------------+-----+----+------+---+----+-------+------+
#|001|          |42C/108F|13TG01116522|   1A|  3A| 256MB│160│ 999|    1GB|     4|
#+---+----------+--------+------------+-----+----+------+---+----+-------+------+

HW_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'normal',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'location',
        'column_name': 'Location',
        'column_color': 'normal',
        'column_fmt_spec': '>10',
        'column_xpos': 5,
    },
    {
        'column_attr': 'temp',
        'column_name': 'Temp',
        'column_color': 'normal',
        'column_fmt_spec': '>8',
        'column_xpos': 16,
    },
    {
        'column_attr': 'serial',
        'column_name': 'Serial',
        'column_color': 'normal',
        'column_fmt_spec': '>12',
        'column_xpos': 25,
    },
    {
        'column_attr': 'chassis_hw',
        'column_name': 'Chass',
        'column_color': 'normal',
        'column_fmt_spec': '>5',
        'column_xpos': 38,
    },
    {
        'column_attr': 'mainboard_hw',
        'column_name': 'Main',
        'column_color': 'normal',
        'column_fmt_spec': '>4',
        'column_xpos': 44,
    },
    {
        'column_attr': 'memory',
        'column_name': 'Memory',
        'column_color': 'normal',
        'column_fmt_spec': '>6',
        'column_xpos': 49,
    },
    {
        'column_attr': 'dsp',
        'column_name': 'DSP',
        'column_color': 'normal',
        'column_fmt_spec': '>3',
        'column_xpos': 56,
    },
    {
        'column_attr': 'announcements',
        'column_name': 'Anno',
        'column_color': 'normal',
        'column_fmt_spec': '>4',
        'column_xpos': 60,
    },
    {
        'column_attr': 'comp_flash',
        'column_name': 'C.Flash',
        'column_color': 'normal',
        'column_fmt_spec': '>7',
        'column_xpos': 65,
    },
    {
        'column_attr': 'faults',
        'column_name': 'Faults',
        'column_color': 'normal',
        'column_fmt_spec': '>6',
        'column_xpos': 73,
    },
]

#Module
#+---+------+------+------+------+------+------+------+------+--------+----+----+
#│BGW│  v1  |  v2  |  v3  |  v4  |  v5  |  v6  |  v7  |  v8  | v10 hw |PSU1|PSU2|
#+---+------+------+------+------+------+------+------+------+--------+----+----+
#|001|S8300E│MM714B│MM714B│MM714B│MM714B│MM714B│S8300E│S8300E│      3A|400W│400W|
#+---+------+------+------+------+------+------+------+------+--------+----+----+

MODULE_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'normal',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'mm_v1',
        'column_name': 'v1',
        'column_color': 'normal',
        'column_fmt_spec': '>6',
        'column_xpos': 5,
    },
    {
        'column_attr': 'mm_v2',
        'column_name': 'v2',
        'column_color': 'normal',
        'column_fmt_spec': '>6',
        'column_xpos': 12,
    },
    {
        'column_attr': 'mm_v3',
        'column_name': 'v3',
        'column_color': 'normal',
        'column_fmt_spec': '>6',
        'column_xpos': 19,
    },
    {
        'column_attr': 'mm_v4',
        'column_name': 'v4',
        'column_color': 'normal',
        'column_fmt_spec': '>6',
        'column_xpos': 27,
    },
    {
        'column_attr': 'mm_v5',
        'column_name': 'v5',
        'column_color': 'normal',
        'column_fmt_spec': '>6',
        'column_xpos': 33,
    },
    {
        'column_attr': 'mm_v6',
        'column_name': 'v6',
        'column_color': 'normal',
        'column_fmt_spec': '>6',
        'column_xpos': 40,
    },
    {
        'column_attr': 'mm_v7',
        'column_name': 'v7',
        'column_color': 'normal',
        'column_fmt_spec': '>6',
        'column_xpos': 47,
    },
    {
        'column_attr': 'mm_v8',
        'column_name': 'v8',
        'column_color': 'normal',
        'column_fmt_spec': '>6',
        'column_xpos': 54,
    },
    {
        'column_attr': 'mm_v10',
        'column_name': 'v10 hw',
        'column_color': 'normal',
        'column_fmt_spec': '>8',
        'column_xpos': 61,
    },
    {
        'column_attr': 'psu1',
        'column_name': 'PSU1',
        'column_color': 'normal',
        'column_fmt_spec': '>4',
        'column_xpos': 70,
    },
    {
        'column_attr': 'psu2',
        'column_name': 'PSU2',
        'column_color': 'normal',
        'column_fmt_spec': '>4',
        'column_xpos': 75,
    },
]

#Port
#+---+----+---------+--------+---------+----+---------+--------+----+----+------+
#|BGW|Port| Status  |  Neg.  |Spd.|Dup.|Port| Status  |  Neg.  |Spd.|Dup.|Redund|
#+---+----+---------+--------+----+----+----+---------+--------+----+----+------+
#|001|10/4|connected| enabled|100M|full|10/5|  no link| enabled|100M|half|   5/4|
#+---+----+---------+--------+----+----+----+---------+--------+----+----+------+

PORT_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'normal',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'port1',
        'column_name': 'Port',
        'column_color': 'normal',
        'column_fmt_spec': '>4',
        'column_xpos': 5,
    },
    {
        'column_attr': 'port1_status',
        'column_name': 'Status',
        'column_color': 'normal',
        'column_fmt_spec': '>9',
        'column_xpos': 10,
    },
    {
        'column_attr': 'port1_neg',
        'column_name': 'Neg',
        'column_color': 'normal',
        'column_fmt_spec': '>8',
        'column_xpos': 20,
    },
    {
        'column_attr': 'port1_speed',
        'column_name': 'Spd.',
        'column_color': 'normal',
        'column_fmt_spec': '>4',
        'column_xpos': 29,
    },
    {
        'column_attr': 'port1_duplex',
        'column_name': 'Dup.',
        'column_color': 'normal',
        'column_fmt_spec': '>4',
        'column_xpos': 34,
    },
    {
        'column_attr': 'port2',
        'column_name': 'Port',
        'column_color': 'normal',
        'column_fmt_spec': '>4',
        'column_xpos': 39,
    },
    {
        'column_attr': 'port2_status',
        'column_name': 'Status',
        'column_color': 'normal',
        'column_fmt_spec': '>9',
        'column_xpos': 44,
    },
    {
        'column_attr': 'port2_neg',
        'column_name': 'Neg',
        'column_color': 'normal',
        'column_fmt_spec': '>8',
        'column_xpos': 54,
    },
    {
        'column_attr': 'port2_speed',
        'column_name': 'Spd.',
        'column_color': 'normal',
        'column_fmt_spec': '>4',
        'column_xpos': 63,
    },
    {
        'column_attr': 'port2_duplex',
        'column_name': 'Dup.',
        'column_color': 'normal',
        'column_fmt_spec': '>4',
        'column_xpos': 68,
    },
    {
        'column_attr': 'port_redu',
        'column_name': 'Redund',
        'column_color': 'normal',
        'column_fmt_spec': '>6',
        'column_xpos': 73,
    },
]

#Service
#+---+---------+---------------+----+---------+--------+---------------+--------+
#|BGW|RTP-Stats|Capture-Service|SNMP|SNMP-Trap| SLAMon | SLAMon Server |  LLDP  |
#+---+---------+---------------+----+---------+--------+---------------+--------+
#|001| disabled|       disabled|v2&3|  enabled| enabled|101.101.111.198|disabled|
#+---+---------+---------------+----+---------+--------+---------------+--------+

SERVICE_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'normal',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'rtp_stat_service',
        'column_name': 'RTP-Stats',
        'column_color': 'normal',
        'column_fmt_spec': '>9',
        'column_xpos': 5,
    },
    {
        'column_attr': 'capture_service',
        'column_name': 'Capture-Service',
        'column_color': 'normal',
        'column_fmt_spec': '>15',
        'column_xpos': 15,
    },
    {
        'column_attr': 'snmp',
        'column_name': 'SNMP',
        'column_color': 'normal',
        'column_fmt_spec': '>4',
        'column_xpos': 31,
    },
    {
        'column_attr': 'snmp_trap',
        'column_name': 'SNMP-Trap',
        'column_color': 'normal',
        'column_fmt_spec': '>9',
        'column_xpos': 36,
    },
    {
        'column_attr': 'slamon_service',
        'column_name': 'SLAMon',
        'column_color': 'normal',
        'column_fmt_spec': '>8',
        'column_xpos': 46,
    },
    {
        'column_attr': 'sla_server',
        'column_name': 'SLAMon Server',
        'column_color': 'normal',
        'column_fmt_spec': '>15',
        'column_xpos': 55,
    },
    {
        'column_attr': 'lldp',
        'column_name': 'LLDP',
        'column_color': 'normal',
        'column_fmt_spec': '>8',
        'column_xpos': 71,
    },
]

#Status
#+---+-----------+-----------+--------+----------+-----+-------+-------+--------+
#|BGW|Act.Session|Tot.Session|InUseDSP|CPU 5s/60s| RAM |PollSec| Polls |LastSeen|
#+---+-----------+-----------+--------+----------+-----+-------+-------+--------+
#|001|        0/0| 32442/1443|     320| 100%/100%|  45%| 120.32|      3|11:02:11|
#+---+-----------+-----------+--------+----------+-----+-------+-------+--------+

STATUS_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'normal',
        'column_fmt_spec': '>3',
        'column_xpos': 1,
    },
    {
        'column_attr': 'active_session',
        'column_name': 'Act.Session',
        'column_color': 'normal',
        'column_fmt_spec': '>11',
        'column_xpos': 5,
    },
    {
        'column_attr': 'total_session',
        'column_name': 'Tot.Session',
        'column_color': 'normal',
        'column_fmt_spec': '>12',
        'column_xpos': 17,
    },
    {
        'column_attr': 'inuse_dsp',
        'column_name': 'InUseDSP',
        'column_color': 'normal',
        'column_fmt_spec': '>8',
        'column_xpos': 29,
    },
    {
        'column_attr': 'cpu_util',
        'column_name': 'CPU 5s/60s',
        'column_color': 'normal',
        'column_fmt_spec': '>10',
        'column_xpos': 38,
    },
    {
        'column_attr': 'ram_util',
        'column_name': 'RAM',
        'column_color': 'normal',
        'column_fmt_spec': '>5',
        'column_xpos': 49,
    },
    {
        'column_attr': 'avg_poll_secs',
        'column_name': 'PollSec',
        'column_color': 'normal',
        'column_fmt_spec': '>7',
        'column_xpos': 55,
    },
    {
        'column_attr': 'polls',
        'column_name': 'Polls',
        'column_color': 'normal',
        'column_fmt_spec': '>7',
        'column_xpos': 63,
    },
    {
        'column_attr': 'last_seen_time',
        'column_name': 'LastSeen',
        'column_color': 'normal',
        'column_fmt_spec': '>8',
        'column_xpos': 71,
    },
]

#RTP-Stat
#+--------+--------+---+---------------+-----+---------------+-----+------+-----+
#|  Start |   End  |BGW| Local-Address |LPort| Remote-Address|RPort| Codec| QoS | 
#+--------+--------+---+---------------+-----+---------------+-----+------+-----+
#|11:09:07|11:11:27|001|192.168.111.111|55555|100.100.100.100|55555| G711U|Fault|
#+--------+--------+---+---------------+-----+---------------+-----+------+-----+

RTPSTAT_ATTRS = [
    {
        'column_attr': 'start_time',
        'column_name': 'Start',
        'column_color': 'normal',
        'column_fmt_spec': '>8',
        'column_xpos': 1,
    },
    {
        'column_attr': 'end_time',
        'column_name': 'End',
        'column_color': 'normal',
        'column_fmt_spec': '>8',
        'column_xpos': 10,
    },
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'column_color': 'normal',
        'column_fmt_spec': '>3',
        'column_xpos': 19,
    },
    {
        'column_attr': 'local_addr',
        'column_name': 'Local-Address',
        'column_color': 'normal',
        'column_fmt_spec': '>15',
        'column_xpos': 23,
    },
    {
        'column_attr': 'local_port',
        'column_name': 'LPort',
        'column_color': 'normal',
        'column_fmt_spec': '>5',
        'column_xpos': 39,
    },
    {
        'column_attr': 'remote_addr',
        'column_name': 'Remote-Address',
        'column_color': 'normal',
        'column_fmt_spec': '>15',
        'column_xpos': 45,
    },
    {
        'column_attr': 'remote_port',
        'column_name': 'RPort',
        'column_color': 'normal',
        'column_fmt_spec': '>5',
        'column_xpos': 61,
    },
    {
        'column_attr': 'codec',
        'column_name': 'Codec',
        'column_color': 'normal',
        'column_fmt_spec': '>6',
        'column_xpos': 67,
    },
    {
        'column_attr': 'qos',
        'column_name': 'QoS',
        'column_color': 'normal',
        'column_fmt_spec': '>5',
        'column_xpos': 74,
    },
]


RTP_DETAILED_PATTERNS = (
    r'.*?Session-ID: (?P<session_id>\d+)',
    r'.*?Status: (?P<status>\S+),',
    r'.*?QOS: (?P<qos>\S+),',
    r'.*?EngineId: (?P<engineid>\d+)',
    r'.*?Start-Time: (?P<start_time>\S+),',
    r'.*?End-Time: (?P<end_time>\S+)',
    r'.*?Duration: (?P<duration>\S+)',
    r'.*?CName: (?P<cname>\S+)',
    r'.*?Phone: (?P<phone>.*?)\s+',
    r'.*?Local-Address: (?P<local_addr>\S+):',
    r'.*?(?P<local_port>\d+)',
    r'.*?SSRC (?P<local_ssrc>\d+)',
    r'.*?Remote-Address: (?P<remote_addr>\S+):',
    r'.*?(?P<remote_port>\d+)',
    r'.*?SSRC (?P<remote_ssrc>\d+)',
    r'.*?(?P<remote_ssrc_change>\S+)',
    r'.*?Samples: (?P<samples>\d+)',
    r'.*?(?P<sampling_interval>\(.*?\))',
    r'.*?Codec:\s+(?P<codec>\S+)',
    r'.*?(?P<codec_psize>\S+)',
    r'.*?(?P<codec_ptime>\S+)',
    r'.*?(?P<codec_enc>\S+),',
    r'.*?Silence-suppression\(Tx/Rx\) (?P<codec_silence_suppr_tx>\S+)/',
    r'.*?(?P<codec_silence_suppr_rx>\S+),',
    r'.*?Play-Time (?P<codec_play_time>\S+),',
    r'.*?Loss (?P<codec_loss>\S+)',
    r'.*?#(?P<codec_loss_events>\d+),',
    r'.*?Avg-Loss (?P<codec_avg_loss>\S+),',
    r'.*?RTT (?P<codec_rtt>\S+)',
    r'.*?#(?P<codec_rtt_events>\d+),',
    r'.*?Avg-RTT (?P<codec_avg_rtt>\S+),',
    r'.*?JBuf-under/overruns (?P<codec_jbuf_underruns>\S+)/',
    r'.*?(?P<codec_jbuf_overruns>\S+),',
    r'.*?Jbuf-Delay (?P<codec_jbuf_delay>\S+),',
    r'.*?Max-Jbuf-Delay (?P<codec_max_jbuf_delay>\S+)',
    r'.*?Packets (?P<rx_rtp_packets>\d+),',
    r'.*?Loss (?P<rx_rtp_loss>\S+)',
    r'.*?#(?P<rx_rtp_loss_events>\d+),',
    r'.*?Avg-Loss (?P<rx_rtp_avg_loss>\S+),',
    r'.*?RTT (?P<rx_rtp_rtt>\S+)',
    r'.*?#(?P<rx_rtp_rtt_events>\d+),',
    r'.*?Avg-RTT (?P<rx_rtp_avg_rtt>\S+),',
    r'.*?Jitter (?P<rx_rtp_jitter>\S+)',
    r'.*?#(?P<rx_rtp_jitter_events>\d+),',
    r'.*?Avg-Jitter (?P<rx_rtp_avg_jitter>\S+),',
    r'.*?TTL\(last/min/max\) (?P<rx_rtp_ttl_last>\d+)/',
    r'.*?(?P<rx_rtp_ttl_min>\d+)/',
    r'.*?(?P<rx_rtp_ttl_max>\d+),',
    r'.*?Duplicates (?P<rx_rtp_duplicates>\d+),',
    r'.*?Seq-Fall (?P<rx_rtp_seqfall>\d+),',
    r'.*?DSCP (?P<rx_rtp_dscp>\d+),',
    r'.*?L2Pri (?P<rx_rtp_l2pri>\d+),',
    r'.*?RTCP (?P<rx_rtp_rtcp>\d+),',
    r'.*?Flow-Label (?P<rx_rtp_flow_label>\d+)',
    r'.*?VLAN (?P<tx_rtp_vlan>\d+),',
    r'.*?DSCP (?P<tx_rtp_dscp>\d+),',
    r'.*?L2Pri (?P<tx_rtp_l2pri>\d+),',
    r'.*?RTCP (?P<tx_rtp_rtcp>\d+),',
    r'.*?Flow-Label (?P<tx_rtp_flow_label>\d+)',
    r'.*?Loss (?P<rem_loss>\S+)',
    r'.*#(?P<rem_loss_events>\S+),',
    r'.*?Avg-Loss (?P<rem_avg_loss>\S+),',
    r'.*?Jitter (?P<rem_jitter>\S+)',
    r'.*?#(?P<rem_jitter_events>\S+),',
    r'.*?Avg-Jitter (?P<rem_avg_jitter>\S+)',
    r'.*?Loss (?P<ec_loss>\S+)',
    r'.*?#(?P<ec_loss_events>\S+),',
    r'.*?Len (?P<ec_len>\S+)',
    r'.*?Status (?P<rsvp_status>\S+),',
    r'.*?Failures (?P<rsvp_failures>\d+)',
)

reDetailed = re.compile(r''.join(RTP_DETAILED_PATTERNS), re.M|re.S|re.I)

COLOR_SCHEMES = {
    'default': {
        'normal': 0,        # white
        'bold': 2097152,    # white bold
        'dim': 1048576,     # white dim
        'standout': 65536,  # white standout
    },

    'blue': {
        'normal': 31744,    # blue
        'bold': 2128896,    # blue bold
        'dim': 1080320,     # blue dim
        'standout': 97280,  # blue standout
    },

    'green': {
        'normal': 12288,    # green
        'bold': 2109440,    # green bold
        'dim': 1060864,     # green dim
        'standout': 77824,  # green standout
    },

    'orange': {
        'normal': 53504,    # orange
        'bold': 2150656,    # orange bold
        'dim': 1102080,     # orange dim
        'standout': 119040, # orange standout
    }
}

################################## CLASSES ##################################
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

class BGW():
    def __init__(self,
        host: str,
        proto: str = '',
        polling_secs = 10,
        gw_name: str = '',
        gw_number: str = '',
        show_announcements_files = '',
        show_capture: str = '',
        show_faults: str = '',
        show_lldp_config: str = '',
        show_mg_list: str = '',
        show_port: str = '',
        show_rtp_stat_summary: str = '',
        show_running_config: str = '',
        show_sla_monitor: str = '',
        show_system: str = '',
        show_temp: str = '',
        show_utilization: str = '',
        show_voip_dsp: str = '',
        **kwargs,
    ) -> None:
        self.host = host
        self.proto = proto
        self.polling_secs = polling_secs
        self.gw_name = gw_name
        self.gw_number = gw_number
        self.polls = 0
        self.avg_poll_secs = 0
        self.last_seen = None
        self.show_announcements_files = show_announcements_files
        self.show_capture = show_capture
        self.show_faults = show_faults
        self.show_lldp_config = show_lldp_config
        self.show_mg_list = show_mg_list
        self.show_port = show_port
        self.show_rtp_stat_summary = show_rtp_stat_summary
        self.show_running_config = show_running_config
        self.show_sla_monitor = show_sla_monitor
        self.show_system = show_system
        self.show_temp = show_temp
        self.show_utilization = show_utilization
        self.show_voip_dsp = show_voip_dsp
        self.queue = Queue()
        self._active_session = None
        self._announcements = None
        self._capture_service = None
        self._chassis_hw = None
        self._comp_flash = None
        self._cpu_util = None
        self._dsp = None
        self._faults = None
        self._fw = None
        self._hw = None
        self._inuse_dsp = None
        self._last_seen_time = None
        self._lldp = None
        self._location = None
        self._mac = None
        self._mainboard_hw = None
        self._memory = None
        self._mm_groupdict = None
        self._mm_v1 = None
        self._mm_v2 = None
        self._mm_v3 = None
        self._mm_v4 = None
        self._mm_v5 = None
        self._mm_v6 = None
        self._mm_v7 = None
        self._mm_v8 = None
        self._mm_v10 = None
        self._model = None
        self._port1 = None
        self._port1_status = None
        self._port1_neg = None
        self._port1_duplex = None
        self._port1_speed = None
        self._port2 = None
        self._port2_status = None
        self._port2_neg = None
        self._port2_duplex = None
        self._port2_speed = None
        self._port_redu = None
        self._psu1 = None
        self._psu2 = None
        self._ram_util = None
        self._rtp_stat_service = None
        self._serial = None
        self._slamon_service = None
        self._sla_server = None
        self._snmp = None
        self._snmp_trap = None
        self._temp = None
        self._total_session = None
        self._uptime = None

    @property
    def active_session(self) -> str:
        """
        Returns the Active Session column from the RTP-Stat summary.
        """
        if self.show_rtp_stat_summary:
            m = re.search(r'nal\s+\S+\s+(\S+)', self.show_rtp_stat_summary)
            return m.group(1) if m else "?/?"
        return "NA"

    @property
    def announcements(self) -> str:
        """
        Returns the number of announcement files as a string.
        """
        if self.show_announcements_files:
            if self._announcements is None:
                m = re.findall(
                    r"announcement file", self.show_announcements_files
                )
                self._announcements = str(len(m))
            return self._announcements
        return "NA"

    @property
    def capture_service(self) -> str:
        """
        Returns the capture service admin and running state.
        """
        if self.show_capture:
            if self._capture_service is None:
                m = re.search(
                    r' service is (\w+) and (\w+)', self.show_capture
                )
                admin_state = m.group(1) if m else "?"
                running_state = m.group(2) if m else "?"
                if admin_state == "disabled":
                    self._capture_service = "disabled"
                else:
                    self._capture_service = f"{admin_state}/{running_state}"
            return self._capture_service
        return "NA"

    @property
    def chassis_hw(self) -> str:
        """
        Returns the chassis hardware version as a string.
        """
        if self.show_system:
            if self._chassis_hw is None:

                vintage_search = re.search(
                    r'Chassis HW Vintage\s+:\s+(\S+)', self.show_system
                )
                vintage = vintage_search.group(1) if vintage_search else "?"
                
                suffix_search = re.search(
                    r"Chassis HW Suffix\s+:\s+(\S+)", self.show_system
                )
                suffix = suffix_search.group(1) if suffix_search else "?"
                
                self._chassis_hw = f"{vintage}{suffix}"
            return self._chassis_hw
        return "NA"

    @property
    def comp_flash(self) -> str:
        """
        Returns the compact flash memory if installed.
        """
        if self.show_system:
            if self._comp_flash is None:
                m = re.search(r'Flash Memory\s+:\s+(.*)', self.show_system)
                if m:
                    if "No" in m.group(1):
                        self._comp_flash = ""
                    else:
                        self._comp_flash = m.group(1).replace(" ", "")
                else:
                    self._comp_flash = ""
            return self._comp_flash
        return "NA"

    @property
    def cpu_util(self) -> str:
        """
        Returns the last 5s and 60s CPU utilization as a string in percentage.
        """
        if self.show_utilization:
            m = re.search(r'10\s+(\d+)%\s+(\d+)%', self.show_utilization)
            self._cpu_util = f"{m.group(1)}%/{m.group(2)}%" if m else "?/?"
            return self._cpu_util
        return "NA"

    @property
    def dsp(self) -> str:
        """
        Returns the total number of DSPs as a string.
        """
        if self.show_system:
            if self._dsp is None:
                m = re.findall(
                    r"Media Socket .*?: M?P?(\d+) ", self.show_system
                )
                self._dsp = str(sum(int(x) for x in m)) if m else "?"
            return self._dsp
        return "NA"

    @property
    def faults(self) -> str:
        """
        Returns the number of faults as string.
        """
        if self.show_faults:
            if self._faults is None:
                if "No Fault Messages" in self.show_faults:
                    self._faults = 0
                else:
                    m = re.findall(r"\s+\+ (\S+)", self.show_faults)
                    self._faults = str(len(m))
            return self._faults
        return "NA"

    @property
    def fw(self) -> str:
        """
        Returns the firmware version as a string.
        """
        if self.show_system:
            if self._fw is None:
                m = re.search(r'FW Vintage\s+:\s+(\S+)', self.show_system)
                self._fw = m.group(1) if m else "?"
            return self._fw
        return "NA"

    @property
    def hw(self) -> str:
        """
        Returns the hardware version as a string.
        """
        if self.show_system:
            if self._hw is None:
                m = re.search(r'HW Vintage\s+:\s+(\S+)', self.show_system)
                hw_vintage = m.group(1) if m else "?"
                m = re.search(r'HW Suffix\s+:\s+(\S+)', self.show_system)
                hw_suffix = m.group(1) if m else "?"
                self._hw = f"{hw_vintage}{hw_suffix}"
            return self._hw
        return "NA"

    @property
    def last_seen_time(self) -> str:
        """
        Returns the last seen time as a string in 24h format.
        """
        if self.last_seen:
            return f"{self.last_seen:{'%H:%M:%S'}}"
        return "NA"

    @property
    def lldp(self) -> str:
        """
        Returns the LLDP configuration state.
        """
        if self.show_lldp_config:
            if self._lldp is None:
                if "Application status: disable" in self.show_lldp_config:
                    self._lldp = "disabled"
                else:
                    self._lldp = "enabled"
            return self._lldp
        return "NA"

    @property
    def location(self) -> str:
        """
        Returns the system location as a string.
        """
        if self.show_system:
            if self._location is None:
                m = re.search(r'System Location\s+:\s+(\S+)', self.show_system)
                self._location = m.group(1) if m else ""
            return self._location
        return "NA"

    @property
    def mac(self) -> str:
        """
        Returns the LAN MAC address as a string, without colons.
        """
        if self.show_system:
            if self._mac is None:
                m = re.search(r"LAN MAC Address\s+:\s+(\S+)", self.show_system)
                self._mac = m.group(1).replace(":", "") if m else "?"
            return self._mac
        return "NA"

    @property
    def mainboard_hw(self) -> str:
        """
        Returns the mainboard hardware version as a string.
        """
        if self.show_system:
            if self._mainboard_hw is None:
                
                vintage = re.search(
                    r'Mainboard HW Vintage\s+:\s+(\S+)', self.show_system
                )
                vintage = vintage.group(1) if vintage else "?"

                suffix = re.search(
                    r"Mainboard HW Suffix\s+:\s+(\S+)", self.show_system
                )
                suffix = suffix.group(1) if suffix else "?"

                self._mainboard_hw = f"{vintage}{suffix}"
            return self._mainboard_hw
        return "NA"

    @property
    def memory(self) -> str:
        """
        Returns the total memory as a string in the format "<number>MB".
        """
        if self.show_system:
            if self._memory is None:
                m = re.findall(r"Memory #\d+\s+:\s+(\S+)", self.show_system)
                self._memory = f"{sum(self._to_mbyte(x) for x in m)}MB"
            return self._memory
        return "NA"

    @property
    def mm_groupdict(self) -> Dict[str, Dict[str, str]]:
        """
        Returns a dictionary of module group information.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary where each key is a slot
            and the corresponding values are a dictionary containing module
            details.
        """
        if self.show_mg_list:
            if self._mm_groupdict is None:
                groupdict: Dict[str, Dict[str, str]] = {}
                for l in (l.strip() for l in self.show_mg_list.splitlines()):
                    if l.startswith("v") and "Not Installed" not in l:
                        m = re.search(r"".join((
                            r'.*?(?P<slot>\S+)',
                            r'.*?(?P<type>\S+)',
                            r'.*?(?P<code>\S+)',
                            r'.*?(?P<suffix>\S+)',
                            r'.*?(?P<hw_vint>\S+)',
                            r'.*?(?P<fw_vint>\S+)',
                        )), l)
                        if m:
                            groupdict.update({m.group("slot"): m.groupdict()})
                self._mm_groupdict = groupdict
            return self._mm_groupdict
        return {}

    def _mm_v(self, slot: int) -> str:
        """
        Retrieves the module code and suffix for the given slot.

        Args:
            slot: The slot number to retrieve the module details for.

        Returns:
            str: The module details for the given slot.
        """
        code = self.mm_groupdict.get(f"v{slot}", {}).get("code", "")
        if code == "ICC":
            code = self.mm_groupdict.get(f"v{slot}", {}).get("type", "")
        suffix = self.mm_groupdict.get(f"v{slot}", {}).get("suffix", "")
        return f"{code}{suffix}"

    @property
    def mm_v1(self) -> str:
        """
        Returns the media module code and suffix for slot 1.
        """
        if self.show_mg_list:
            if self._mm_v1 is None:
                self._mm_v1 = self._mm_v(1)
            return self._mm_v1
        return "NA"

    @property
    def mm_v2(self) -> str:
        """
        Returns the media module code and suffix for slot 2.
        """
        if self.show_mg_list:
            if self._mm_v2 is None:
                self._mm_v2 = self._mm_v(2)
            return self._mm_v2
        return "NA"

    @property
    def mm_v3(self) -> str:
        """
        Returns the media module code and suffix for slot 3.
        """
        if self.show_mg_list:
            if self._mm_v3 is None:
                self._mm_v3 = self._mm_v(3)
            return self._mm_v3
        return "NA"

    @property
    def mm_v4(self) -> str:
        """
        Returns the media module code and suffix for slot 4.
        """
        if self.show_mg_list:
            if self._mm_v4 is None:
                self._mm_v4 = self._mm_v(4)
            return self._mm_v4
        return "NA"

    @property
    def mm_v5(self) -> str:
        """
        Returns the media module code and suffix for slot 5.
        """
        if self.show_mg_list:
            if self._mm_v5 is None:
                self._mm_v5 = self._mm_v(5)
            return self._mm_v5
        return "NA"

    @property
    def mm_v6(self) -> str:
        """
        Returns the media module code and suffix for slot 6.
        """
        if self.show_mg_list:
            if self._mm_v6 is None:
                self._mm_v6 = self._mm_v(6)
            return self._mm_v6
        return "NA"

    @property
    def mm_v7(self) -> str:
        """
        Returns the media module code and suffix for slot 7.
        """        
        if self.show_mg_list:
            if self._mm_v7 is None:
                self._mm_v7 = self._mm_v(7)
            return self._mm_v7
        return "NA"

    @property
    def mm_v8(self) -> str:
        """
        Returns the media module code and suffix for slot 8.
        """
        if self.show_mg_list:
            if self._mm_v8 is None:
                self._mm_v8 = self._mm_v(8)
            return self._mm_v8
        return "NA"

    @property
    def mm_v10(self) -> str:
        """
        Returns the media module hw vintage and suffix for slot 10.
        """
        if self.show_mg_list:
            if self._mm_v10 is None:
                suffix = self.mm_groupdict.get("v10", {}).get("suffix", "")
                hw_vint = self.mm_groupdict.get("v10", {}).get("hw_vint", "")
                self._mm_v10 = f"{hw_vint}{suffix}"
            return self._mm_v10
        return "NA"

    @property
    def model(self) -> str:
        """
        Returns the gateway model as a string.
        """
        if self.show_system:
            if self._model is None:
                m = re.search(r'Model\s+:\s+(\S+)', self.show_system)
                self._model = m.group(1) if m else "?"
            return self._model
        return "NA"

    @property
    def port1(self) -> str:
        """
        Returns the LAN port 1 identifier as a string.
        """
        if self._port1 is None:
            pdict = self._port_groupdict(0)
            self._port1 = pdict.get("port", "?") if pdict else "NA"
        return self._port1

    @property
    def port1_status(self) -> str:
        """
        Returns the LAN port 1 link status as a string.
        """
        if self._port1_status is None:
            pdict = self._port_groupdict(0)
            self._port1_status = pdict.get("status", "?") if pdict else "NA"
        return self._port1_status

    @property
    def port1_neg(self) -> str:
        """
        Returns the LAN port 1 auto-negotiation status as a string.
        """
        if self._port1_neg is None:
            pdict = self._port_groupdict(0)
            self._port1_neg = pdict.get("neg", "?") if pdict else "NA"
        return self._port1_neg

    @property
    def port1_duplex(self) -> str:
        """
        Returns the LAN port 1 duplexity status as a string.
        """
        if self._port1_duplex is None:
            pdict = self._port_groupdict(0)
            self._port1_duplex = pdict.get("duplex", "?") if pdict else "NA"
        return self._port1_duplex

    @property
    def port1_speed(self) -> str:
        """
        Returns the LAN port 1 speed as a string.
        """
        if self._port1_speed is None:
            pdict = self._port_groupdict(0)
            self._port1_speed = pdict.get("speed", "?") if pdict else "NA"
        return self._port1_speed

    @property
    def port2(self) -> str:
        """
        Returns the LAN port 2 identifier as a string.
        """
        if self._port2 is None:
            pdict = self._port_groupdict(1)
            self._port2 = pdict.get("port", "?") if pdict else "NA"
        return self._port2

    @property
    def port2_status(self) -> str:
        """
        Returns the LAN port 2 link status as a string.
        """
        if self._port2_status is None:
            pdict = self._port_groupdict(1)
            self._port2_status = pdict.get("status", "?") if pdict else "NA"
        return self._port2_status

    @property
    def port2_neg(self) -> str:
        """
        Returns the LAN port 2 auto-negotiation status as a string.
        """
        if self._port2_neg is None:
            pdict = self._port_groupdict(1)
            self._port2_neg = pdict.get("neg", "?") if pdict else "NA"
        return self._port2_neg

    @property
    def port2_duplex(self) -> str:
        """
        Returns the LAN port 2 duplexity status as a string.
        """
        if self._port2_duplex is None:
            pdict = self._port_groupdict(1)
            self._port2_duplex = pdict.get("duplex", "?") if pdict else "NA"
        return self._port2_duplex

    @property
    def port2_speed(self) -> str:
        """
        Returns the LAN port 2 speed as a string.
        """
        if self._port2_speed is None:
            pdict = self._port_groupdict(1)
            self._port2_speed = pdict.get("speed", "?") if pdict else "NA"
        return self._port2_speed

    @property
    def port_redu(self) -> str:
        """
        Returns the port numbers used for port redundancy.
        """
        if self.show_running_config:
            if self._port_redu is None:
                m = re.search(r'port redundancy \d+/(\d+) \d+/(\d+)',
                    self.show_running_config)
                self._port_redu = f"{m.group(1)}/{m.group(2)}" if m else ""
            return self._port_redu
        return "NA"

    @property
    def psu1(self) -> str:
        """
        Returns the Power Supply Unit 1 as a string.
        """
        if self.show_system:
            if self._psu1 is None:
                m = re.search(r"PSU #1\s+:\s+\S+ (\S+)", self.show_system)
                self._psu1 = m.group(1) if m else ""
            return self._psu1
        return "NA"

    @property
    def psu2(self) -> str:
        """
        Returns the Power Supply Unit 2 as a string.
        """
        if self.show_system:
            if self._psu2 is None:
                m = re.search(r"PSU #2\s+:\s+\S+ (\S+)", self.show_system)
                self._psu2 = m.group(1) if m else ""
            return self._psu2
        return "NA"

    @property
    def ram_util(self) -> str:
        """
        Returns the current RAM utilization as percentage.
        """
        if self.show_utilization:
            m = re.search(r'10\s+S+\s+\S+\s+(\d+)%', self.show_utilization)
            self._ram_util = f"{m.group(1)}%" if m else ""
            return self._ram_util
        return "NA"

    @property
    def rtp_stat_service(self) -> str:
        """
        Returns the RTP-Stat service status as a string.
        """
        if self._rtp_stat_service is None:
            m = re.search(r'rtp-stat-service', self.show_running_config)
            self._rtp_stat_service = "enabled" if m else "disabled"
        return self._rtp_stat_service

    @property
    def serial(self) -> str:
        """
        Returns the serial number of the gateway as a string.
        """
        if self.show_system:
            if self._serial is None:
                m = re.search(r'Serial No\s+:\s+(\S+)', self.show_system)
                self._serial = m.group(1) if m else "?"
            return self._serial
        return "NA"

    @property
    def slamon_service(self) -> str:
        """
        Returns the SLAMon service admin status as a string.
        """
        if self.show_sla_monitor:
            if self._slamon_service is None:
                m = re.search(r'SLA Monitor:\s+(\S+)', self.show_sla_monitor)
                self._slamon_service = m.group(1).lower() if m else "?"
            return self._slamon_service
        return "NA"

    @property
    def sla_server(self) -> str:
        """
        Returns the SLAMon server IP address the gateway is registered to.
        """
        if self.show_sla_monitor:
            if self._sla_server is None:
                m = re.search(r'Registered Server IP Address:\s+(\S+)',
                              self.show_sla_monitor)
                self._sla_server = m.group(1) if m else ""
            return self._sla_server
        return "NA"

    @property
    def snmp(self) -> str:
        """
        Returns the configured SNMP version(s) as a string.

        Returns "v2&3" if both SNMPv2 and SNMPv3 are configured,
        "v2" if only SNMPv2 is configured, "v3" if only SNMPv3
        is configured, and "NA" if neither is configured.
        """
        if self.show_running_config:
            if self._snmp is None:
                snmp = []
                lines = [line.strip() for line in
                    self.show_running_config.splitlines()]
                
                if any(line.startswith("snmp-server community")
                       for line in lines):
                    snmp.append("2")
                
                if any(line.startswith("encrypted-snmp-server community")
                       for line in lines):
                    snmp.append("3")
                
                self._snmp = "v" + "&".join(snmp) if snmp else ""
            return self._snmp
        return "NA"

    @property
    def snmp_trap(self) -> str:
        """
        Returns "enabled" if SNMP traps are configured and "disabled" if not.
        """
        if self.show_running_config:
            if self._snmp_trap is None:
                m = re.search(
                    r'snmp-server host (\S+) traps', self.show_running_config
                )
                self._snmp_trap = "enabled" if m else "disabled"
            return self._snmp_trap
        return "NA"

    @property
    def temp(self) -> str:
        """
        Returns the ambient temperature as a string.
        """
        if self.show_temp:
            if self._temp is None:
                m = re.search(
                    r'Temperature\s+:\s+(\S+) \((\S+)\)', self.show_temp
                )
                self._temp = f"{m.group(1)}/{m.group(2)}" if m else "?/?"
            return self._temp
        return "NA"

    @property
    def total_session(self) -> str:
        """
        Returns the Total Session column from the RTP-Stat summary.
        """
        if self.show_rtp_stat_summary:
            m = re.search(r'nal\s+\S+\s+\S+\s+(\S+)',
                          self.show_rtp_stat_summary)
            return m.group(1) if m else "?/?"
        return "NA"

    @property
    def uptime(self) -> str:
        """
        Returns the gateway's uptime as a string.
        """
        if self.show_system:
            if self._uptime is None:
                m = re.search(r'Uptime \(\S+\)\s+:\s+(\S+)', self.show_system)
                if m:
                    self._uptime = m.group(1)\
                                    .replace(",", "d")\
                                    .replace(":", "h", 1)\
                                    .replace(":", "m") + "s"
                else:
                    self._uptime = "?"
            return self._uptime
        return "NA"

    @property
    def inuse_dsp(self) -> str:
        """
        Returns the total number of in-use DSPs as a string.
        """
        inuse = 0
        dsps = re.findall(r"In Use\s+:\s+(\d+)", self.show_voip_dsp)
        for dsp in dsps:
            try:
                inuse += int(dsp)
            except:
                pass
        return f"{inuse}"

    def update(
        self,
        last_seen: Optional[str] = None,
        gw_name: Optional[str] = None,
        gw_number: Optional[str] = None,
        commands: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> None:
        """
        Updates the BGW instance with new data.

        Args:
            last_seen: The last time the BGW was seen, in the format
                "%Y-%m-%d,%H:%M:%S".
            gw_name: The name of the gateway.
            gw_number: The number of the gateway.
            commands: A dictionary of commands and their output.
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        if last_seen:
            last_seen = datetime.strptime(last_seen, "%Y-%m-%d,%H:%M:%S")
            if not self.last_seen:
                self.last_seen = last_seen

            delta = last_seen - self.last_seen
            if delta:
                self.avg_poll_secs = round((self.avg_poll_secs + delta) / 2, 1)
            else:
                self.avg_poll_secs = self.polling_secs

            if not self.gw_number and gw_number:
                self.gw_number = gw_number
            if not self.gw_name and gw_name:
                self.gw_name = gw_name

            self.polls += 1

        if commands:
            for cmd, value in commands.items():
                bgw_attr = cmd.replace(" ", "_").replace("-", "_")
                setattr(self, bgw_attr, value)

    def _port_groupdict(self, idx: int) -> Dict[str, str]:
        """
        Extract port information from the 'show_port' string.

        Args:
            idx: The index of the port information to extract.

        Returns:
            A dictionary containing port details.
        """
        if self.show_port:
            matches = re.findall(r'(.*Avaya Inc)', self.show_port)
            if matches:
                line = matches[idx] if idx < len(matches) else ""
                if line:
                    return re.search(r"".join((
                        r'.*?(?P<port>\d+/\d+)',
                        r'.*?(?P<name>.*)',
                        r'.*?(?P<status>(connected|no link))',
                        r'.*?(?P<vlan>\d+)',
                        r'.*?(?P<level>\d+)',
                        r'.*?(?P<neg>\S+)',
                        r'.*?(?P<duplex>\S+)',
                        r'.*?(?P<speed>\S+)')), line).groupdict()
        return {}

    def properties_asdict(self) -> Dict[str, Any]:
        """
        Return a dictionary of this instance's properties.

        The dictionary will contain the names of the properties as keys and
        the values of the properties as values.

        Returns:
            A dictionary of the instance's properties.
        """
        properties = {}
        for name in dir(self.__class__):
            obj = getattr(self.__class__, name)
            if isinstance(obj, property):
                val = obj.__get__(self, self.__class__)
                properties[name] = val
        return properties   

    def asdict(self) -> Dict[str, Any]:
        """
        Return a dictionary of this instance's properties and attributes.

        The dictionary will contain the names of the properties and attributes
        as keys and the values of the properties and attributes as values.

        Returns:
            A dictionary of the instance's properties and attributes.
        """
        attrs = self.__dict__
        return {**self.properties_asdict(), **attrs}

    @staticmethod
    def _to_mbyte(str: str) -> int:
        """
        Converts the string representation of Memory to MB as an integer.

        Args:
            str: A Memory string from the output of 'show_system'

        Returns:
            An integer representing the number of megabytes.
        """
        m = re.search(r'(\d+)([MG]B)', str)
        if m:
            num, unit = int(m.group(1)), m.group(2)
            if unit == "MB":
                return num
            elif unit == "GB":
                return 1024 * num
        return 0

    def __str__(self):
        return f"BGW({self.host})"

    def __repr__(self):
        return f"BGW(host={self.host})"

class RTPSession:
    def __init__(self, params: Dict[str, str]) -> None:
        """
        Initialize an RTPSession from a dictionary of key-value pairs.

        :param params: A dictionary of key-value pairs where the keys are the
            names of the attributes of the RTPSession object and the values are the
            values of those attributes.
        """
        for k, v in params.items():
            setattr(self, k, v)

    @property
    def is_ok(self) -> bool:
        """
        Return True if the QoS is 'ok', False otherwise.

        :return: Whether the QoS is 'ok'.
        """
        return self.qos.lower() == 'ok'

    def __repr__(self) -> str:
        """
        Return a string representation of the RTPSession object.

        :return: A string representation of the RTPSession object.
        """
        return f'RTPSession=({self.__dict__})'

    def __str__(self) -> str:
        """
        Return a string representation of the RTPSession object.

        The string is formatted according to the SESSION_FORMAT string,
        which is a template string that uses the attributes of the RTPSession
        object as replacement values.

        :return: A string representation of the RTPSession object
        """
        return str(self.__dict__)

    def asdict(self):
        return self.__dict__

class Button:
    def __init__(self, *chars_int: int,
        win: "_curses._CursesWindow",
        y: Optional[int] = 0,
        x: Optional[int] = 0,
        char_alt: Optional[str] = None,
        label_on: Optional[str] = None,
        label_off: Optional[str] = None,
        attr_on: Optional[int] = None,
        attr_off: Optional[int] = None,
        callback_on: Optional[Callable[[], None]] = None,
        callback_off: Optional[Callable[[], None]] = None,
        done_callback_on: Optional[Callable[[], None]] = None,
        done_callback_off: Optional[Callable[[], None]] = None,
        status_label: Optional[str] = None,
        status_attr_on: Optional[int] = None,
        status_attr_off: Optional[int] = None,
        **callback_kwargs: Any) -> None:
        """
        Initialize a Button.

        Parameters
        ----------
        chars_int : int
            A list of integer values of characters to listen for.
        win : _curses._CursesWindow
            The curses window where the button is displayed.
        y : int, optional
            The y-coordinate of the button. Defaults to 0.
        x : int, optional
            The x-coordinate of the button. Defaults to 0.
        char_alt : str, optional
            An alternative character to display instead of the first character
            in chars_int. Defaults to None.
        label_on : str, optional
            The label to display when the button is on. Defaults to "On ".
        label_off : str, optional
            The label to display when the button is off. Defaults to "Off" if
            not label_on else label_on.
        attr_on : int, optional
            The curses attribute to use when the button is on. Defaults to
            curses.A_REVERSE.
        attr_off : int, optional
            The curses attribute to use when the button is off. Defaults to
            curses.A_NORMAL.
        callback_on : Callable[[], None], optional
            The function to call when the button is turned on. Defaults to None.
        callback_off : Callable[[], None], optional
            The function to call when the button is turned off. Defaults to None.
        done_callback_on : Callable[[], None], optional
            The function to call when the on action is completed. Defaults to
            None.
        done_callback_off : Callable[[], None], optional
            The function to call when the off action is completed. Defaults to
            None.
        status_label : str, optional
            The label to display in the status bar when the button is on.
            Defaults to "".
        status_attr_on : int, optional
            The curses attribute to use when the button is on in the status bar.
            Defaults to the attribute_on value.
        status_attr_off : int, optional
            The curses attribute to use when the button is off in the status
            bar. Defaults to the attribute_off value.
        **callback_kwargs : Any
            Additional keyword arguments to pass to the callbacks.

        Returns
        -------
        None
        """

        self.chars_int = chars_int
        self.win = win
        self.y = y
        self.x = x
        self.char_alt = char_alt
        self.label_on = label_on or "Off"
        self.label_off = label_off or ("On" if not label_on else label_on)
        self.attr_on = attr_on or curses.A_REVERSE
        self.attr_off = attr_off or curses.A_REVERSE
        self.callback_on = callback_on
        self.callback_off = callback_off
        self.done_callback_on = done_callback_on
        self.done_callback_off = done_callback_off
        self.status_label = status_label if status_label else ""
        self.status_attr_on = status_attr_on or self.attr_on
        self.status_attr_off = status_attr_off or self.attr_off
        self.callback_kwargs = callback_kwargs or {}
        self.callback_kwargs = {**self.callback_kwargs, **{"button": self}}
        self.state = False if callback_on and callback_off else True
        self.callback_on_task = None
        self.callback_off_task = None

    def draw(self) -> None:
        """
        Draw the button on the given curses window.

        Returns
        -------
        None
        """
        if self.char_alt:
            char = self.char_alt
        elif any(chr(c).isalnum() for c in self.chars_int):
            char = next(c for c in self.chars_int if chr(c).isalnum())
        else:
            char = repr(chr(self.chars_int[0]))

        label = self.label_on if self.state else self.label_off
        attr = self.attr_on if self.state else self.attr_off

        try:
            self.win.addstr(self.y, self.x, f"{char}={label}", attr)
        except curses.error:
            pass

        self.win.refresh()

    def toggle(self) -> None:
        """
        Toggle the button state.

        Returns
        -------
        None
        """
        if self.callback_on and self.callback_off: 
            self.state = not self.state

    def press(self) -> None:
        """
        Handle a button press synchronously:
         - Toggle the state.
         - Schedule the appropriate callback onto the event loop.

        Returns
        -------
        None
        """
        self.toggle()

        if self.state:
            if self.callback_on:
                if asyncio.iscoroutinefunction(self.callback_on):
                    self.callback_on_task: asyncio.Task = create_task(
                        self.callback_on(**self.callback_kwargs),
                        name="callback_on")
                    if self.done_callback_on:
                        self.callback_on_task.add_done_callback(
                            self.done_callback_on)
                else:
                    self.callback_on(**self.callback_kwargs)
        else:
            if self.callback_off:
                if asyncio.iscoroutinefunction(self.callback_off):
                    self.callback_off_task: asyncio.Task = create_task(
                        self.callback_off(**self.callback_kwargs),
                        name="callback_off")
                    if self.done_callback_off:
                        self.callback_off_task.add_done_callback(
                            self.done_callback_off)
                else:
                    self.callback_off(**self.callback_kwargs)
                
                if self.callback_on_task and not self.callback_on_task.done():
                    self.callback_on_task.remove_done_callback(
                        self.done_callback_on)
                    self.callback_on_task = None

    async def handle_char(self, key: int) -> None:
        """
        Process a keypress.

        Parameters
        ----------
        key : int
            The character code of the key that was pressed.

        Returns
        -------
        None
        """
        if key in self.chars_int:
            logging.info(f"Received: {key}")
            self.press()

    def status(self) -> str:
        """
        Get the current label of the button.

        Returns
        -------
        str
            The label of the button.
        """
        attr = self.status_attr_on if self.state else self.status_attr_off
        return self.status_label, attr

class Tab:
    def __init__(self,
        stdscr,
        tab_names,
        nlines=2,
        yoffset=0,
        xoffset=0,
        color_scheme=None,
    ):
        self.stdscr = stdscr
        self.tab_names = tab_names
        self.tab_width = max(len(x) for x in self.tab_names)
        self.yoffset = yoffset
        self.xoffset = xoffset
        self.color_scheme = color_scheme or {"normal": 0}
        self.active_tab_idx = 0
        self.maxy = nlines
        self.maxx = self.stdscr.getmaxyx()[1]
        self.win = self.stdscr.subwin(nlines, self.maxx, yoffset, xoffset)

    def draw(self):
        xpos = self.xoffset
        for idx, tab_names in enumerate(self.tab_names):
            active = bool(idx == self.active_tab_idx)
            self.draw_tab(tab_names, self.yoffset, xpos, active)
            xpos += self.tab_width + 2
        self.win.refresh()

    def draw_tab(self, tab_name, ypos, xpos, active):
        attr = self.color_scheme["normal"]
        border1 = "╭" + self.tab_width * "─" + "╮"
        border2 = "│" + " " * self.tab_width + "│"
        self.win.addstr(ypos, xpos, border1, attr)
        for linen in range(1, self.maxy):
            self.win.addstr(ypos + linen, xpos, border2, attr)
        text = tab_name.center(self.tab_width)
        if not active:
            attr = self.color_scheme["normal"]
        else:
            attr = self.color_scheme.get("standout", 0)
        self.win.addstr(ypos + 1, xpos+1, text, attr)

    async def handle_char(self, char):
        if chr(char) == "\t":
            if self.active_tab_idx < len(self.tab_names) - 1: 
                self.active_tab_idx += 1
            else:
                self.active_tab_idx = 0
            self.draw()

class Workspace:
    def __init__(self, stdscr,
        column_attrs,
        column_names=None,
        column_fmt_specs=None,
        column_colors=None,
        column_xposes=None,
        *,
        menubar=None,
        name=None,
        storage=None,
        offset_y=2,
        offset_x=0,
        title_width=3,
        color_scheme=None,
        **kwargs,
    ):
        self.stdscr = stdscr
        self.column_attrs = column_attrs
        self.column_names = column_names or column_attrs
        self.column_fmt_specs = column_fmt_specs or [f"^{len(x)}" for x in column_names]
        self.column_colors = column_colors or [None for x in column_names]
        self.column_xposes = column_xposes or [None for x in column_names]
        self.menubar = menubar
        self.name = name
        self.storage = storage if storage is not None else []
        self.offset_y = offset_y
        self.offset_x = offset_x
        self.color_scheme= color_scheme or {"normal": 0}
        self.title_width = title_width
        self.posy = 0
        self.posx = 0
        self.row_pos = 0
        self.attr = self.color_scheme["normal"]
        self.maxy = self.stdscr.getmaxyx()[0] - offset_y
        self.maxx = self.stdscr.getmaxyx()[1]
        self.titlewin = stdscr.subwin(title_width, self.maxx,
            offset_y, offset_x)
        self.bodywin = self.stdscr.subwin(
            self.maxy - title_width, self.maxx, offset_y + title_width,
            offset_x)

    def iter_attrs(self, obj: object, xoffset: int = 0) -> Iterator[Tuple[int, str, str]]:
        """
        Iterate over the attributes of the given object.

        - `xpos`: The x position of the attribute
        - `attr_value`: The value of the attribute, formatted with `fmt_spec`
        - `color`: The color of the attribute as a string

        :param obj: The object whose attributes are to be iterated over
        :param xoffset: An x offset as an integer that is added to the x position
        """
    
        offset = 1
        
        params = zip(self.column_attrs, self.column_names,
            self.column_fmt_specs, self.column_colors, self.column_xposes)
        
        for attr, name, fmt_spec, color, xpos in params:
            _len = len(name)

            if hasattr(obj, attr):
                attr_value = getattr(obj, attr)
            else:
                attr_value = obj.get(attr, attr)

            if isinstance(attr_value, int):
                attr_value = str(attr_value)

            if fmt_spec:
                m = re.search(r"[<>^](\d+)", fmt_spec)
                _len = int(m.group(1)) if m else _len
                attr_value = f"{attr_value:{fmt_spec}}"
            
            if isinstance(attr_value, str):
                attr_value = f"{attr_value[:_len]}"

            if not xpos:
                xpos = offset
            
            yield xpos + xoffset, attr_value, color
            offset += len(attr_value) + 1

    def iter_column_names(self, xoffset: int = 0) -> Iterator[Tuple[int, str, str]]:
        """
        Iterate over the column names with formatting, color, and x position.

        :param xoffset: An integer that is added to the x position
        :return: An iterator of tuples with x position, name and color
        """
        offset = 1

        params = zip(self.column_names, self.column_fmt_specs,
            self.column_colors, self.column_xposes)

        for name, fmt_spec, color, xpos in params:
            _len = len(name)

            if fmt_spec:
                m = re.search(r"[<>^](\d+)", fmt_spec)
                _len = int(m.group(1)) if m else _len
            
            name = f"{name:^{_len}}"

            if not xpos:
                xpos = offset

            yield xpos + xoffset, name, color
            offset += len(name) + 1

    def draw(self):
        self.draw_titlewin()
        self.draw_bodywin()
        self.draw_menubar()

    def draw_titlewin(self):
        self.titlewin.attron(self.attr)
        self.titlewin.box()
        self.titlewin.attroff(self.attr)
        offset = 0

        for idx, (xpos, name, color) in enumerate(self.iter_column_names()):
            attr = self.color_scheme.get(color, 0)
            if idx > 0:
                self.titlewin.addstr(1, xpos - 1, "│", attr)
                self.titlewin.addstr(0, xpos - 1, "┬", attr)
                self.titlewin.addstr(2, xpos - 1, "┼", attr)
            self.titlewin.addstr(1, xpos, name, attr)
            self.titlewin.refresh()

        try:
            self.titlewin.addstr(2, self.offset_x, "├", attr)
            self.titlewin.addstr(2, self.maxx - 1, "┤", attr)
        except curses.error:
            pass
        self.titlewin.refresh()

    def draw_bodywin(self):
        start_row = self.row_pos
        end_row = min(self.row_pos + (self.maxy - 3), len(self.storage))
        
        for ridx, obj in enumerate(self.storage[start_row:end_row]):
            try:
                for xpos, attr_value, color in iter_attrs(obj,
                        self.column_attrs, self.column_names,
                        self.column_fmt_specs, self.column_colors,
                        self.column_xposes, self.offset_x):
                    
                    attr = self.colors_scheme.get(color, 0)
                    self.bodywin.addstr(
                        ridx, xpos - 1, "│" + attr_value + "│", attr
                    )
            except curses.error:
                pass
        self.bodywin.refresh()

    def draw_menubar(self):
        if self.menubar:
            self.menubar.draw()

    async def handle_char(self, char):
        if char == curses.KEY_DOWN:
            self.row_pos = self.row_pos + 1 if self.posy == (self.maxy - (self.title_width + 1)) and self.row_pos + 1 <= len(self.storage) - (self.maxy - self.title_width) else self.row_pos
            self.posy = self.posy + 1 if self.posy < (self.maxy - (self.title_width + 1)) and len(self.storage) - 1 > self.posy else self.posy
        elif char == curses.KEY_UP:
            self.row_pos = self.row_pos - 1 if self.row_pos > 0 and self.posy == 0 else self.row_pos
            self.posy =  self.posy - 1 if self.posy > 0 else self.posy
        elif char == curses.KEY_HOME:
            self.row_pos = 0
            self.posy = 0
        elif char == curses.KEY_END:
            self.posy = min(self.maxy - (self.title_width + 1), len(self.storage) - 1)
            self.row_pos = max(0, len(self.storage) - (self.maxy - self.title_width))
        elif char == curses.KEY_NPAGE:
            self.row_pos = min(self.row_pos + (self.maxy - self.title_width), max(0, len(self.storage) - (self.maxy - self.title_width)))
            self.posy = 0 if self.row_pos + (self.maxy - self.title_width) <= len(self.storage) - 1 else min(len(self.storage) - 1, (self.maxy - self.title_width) - 1)
        elif char == curses.KEY_PPAGE:
            self.posy = 0
            self.row_pos = max(self.row_pos - (self.maxy - self.title_width), 0)
        else:
            await self.menubar.handle_char(char)
        self.draw_bodywin()

class MyPanel:
    def __init__(
        self,
        stdscr,
        body,
        attr=None,
        offset_y=1,
        offset_x=1,
        margin=1,
    ) -> None:
        self.stdscr = stdscr
        self.body = body
        self.attr = attr
        self.offset_y = offset_y
        self.offset_x = offset_x
        self.margin = margin
        self._initialize()

    def _initialize(self):
        maxy, maxx = self.stdscr.getmaxyx()
        nlines = maxy - (2 * self.margin)
        ncols = maxx - (2 * self.margin)
        begin_y = self.offset_y
        begin_x = self.offset_x
        self.win = curses.newwin(nlines, ncols, begin_y, begin_x)
        self.panel = curses.panel.new_panel(self.win)
        self.attr = self.attr if self.attr else curses.color_pair(0)

    def draw(self, body=None):
        if body:
            self.win.erase()
            self.body = body
        self.win.box()
        self.win.addstr(self.margin, self.margin, self.body, self.attr)
        self.win.refresh()
        return self

    def erase(self):
        self.win.erase()
        self.win.refresh()
        return self

class ProgressBar:
    def __init__(self, stdscr: "_curses._CursesWindow",
        fraction: float = 0,
        width: int = 21,
        attr_fg: Optional[int] = None,
        attr_bg: Optional[int] = None,
        offset_y: int = 0) -> None:
        """
        Initialize the progress bar.

        Parameters
        ----------
        stdscr : _curses._CursesWindow
            The curses window that the progress bar should be drawn on.
        fraction : float, optional
            The fraction of the bar that should be filled. Defaults to 0.
        width : int, optional
            The width of the progress bar. Defaults to 21.
        attr_fg : Optional[int], optional
            The curses attribute to use for the foreground. Defaults to
            curses.color_pair(221)|curses.A_REVERSE.
        attr_bg : Optional[int], optional
            The curses attribute to use for the background. Defaults to
            curses.color_pair(239)|curses.A_REVERSE.
        offset_y : int, optional
            The y offset of the progress bar. Defaults to 0.
        """
        self.stdscr = stdscr
        self.fraction = fraction
        self.width = width
        self.attr_fg = attr_fg or curses.color_pair(221)|curses.A_REVERSE
        self.attr_bg = attr_bg or curses.color_pair(239)|curses.A_REVERSE
        maxy, maxx = stdscr.getmaxyx()
        begin_y = maxy // 2 + offset_y
        begin_x = maxx // 2 - (width // 2)
        self.win = curses.newwin(1, width, begin_y, begin_x)
        curses.panel.new_panel(self.win)
        self.win.attron(self.attr_bg)

    def draw(self, fraction: Optional[float] = None) -> "ProgressBar":
        """
        Draw the progress bar on the screen.

        Parameters
        ----------
        fraction : Optional[float], optional
            The fraction of the bar that should be filled. Defaults to None.

        Returns
        -------
        ProgressBar
            The same instance.
        """
        if fraction:
            self.win.erase()
            self.fraction = fraction
        
        filled_width = int(self.fraction * self.width)
        remaining_width = self.width - filled_width
        
        try:
            self.win.addstr(0, 0, " " * filled_width, self.attr_fg)
            self.win.addstr(0, filled_width, " " * remaining_width, self.attr_bg)
        except _curses.error:
            pass
        
        self.win.refresh()
        return self

    def erase(self) -> "ProgressBar":
        """
        Erase the progress bar from the screen.

        Returns
        -------
        ProgressBar
            The same instance.
        """
        self.win.erase()
        self.win.refresh()

class Confirmation:
    def __init__(self, stdscr, body=None, attr=None, yoffset=-1, margin=1,
    ) -> None:
        self.stdscr = stdscr
        self.body = body or "Do you confirm (Y/N)?"
        self.attr = attr or curses.color_pair(0)
        self.yoffset = yoffset
        self.margin = margin
        
        maxy, maxx = self.stdscr.getmaxyx()
        nlines = 3 + (2 * self.margin)
        ncols = len(self.body) + (2 * self.margin) + 2
        begin_y = maxy // 2 + self.yoffset - (self.margin + 1)
        begin_x = maxx // 2 - (len(self.body) // 2) - (self.margin + 1)
        self.win = curses.newwin(nlines, ncols, begin_y, begin_x)
        self.panel = curses.panel.new_panel(self.win)
        self.win.attron(self.attr)
        self.win.nodelay(True)
        self.panel.top()
    
    async def draw(self):
        self.win.box()
        self.win.addstr(self.margin + 1, self.margin + 1, self.body, self.attr)
        self.win.refresh()
        while True:
            char = self.win.getch()
            if char in (ord('y'), ord('Y')):
                logging.info(f"Received: {char}")
                return True
            elif char in (ord('n'), ord('N')):
                logging.info(f"Received: {char}")
                return False
            else:
                await asyncio.sleep(0.01)

    def erase(self):
        self.win.erase()
        self.win.refresh()

class Menubar:
    def __init__(self, stdscr: "_curses._CursesWindow",
        nlines: Optional[int] = 1,
        attr: Optional[int] = None,
        offset_x: Optional[int] = 0,
        status_bar_width: Optional[int] = 13,
        buttons: List[Button] = None) -> None:
        """
        Initialize the menubar.

        Parameters
        ----------
        stdscr : _curses._CursesWindow
            The curses window that the menubar will be drawn on.
        nlines : int, optional
            The number of lines the menubar should use. Defaults to 1.
        attr : int, optional
            The curses attribute to use when drawing the menubar. Defaults to
            curses.A_REVERSE.
        offset_x : int, optional
            The x offset of the menubar. Defaults to 0.
        status_bar_width : int, optional
            The width of the status bar. Defaults to 20.
        buttons : List[Button], optional
            A list of Button objects that should be used to populate the
            menubar. Defaults to an empty list.
        """
        self.stdscr = stdscr
        self.nlines = nlines
        self.attr = attr or curses.color_pair(0)|curses.A_REVERSE
        self.buttons = buttons if buttons else []
        self.offset_x = offset_x
        self.status_bar_width = status_bar_width
        maxy, ncols = stdscr.getmaxyx()
        begin_y, begin_x = maxy - nlines, offset_x
        self.win = stdscr.subwin(nlines, ncols, begin_y, begin_x)
        self.maxy, self.maxx = self.win.getmaxyx()

    def draw(self) -> None:
        """
        Draw the menubar.

        Returns
        -------
        None
        """
        for y in range(0, self.maxy):
            try:
                self.win.addstr(y, 0, " " * (self.maxx), self.attr)
            except _curses.error:
                pass
        
        self.draw_status_bar()
        self.draw_buttons()
        self.win.refresh()

    def draw_status_bar(self, offset: int = 0) -> None:
        """
        Draw the status bar for all buttons in the menubar.

        Parameters
        ----------
        offset : int, optional
            The x offset for the status bar. Defaults to 0.

        Returns
        -------
        None
        """
        labels, attrs = zip(*[b.status() for b in self.buttons])
        labels, attrs = list(labels), list(attrs)
        visible_labels = [l for l in labels if l]
        nseparators = max(0, len(visible_labels) - 1)
        noffset = offset

        if visible_labels:
            width = (self.status_bar_width - nseparators) // len(visible_labels)
        else:
            width = (self.status_bar_width - nseparators)

        for label, attr in zip(labels, attrs):
            if label:
                if nseparators and noffset > offset:
                    self.win.addstr(0, noffset, "│", self.attr)
                    noffset += 1
                label = f"{label[:width]:^{width}}"
                self.win.addstr(0, noffset, label, attr)
                noffset += len(label)

    def draw_buttons(self) -> None:
        """
        Draw all buttons in the list.

        Returns
        -------
        None
        """
        for button in self.buttons:
            button.draw()

    async def handle_char(self, char: int) -> None:
        """
        Process a keypress for one of the buttons in the menubar.

        Parameters
        ----------
        char : int
            The character code of the key that was pressed.

        Returns
        -------
        None
        """
        chars_list = [b.chars_int for b in self.buttons]
        for idx, chars in enumerate(chars_list):
            if char in chars:
                logging.info(f"Received: {char}")
                await self.buttons[idx].handle_char(char)
                self.draw()
                break

class MyDisplay():
    def __init__(self,
        stdscr: "_curses._CursesWindow",
        miny: int = 24,
        minx: int = 80,
        workspaces = None,
        tab = None,
    ) -> None:
        self.stdscr = stdscr
        self.miny = miny
        self.minx = minx
        self.workspaces = workspaces
        self.tab = tab
        self.confirmation = None
        self.done: bool = False
        self.posx = 1
        self.posy = 1
        self.maxy, self.maxx = self.stdscr.getmaxyx()
        self.active_ws_idx = 0
        self.color_pairs = self.init_color_pairs()

    def set_exit(self) -> None:
        self.done = True

    @classmethod
    def init_color_pairs(cls):
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)
        
        return {
            "RED": curses.color_pair(2),
            "RED_LIGHT": curses.color_pair(197),
            "GREEN": curses.color_pair(42),
            "GREEN_LIGHT": curses.color_pair(156),
            "YELLOW": curses.color_pair(12),
            "YELLOW_LIGHT": curses.color_pair(230),
            "BLUE": curses.color_pair(13),
            "BLUE_LIGHT": curses.color_pair(34),
            "MAGENTA": curses.color_pair(6),
            "MAGENTA_LIGHT": curses.color_pair(14),
            "CYAN": curses.color_pair(46),
            "CYAN_LIGHT": curses.color_pair(15),
            "GREY": curses.color_pair(246),    
            "GREY_LIGHT": curses.color_pair(252),        
            "ORANGE": curses.color_pair(203),
            "ORANGE_LIGHT": curses.color_pair(209),
            "PINK": curses.color_pair(220),
            "PINK_LIGHT": curses.color_pair(226),
            "PURPLE": curses.color_pair(135),
            "PURPLE_LIGHT": curses.color_pair(148),
        }

    async def run(self) -> None:
        self.stdscr.nodelay(True)
        self.make_display()
        
        while not self.done:
            char = self.stdscr.getch()
            if char == curses.ERR:
                await asyncio.sleep(0.05)
            elif char == curses.KEY_RESIZE:
                self.maxy, self.maxx = self.stdscr.getmaxyx()
                if self.maxy >= self.miny and self.maxx >= self.minx:
                    self.make_display()
                else:
                    self.stdscr.erase()
                    break
            else:
                await self.handle_char(char)

    def make_display(self):
        self.maxy, self.maxx = self.stdscr.getmaxyx()
        self.stdscr.erase()  
        if self.tab:
            self.tab.draw()
        self.workspaces[self.active_ws_idx].draw()

    async def handle_char(self, char: int) -> None:
        if chr(char) in ("q", "Q"):
            self.set_exit()
        elif chr(char) == "\t":
            self.active_ws_idx = (self.active_ws_idx + 1) % len(self.workspaces)
            self.stdscr.erase()
            self.workspaces[self.active_ws_idx].draw()
            await self.tab.handle_char(char)
        else:
            await self.workspaces[self.active_ws_idx].handle_char(char)

    def draw_maxyx(self, stdscr, maxy, maxx, ypos):
            text = f"{maxy}x{maxx} ypos={ypos}"
            attr = curses.color_pair(3)
            stdscr.addstr(maxy // 2, maxx // 2 - 6, (len(text)+2) * " ", attr)
            stdscr.addstr(maxy // 2, maxx // 2 - 6, text, attr)
            stdscr.refresh()

    @property
    def active_workspace(self):
        return self.workspaces[self.active_ws_idx]

################################# FUNCTIONS ################################# 

def asyncio_run(
    main: Callable[..., Coroutine[Any, Any, Any]],
    *,
    debug: Optional[bool] = None
) -> Any:
    """Execute the coroutine and return the result.

    This function runs the passed coroutine, taking care of
    managing the asyncio event loop and finalizing asynchronous
    generators.

    This function cannot be called when another asyncio event loop is
    running in the same thread.

    If debug is True, the event loop will be run in debug mode.

    This function always creates a new event loop and closes it at the end.
    It should be used as a main entry point for asyncio programs, and should
    ideally only be called once.
    """
    if events._get_running_loop() is not None:
        raise RuntimeError(
            "asyncio.run() cannot be called from a running event loop")

    if not coroutines.iscoroutine(main):
        raise ValueError("a coroutine was expected, got {!r}".format(main))

    loop = events.new_event_loop()
    loop.set_exception_handler(custom_exception_handler)
    try:
        events.set_event_loop(loop)
        if debug is not None:
            loop.set_debug(debug)
        return loop.run_until_complete(main)
    except KeyboardInterrupt:
        print("Got signal: SIGINT, shutting down.")
    finally:
        try:
            _cancel_all_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            events.set_event_loop(None)
            loop.close()

def _cancel_all_tasks(loop):
    to_cancel = asyncio.Task.all_tasks()
    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(tasks.gather(*to_cancel, return_exceptions=True))

    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'task': task,
            })

def custom_exception_handler(loop, context):
    exc = context.get('exception')
    # Suppress the spurious TimeoutError reported at shutdown.
    if isinstance(exc, asyncio.CancelledError) or isinstance(exc, asyncio.TimeoutError):
        logger.error(f"{repr(exc)} silenced")
        return
    loop.default_exception_handler(context)

def iter_attrs(
    obj: object,
    column_attrs: List[str],
    column_names: List[str] = None,
    column_fmt_specs: List[str] = None,
    column_colors: List[str] = None,
    column_xposes: List[int] = None,
    xoffset: int = 0
) -> Iterator[Tuple[int, str, str]]:
    """
    Iterate over the attributes of the given object.

    - `xpos`: The x position of the attribute
    - `attr_value`: The value of the attribute, formatted with `fmt_spec`
    - `color`: The color of the attribute as a string

    :param obj: The object whose attributes are to be iterated over
    :param column_attrs: A list of attribute/key names of the object
    :param column_names: A list of column name
    :param column_fmt_specs: A list of format specifications, one per attribute
    :param column_colors: A list of colors, one per attribute
    :param column_xposes: A list of x positions as integers, one per attribute
    :param xoffset: An x offset as an integer that is added to the x position
    """
    column_names = column_names or column_attrs
    column_fmt_specs = column_fmt_specs or [f">{len(x)}" for x in column_names]
    column_colors = column_colors or ["base" for x in column_names]
    column_xposes = column_xposes or [None for x in column_names]
    offset = 1
    
    column_params = zip(column_attrs, column_names, column_fmt_specs,
        column_colors, column_xposes)
    
    for attr, name, fmt_spec, color, xpos in column_params:
        _len = len(name)

        if hasattr(obj, attr):
            attr_value = getattr(obj, attr)
        else:
            attr_value = obj.get(attr, attr)

        if isinstance(attr_value, int):
            attr_value = str(attr_value)

        if fmt_spec:
            m = re.search(r"[<>^](\d+)", fmt_spec)
            _len = int(m.group(1)) if m else _len
            attr_value = f"{attr_value:{fmt_spec}}"
        
        if isinstance(attr_value, str):
            attr_value = f"{attr_value[:_len]}"

        if not xpos:
            xpos = offset
        
        yield xpos + xoffset, attr_value, color
        offset += len(attr_value) + 1

def iter_column_names(
    column_names: List[str],
    column_fmt_specs: Optional[List[str]] = None,
    column_colors: Optional[List[str]] = None,
    column_xposes: Optional[List[int]] = None,
    xoffset: int = 0
) -> Iterator[Tuple[int, str, str]]:
    """
    Iterate over the column names with formatting, color, and x position.

    :param column_names: A list of column names as strings
    :param column_fmt_specs: A list of format specifications
    :param column_colors: A list of colors, one per column name
    :param column_xposes: A list of x positions as integers
    :param xoffset: An integer that is added to the x position
    :return: An iterator of tuples with x position, name and color
    """
    column_fmt_specs = column_fmt_specs or [f"^{len(x)}" for x in column_names]
    column_colors = column_colors or ["base" for x in column_names]
    column_xposes = column_xposes or [None for x in column_names]
    offset = 1

    column_name_params = zip(column_names, column_fmt_specs, column_colors, column_xposes)

    for name, fmt_spec, color, xpos in column_name_params:
        _len = len(name)

        if fmt_spec:
            m = re.search(r"[<>^](\d+)", fmt_spec)
            _len = int(m.group(1)) if m else _len
        
        name = f"{name:^{_len}}"

        if not xpos:
            xpos = offset

        yield xpos + xoffset, name, color
        offset += len(name) + 1

def create_bgw_script(bgw: BGW) -> List[str]:
    """
    Create the script passed to expect to connect to the BGW.

    Parameters
    ----------
    bgw : BGW
        A BGW object representing the gateway we want to talk to.

    Returns
    -------
    List[str]
        A list of the arguments to execute the expect script.
    """
    if logger.getEffectiveLevel() == 10:
        expect_log = "_".join((CONFIG["expect_log"], bgw.host))
    else:    
        expect_log = "/dev/null"
    if not bgw.last_seen:
        rtp_stat = 0
        commands = CONFIG["discovery_commands"]
    else:
        rtp_stat = 1
        commands = CONFIG["query_commands"]
        if not bgw.queue.empty():
            queued_commands = bgw.queue.get_nowait()
            if isinstance(queued_commands, str):
                queued_commands = [queued_commands]
            commands.extend(queued_commands)
    
    script_template = unwrap_and_decompress(CONFIG["script_template"])
    script = script_template.format(**{
        "host": bgw.host,
        "username": CONFIG["username"],
        "passwd": CONFIG["passwd"],
        "rtp_stat": rtp_stat,
        "lastn_secs": CONFIG["lastn_secs"],
        "commands": " ".join(f'"{c}"' for c in commands),
        "expect_log": expect_log,
    })
    
    return ["/usr/bin/env", "expect", "-c", script]

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
        m = re.search(r"([0-9.]+):(1039|2944|2945)\s+([0-9.]+):([0-9]+)", line)
        if m:
            ip = m.group(3)
            if m.group(2) in ("1039", "2944"):
                proto = "encrypted"
            else:
                proto = "unencrypted"
            logging.info(f"Found gateway {ip} using {proto} protocol")
            if not ip_filter or ip in ip_filter:
                result[ip] = proto
                logging.info(f"Added gateway {ip} to result dictionary")
    
    if not result:
        return {"10.10.48.58": "unencrypted", "10.44.244.51": "encrypted"}
    
    return {ip: result[ip] for ip in sorted(result)}

def create_query_tasks(queue=None) -> List[asyncio.Task]:
    """
    Create tasks that query all gateways in GATEWAYS.

    Returns:
        A list of Tasks.
    """
    tasks = []
    
    for bgw in GATEWAYS.values():
        task = create_task(query_gateway(
            bgw,
            queue=queue,
        ), name=f"coro query_gateway() for {bgw.host}")
        tasks.append(task)
    
    return tasks

async def exec_script(
    *args,
    timeout: Optional[int] = None,
    name: Optional[str] = None
) -> Tuple[str, str]:
    """
    Runs command asynchronously with support for timeouts and error handling.

    Args:
        args (List[str]): The command arguments to execute.
        timeout (Optional[int]): Duration (in secs) before the process is terminated.
        name (Optional[str]): The name of the process for logging purposes.

    Returns:
        Tuple[str, str]: A tuple containing stdout and stderr. If timeout occurs 
        or process is cancelled, appropriate messages are returned.
    """
    name = name if name else "coro exec_script()"
    proc: Optional[asyncio.subprocess.Process] = None

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        logger.info(f"Created process PID {proc.pid} in {name}")
        
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        if proc.returncode == 0 and not stderr_str:
            logger.debug(f"Got '{stdout_str}' from PID {proc.pid} in {name}")
            return stdout_str

        logger.error(f"{stderr_str} for PID {proc.pid} in {name}")
        return ""

    finally:
        if proc and proc.returncode is None:
            logger.info(f"Terminating PID {proc.pid} in {name}")
            try:
                proc._transport.close()
                proc.kill()
                await proc.wait()
            except Exception as e:
                logger.error(f"{repr(e)} for PID {proc.pid} in {name}")

async def query_gateway(
    bgw: BGW,
    queue: Optional[asyncio.Queue] = None,
) -> Optional[str]:
    """
    Asynchronously queries a BGW and returns the command output.

    If a queue is provided, the output is placed onto the queue and the
    function does not return a value.
    Otherwise, the output is returned directly.

    Args:
        bgw (BGW): The BGW instance to query.
        timeout (float, optional): The timeout for the command execution.
        queue (Optional[asyncio.Queue], optional): A queue to place the output.
        polling_secs (float, optional): The interval between polling attempts.
        semaphore (Optional[asyncio.Semaphore], optional): A semaphore.
        name (Optional[str], optional): The name of the task for logging.

    Returns:
        Optional[str]: The output of the command if no queue is provided.
    """

    timeout = CONFIG.get("timeout", 10)
    polling_secs = CONFIG.get("polling_secs", 10)
    max_polling = CONFIG.get("max_polling", 20)
    semaphore = asyncio.Semaphore(max_polling)
    name = f"coro query_gateway() for {bgw.host}"
    avg_sleep = polling_secs

    while True:
        try:
            start = time.perf_counter()
            async with semaphore:
                logger.info(
                    f"Acquired semaphore in {name}, free {semaphore._value}"
                )
                
                diff = time.perf_counter() - start
                script = create_bgw_script(bgw)
                name = f"coro exec_script() for {bgw.host}"
                stdout = await exec_script(*script, timeout=timeout, name=name)

                if not queue:
                    return stdout
                await queue.put(stdout)

                sleep = round(max(polling_secs - diff, 0), 2)
                avg_sleep = round((avg_sleep + sleep) / 2, 2)
                logger.info(f"Sleeping {sleep}s (avg {avg_sleep}s) in {name}")
                await asyncio.sleep(sleep)

        except asyncio.CancelledError:
            logger.error(f"CancelledError in {name}")
            raise

        except asyncio.TimeoutError:
            logger.error(f"TimeoutError in {name}")
            if not queue:
                raise

        except Exception as e:
            logger.exception(f"{repr(e)} in {name}")
            if not queue:
                raise

async def discover_gateways(storage=None, callback=None) -> Tuple[int, int]:
    """Discover all connected gateways and query them.

    The function will discover all connected gateways, query each of them and
    store the result in the global GATEWAYS dictionary.

    Args:
        timeout: The timeout for each query.
        max_polling: The maximum number of concurrent queries.
        callback: A callback function that will be called with the number of
            queries performed and the total number of queries.
        ip_filter: An optional set of IP addresses to filter the gateways.

    Returns:
        A tuple with the number of successful queries, and the
        total number of queries.
    """

    GATEWAYS.clear()
    BGWS.clear()

    ip_filter = CONFIG.get("ip_filter", None)
    maxlen = CONFIG.get("storage_maxlen", None)
    storage = storage or CONFIG.get("storage", AsyncMemoryStorage(maxlen))
    name = "coro discover_gateways()"

    GATEWAYS.update({ip: BGW(ip, proto) for ip, proto in
        connected_gateways(ip_filter).items()})

    tasks = create_query_tasks()
    ok, total = 0, len(tasks)
    logger.info(f"Scheduled {total} tasks in {name}")
    
    for idx, fut in enumerate(asyncio.as_completed(tasks), start=1):
        try:
            result = await fut
            if result:
                bgw = await process_item(result, storage=storage)
                if bgw:
                    ok += 1
                    logger.info(f"Discovery {bgw.host} successful in {name}")
        except Exception as e:
            logging.exception(f"{repr(e)} in {name}")

        if callback:
            callback(idx/total)

    BGWS.extend(sorted(GATEWAYS.values(), key=lambda bgw: bgw.gw_number))
    return (idx/total)

async def poll_gateways(
    storage = None,
    callback = None,
) -> None:
    """
    Creates tasks that poll all connected gateways.

    Args:
        timeout (float, optional): The timeout for each query.
        polling_secs (float, optional): The interval between polling attempts.
        max_polling (int, optional): The maximum number of concurrent queries.
        callback (Optional[Callable[[BGW], None]], optional): A callback.

    Returns:
        None
    """

    maxlen = CONFIG.get("storage_maxlen", None)
    storage = storage or CONFIG.get("storage", AsyncMemoryStorage(maxlen))
    queue = asyncio.Queue()
    name = "poll_gateways()"

    tasks = create_query_tasks(queue=queue)
    task = create_task(
        process_queue(queue=queue, storage=storage, callback=callback),
        name="coro process_queue()",
    )
    tasks.append(task)
    logger.info(f"Started {len(tasks)} tasks in {name}")

def discovery_func_factory(stdscr):
    progress = ProgressBar(stdscr)
    async def discover_callback(fraction, **kwargs):
        nonlocal progress
        await discover_gateways(callback=progress.draw)
    return discover_callback

def cancel_func_factory(stdscr):
    async def cancel_callback(fraction, **kwargs):
        await cancel_query_coros()
    return cancel_callback

def poll_callback(bgw):
    print(f"poll_callback(): {bgw.gw_name:15} last_seen:{bgw.last_seen}")

async def process_queue(
    queue,
    storage,
    callback = None,
) -> None:
    """
    Asynchronously processes items from a queue.

    Args:
        queue (asyncio.Queue): The queue to process.
        callback (Optional[Callable[[BGW], None]], optional): A callback.
        name (str, optional): The name of the task for logging.

    Returns:
        None
    """
    name = "coro process_queue()"
    c = 0
    while True:
        item = await queue.get()
        if item:
            await process_item(item, storage=storage, callback=callback)
            c += 1
        logger.info(f"Got {c} items from queue in {name}")

async def process_item(
    item,
    storage,
    callback = None,
    name: str = "process_item()"
) -> None:
    """
    Updates a BGW object with item from a JSON string.

    Args:
        item (str): The JSON string containing the data.
        callback (Optional[Callable[[BGW], None]], optional): A callback.
        name (str, optional): The name of the function for logging.

    Returns:
        None
    """
    try:
        data = json.loads(item, strict=False)
    except json.JSONDecodeError:
        logger.error(f"JSONDecodeError in {name}")
    else:
        host = data.get("host")
        if host in GATEWAYS:
            rtp_sessions = data.get("rtp_sessions")
            if rtp_sessions:
                await storage.put(rtp_sessions)
                logger.info(
                    f"Put {len(rtp_sessions)} rtp-stats in storage in {name}"
                )
            
            bgw = GATEWAYS[host]
            bgw.update(**data)
            
            if callback:
                logger.info(f"Calling {callback.__name__}({bgw}) in {name}")
                callback(bgw)
            return bgw

def create_task(
    coro: Coroutine[Any, Any, Any], 
    name: Optional[str] = None,
    loop: asyncio.AbstractEventLoop = None,
) -> asyncio.Task:
    """Patched version of create_task that assigns a name to the task.

    Parameters
    ----------
    loop : asyncio.AbstractEventLoop
        The event loop to create the task in.
    coro : Coroutine[Any, Any, Any]
        The coroutine to run in the task.
    name : Optional[str], optional
        The name to assign to the task. Defaults to None.

    Returns
    -------
    asyncio.Task
        The newly created task.
    """
    loop = loop if loop else asyncio.get_event_loop()
    task = asyncio.ensure_future(coro, loop=loop)
    task.name = name
    return task

async def cancel_query_coros(**kwargs):
    for task in asyncio.Task.all_tasks():
        if hasattr(task, "name") and task.name.startswith("coro query_gateway"):
            task.cancel()
            await task

def change_terminal(to_type="xterm-256color"):
    old_term = os.environ.get("TERM")
    types = os.popen("toe -a").read().splitlines()
    if any(x for x in types if x.startswith(to_type)):
        os.environ["TERM"] = to_type
    return old_term

def startup():
    #logger.setLevel(CONFIG["loglevel"].upper())
    orig_term = change_terminal()
    orig_stty = os.popen("stty -g").read().strip()
    atexit.register(shutdown, orig_term, orig_stty)

def shutdown(term, stty):
    print("Shutting down")
    _ = change_terminal(term)
    os.system(f"stty {stty}")
    curses.endwin()

def get_username() -> str:
    """Prompt user for SSH username of gateways.

    Returns:
        str: The input string of SSH username.
    """
    while True:
        username = input("Enter SSH username of media-gateways: ")
        confirm = input("Is this correct (Y/N)?: ")
        if confirm.lower().startswith("y"):
            break
    return username.strip()

def get_passwd() -> str:
    """Prompt user for SSH password of gateways.

    Returns:
        str: The input string of SSH password.
    """
    while True:
        passwd = input("Enter SSH password of media-gateways: ")
        confirm = input("Is this correct (Y/N)?: ")
        if confirm.lower().startswith("y"):
            break
    return passwd.strip()

def must_resize(stdscr, miny, minx):
    stdscr.erase()
    maxy, maxx = stdscr.getmaxyx()
    
    if maxy >= miny and maxx >= minx:
        stdscr.refresh()
        return False

    msgs = [f"Resize screen to at least {miny:>3} x {minx:>3}",
            f"             Current size {maxy:>3} x {maxx:>3}",
            "Press 'q' to exit"]
    for i, msg in enumerate(msgs, start=-1):
        stdscr.addstr(maxy // 2 + 2*i, (maxx - len(msg)) // 2, msg)
    stdscr.refresh()
    return True

async def discovery_on_callback(progressbar, storage, *args, **kwargs):
    try:
        progressbar.draw()
        await create_task(discover_gateways(storage=storage,
            callback=progressbar.draw))
    except asyncio.CancelledError:
        return

async def discovery_off_callback(progressbar, *args, **kwargs):
    progressbar.erase()
    for task in asyncio.Task.all_tasks():
        if hasattr(task, "name") and task.name == "callback_on":
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            break

def discovery_done_callback(char, mydisplay, fut):
    try:
        fut.result()
    except asyncio.CancelledError:
        return
    except Exception:
        return
    curses.ungetch(char)
    mydisplay.active_workspace.draw_bodywin()

def clear_done_callback(mydisplay, fut):
    try:
        fut.result()
    except asyncio.CancelledError:
        pass
    except Exception:
        pass
    mydisplay.active_workspace.bodywin.erase()
    mydisplay.active_workspace.bodywin.refresh()

def unwrap_and_decompress(wrapped_text):
    base64_str = wrapped_text.replace('\n', '')
    compressed_bytes = base64.b64decode(base64_str)
    original_string = zlib.decompress(compressed_bytes).decode('utf-8')
    return original_string

async def clear_storage_callback(stdscr, storage, *args, **kwargs):
    logging.info("Created clear_storage_callback()")
    confirmation = Confirmation(stdscr)
    result = await confirmation.draw()
    if result:
        if asyncio.iscoroutinefunction(storage.clear):
            await storage.clear()
        else:
            storage.clear()
    confirmation.erase()

def main(stdscr, miny: int = 24, minx: int = 80):
    curses.curs_set(0)
    curses.noecho()
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)

    color_scheme = COLOR_SCHEMES[CONFIG["color_scheme"]]
    stdscr.attron(color_scheme['normal'])

    while must_resize(stdscr, miny, minx):
        char = stdscr.getch()
        if char == curses.ERR:
            time.sleep(0.1)
        elif char == curses.KEY_RESIZE:
            stdscr.erase()
        elif chr(char) in ("q", "Q"):
            return

    stdscr.resize(miny, minx)
    stdscr.box()
    stdscr.refresh()

    system_menubar = Menubar(stdscr)
    status_menubar = Menubar(stdscr)
    rtpstat_menubar = Menubar(stdscr)
    
    workspaces = [
        Workspace(
            stdscr,
            column_attrs=[x['column_attr'] for x in SYSTEM_ATTRS],
            column_names=[x['column_name'] for x in SYSTEM_ATTRS],
            column_fmt_specs=[x['column_fmt_spec'] for x in SYSTEM_ATTRS],
            column_colors=[x['column_color'] for x in SYSTEM_ATTRS],
            column_xposes=[x['column_xpos'] for x in SYSTEM_ATTRS],
            color_scheme=color_scheme,
            menubar=system_menubar,
            storage=BGWS,
            name="System",
        ),

        Workspace(
            stdscr,
            column_attrs=[x['column_attr'] for x in HW_ATTRS],
            column_names=[x['column_name'] for x in HW_ATTRS],
            column_fmt_specs=[x['column_fmt_spec'] for x in HW_ATTRS],
            column_colors=[x['column_color'] for x in HW_ATTRS],
            column_xposes=[x['column_xpos'] for x in HW_ATTRS],
            color_scheme=color_scheme,
            menubar=system_menubar,
            storage=BGWS,
            name="HW",
        ),

        Workspace(
            stdscr,
            column_attrs=[x['column_attr'] for x in MODULE_ATTRS],
            column_names=[x['column_name'] for x in MODULE_ATTRS],
            column_fmt_specs=[x['column_fmt_spec'] for x in MODULE_ATTRS],
            column_colors=[x['column_color'] for x in MODULE_ATTRS],
            column_xposes=[x['column_xpos'] for x in MODULE_ATTRS],
            color_scheme=color_scheme,
            menubar=system_menubar,
            storage=BGWS,
            name="Module",
        ),

        Workspace(
            stdscr,
            column_attrs=[x['column_attr'] for x in PORT_ATTRS],
            column_names=[x['column_name'] for x in PORT_ATTRS],
            column_fmt_specs=[x['column_fmt_spec'] for x in PORT_ATTRS],
            column_colors=[x['column_color'] for x in PORT_ATTRS],
            column_xposes=[x['column_xpos'] for x in PORT_ATTRS],
            color_scheme=color_scheme,
            menubar=system_menubar,
            storage=BGWS,
            name="Port",
        ),

      Workspace(
            stdscr,
            column_attrs=[x['column_attr'] for x in SERVICE_ATTRS],
            column_names=[x['column_name'] for x in SERVICE_ATTRS],
            column_fmt_specs=[x['column_fmt_spec'] for x in SERVICE_ATTRS],
            column_colors=[x['column_color'] for x in SERVICE_ATTRS],
            column_xposes=[x['column_xpos'] for x in SERVICE_ATTRS],
            color_scheme=color_scheme,
            menubar=system_menubar,
            storage=BGWS,
            name="Config",
        ),

        Workspace(
            stdscr,
            column_attrs=[x['column_attr'] for x in STATUS_ATTRS],
            column_names=[x['column_name'] for x in STATUS_ATTRS],
            column_fmt_specs=[x['column_fmt_spec'] for x in STATUS_ATTRS],
            column_colors=[x['column_color'] for x in STATUS_ATTRS],
            column_xposes=[x['column_xpos'] for x in STATUS_ATTRS],
            color_scheme=color_scheme,
            menubar=status_menubar,
            storage=BGWS,
            name="Status",
        ),

        Workspace(
            stdscr,
            column_attrs=[x['column_attr'] for x in RTPSTAT_ATTRS],
            column_names=[x['column_name'] for x in RTPSTAT_ATTRS],            
            column_fmt_specs=[x['column_fmt_spec'] for x in RTPSTAT_ATTRS],
            column_colors=[x['column_color'] for x in RTPSTAT_ATTRS],
            column_xposes=[x['column_xpos'] for x in RTPSTAT_ATTRS],
            color_scheme=color_scheme,
            menubar=rtpstat_menubar,
            storage=CONFIG["storage"],
            name="RTP-Stat",
        )   
    ]

    tab = Tab(stdscr, tab_names=[w.name for w in workspaces],
        color_scheme=color_scheme)
    mydisplay = MyDisplay(stdscr, workspaces=workspaces, tab=tab)

    button_d = Button(ord("d"), ord("D"),
        win=system_menubar.win,
        y=0, x=18,
        char_alt="🄳 ",
        label_off="Discovery Start",
        label_on="Discovery Stop ",
        callback_on=discovery_on_callback,
        callback_off=discovery_off_callback,
        done_callback_on=functools.partial(discovery_done_callback, ord("d"), mydisplay),
        status_label="Discovery",
        status_attr_on=curses.color_pair(42)|curses.A_REVERSE,
        status_attr_off=curses.color_pair(2)|curses.A_REVERSE,
        stdscr=stdscr,
        progressbar=ProgressBar(stdscr),
        storage=BGWS,
    )

    button_c1 = Button(ord("c"), ord("C"),
        win=system_menubar.win,
        y=0, x=38,
        char_alt="🄲 ",
        label_on="Clear",
        callback_on=clear_storage_callback,
        done_callback_on=functools.partial(clear_done_callback, mydisplay),
        stdscr=stdscr,
        storage=BGWS,
    )

    button_s = Button(ord("s"), ord("S"),
        win=rtpstat_menubar.win,
        y=0, x=18,
        char_alt="🅂 ",
        label_off="Start Polling",
        label_on="Stop  Polling",
        callback_on=None,
        callback_off=None,
        done_callback_on=None,
        status_label="Polling",
        status_attr_on=curses.color_pair(42)|curses.A_REVERSE,
        status_attr_off=curses.color_pair(2)|curses.A_REVERSE,
        stdscr=stdscr,
    )

    button_r = Button(ord("s"), ord("S"),
        win=rtpstat_menubar.win,
        y=0, x=38,
        char_alt="🅁 ",
        label_off="RTP Details",
        label_on="RTP Details",
        callback_on=None,
        callback_off=None,
        done_callback_on=None,
        status_attr_on=curses.color_pair(42)|curses.A_REVERSE,
        status_attr_off=curses.color_pair(2)|curses.A_REVERSE,
        stdscr=stdscr,
    )

    button_c2 = Button(ord("c"), ord("C"),
        win=system_menubar.win,
        y=0, x=56,
        char_alt="🄲 ",
        label_on="Clear",
        callback_on=clear_storage_callback,
        done_callback_on=functools.partial(clear_done_callback, mydisplay),
        stdscr=stdscr,
        storage=BGWS,
    )

    system_menubar.buttons = [button_d, button_c1]
    status_menubar.buttons = [button_s]
    rtpstat_menubar.buttons = [button_s, button_r, button_c2]
    
    asyncio_run(mydisplay.run())

GATEWAYS = {}
BGWS = []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Monitors Avaya Branch Gateways (BGW)')
    parser.add_argument('-c', dest='color_scheme', default='default',
                        help='Color scheme: default|green|blue|orange')
    parser.add_argument('-u', dest='username', default='',
                        help='BGW SSH username')
    parser.add_argument('-p', dest='passwd', default='',
                        help='BGW SSH password')
    parser.add_argument('-n', dest='lastn_secs', default=30,
                        help='secs to look back in RTP stats, default 30s')
    parser.add_argument('-m', dest='max_polling', default=19,
                        help='max simultaneous polling sessons, default 20')
    parser.add_argument('-l', dest='loglevel', default="ERROR",
                        help='loglevel')
    parser.add_argument('-t', dest='timeout', default=12,
                        help='timeout in secs, default 10secs')
    parser.add_argument('-f', dest='polling_secs', default=5,
                        help='polling frequency in seconds, default 5secs')
    parser.add_argument('-i', dest='ip_filter', default=None, nargs='+',
                        help='BGW IP filter')
    parser.add_argument('-s', dest='storage', 
                        default=AsyncMemoryStorage(
                                maxlen=CONFIG.get("storage_maxlen")),
                        help='RTP storage type')
    args = parser.parse_args()
    args.username = args.username or (CONFIG.get("username") or get_username())
    args.passwd = args.passwd or (CONFIG.get("passwd") or get_passwd())
    CONFIG.update(args.__dict__)
    logging.basicConfig(
        format=LOG_FORMAT,
        filename=CONFIG["logfile"],
        level=CONFIG["loglevel"].upper(),
    )
    startup()
    curses.wrapper(main)
