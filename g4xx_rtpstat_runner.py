#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
#############################################################################
## Name: g4xx_cmd_runner.py
## Runs Avaya G4xx gateway commands from CM shell and returns output in JSON
## Date: 2024-12-05
## Author: sszokoly@netagen.com
#############################################################################
'''
import argparse
import json
import pprint
import sys
from subprocess import Popen, PIPE
from typing import Any, Coroutine, TypeVar, Optional, Set, Callable, Any, TypeVar, Tuple, List

cmd_template = '''
#!/usr/bin/expect
############################# Template Variables #############################

set timeout {timeout}
set host {host}
set user {user}
set passwd {passwd}
set lastn_secs {lastn_secs}
set rtp_stat {rtp_stat}
set commands {{ {commands} }}
set log_file {log_file}

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
    global host gw_number commands_array rtp_sessions_array
    set json "{{"
    append json "\\"host\\": \\"$host\\", "
    append json "\\"gw_number\\": \\"$gw_number\\", "  
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
    set pattern {{^(\\S+)\\s+(\\S+),(\\S+)\\s+(\\S+)\\s+.*$}}
    if {{[regexp $pattern $input _ id start_date start_time end_time]}} {{
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

#Iterate through "commands" and run each
foreach command $commands {{
    set output [cmd "$command\\n"]
    if {{$output ne ""}} {{
        set commands_array($command) $output
    }}
}}

#Collect RTP statistics if requested
if {{$rtp_stat}} {{
    #Active global session ids
    set active_global_ids [get_active_global_ids]
    #Recent global session ids
    set recent_global_ids [get_recent_global_ids $lastn_secs]
    #Merged global session ids
    set merged_global_ids [merge_lists $active_global_ids $recent_global_ids]

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

send "exit\\n"

#Output results in JSON format
puts [to_json]
'''

def run_script(cmd):
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = proc.communicate()
    try:
        if proc.returncode:
            return "", stderr.decode().strip()
        return stdout.decode().strip(), stderr.decode().strip()
    except Exception as e:
        return "", repr(e)

def main(args):
    kwargs = vars(args)
    kwargs['rtp_stat'] = int(kwargs['rtp_stat'])
    log_file = f"debug_{kwargs['host']}.log" if kwargs["debug"] else "/dev/null"
    kwargs.update({"log_file": log_file})
    if kwargs["commands"]:
        cmds = []
        for item in kwargs["commands"]:
            cmds.extend(item.split("|"))
        commands = " ".join(f'"{c}"' for c in cmds)
        kwargs["commands"] = commands
    script = cmd_template.format(**kwargs)
    cmd = f"/usr/bin/env expect -c '{script}'"
    stdout, stderr = run_script(cmd)
    if stdout:
        parsed = json.loads(stdout, strict=False)
        #if parsed.get("rtp_sessions"):
            #gw_number = parsed["gw_number"]
            #rtp_sessions = '\n\t'.join(parsed["rtp_sessions"].keys())
            #print('{0}\t{1}'.format(gw_number, rtp_sessions))
        pprint.pprint(parsed, compact=True)
    else:
        print(stderr)

if __name__ == "__main__":
    #sys.argv.extend(['-i', '10.10.48.58', '-u', 'root', '-p', 'cmb@Dm1n', '-r', 'show utilization|show voip-dsp|show capture'])
    parser = argparse.ArgumentParser(description='Runs Avaya G4xx commands from CM shell and returns JSON')
    required = parser.add_argument_group('required arguments', '')
    required.add_argument('-i', dest='host', type=str, required=True, help='G4xx IP address')
    required.add_argument('-u', dest='user', type=str, required=True, help='username')
    required.add_argument('-p', dest='passwd', type=str, required=True, help='password')
    parser.add_argument('-d', action='store_true', dest='debug', default=False, help='enable debug logging')
    parser.add_argument('-t', dest='timeout', default=10, help='timeout in secs')
    parser.add_argument('-n', dest='lastn_secs', default=3620, help='secs to look back in RTP statistics')
    parser.add_argument('-r', dest='rtp_stat', action='store_true', default=False, help='collect RTP statistics')
    parser.add_argument('commands', action='store', default='', nargs='*', help='G4xx commands')
    sys.exit(main(parser.parse_args()))
