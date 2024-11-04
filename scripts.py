#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from typing import Optional, List

cmd_template = '''
log_user {log_user}
exp_internal {exp_internal}

# Set variables
set timeout {timeout}
set host {host}
set user {user}
set passwd {passwd}
set prompt "\\)# "
set session_ids {{ {session_ids} }}
set commands {{
{commands}
}}

# Procedures
proc merge_lists {{list1 list2}} {{
    set combined [concat $list1 $list2]
    set result [lsort -unique $combined]
    return $result
}}

proc clean_output {{output}} {{
    set type_removed [regsub "\\r\\n--type q to quit or space key to continue-- \\r\\[^ \\]*K" $output ""]
    set note_removed [regsub "Note that field.*" $type_removed ""]
    set done_removed [regsub "Done!.*" $note_removed ""]
    set prompt_removed [regsub "\\r\\n\\[^ \\]*\\[)\\]# " $done_removed ""]
    set result [string trimright $prompt_removed]
    return $result
}}

proc cmd {{command}} {{
    global prompt
    set output "#BEGIN\\n"
    send $command
    expect {{
        "*continue-- " {{
            set current_output $expect_out(buffer)
            append output $current_output
            send "\\n"
            exp_continue
        }}
        "*to continue." {{
            set current_output $expect_out(buffer)
            append output $current_output
            sleep 3
            exp_continue
        }}
        $prompt {{  
            set current_output $expect_out(buffer)
            append output $current_output
        }}
        timeout {{puts stderr "Timeout"; exit 255}}
    }}
    set result [clean_output $output]
    append result "\\n#END"
    return $result
}}

proc active_sessions_ids {{}} {{
    global cmd
    set active_ids [list]
    set command "show rtp-stat sessions active\\n"
    set active_sessions [cmd $command]
    foreach line [split $active_sessions "\\n"] {{
        if {{[regexp {{^\\s*(\\d+)}} $line match number]}} {{
            lappend active_ids $number
        }}
    }}
    return $active_ids
}}

# Spawn SSH connection
spawn ssh -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=$timeout $user@$host

# Handle SSH connection
expect {{
    "Password: " {{send "$passwd\\n"}}
    timeout {{puts stderr "Timeout"; exit 255}}
    eof {{puts stderr "Timeout"; exit 255}}
}}
expect {{
    "*Permission denied*" {{puts stderr "Permission denied"; exit 254}}
    $prompt {{}}
}}

# Loop through session ids and run "show rtp-stats detailed" id on it
set active_ids [active_sessions_ids]
set merged_ids [merge_lists $active_ids $session_ids]
set rtp_stat_output ""
if {{$merged_ids ne {{}}}} {{
    foreach id $merged_ids {{
        set command "show rtp-stat detailed $id\\n"
        append rtp_stat_output [cmd $command]
    }}
}}

if {{$rtp_stat_output ne ""}} {{
    log_user 1
    puts $rtp_stat_output
    log_user 0
}}

# Loop through the other commands
set cmd_output ""
foreach command $commands {{
    append cmd_output [cmd $command]
}}

if {{$cmd_output ne ""}} {{
    log_user 1
    puts $cmd_output
    log_user 0
}}

send "exit\\n"
'''

def expect_cmd_script(
    host: str,
    user: str,
    passwd: str,
    session_ids: Optional[List[str]] = None,
    commands: Optional[List[str]] = None,
    timeout: Optional[int] = 2,
    log_user: Optional[int] = 0,
    exp_internal: Optional[int] = 0,
    ) -> str:
    """Interpolates and formats the 'cmd_template' Expect script.

    Args:
        host (str): Host (BGW) IP address
        user (str): Host (BGW) SSH username
        passwd (str): Host (BGW) SSH password
        session_ids (Optional[List[str]], optional): BGW RTP session IDs. Defaults to None.
        commands (Optional[List[str]], optional): BGW Shell commands. Defaults to None.
        timeout (Optional[int], optional): Expect script timeout in secs. Defaults to 2.
        log_user (Optional[int], optional): Expect logging to stdout. Defaults to 0.
        exp_internal (Optional[int], optional): Expect diagnostic info to stderr. Defaults to 0.

    Returns:
        str: interpolated/formated Expect script
    """
    session_ids = ' '.join(session_ids) if session_ids else ''
    commands = '\n'.join(f'  "{c}\\n"' for c in commands) if commands else ''
    script = cmd_template.format(**{
        'host': host,
        'user': user,
        'passwd': passwd,
        'session_ids': session_ids,
        'commands': commands,
        'timeout': timeout,
        'log_user': log_user,
        'exp_internal': exp_internal,
    })
    return script

if __name__ == "__main__":
    print(expect_cmd_script(**{
        'host': '10.10.48.58',
        'user': 'root',
        'passwd': 'cmb@Dm1n',
        'session_ids': ['00001', '00002'],
        'commands': ['show system', 'show running-config'],
        'timeout': 3,
        'log_user': 0,
        'exp_internal': 0
    }))
