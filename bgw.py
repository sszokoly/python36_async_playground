
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import asyncio
import argparse
import json
import os
import re
import sys
from typing import Dict, Iterator, List, Tuple, Union
from utils import asyncio_run, async_shell
from collections import defaultdict

BGWS = {}
DEFAULTS = {
    "user": "root",
    "passwd": "cmb@Dm1n",
    "lastn_secs": 30,
    "timeout": 10,
    "debug": False,
    "log_file": "/dev/null"
}

script_template = '''
#!/usr/bin/expect
############################# Template Variables #############################

set host {host}
set user {user}
set passwd {passwd}
set rtp_stat {rtp_stat}
set lastn_secs {lastn_secs}
set commands {{ {commands} }}
set log_file {log_file}
set timeout {timeout}

############################## Expect Variables ##############################

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
    global host gw_number timestamp commands_array rtp_sessions_array
    set json "{{"
    append json "\\"host\\": \\"$host\\", "
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
    global host cmd parse_session_summary_line
    set ids [list]
    foreach line [split [cmd "show rtp-stat sessions active\\n"] "\\n"] {{
        if {{[regexp {{^[0-9]+}} $line]}} {{
            set result [parse_session_summary_line $line]
            lassign $result session_id start_date start_time end_date end_time
            lappend ids [format "%s,%s,%s,%s" $start_date $start_time $host $session_id]
        }}
    }}
    return $ids
}}

proc get_recent_global_ids {{{{lastn_secs {{20}}}}}} {{
    global host cmd parse_session_summary_line is_date1_gt_date2
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
                    lappend ids [format "%s,%s,%s,%s" $start_date $start_time $host $session_id]
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
spawn ssh -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $user@$host

#Handle SSH connection
expect {{
    "Password: " {{send "$passwd\\n"}}
    timeout {{
        puts stderr "Timeout";
        exit 255
    }}
    eof {{
        puts stderr "Timeout";
        exit 255
    }}
}}
expect {{
    "*Permission denied*" {{
        puts stderr "Permission denied";
        exit 254
    }}
    $prompt {{}}
}}

#Extract gateway number from prompt
regexp {{([^\\s]+)-(\\d+)[\\(]}} $expect_out(buffer) "" _ gw_number
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
            lassign [split $global_id ","] start_date start_time host session_id
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

def registered_bgws() -> Dict[str, str]:
    """Return a dictionary of registered media-gateways

    The dictionary has the gateway iIP as the key and the protocol
    type 'encrypted' or 'unencrypted' as the value.

    Returns:
        dict: A dictionary of connected bgws
    """
    bgws = {}
    output: str = os.popen('netstat -tan | grep ESTABLISHED').read()
    for line in output.splitlines():
        m = re.search(r'([0-9.]+):(1039|2945)\s+([0-9.]+):([0-9]+)', line)
        if not m:
            continue
        proto: str = 'encrypted' if m.group(2) == '1039' else 'unencrypted'
        bgws[m.group(3)] = proto
    return bgws

class BGW():
    def __init__(self,
        host: str,
        user: str = '',
        passwd: str = '',
        gw_number: str = '',
        proto: str = '',
        show_config: str = '',
        show_system: str = '',
        show_faults: str = '',
        show_capture: str = '',
        show_temp: str = '',
    ) -> None:   
        self.host = host
        self.user = user
        self.passwd = passwd
        self.gw_number = gw_number
        self.proto = proto
        self.show_config = show_config
        self.show_system = show_system
        self.show_faults = show_faults
        self.show_capture = show_capture
        self.show_temp = show_temp
        self._faults = None
        self._capture = None
        self._model = None
        self._firmware = None
        self._serial = None
        self._rtp_stat = None
        self._capture = None
        self._temp = None

    @property
    def model(self):
        if not self._model:
            m = re.search(r'Model\s+:\s+(\S+)', self.show_system)
            self._model = m.group(1) if m else "G???v?"
        return self._model

    @property
    def firmware(self):
        if not self._firmware:
            m = re.search(r'FW Vintage\s+:\s+(\S+)', self.show_system)
            self._firmware = m.group(1) if m else "??.??.?"
        return self._firmware
    
    @property
    def serial(self):
        if not self._serial:
            m = re.search(r'Serial No\s+:\s+(\S+)', self.show_system)
            self._serial = m.group(1) if m else "??????????"
        return self._serial

    @property
    def rtp_stat(self):
        if not self._rtp_stat:
            m = re.search(r'rtp-stat-service', self.show_config)
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
                self._capture = "unknown"
        return self._capture

    @property
    def temp(self):
        if not self._temp:
            m = re.search(r'Temperature\s+:\s+(\S+) \((\S+)\)', self.show_temp)
            if m:
                cels, faren = m.group(1, 2)
                self._temp = f"{cels}/{faren}"
            else:
                self._temp = "unknown"
        return self._temp

    @property
    def faults(self):
        if not self._faults:
            if "No Fault Messages" in self.show_faults:
                self._faults = "none"
            else:
                self._faults = "faulty"
        return self._faults

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

async def query_bgw(**kwargs):
    cmd = f"/usr/bin/env expect -c '{script_template.format(**kwargs)}'"
    data, err, rc = await async_shell(
        cmd, timeout=kwargs["timeout"], name=f"query_{kwargs['host']}")
    if rc or err:
        return {}
    return json.loads(data, strict=False)

async def query_bgws(bgws=None, kwargs=None, commands=None, rtp_stat=1):
    bgws = bgws if bgws else BGWS.keys()
    kwargs = kwargs if kwargs else DEFAULTS
    commands = " ".join(f'"{c}"' for c in commands) if commands else ""
    kwargs.update({"commands": commands, "rtp_stat": rtp_stat})
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(query_bgw(host=host, **kwargs)) for host in bgws]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if r]

async def discover_bgws():
    kwargs = DEFAULTS
    commands = [
            "show running-config",
            "show system",
            "show faults",
            "show capture",
            "show temp"
        ]
    bgws = registered_bgws()
    results = await query_bgws(bgws.keys(), kwargs=kwargs, commands=commands, rtp_stat=0)
    for result in results:
        if not result:
            continue
        
        bgw = BGW(
            host=result["host"],
            user=DEFAULTS["user"],
            passwd=DEFAULTS["passwd"],
            gw_number=result["gw_number"],
            proto=bgws[result["host"]],
            show_config=result["commands"]["show running-config"],
            show_system=result["commands"]["show system"],
            show_faults=result["commands"]["show faults"],
            show_capture=result["commands"]["show capture"],
            show_temp=result["commands"]["show temp"],
        )
        BGWS[result["host"]] = bgw

async def run():
    print("DISCOVERYING")
    await discover_bgws()
    for ip, bgw in BGWS.items():
        print(ip, bgw.proto, bgw.gw_number, bgw.model, bgw.firmware, bgw.serial, bgw.capture, bgw.rtp_stat, bgw.faults, bgw.temp)
    print("UPDATING")
    results = await query_bgws()
    print(results)

def get_user():
    while True:
        user = input("Enter SSH username of BGWs: ")
        comfirm = input("Is this correct (Y/N)?: ")
        if comfirm.lower().startswith("y"):
            break
    return user.strip()

def get_passwd():
    while True:
        passwd = input("Enter SSH passwd of BGWs: ")
        comfirm = input("Is this correct (Y/N)?: ")
        if comfirm.lower().startswith("y"):
            break
    return passwd.strip()

def main(**kwargs):
    kwargs["user"] = kwargs["user"] if kwargs["user"] else get_user()
    kwargs["passwd"] = kwargs["passwd"] if kwargs["passwd"] else get_passwd()
    if kwargs["debug"]:
        kwargs["log_file"] = "bgw_debug.log"
    DEFAULTS.update(kwargs)
    asyncio_run(run())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-u', dest='user', type=str, default=DEFAULTS["user"], help='user')
    parser.add_argument('-p', dest='passwd', type=str, default=DEFAULTS["passwd"], help='password')
    parser.add_argument('-t', dest='timeout', default=DEFAULTS["timeout"], help='timeout in secs')
    parser.add_argument('-n', dest='lastn_secs', default=DEFAULTS["lastn_secs"], help='secs to look back in RTP statistics')
    parser.add_argument('-d', action='store_true', dest='debug', default=DEFAULTS["debug"], help='debug')
    parser.add_argument('-l', dest='log_file', default=DEFAULTS["log_file"], help='log file')
    sys.exit(main(**vars(parser.parse_args())))
