import logging
from bgw import BGW

config = {
    "username": "root",
    "passwd": "cmb@Dm1n",
    "polling_secs": 5,
    "max_polling": 20,
    "lastn_secs": 3630,
    "loglevel": "DEBUG",
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
set host {host}
set username {username}
set passwd {passwd}
set rtp_stat {rtp_stat}
set lastn_secs {lastn_secs}
set commands {{ {commands} }}
set log_file {expect_log}

set randomInt [expr {{int(rand() * 4)}}]

#sleep 2

if {{$randomInt == 4}} {{
    puts -nonewline stderr "ExpectTimeout"; exit 255
}}
sleep 1
puts "{{\\"gw_number\\": \\"001\\", \\"host\\": \\"$host\\", \\"timestamp\\": \\"2024-12-30,11:06:15\\", \\"commands\\": {{\\"show system\\": \\"location: 1\\", \\"show running-config\\": \\"location: 1\\"}}, \\"rtp_sessions\\": {{\\"2024-12-30,11:06:15,$host,000$randomInt\\": \\"session 000$randomInt\\"}}}}"
'''

logger = logging.getLogger(__name__)
logger.setLevel(config["loglevel"])

def create_bgw_script(bgw):
    debug = True if logger.getEffectiveLevel() == 10 else False
    if not bgw.show_running_config:
        commands = config["discovery_commands"]
        rtp_stat = 0
    else:
        commands = config["query_commands"]
        if not bgw.queue.empty():
            queued_commands = bgw.queue.get_nowait()
            if isinstance(queued_commands, str):
                queued_commands = [queued_commands]
                commands.extend(queued_commands)
        rtp_stat = 1
    d = {
        "host": bgw.host,
        "username": config["username"],
        "passwd": config["passwd"],
        "rtp_stat": rtp_stat,
        "lastn_secs": config["lastn_secs"],
        "commands": " ".join(f'"{c}"' for c in commands),
        "expect_log": config["expect_log"] if debug else "/dev/null",
    }
    script = script_template.format(**d)
    return ["/usr/bin/env", "expect", "-c", script]

if __name__ == "__main__":
    bgw = BGW("10.10.10.48", "encrypted")
    print(create_bgw_script(bgw))
    bgw.show_running_config = "test"
    bgw.queue.put_nowait("show image version")
    print(create_bgw_script(bgw))
