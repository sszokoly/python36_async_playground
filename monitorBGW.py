
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import asyncio
import atexit
import _curses, curses, curses.ascii, curses.panel
import enum
import functools
import json
import logging
import os
import re
import sys
import time
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
GATEWAYS = {}
CONFIG = {
    "username": "root",
    "passwd": "cmb@Dm1n",
    "timeout": 15,
    "polling_secs": 5,
    "max_polling": 20,
    "lastn_secs": 30,
    "loglevel": "INFO",
    "logfile": "bgw.log",
    "expect_log": "expect_log",
    "ip_filter": None,
    "storage": None,
    "storage_maxlen": None,
    "discovery_commands": [ 
        "show running-config",
        "show system",
        "show faults",
        "show capture",
        "show temp",
        "show sla-monitor",
        "show lldp config",
        "show port",
        "show mg list",
        "show voip-dsp",
        "show rtp-stat summary",
    ],
    "query_commands": [
        "show voip-dsp",
        "show rtp-stat summary",
    ]
}


script_template = '''
#!/usr/bin/expect
############################# Template Variables #############################

set host {host}
set username {username}
set passwd {passwd}
set rtp_stat {rtp_stat}
set lastn_secs {lastn_secs}
set commands {{ {commands} }}
set log_file {expect_log}

############################## Expect Variables ##############################

set timeout 10
set prompt "\\)# "
array set commands_array {{}}
array set rtp_sessions_array {{}}
set global_ids [list]
log_user 0

if {{[info exists log_file] && $log_file ne "/dev/null"}} {{
    if {{[file exists $log_file]}} {{
        file delete $log_file
    }}
}}
exp_internal -f $log_file 0

################################# Procedures #################################

proc to_json {{}} {{
    global host gw_name gw_number last_seen commands_array rtp_sessions_array
    set json "{{"
    append json "\\"host\\": \\"$host\\", "
    append json "\\"gw_name\\": \\"$gw_name\\", "
    append json "\\"gw_number\\": \\"$gw_number\\", "
    append json "\\"last_seen\\": \\"$last_seen\\", "
    append json "\\"commands\\": {{"
    foreach {{key value}} [array get commands_array] {{
        append json "\\"$key\\": \\"$value\\", "
    }}
    set json [string trimright $json ", "]
    append json "}}, "
    append json "\\"rtp_sessions\\": {{"
    foreach {{key value}} [array get rtp_sessions_array] {{
        append json "\\"$key\\": \\"$value\\", "
    }}
    set json [string trimright $json ", "]
    append json "}}}}"
    return $json
}}

proc merge_lists {{list1 list2}} {{
    set combined [concat $list1 $list2]
    set result [lsort -unique $combined]
    return $result
}}

proc clean_output {{output}} {{
    set pattern {{\\r\\n\\-\\-type q to quit or space key to continue\\-\\- .+?K}}
    regsub -all $pattern $output "" output
    set lines [split $output "\\n"]
    set prompt_removed [lrange $lines 0 end-1]
    set output [join $prompt_removed "\\n"]
    regsub -all {{"}} $output {{\\"}} output_escaped_quotes
    set result [string trimright $output_escaped_quotes "\\r\\n"]
    return $result
}}

proc cmd {{command}} {{
    global prompt
    set output ""
    send "$command"
    expect {{
        $prompt {{
            set current_output $expect_out(buffer)
            append output $current_output
        }}
        "*continue-- " {{
            set current_output $expect_out(buffer)
            append output $current_output
            send "\\n"
            exp_continue
        }}
        "*to continue." {{
            set current_output $expect_out(buffer)
            append output $current_output
            exp_continue
        }}
        "*." {{
            set current_output $expect_out(buffer)
            append output $current_output
            sleep 1
            exp_continue
        }}
        timeout {{
            puts stderr "Timeout";
            return ""
        }}
    }}
    set result [clean_output $output]
    return [string trimleft $result $command]
}}

proc get_active_global_ids {{}} {{
    global cmd parse_session_summary_line, gw_number
    set ids [list]
    foreach line [split [cmd "show rtp-stat sessions active\\n"] "\\n"] {{
        if {{[regexp {{^[0-9]+}} $line]}} {{
            set result [parse_session_summary_line $line]
            lassign $result session_id start_date start_time end_date end_time
            lappend ids [format "%s,%s,%s,%s" $start_date $start_time $gw_number $session_id]
        }}
    }}
    return $ids
}}

proc get_recent_global_ids {{{{lastn_secs {{20}}}}}} {{
    global cmd parse_session_summary_line is_date1_gt_date2 gw_number
    set ref_datetime [exec date "+%Y-%m-%d,%H:%M:%S" -d "now - $lastn_secs secs"]
    set ids [list]
    foreach line [split [cmd "show rtp-stat sessions last 20\\n"] "\\n"] {{
        if {{[regexp {{^[0-9]+}} $line]}} {{
            set result [parse_session_summary_line $line]
            lassign $result session_id start_date start_time end_date end_time
            if {{$end_time ne "-"}} {{
                set end_datetime [format "%s,%s" $end_date $end_time]
                set is_end_datetime_gt_ref_datetime [is_date1_gt_date2 $end_datetime $ref_datetime]
                if {{$is_end_datetime_gt_ref_datetime}} {{
                    lappend ids [format "%s,%s,%s,%s" $start_date $start_time $gw_number $session_id]
                }}
            }}
        }}
    }}
    return $ids
}}

proc parse_session_summary_line {{input}} {{
    set pattern {{^(\\S+)  (\\*|\\s)  (\\S+),(\\S+)\\s+(\\S+)\\s+.*$}}
    if {{[regexp $pattern $input _ id qos start_date start_time end_time]}} {{
        # if end time rolled over to the next day
        if {{$end_time < $start_time}} {{
            set end_date [exec date "+%Y-%m-%d" -d "$start_date + 1 day"]
        }} else {{
            set end_date $start_date
        }}
        return [list $id "$start_date" "$start_time" "$end_date" "$end_time"]
    }} else {{
        puts stderr "Error: Input format does not match: $input";
        return ""
    }}
}}

proc is_date1_gt_date2 {{date1 date2}} {{
    # Convert the date strings into epoch timestamps
    set timestamp1 [clock scan $date1 -format "%Y-%m-%d,%H:%M:%S"]
    set timestamp2 [clock scan $date2 -format "%Y-%m-%d,%H:%M:%S"]
    # Compare the timestamps
    if {{$timestamp1 > $timestamp2}} {{
        return 1
    }} else {{
        return 0 
    }}
}}

################################# Main Script ################################

#Spawn SSH connection
spawn ssh -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $username@$host

#Handle SSH connection
expect {{
    "Password: " {{send "$passwd\\n"}}
    timeout {{
        puts -nonewline stderr "ExpectTimeout";
        exit 255
    }}
    eof {{
        puts -nonewline stderr "ExpectTimeout";
        exit 255
    }}
}}
expect {{
    "*Permission denied*" {{
        puts -nonewline stderr "PermissionDenied";
        exit 255
    }}
    $prompt {{}}
}}

#Extract gateway name and number from prompt
regexp {{([^\\s]+)-(\\d+)[\\(]}} $expect_out(buffer) "" gw_name gw_number
if {{$gw_name ne ""}} {{
    set gw_name $gw_name
}} else {{
    set gw_name ""
}}
if {{$gw_number ne ""}} {{
    set gw_number $gw_number
}} else {{
    set gw_number ""
}}

#Capture last_seen
set last_seen [exec date "+%Y-%m-%d,%H:%M:%S"]

#Collect RTP statistics if requested
if {{$rtp_stat}} {{
    #Recent global session ids
    set recent_global_ids [get_recent_global_ids $lastn_secs]
    #Active global session ids
    set active_global_ids [get_active_global_ids]
    #Merged global session ids
    set merged_global_ids [merge_lists $recent_global_ids $active_global_ids]

    if {{$merged_global_ids ne {{}}}} {{
        foreach global_id $merged_global_ids {{
            lassign [split $global_id ","] start_date start_time gw_number session_id
            set output [cmd "show rtp-stat detailed $session_id\\n"]
            set status [catch {{set output [cmd "show rtp-stat detailed $session_id\\n"]}} errmsg]
            if {{$status != 0}} {{
                puts -nonewline stderr "ExpectTimeout during \\"show rtp-stat detailed $session_id\\"";
                exit 255
            }} else {{
                if {{$output ne ""}} {{
                    set rtp_sessions_array($global_id) $output
                }}
            }}
        }}
    }}
}}

#Iterate through "commands" and run each
foreach command $commands {{
    #set output [cmd "$command\\n"]
    set status [catch {{set output [cmd "$command\\n"]}} errmsg]
    if {{$status != 0}} {{
        puts -nonewline stderr "ExpectTimeout during \\"$command\\"";
        exit 255
    }} else {{
        if {{$output ne ""}} {{
            set commands_array($command) $output
        }}
    }}
}}

#Output results in JSON format
puts [to_json]

send "exit\\n"
'''

