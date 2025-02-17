
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from asyncio import coroutines
from asyncio import events
from asyncio import tasks
from asyncio import Lock, Queue, Semaphore
from bisect import insort_left
from collections import deque
from collections.abc import MutableMapping
from typing import Any, Callable, Coroutine, Optional, Tuple
from subprocess import CalledProcessError
from datetime import datetime
from typing import AsyncIterator, Iterable, Iterator, Optional, Tuple, Union, TypeVar, Any, Dict, List, Set

logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s - %(levelname)8s - %(message)s [%(filename)s:%(lineno)s]"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)

############################ CONSTATS, VARIABLES ############################

GATEWAYS = {}

config = {
    "username": "root",
    "passwd": "cmb@Dm1n",
    "timeout": 10,
    "polling_secs": 5,
    "max_polling": 20,
    "lastn_secs": 30,
    "loglevel": "ERROR",
    "logfile": "bgw.log",
    "expect_log": "expect_log",
    "ip_filter": None,
    "discovery_commands": [ 
        "show running-config",
        "show system",
        "show faults",
        "show capture",
        "show voip-dsp",
        "show temp",
    ],
    "query_commands": [
        "show voip-dsp",
        "show capture",
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

#if {{$randomInt == 1}} {{
#    puts -nonewline stderr "ExpectTimeout"; exit 255
#}}
puts "{{\\"gw_number\\": \\"001\\", \\"gw_name\\": \\"$host\\", \\"host\\": \\"$host\\", \\"last_seen\\": \\"$last_seen\\", \\"commands\\": {{\\"show system\\": \\"location: 1\\", \\"show running-config\\": \\"location: 1\\"}}, \\"rtp_sessions\\": {{\\"2024-12-30,11:06:15,$host,000$randomInt\\": \\"session 000$randomInt\\"}}}}"
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
        self.queue = Queue()
        self._faults = None
        self._capture = None
        self._model = None
        self._hw = None
        self._firmware = None
        self._slamon = None
        self._serial = None
        self._rtp_stat = None
        self._capture = None
        self._temp = None
        self._uptime = None
        self._voip_dsp = None

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
    def firmware(self):
        if not self._firmware:
            m = re.search(r'FW Vintage\s+:\s+(\S+)', self.show_system)
            self._firmware = m.group(1) if m else "?"
        return self._firmware

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
            if not self.show_running_config:
                self._rtp_stat = "?"
            else:
                m = re.search(r'rtp-stat-service', self.show_running_config)
                self._rtp_stat = "enabled" if m else 'disabled'
        return self._rtp_stat

    @property
    def capture(self):
        if not self._capture:
            m = re.search(r'Capture service is (\w+) and (\w+)', self.show_capture)
            if m:
                config, state = m.group(1, 2)
                self._capture = config if config == "disabled" else state
            else:
                self._capture = "?"
        return self._capture

    @property
    def temp(self):
        if not self._temp:
            m = re.search(r'Temperature\s+:\s+(\S+) \((\S+)\)', self.show_temp)
            if m:
                cels, faren = m.group(1, 2)
                self._temp = f"{cels}/{faren}"
            else:
                self._temp = "?"
        return self._temp

    @property
    def faults(self):
        if not self._faults:
            if not self.show_faults:
                self._faults = "?"
            elif "No Fault Messages" in self.show_faults:
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
        dsps = re.findall(r"In Use\s+:\s+(\d+) of (\d+) channels", self.show_voip_dsp)
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

    def update(self, data):
        self.last_seen = data.get("last_seen", self.last_seen)
        self.gw_name = data.get("gw_name", self.gw_name)
        self.gw_number = data.get("gw_number", self.gw_number)
        self.show_running_config = data.get("commands", {}).get("show running-config", self.show_running_config)
        self.show_system = data.get("commands", {}).get("show system", self.show_system)
        self.show_faults = data.get("commands", {}).get("show faults", self.show_faults)
        self.show_capture = data.get("commands", {}).get("show capture", self.show_capture)
        self.show_voip_dsp = data.get("commands", {}).get("show voip-dsp", self.show_voip_dsp)
        self.show_temp = data.get("commands", {}).get("show temp", self.show_temp)

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

    def __len__(self):
        return len(self._items)

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

def custom_create_task(
    loop: asyncio.AbstractEventLoop, 
    coro: Coroutine[Any, Any, Any], 
    name: Optional[str] = None
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
    task = asyncio.tasks.Task(coro, loop=loop)
    task.name = name
    return task

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
        A list of the command, arguments, and script to execute the expect script.
    """
    if logger.getEffectiveLevel() == 10:
        expect_log = "_".join((config["expect_log"], bgw.host))
    else:    
        expect_log = "/dev/null"
    if not bgw.last_seen:
        rtp_stat = 0
        commands = config["discovery_commands"]
    else:
        rtp_stat = 1
        commands = config["query_commands"]
        if not bgw.queue.empty():
            queued_commands = bgw.queue.get_nowait()
            if isinstance(queued_commands, str):
                queued_commands = [queued_commands]
            commands.extend(queued_commands)
    
    script = script_template.format(**{
        "host": bgw.host,
        "username": config["username"],
        "passwd": config["passwd"],
        "rtp_stat": rtp_stat,
        "lastn_secs": config["lastn_secs"],
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

async def query_gateway(
    bgw: BGW,
    timeout: float = 2,
    queue: Optional[Queue] = None,
    polling_secs: float = 5,
    semaphore: Optional[Semaphore] = None,
    name: Optional[str] = None
) -> str:
    """
    Asynchronously runs a ping command and returns the output.
    If `queue` is provided, the output is put onto the queue and the function
    does not return. Otherwise, the output is returned directly.

    :param ip: The IP address to ping
    :param timeout: The timeout for the ping command
    :param queue: The queue to put the output onto
    :param polling_secs: The time to wait between pings
    :param semaphore: The semaphore to use for limiting concurrency
    :param name: The name of the task
    :return: The output of the cmd
    """
    name = name if name else bgw.host
    semaphore = semaphore if semaphore else Semaphore(1)
    proc = None

    while True:
        try:
            start = time.perf_counter()
            async with semaphore:
                logger.debug(f"Acquired semaphore in '{name}', free {semaphore._value}")
                
                diff = time.perf_counter() - start
                script = create_bgw_script(bgw)
                proc = await asyncio.create_subprocess_exec(
                    *script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                logger.debug(f"Created process PID {proc.pid} in '{name}'")
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(), timeout
                    )

                    stdout_str = stdout.decode().strip()
                    stderr_str = stderr.decode().strip()

                    if proc.returncode != 0:
                        caught_exception = CalledProcessError(
                            returncode=proc.returncode,
                            cmd=script,
                            stderr=stderr_str,
                            output=stdout_str,
                        )
                        logger.error(f"CalledProcessError with stderr={stderr_str} in '{name}'")

                        if queue and stderr_str and proc.returncode == 255:
                            pass
                        else:
                            raise caught_exception
                    
                    else:
                        if not queue:
                            return stdout_str
                        else:
                            queue.put_nowait(stdout_str)
                
                except asyncio.TimeoutError:
                    logger.error(f"TimeoutError in '{name}'")
                    if not queue:
                        raise

                sleep_secs = round(max(polling_secs - diff, 0), 2)
                logger.debug(f"Sleeping {sleep_secs}s in '{name}'")
                await asyncio.sleep(sleep_secs)

        except asyncio.CancelledError:
            logger.error(f"CancelledError in '{name}'")
            raise

        finally:
            logger.debug(f"Released semaphore in {name}, free {semaphore._value}")
            if proc and proc.returncode is None:
                logger.debug(f"Terminating PID {proc.pid} in '{name}'")
                proc.kill()
                #proc._transport.close()
                try:
                    await proc.wait()
                except Exception as e:
                    logger.error(f"{repr(e)} for PID {proc.pid} in '{name}'")

async def discover_gateways(
    loop,
    timeout=10,
    max_polling=20,
    callback=None,
) -> None:
    global GATEWAYS
    GATEWAYS = {}
    semaphore = Semaphore(max_polling)
    
    GATEWAYS = {ip: BGW(ip, proto) for ip, proto in
        connected_gateways().items()}

    tasks = []
    for bgw in GATEWAYS.values():
        name = f"'query_gateway({bgw.host})'"
        task = loop.create_task(query_gateway(
            bgw,
            timeout=timeout,
            semaphore=semaphore,
            name=name
        ), name=name)
        tasks.append(task)

    ok, ex, total = 0, 0, len(tasks)
    for fut in asyncio.as_completed(tasks):
        try:
            result = await fut
            update_gateway(result)
            ok += 1
        except Exception as e:
            ex += 1
        if callback:
            callback(ok, ex, total)
    
    return (ok, ex, total)


async def poll_gateways(
    loop,
    timeout=10,
    max_polling=20,
    callback=None,
) -> None:
    global GATEWAYS
    semaphore = Semaphore(max_polling)
    queue = asyncio.Queue(loop=loop)

    tasks = []
    for bgw in GATEWAYS.values():
        name = f"query_gateway({bgw.host})"
        task = loop.create_task(query_gateway(
            bgw,
            timeout=timeout,
            semaphore=semaphore,
            queue=queue,
            name=name
        ), name=name)
        tasks.append(task)

    name = "process_queue()"
    task = loop.create_task(process_queue(
        queue=queue, callback=callback, name=name,
    ), name=name)
    tasks.append(task)

def discover_callback(ok, ex, total):
    print(f"ok:{ok}/ex:{ex}/total:{total}")

def poll_callback(bgw):
    print(f"{bgw.gw_name:15} last seen at {bgw.last_seen}")

async def process_queue(queue, callback=None, name=None):
    c = 0
    while True:
        data = await queue.get()
        update_gateway(data, callback=callback)
        c += 1
        logging.debug(f"Processed {c} data in '{name}'")

def update_gateway(data, callback=None):
    try:
        data = json.loads(data, strict=False)
    except json.JSONDecodeError:
        logging.error("JSONDecodeError")
    else:
        host = data.get("host")
        if host:
            GATEWAYS[host].update(data)
            if callback:
                callback(GATEWAYS[host])

async def main():
    loop = asyncio.get_event_loop()
    loop.create_task = lambda coro, name=None: custom_create_task(loop, coro, name)

    print("##### DISCOVER GATEWAYS #####")
    discover_task = loop.create_task(discover_gateways(
        loop=loop,
        timeout=config["timeout"],
        max_polling=config["max_polling"],
        callback=discover_callback,
    ), name="discover_gateways()")
    
    await asyncio.gather(discover_task)

    print("##### POLLING  GATEWAYS #####")
    polling_task = loop.create_task(poll_gateways(
        loop=loop,
        timeout=config["timeout"],
        max_polling=config["max_polling"],
        callback=poll_callback,
    ), name="poll_gateways()")
    
    await asyncio.sleep(20)
    print("##### SHUTTING DOWN #####")
    cancel_tasks = []
    for task in asyncio.Task.all_tasks(loop):
        if hasattr(task, "name") and not task.done():
            print(f"Canceling task '{task.name}'")
            task.cancel()
            cancel_tasks.append(task)
    await asyncio.gather(*cancel_tasks, return_exceptions=True)

if __name__ == "__main__":
    def get_username() -> str:
        """Prompt user for SSH username of gateways.

        Returns:
            str: The input string of SSH username.
        """
        while True:
            username = input("Enter SSH username of media-gateways: ")
            comfirm = input("Is this correct (Y/N)?: ")
            if comfirm.lower().startswith("y"):
                break
        return username.strip()

    def get_passwd() -> str:
        """Prompt user for SSH password of gateways.

        Returns:
            str: The input string of SSH password.
        """
        while True:
            passwd = input("Enter SSH password of media-gateways: ")
            comfirm = input("Is this correct (Y/N)?: ")
            if comfirm.lower().startswith("y"):
                break
        return passwd.strip()

    parser = argparse.ArgumentParser(description='Monitors Avaya Branch Gateways (BGW)')
    parser.add_argument('-u', dest='username', default='', help='BGW username')
    parser.add_argument('-p', dest='passwd', default='', help='BGW password')
    parser.add_argument('-n', dest='lastn_secs', default=30, help='secs to look back in RTP statistics')
    parser.add_argument('-m', dest='max_polling', default=20, help='max simultaneous polling sessons')
    parser.add_argument('-l', dest='loglevel', default="ERROR", help='loglevel')
    parser.add_argument('-t', dest='timeout', default=10, help='timeout in secs')
    parser.add_argument('-f', dest='polling_secs', default=5, help='polling frequency in seconds')
    parser.add_argument('-i', dest='ip_filter', default=None, help='BGW IP filter')
    args = parser.parse_args()

    args.username = args.username or (config.get("username") or get_username())
    args.passwd = args.passwd or (config.get("passwd") or get_passwd())
    config.update(args.__dict__)
    logger.setLevel(config["loglevel"].upper())
    asyncio_run(main())
