
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import asyncio
import json
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
from storage import AsyncMemoryStorage
from session import reDetailed

logger = logging.getLogger('__name__')
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s %(levelname)-8s %(message)s')

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
    global host gw_name gw_number timestamp commands_array rtp_sessions_array
    set json "{{"
    append json "\\"host\\": \\"$host\\", "
    append json "\\"gw_name\\": \\"$gw_name\\", "
    append json "\\"gw_number\\": \\"$gw_number\\", "
    append json "\\"timestamp\\": \\"$timestamp\\", "
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

#Capture timestamp
set timestamp [exec date "+%Y-%m-%d,%H:%M:%S"]

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
            if {{$output ne ""}} {{
                set rtp_sessions_array($global_id) $output
            }}
        }}
    }}
}}

#Iterate through "commands" and run each
foreach command $commands {{
    set output [cmd "$command\\n"]
    if {{$output ne ""}} {{
        set commands_array($command) $output
    }}
}}

send "exit\\n"

#Output results in JSON format
puts [to_json]
'''

script_template_test = '''
set host {host}
set randomInt [expr {{int(rand() * 3)}}]

sleep 2

if {{$randomInt == 4}} {{
    puts -nonewline stderr "ExpectTimeout"; exit 255
}}
sleep 1
puts "{{\\"gw_number\\": \\"001\\", \\"host\\": \\"$host\\", \\"timestamp\\": \\"2024-12-30,11:06:15\\", \\"commands\\": {{\\"show system\\": \\"location: 1\\", \\"show running-config\\": \\"location: 1\\"}}, \\"rtp_sessions\\": {{\\"2024-12-30,11:06:15,$host,000$randomInt\\": \\"session 000$randomInt\\"}}}}"
'''

DEFAULTS = {
    "username": "root",
    "passwd": "cmb@Dm1n",
    "polling_secs": 5,
    "max_polling": 20,
    "lastn_secs": 3630,
    "debug": False,
    "loglevel": "ERROR",
    "logfile": "bgw.log",
    "expect_logging": "/dev/null",
    "script_template": script_template,
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


MAIN_ATTRS = [
    {'xpos':  1, 'text': 'start_time', 'format_spec': '', 'color': 'normal'},
    {'xpos': 10, 'text': 'end_time', 'format_spec': '', 'color': 'normal'},
    {'xpos': 19, 'text': 'bgw_num', 'format_spec': '0>3', 'color': 'normal'},
    {'xpos': 23, 'text': 'local_ip', 'format_spec': '>15', 'color': 'address'},
    {'xpos': 39, 'text': 'local_port', 'format_spec': '>5', 'color': 'port'},
    {'xpos': 46, 'text': 'remote_ip', 'format_spec': '>15', 'color': 'address'},
    {'xpos': 61, 'text': 'remote_port', 'format_spec': '>5', 'color': 'port'},
    {'xpos': 67, 'text': 'status', 'format_spec': '^6', 'color': 'active'},
    {'xpos': 74, 'text': 'qos', 'format_spec': '^3', 'color': 'ok'},
]

BGW_ATTRS = [
    {'xpos':  1, 'text': 'number', 'format_spec': '', 'color': 'normal'},
    {'xpos':  5, 'text': 'model', 'format_spec': '>6', 'color': 'normal'},
    {'xpos': 12, 'text': 'firmware', 'format_spec': '>8', 'color': 'normal'},
    {'xpos': 21, 'text': 'ip', 'format_spec': '>15', 'color': 'address'},
    {'xpos': 37, 'text': 'serial', 'format_spec': '>12', 'color': 'normal'},
    {'xpos': 50, 'text': 'snmp', 'format_spec': '^4', 'color': 'normal'},
    {'xpos': 55, 'text': 'rtp_stat', 'format_spec': '>8', 'color': 'normal'},
    {'xpos': 64, 'text': 'capture', 'format_spec': '>7', 'color': 'normal'},
    {'xpos': 72, 'text': 'fault', 'format_spec': '>5', 'color': 'normal'},
]

def registered_bgw_ips() -> Dict[str, str]:
    """Return a dictionary of registered media-gateways

    The dictionary has the gateway iIP as the key and the protocol
    type 'encrypted' or 'unencrypted' as the value.

    Returns:
        dict: A dictionary of connected bgws
    """
    bgws_ips = {}
    output: str = os.popen('netstat -tan | grep ESTABLISHED').read()
    for line in output.splitlines():
        m = re.search(r'([0-9.]+):(1039|2945)\s+([0-9.]+):([0-9]+)', line)
        if not m:
            continue
        proto: str = 'encrypted' if m.group(2) == '1039' else 'unencrypted'
        bgws_ips[m.group(3)] = proto
    return bgws_ips

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

def iter_session_main_attrs(
    session_dict: Dict[str, str],
    main_attrs: List[Dict[str, Union[int, str]]] = MAIN_ATTRS,
    xoffset: int = 0
) -> Iterator[Tuple[int, str, str]]:
    """
    Iterate over the main attributes of a session dictionary and yield a tuple of 3 values:

    - `ypos`: The y position of the attribute
    - `text`: The text of the attribute, formatted according to the `format_spec`
    - `color`: The color of the attribute

    :param session_dict: A dictionary of key-value pairs of the attributes of the session
    :param main_attrs: A list of dictionaries of the main attributes of the session
    :param xoffset: The offset of xpos
    :return: An iterator of tuples of 3 values
    """
    for attrs in main_attrs:
        text = session_dict.get(attrs['text'], attrs['text'])
        color = attrs['color']
        if attrs['text'] == 'status':
            text = 'active' if text == 'Active' else 'ended'
            color = 'active' if text == 'Active' else 'ended'
        if attrs['text'] == 'qos':
            text = '✔' if text == 'OK' else '✘'
            color = 'ok' if text == 'OK' else 'fault'
        text = f'{text:{attrs["format_spec"]}}'
        yield attrs['xpos'] + xoffset, text, color

def iter_bgw_attrs(
    bgw: BGW,
    bgw_attrs: List[Dict[str, Union[int, str]]] = BGW_ATTRS
) -> Iterator[Tuple[int, str, str]]:
    """
    Iterate over the attributes of a BGW object and yield a tuple of 3 values:

    - `xpos`: The x position of the attribute
    - `text`: The text of the attribute, formatted according to the `format_spec`
    - `color`: The color of the attribute

    :param bgw: A BGW object
    :param bgw_attrs: A list of dictionaries of the attributes of the BGW
    :return: An iterator of tuples of 3 values
    """
    for attrs in bgw_attrs:
        text = getattr(bgw, attrs['text'])
        text = f'{text:{attrs["format_spec"]}}'
        yield attrs['xpos'], text, attrs['color']

class BGWMonitor():
    def __init__(
        self,
        username,
        passwd,
        script_template,
        polling_secs=10,
        max_polling=20,
        lastn_secs=30,
        storage=None,
        loop=None,
        discovery_commands=None,
        query_commands=None,
        bgw_filter=None,
    ):
        self.username = username
        self.passwd = passwd
        self.script_template = script_template
        self.polling_secs= polling_secs
        self.max_polling = max_polling
        self.lastn_secs = lastn_secs
        self.storage = storage if storage else AsyncMemoryStorage(maxlen=1000)
        self.loop = loop if loop else asyncio.get_event_loop()
        self.discovery_commands = discovery_commands if discovery_commands else [
            "show running-config",
            "show system",
            "show faults",
            "show capture",
            "show voip-dsp",
            "show temp",
        ]
        self.query_commands = query_commands if query_commands else [
            "show voip-dsp",
            "show temp",
        ]
        self.timeout = 20
        self.bgws = {host:BGW(host, proto) for host, proto in
                      self._registered_bgw_hosts(bgw_filter).items()}
        self.discovered_bgws = {}
        self._query_bgw_tasks = []
        self._processing_task = None
        self._processing_queue = Queue()
        self._semaphore = Semaphore(max_polling)

    async def _query_bgw(self, bgw, run_once=False):
        name = f"BGWMonitor._query_bgw({bgw.host})".ljust(38)
        args = self._generate_query_args(bgw.host, run_once)
        proc = None
        while True:
            try:
                start = time.perf_counter()
                async with self._semaphore:
                    diff = time.perf_counter() - start
                    proc: Process = await asyncio.create_subprocess_exec(
                        *args, stdout=PIPE, stderr=PIPE)
                    logging.debug(f"{name} Created process PID {proc.pid}")
                    try:
                        stdout, stderr = await asyncio.wait_for(
                            proc.communicate(), self.timeout)
                    except asyncio.TimeoutError:
                        logging.error(f"{name} TimeoutError")
                    else:
                        if proc.returncode:
                            logging.error(f"{name} {stderr.decode()}")
                        else:
                            self._processing_queue.put_nowait(stdout.decode())
                        if run_once:
                            break
                sleep_secs = round(max(self.polling_secs - diff, 0), 1)
                logging.info(f"{name} Sleeping {sleep_secs}s")
                await asyncio.sleep(sleep_secs)
            except asyncio.CancelledError:
                logging.warning(f"{name} Cancelling task")
                if proc and proc.returncode == None:
                    logging.debug(f"{name} Terminating process PID {proc.pid}")
                    proc.terminate()
                    await proc.wait()
                break

    async def _processing(self):
        name = "BGWMonitor._processing()"
        while True:
            try:
                item = await self._processing_queue.get()
                logging.debug(f"{name} got {item}")
                try:
                    dictitem = json.loads(item, strict=False)
                except json.JSONDecodeError:
                    logging.error(f"{name} JSONDecodeError")
                    continue
                await self._process_dictitem(dictitem)
                self._processing_queue.task_done()
            except asyncio.CancelledError:
                logging.warning(f"{name} Cancelling task")
                while not self._processing_queue.empty():
                    item = await self._processing_queue.get_nowait()
                    logging.debug(f"{name} got {item}")
                    try:
                        dictitem = json.loads(item, strict=False)
                    except json.JSONDecodeError:
                        logging.error(f"{name} JSONDecodeError")
                        continue
                    await self._process_dictitem(dictitem)
                    self._processing_queue.task_done()
                await asyncio.wait_for(self._processing_queue.join(), 1)
                self._processing_task = None
                break

    async def _process_dictitem(self, dictitem):
        host = dictitem.get("host", None)
        if not host:
            return
        
        bgw = self.bgws[host]
        logging.debug(f"Update {bgw} with {dictitem}")
        
        if not bgw.gw_number and dictitem.get("gw_number"):
            bgw.gw_number = dictitem.get("gw_number")
        
        if not bgw.gw_name and dictitem.get("gw_name"):
            bgw.gw_name = dictitem.get("gw_name")
        
        if dictitem.get("timestamp"):
            bgw.last_seen = dictitem.get("timestamp")

        for cmd, value in dictitem.get("commands", {}).items():
            bgw_attr = cmd.replace(" ", "_").replace("-", "_")
            if value:
                setattr(bgw, bgw_attr, value)
        
        for global_id, attrs in dictitem.get("rtp_sessions", {}).items():
            await self.storage.put({global_id: attrs})

    async def _start_processing(self):
        if self._processing_task:
            await self._stop_processing()
        self._processing_task = self.loop.create_task(self._processing())
    
    async def _stop_processing(self):
        if self._processing_task:
            self._processing_task.cancel()
            await asyncio.gather(self._processing_task, return_exceptions=True)
        self._processing_task = None

    async def _start_query_bgws(self, run_once=False):
        if self._query_bgw_tasks:
            await self._stop_query_bgws()       
        
        if run_once:
            bgws = [bgw for bgw in self.bgws.values()]
        else:
            bgws = [bgw for bgw in self.discovered_bgws.values()]
        
        logger.debug(f"_start_query_bgws() with 'run_once={run_once}' and bgws={bgws}")
        self._query_bgw_tasks = [self.loop.create_task(self._query_bgw(
            bgw=bgw, run_once=run_once)) for bgw in bgws]
    
    async def _stop_query_bgws(self):
        if self._query_bgw_tasks:
            for task in self._query_bgw_tasks:
                task.cancel()
            await asyncio.gather(*self._query_bgw_tasks, return_exceptions=True)
        self._query_bgw_tasks = []

    async def start(self, run_once=False):
        await self._start_processing()
        await self._start_query_bgws(run_once=run_once)

    async def stop(self):
        await self._stop_query_bgws()
        await self._stop_processing()

    async def discover(self):
        await self.start(run_once=True)
        await asyncio.gather(*self._query_bgw_tasks)
        await self.stop()
        self.discovered_bgws = {host:bgw for host, bgw in self.bgws.items()
                                if bgw.last_seen}

    def _generate_query_args(self, host, run_once=False):
        rtp_stat = 0 if run_once else 1
        commands = self.discovery_commands if run_once else self.query_commands
        commands = " ".join(f'"{c}"' for c in commands)
        script = self.script_template.format(**{
            "host": host,
            "username": self.username,
            "passwd": self.passwd,
            "rtp_stat": rtp_stat,
            "lastn_secs": self.lastn_secs,
            "commands": commands,
            "expect_log_file": "/dev/null",
        })
        return ["/usr/bin/env", "expect", "-c", script]

    @staticmethod
    def timestamp_parser(dictitem):
        for k, v in dictitem.items():
            if k == "timestamp" and isinstance(v, str):
                try:
                    dictitem[k] = datetime.strptime(v, "%Y-%m-%d,%H:%M:%S")
                except:
                    pass
        return dictitem


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
        passwd = input("Enter SSH passwd of media-gateways: ")
        comfirm = input("Is this correct (Y/N)?: ")
        if comfirm.lower().startswith("y"):
            break
    return passwd.strip()


if __name__ == '__main__':
    logger.setLevel("DEBUG")
    async def run():
        bgwmonitor = BGWMonitor(
            username=DEFAULTS["username"],
            passwd=DEFAULTS["passwd"],
            script_template=DEFAULTS["script_template"],
            polling_secs=DEFAULTS["polling_secs"],
            max_polling=DEFAULTS["max_polling"],
            lastn_secs=DEFAULTS["lastn_secs"],
            loop=asyncio.get_event_loop(),
            discovery_commands=DEFAULTS["discovery_commands"],
            query_commands=DEFAULTS["query_commands"],
            bgw_filter=[],
        )
        try:
            await bgwmonitor.discover()
            print("===============BGWS===============")
            for bgw in bgwmonitor.bgws.values():
                    print(f"last_seen:{bgw.last_seen} host:{bgw.host:<15} gw_name:{bgw.gw_name:<10} gw_number:{bgw.gw_number:>3} model:{bgw.model:>4} firmware:{bgw.firmware:>8}")
            print("==================================")
            if not bgwmonitor.discovered_bgws:
                print("No BGWs found. Exiting...")
                return
            await bgwmonitor.start()
            while True:
                print("=========DISCOVERED BGWS==========")
                for bgw in bgwmonitor.discovered_bgws.values():
                    print(f"last_seen:{bgw.last_seen} host:{bgw.host:<15} gw_name:{bgw.gw_name:<10} gw_number:{bgw.gw_number:>3} model:{bgw.model:>4} firmware:{bgw.firmware:>8}")
                print(f"No. of RTP Sessions in Storage: {len(bgwmonitor.storage)}")
                print("Last 6 sessions")
                async for value in bgwmonitor.storage.get((-6, None)):
                    try:
                        session_dict = reDetailed.match(value).groupdict()
                    except:
                        continue
                    print(session_dict["session_id"].zfill(5), session_dict["start_time"], session_dict["end_time"], session_dict["qos"])
                print("==================================")
                await asyncio.sleep(10)
        except Exception as e:
            logging.warning(f"run() Exception {repr(e)}")
    
    asyncio_run(run())