script_template = '''
set host {host}
set username {username}
set passwd {passwd}
set rtp_stat {rtp_stat}
set lastn_secs {lastn_secs}
set commands {{ {commands} }}
set log_file {expect_log}

set randomInt [expr {{int(rand() * 4)}}]

sleep 2
set last_seen [exec date "+%Y-%m-%d,%H:%M:%S"]

if {{$randomInt == 1}} {{
    puts -nonewline stderr "ExpectTimeout"; exit 255
}}
puts "{{\\"gw_number\\": \\"001\\", \\"gw_name\\": \\"$host\\", \\"host\\": \\"$host\\", \\"last_seen\\": \\"$last_seen\\", \\"commands\\": {{\\"show system\\": \\"location: 1\\", \\"show running-config\\": \\"location: 1\\"}}, \\"rtp_sessions\\": {{\\"2024-12-30,11:06:15,$host,0000$randomInt\\": \\"session 0000$randomInt\\"}}}}"
'''

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

################################## CLASSES ##################################

class BGW():
    def __init__(self,
        host: str,
        proto: str = '',
        last_seen = None,
        gw_name: str = '',
        gw_number: str = '',
        show_running_config: str = '',
        show_system: str = '',
        show_faults: str = '',
        show_capture: str = '',
        show_voip_dsp: str = '',
        show_temp: str = '',
        show_sla_monitor: str = '',
    ) -> None:
        self.host = host
        self.proto = proto
        self.last_seen = last_seen
        self.gw_name = gw_name
        self.gw_number = gw_number
        self.show_running_config = show_running_config
        self.show_system = show_system
        self.show_faults = show_faults
        self.show_capture = show_capture
        self.show_voip_dsp = show_voip_dsp
        self.show_temp = show_temp
        self.show_sla_monitor = show_sla_monitor
        self.queue = Queue()
        self._faults = None
        self._capture = None
        self._model = None
        self._hw = None
        self._fw = None
        self._slamon = None
        self._serial = None
        self._rtp_stat = None
        self._capture = None
        self._temp = None
        self._uptime = None
        self._voip_dsp = None
        self._sla_server = None

    @property
    def model(self):
        if not self._model:
            m = re.search(r'Model\s+:\s+(\S+)', self.show_system)
            self._model = m.group(1) if m else "?"
        return self._model

    @property
    def hw(self):
        if not self._hw:
            m = re.search(r'HW Vintage\s+:\s+(\S+)', self.show_system)
            hw_vintage = m.group(1) if m else "?"
            m = re.search(r'HW Suffix\s+:\s+(\S+)', self.show_system)
            hw_suffix = m.group(1) if m else "?"
            self._hw = f"{hw_vintage}{hw_suffix}"
        return self._hw

    @property
    def fw(self):
        if not self._fw:
            m = re.search(r'FW Vintage\s+:\s+(\S+)', self.show_system)
            self._fw = m.group(1) if m else "?"
        return self._fw

    @property
    def slamon(self):
        if not self._slamon:
            m = re.search(r'sla-server-ip-address (\S+)', self.show_system)
            self._slamon = m.group(1) if m else ""
        return self._slamon

    @property
    def serial(self):
        if not self._serial:
            m = re.search(r'Serial No\s+:\s+(\S+)', self.show_system)
            self._serial = m.group(1) if m else "?"
        return self._serial

    @property
    def rtp_stat(self):
        if not self._rtp_stat:
            m = re.search(r'rtp-stat-service', self.show_running_config)
            self._rtp_stat = "enabled" if m else "disabled"
        return self._rtp_stat

    @property
    def capture(self):
        if not self._capture:
            m = re.search(r'Capture service is (\w+) and (\w+)', self.show_capture)
            config, state = m.group(1, 2) if m else ("?", "?")
            self._capture = config if config == "disabled" else state
        return self._capture

    @property
    def temp(self):
        if not self._temp:
            m = re.search(r'Temperature\s+:\s+(\S+) \((\S+)\)', self.show_temp)
            cels, faren = m.group(1, 2) if m else ("?", "?")
            self._temp = f"{cels}/{faren}"
        return self._temp

    @property
    def faults(self):
        if not self._faults:
            if "No Fault Messages" in self.show_faults:
                self._faults = "none"
            else:
                self._faults = "faulty"
        return self._faults

    @property
    def uptime(self):
        if not self._uptime:
            m = re.search(r'Uptime.+?:\s+(\S+)', self.show_system)
            self._uptime = m.group(1) if m else "?"
        return self._uptime

    @property
    def voip_dsp(self):
        inuse, total = 0, 0
        dsps = re.findall(
            r"In Use\s+:\s+(\d+) of (\d+) channels", self.show_voip_dsp
        )
        for dsp in dsps:
            try:
                dsp_inuse, dsp_total = dsp
                inuse += int(dsp_inuse)
                total += int(dsp_total)
            except:
                pass
        total = total if total > 0 else "?"
        inuse = inuse if total > 0 else "?"
        return f"{inuse}/{total}"

    @property
    def sla_server(self):
        if not self._sla_server:
            m = re.search(
                r'Registered Server IP Address:\s+(\S+)', self.show_sla_monitor
            )
            self._sla_server = m.group(1) if m.group(1) != "0.0.0.0" else ""
        return self._sla_server

    def update(self, data):
        self.last_seen = data.get("last_seen", self.last_seen)
        self.gw_name = data.get("gw_name", self.gw_name)
        self.gw_number = data.get("gw_number", self.gw_number)
        commands = data.get("commands", {})
        if commands:
            for cmd, value in commands.items():
                bgw_attr = cmd.replace(" ", "_").replace("-", "_")
                setattr(self, bgw_attr, value)

    def __str__(self):
        return f"BGW({self.host})"

    def __repr__(self):
        return f"BGW(host={self.host})"

    def asdict(self):
        return self.__dict__

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
        self.state = False
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
        color_pair=None,
    ):
        self.stdscr = stdscr
        self._tab_names = tab_names
        self._tab_width = max(len(x) for x in self._tab_names) + 2
        self._yoffset = yoffset
        self._xoffset = xoffset
        self._color_pair = color_pair if color_pair else curses.color_pair(0)
        self._active_tab_idx = 0
        self.maxy = nlines
        self.maxx = self.stdscr.getmaxyx()[1]
        self.win = self.stdscr.subwin(nlines, self.maxx, yoffset, xoffset)

    def draw(self):
        xpos = self._xoffset
        for idx, tab_names in enumerate(self._tab_names):
            active = bool(idx == self._active_tab_idx)
            self._draw_tab(tab_names, self._yoffset, xpos, active)
            xpos += self._tab_width + 2
        self.win.refresh()

    def _draw_tab(self, tab_name, ypos, xpos, active):
        border1 = "╭" + self._tab_width * "─" + "╮"
        border2 = "│" + " " * self._tab_width + "│"
        self.win.addstr(ypos, xpos, border1, self._color_pair)
        for linen in range(1, self.maxy):
            self.win.addstr(ypos + linen, xpos, border2, self._color_pair)
        text = tab_name.center(self._tab_width)
        if not active:
            text_color_pair = self._color_pair
        else:
            text_color_pair = self._color_pair|curses.A_REVERSE
        self.win.addstr(ypos + 1, xpos+1, text, text_color_pair)

    async def handle_char(self, char):
        if chr(char) == "\t":
            if self._active_tab_idx < len(self._tab_names) - 1: 
                self._active_tab_idx += 1
            else:
                self._active_tab_idx = 0
            self.draw()

