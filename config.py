import logging
from bgw import BGW

config = {
    "username": "root",
    "passwd": "cmb@Dm1n",
    "polling_secs": 5,
    "max_polling": 20,
    "lastn_secs": 3630,
    "loglevel": "ERROR",
    "logfile": "bgw.log",
    "expect_log": "expect_log",
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

script_template_test = '''
set host {host}
set username {username}
set passwd {passwd}
set rtp_stat {rtp_stat}
set lastn_secs {lastn_secs}
set commands {{ {commands} }}
set log_file {expect_log}

set randomInt [expr {{int(rand() * 4)}}]

sleep 2

if {{$randomInt == 4}} {{
    puts -nonewline stderr "ExpectTimeout"; exit 255
}}
sleep 1
puts "{{\\"gw_number\\": \\"001\\", \\"host\\": \\"$host\\", \\"timestamp\\": \\"2024-12-30,11:06:15\\", \\"commands\\": {{\\"show system\\": \\"location: 1\\", \\"show running-config\\": \\"location: 1\\"}}, \\"rtp_sessions\\": {{\\"2024-12-30,11:06:15,$host,000$randomInt\\": \\"session 000$randomInt\\"}}}}"
'''

logger = logging.getLogger(__name__)
logger.setLevel(config["loglevel"])

def create_bgw_script(bgw):
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

if __name__ == "__main__":
    bgw = BGW("10.10.10.48", "encrypted")
    print(create_bgw_script(bgw))
    bgw.last_seen = "test"
    bgw.queue.put_nowait("show image version")
    print(create_bgw_script(bgw))
