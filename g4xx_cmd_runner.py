#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import argparse
import json
import pprint
import sys
from subprocess import Popen, PIPE
from typing import Any, Coroutine, TypeVar, Optional, Set, Callable, Any, TypeVar, Tuple, List

cmd_template = '''
#!/usr/bin/expect
log_user 0
set log_file {log_file}

if {{[info exists log_file] && $log_file ne "/dev/null"}} {{
    if {{[file exists $log_file]}} {{
        file delete $log_file
    }}
}}

exp_internal -f $log_file 0

################################# Variables ##################################

set timeout {timeout}
set host {host}
set user {user}
set passwd {passwd}
set prompt "\\)# "
set commands {{ {commands} }}
array set commands_array {{}}

################################# Procedures #################################

proc to_json {{}} {{
    global host gw_number commands_array
    set json "{{"
    append json "\\"host\\": \\"$host\\", "
    append json "\\"gw_number\\": \\"$gw_number\\", "  
    if {{[llength [array names commands_array]] > 0}} {{
        append json "\\"commands\\": {{"
        foreach {{key value}} [array get commands_array] {{
            append json "\\"$key\\": \\"$value\\", "
        }}
        set json [string trimright $json ", "]
        append json "}}"
    }}
    set json [string trimright $json ", "]
    append json "}}"
    return $json
}}

proc clean_output {{output}} {{
    #set type_removed [string map {{"\\r\\n--type q to quit or space key to continue-- \\r\\u\\001b[K" ""}} $output]
    set type_removed [regsub "\\r\\n--type q to quit or space key to continue-- \\r\\[^ \\]*K" $output ""]
    set note_removed [regsub "Note that field.*" $type_removed ""]
    set done_removed [regsub "Done!.*" $note_removed ""]s
    set prompt_removed [regsub "\\r?\\n\\[^ \\]*\\[)\\]# " $done_removed ""]
    set result [string trimright $prompt_removed "\\r\\n"]
    return $result
}}

proc cmd {{command}} {{
    global prompt
    set output ""
    send "$command"
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
        "*." {{
            set current_output $expect_out(buffer)
            append output $current_output
            sleep 3
            exp_continue
        }}
        $prompt {{
            set current_output $expect_out(buffer)
            append output $current_output
        }}
        timeout {{
            puts stderr "Timeout";
            return ""
        }}
    }}
    set result [clean_output $output]
    return [string trimleft $result $command]
}}

#################################### Main ####################################

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

send "exit\\n"

#Output results in JSON format
puts [to_json]
'''

def run_script(cmd):
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = proc.communicate()
    print([stdout])
    try:
        if proc.returncode:
            return "", stderr.decode().strip()
        return stdout.decode().strip(), stderr.decode().strip()
    except Exception as e:
        return "", repr(e)

def main(args):
    kwargs = vars(args)
    log_file = f"debug_{kwargs['host']}.log" if kwargs["d"] else "/dev/null"
    kwargs.update({"log_file": log_file})
    if kwargs["commands"]:
        commands = " ".join(f'"{c}"' for c in kwargs["commands"].split("|"))
        kwargs["commands"] = commands
    script = cmd_template.format(**kwargs)
    cmd = f"/usr/bin/env expect -c '{script}'"
    stdout, stderr = run_script(cmd)
    if stdout:
        print([stdout])
        parsed = json.loads(stdout, strict=False)
        pprint.pprint(parsed, compact=True)
    else:
        print(stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='runs G4xx commands from CM shell')
    parser.add_argument('-i', dest='host', type=str, help='G4xx IP address')
    parser.add_argument('-u', dest='user', type=str, default='root', help='username')
    parser.add_argument('-p', dest='passwd', type=str, help='password')
    parser.add_argument('-d', action='store_true', default=False, help='enable debug logging')
    parser.add_argument('-t', dest='timeout', default=10, help='timeout in secs')
    parser.add_argument('commands', action='store', default='', nargs='?', help='G4xx commands separated by "|"')
    sys.exit(main(parser.parse_args()))