class Workspace:
    def __init__(self, stdscr, column_attrs, *,
        column_names=None,
        column_widths=None,
        menubar=None,
        name=None,
        storage=None,
        attr=None,
        offset_y=2,
        offset_x=0,
        title_width=3,
        colors_pairs=None,
    ):
        self.stdscr = stdscr
        self.column_attrs = column_attrs
        self.column_names = column_names or column_attrs
        self.column_widths = column_widths or [len(x) for x in column_attrs]
        self.menubar = menubar
        self.name = name
        self.storage = storage or []
        self.attr = attr or curses.color_pair(0)
        self.offset_y = offset_y
        self.offset_x = offset_x
        self.colors_pairs = colors_pairs
        self.title_width = title_width
        self.posy = 0
        self.posx = 0
        self.row_pos = 0
        self.maxy = self.stdscr.getmaxyx()[0] - offset_y
        self.maxx = sum(x + 1 for x in self.column_widths) + 1
        self.titlewin = stdscr.subwin(title_width, self.maxx,
            offset_y, offset_x)
        self.bodywin = self.stdscr.subwin(
            self.maxy - title_width, self.maxx, offset_y + title_width,
            offset_x)

    def draw(self):
        self.draw_titlewin()
        self.draw_bodywin()
        self.draw_menubar()

    def draw_titlewin(self):
        self.titlewin.attron(self.attr)
        self.titlewin.box()
        self.titlewin.attroff(self.attr)
        offset = 0
        for idx, (cname, cwidth) in enumerate(zip(self.column_names,
                                                self.column_widths)):
            cname = f"│{cname:^{cwidth}}"
            xpos = self.offset_x if idx == 0 else offset
            offset = xpos + len(cname)
            self.titlewin.addstr(1, xpos, cname, self.attr)
            if idx > 0:
                self.titlewin.addstr(0, xpos, "┬", self.attr)
                self.titlewin.addstr(2, xpos, "┼", self.attr)
        try:
            self.titlewin.addstr(2, self.offset_x, "├", self.attr)
            self.titlewin.addstr(2, self.maxx - 1, "┤", self.attr)
        except curses.error:
            pass
        self.titlewin.refresh()

    def draw_bodywin(self):
        start_row = self.row_pos
        end_row = min(self.row_pos + (self.maxy - 3), len(self.storage))
        for ridx, row in enumerate(self.storage[start_row:end_row]):
            offset = 0
            try:
                for cidx, (attr, width) in enumerate(zip(self.column_attrs,
                                                         self.column_widths)):
                    xpos = self.offset_x if cidx == 0 else offset
                    
                    if hasattr(row, attr):
                        item = getattr(row, attr)
                    else:
                        item = row.get(attr)
                    item = f"│{str(item)[-width:]:>{width}}"
                    
                    if hasattr(item, "attr"):
                        cpair = getattr(row, "attr")
                    elif hasattr(item, "get"):
                        cpair = item.get("attr", self.attr)
                    else:
                        cpair = self.attr
                    if ridx == self.posy:
                        cpair = cpair|curses.A_REVERSE
                    
                    offset = xpos + len(item)
                    self.bodywin.addstr(ridx, xpos, item, cpair)
                self.bodywin.addstr(ridx, xpos + len(item), "│", cpair)
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

