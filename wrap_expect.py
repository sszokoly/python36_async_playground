import base64
import zlib
import textwrap

script_template ='''
set host {host}
set username {username}
set passwd {passwd}
set rtp_stat {rtp_stat}
set lastn_secs {lastn_secs}
set commands {{ {commands} }}
set log_file {expect_log}

set randomsleep [expr {{int(rand() * 3)}}]
set randomInt [expr {{int(rand() * 9)}}]
set randomInt2 [expr {{int(rand() * 250)}}]
set cpuutil [expr {{int(rand() * 99)}}]
set memutil [expr {{int(rand() * 70)}}]
set activesessions [expr {{int(rand() * 30)}}]
set voipdsp [expr {{int(rand() * 60)}}]


set last_seen [exec date "+%Y-%m-%d,%H:%M:%S"]
sleep $randomsleep
set end_time [exec date "+%Y-%m-%d,%H:%M:%S"]
if {{$randomsleep == 3}} {{
    puts -nonewline stderr "ExpectTimeout"; exit 255
}}
puts "{{\\"gw_number\\": \\"00$randomInt\\",
        \\"gw_name\\": \\"g450-00$randomInt\\",
        \\"host\\": \\"$host\\",
        \\"last_seen\\": \\"$last_seen\\",
        \\"commands\\": {{
            \\"show system\\": \\"System Location: Location1\\",
            \\"show running-config\\": \\"snmp-server community public\\",
            \\"show platform\\": \\"Power Supply 125W\\",
            \\"show utilization\\": \\"10      $cpuutil%       $cpuutil%    $memutil%     447489 Kb\\",
            \\"show rtp-stat summary\\": \\"010        internal  53,05:23:06   $activesessions/0   332442/1443   00:05:17    64\\",
            \\"show port\\": \\"10/5   NO NAME          connected 1     0     enable  full 1G   Avaya Inc., G450 Media Gateway 10/100/1000BaseTx Port 10/5\\",
            \\"show voip-dsp\\": \\"In Use         : $voipdsp of 160 channels\\"
        }},
        \\"rtp_sessions\\": {{
            \\"$last_seen,$host,000$randomInt2\\": \\"Session-ID: 000$randomInt2  Status: Active, QOS: Ok,  EngineId: 10  Start-Time: $last_seen, End-Time: $end_time,\\"
        }}
    }}"
'''


def compress_and_wrap(input_string, column_width=78):
    compressed_bytes = zlib.compress(input_string.encode('utf-8'))
    base64_bytes = base64.b64encode(compressed_bytes)
    wrapped = textwrap.fill(base64_bytes.decode('utf-8'), width=column_width)
    return wrapped

def unwrap_and_decompress(wrapped_text):
    base64_str = wrapped_text.replace('\n', '')
    compressed_bytes = base64.b64decode(base64_str)
    original_string = zlib.decompress(compressed_bytes).decode('utf-8')
    return original_string

wrapped = compress_and_wrap(script_template)
print(wrapped)
unwrapped = unwrap_and_decompress(wrapped)
print(unwrapped == script_template)