class Popup:
    def __init__(
        self,
        stdscr,
        body,
        attr=None,
        offset_y=-1,
        margin=1,
    ) -> None:
        self.stdscr = stdscr
        self.body = body
        self.attr = attr if attr else curses.color_pair(0)
        self.offset_y = offset_y
        self.margin = margin
        self._initialize()
    
    def draw(self, body=None):
        if body:
            self.win.erase()
            self.body = body
        self.win.box()
        self.win.addstr(self.margin + 1, self.margin + 1, self.body, self.attr)
        self.win.refresh()
        return self

    def erase(self):
        self.win.erase()
        self.win.refresh()
        return self

    def _initialize(self):
        maxy, maxx = self.stdscr.getmaxyx()
        nlines = 3 + (2 * self.margin)
        ncols = len(self.body) + (2 * self.margin) + 2
        begin_y = maxy // 2 + self.offset_y - (self.margin + 1)
        begin_x = maxx // 2 - (len(self.body) // 2) - (self.margin + 1)
        self.win = curses.newwin(nlines, ncols, begin_y, begin_x)
        curses.panel.new_panel(self.win)
        self.win.attron(self.attr)

class Menubar:
    def __init__(self, stdscr: "_curses._CursesWindow",
        nlines: Optional[int] = 1,
        attr: Optional[int] = None,
        offset_x: Optional[int] = 0,
        status_bar_width: Optional[int] = 20,
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
                #self.stdscr.refresh()
                #curses.doupdate()

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

    def start(self):
        time.sleep(1)
        return True

    def stop(self):
        time.sleep(1)
        return True

    def draw_rtppanel(self, stdscr, maxy, maxx, ypos):
        rtppanel = MyPanel(stdscr, body="whatever")
        time.sleep(0.2)
        rtppanel.draw()
        curses.panel.update_panels()
        return True

    def erase_rtppanel(self, ypos, rtppanel, stdpanel):
        time.sleep(0.2)
        rtppanel.erase()
        return True

    def discover_start(self, stdscr):
        fraction = 0
        progbar = ProgressBar(stdscr, fraction=fraction)
        for _ in range(20):
            fraction += 0.05
            progbar.draw(fraction)
            time.sleep(0.2)

    def discover_stop():
        curses.panel.update_panels()


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

    global GATEWAYS
    ip_filter = CONFIG.get("ip_filter", None)
    maxlen = CONFIG.get("storage_maxlen", None)
    storage = storage or CONFIG.get("storage", AsyncMemoryStorage(maxlen))
    name = "coro discover_gateways()"

    GATEWAYS = {ip: BGW(ip, proto) for ip, proto in
        connected_gateways(ip_filter).items()}

    tasks = create_query_tasks()
    ok, total = 0, len(tasks)
    logger.info(f"Scheduled {total} tasks in {name}")
    
    for idx, fut in enumerate(asyncio.as_completed(tasks), start=1):
        try:
            result = await fut
            if result:
                bgw = await process_item(result, storage=storage, callback=callback)
                if bgw:
                    ok += 1
                    logger.info(f"Discovery {bgw.host} successful in {name}")
        except Exception:
            pass

        if callback:
            callback(idx/total)
    
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
            bgw.update(data)
            
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

def draw_rtppanel(**kwargs):
    print(kwargs)
    rtppanel = MyPanel(kwargs['stdscr'], body="whatever")
    rtppanel.draw()
    return rtppanel

def erase_rtppanel(**kwargs):
    kwargs["rtppanel"].erase()
    curses.panel.update_panels()


async def discovery_on_callback(progressbar, *args, **kwargs):
    try:
        for i in range(1, progressbar.width):
            progressbar.draw(i / 20)
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        return

async def discovery_off_callback(progressbar, *args, **kwargs):
    for task in asyncio.Task.all_tasks():
        if hasattr(task, "name") and task.name == "callback_on":
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            break
    progressbar.erase()

def ungetch_done_callback(char, fut):
    try:
        fut.result()  # Will raise CancelledError if the task was cancelled.
    except asyncio.CancelledError:
        # If cancelled, leave self.state True.
        return
    except Exception:
        # Optionally log or handle exceptions here.
        return
    curses.ungetch(char)

def main(stdscr, miny: int = 24, minx: int = 80):
    curses.curs_set(0)
    curses.noecho()
    curses.start_color()
    curses.use_default_colors()

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
    
    button_d = Button(ord("d"), ord("D"),
        win=system_menubar.win,
        y=0, x=25,
        char_alt="🄳 ",
        label_on="Discovery Stop ",
        label_off="Discovery Start",
        callback_on=discovery_on_callback,
        callback_off=discovery_off_callback,
        done_callback_on=functools.partial(ungetch_done_callback, ord("d")),
        status_label="Discovery",
        status_attr_on=curses.color_pair(42)|curses.A_REVERSE,
        status_attr_off=curses.color_pair(2)|curses.A_REVERSE,
        stdscr=stdscr,
        progressbar=ProgressBar(stdscr)
    )

    button_c = Button(ord("c"), ord("C"),
        win=system_menubar.win,
        y=0, x=45,
        char_alt="🄲 ",
        label_on="Clear",
    )

    system_menubar.buttons = [button_d, button_c]

    rtpstat_menubar = Menubar(stdscr)

    button_s = Button(ord("s"), ord("S"),
        win=rtpstat_menubar.win,
        y=0, x=45,
        char_alt="🄲 ",
        label_off="Start",
        label_on="Stop",
    )

    rtpstat_menubar.buttons = [button_s]
    
    workspaces = [
        Workspace(
            stdscr,
            column_attrs = [
                "gw_number", "model", "firmware", "hw",
                "host", "slamon", "rtp_stat", "faults",
            ],
            column_names = [
                "BGW", "Model", "FW", "HW", "LAN IP",
                "SLAMon IP", "RTP-Stat", "Faults",
            ],
            column_widths = [3, 5, 8, 2, 15, 15, 8, 6],
            menubar = system_menubar,
            storage = GATEWAYS,
            name = "Systems",
        ),
        
        Workspace(
            stdscr,
            column_attrs=[
                "start_time", "end_time", "gw_number",
                "local_addr", "local_port", "remote_addr",
                "remote_port", "codec", "qos",
            ],
            column_names=[
                "Start", "End", "BGW", "Local-Address", "LPort",
                "Remote-Address", "RPort", "Codec", "QoS",
            ],
            column_widths=[8, 8, 3, 15, 5, 15, 5, 5, 3],
            menubar = rtpstat_menubar,
            storage = CONFIG["storage"],
            name = "RTPStat",
        )   
    ]
    
    tab = Tab(stdscr, tab_names=[w.name for w in workspaces])
    display = MyDisplay(stdscr, workspaces=workspaces, tab=tab)
    asyncio_run(display.run())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Monitors Avaya Branch Gateways (BGW)')
    parser.add_argument('-u', dest='username', default='', help='BGW username')
    parser.add_argument('-p', dest='passwd', default='', help='BGW password')
    parser.add_argument('-n', dest='lastn_secs', default=30, help='secs to look back in RTP statistics, default 30secs')
    parser.add_argument('-m', dest='max_polling', default=19, help='max simultaneous polling sessons, default 20')
    parser.add_argument('-l', dest='loglevel', default="INFO", help='loglevel')
    parser.add_argument('-t', dest='timeout', default=12, help='timeout in secs, default 10secs')
    parser.add_argument('-f', dest='polling_secs', default=5, help='polling frequency in seconds, default 5secs')
    parser.add_argument('-i', dest='ip_filter', default=None, nargs='+', help='BGW IP filter')
    parser.add_argument('-s', dest='storage', default=AsyncMemoryStorage(maxlen=CONFIG.get("storage_maxlen")), help='RTP storage type')
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

# System
# +---+---------------+-----+--+--------+------------+------+---+---+-----+----+
# |BGW|     LAN IP    |Model|HW|Firmware|  Serial No |Memory|DSP|PSU|Fault|Anns|   
# +---+---------------+-----+--+--------+------------+------+---+---+-----+----+
# |001|192.168.111.111| g430|1A|43.11.12|13TG01116522| 256MB|160|  1|    3| 999|
# +---+---------------+-----+--+--------+------------+------+---+---+-----+----+

# Port
# +---+----+---------+-------+-----+----+----+---------+-------+-----+----+----+
# |BGW|Port| Status  |  Neg  |Speed|Dupl|Port| Status  |  Neg  |Speed|Dupl|Redu|
# +---+----+---------+-------+-----+----+----+---------+-------+-----+----+----+
# |001|10/4|connected|disable| 100M|half|10/5|connected|disable| 100M|half| 4&5|
# +---+----+---------+-------+-----+----+----+---------+-------+-----+----+----+

# Config
# +---+---------+---------------+----+--------+---------------+--------+-------+
# |BGW|rtp-stats|capture-service|snmp| slamon | slamon server |  lldp  |  lsp  |
# +---+---------+---------------+----+--------+---------------+--------+-------+
# |001| disabled|       disabled|v2&3|disabled|101.101.111.198|disabled| S8300E|
# +---+---------+---------------+----+--------+---------------+--------+-------+

# Status
# +---+-------------+------------+------------+---------------+----------+-----+
# |BGW|    Uptime   |Act Sessions|Tot Sessions|In-Use/Tot DSPs|AvgPollSec|Polls|
# +---+-------------+------------+------------+---------------+----------+-----+
# |001|153d05h23m06s|         0/0|  32442/1443|        320/230|    120.32|    3|
# +---+-------------+------------+------------+---------------+----------+-----+

# RTP-Stat
# +--------+--------+---+---------------+-----+---------------+-----+-----+----+
# |  Start |   End  |BGW| Local-Address |LPort| Remote-Address|RPort|Codec| QoS|
# +--------+--------+---+---------------+-----+---------------+-----+-----+----+
# |11:09:07|11:11:27|001|192.168.111.111|55555|100.100.100.100|55555|G711U|  OK|
# +--------+--------+---+---------------+-----+---------------+-----+-----+----+
