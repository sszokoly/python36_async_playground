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

set randomInt [expr {{int(rand() * 4)}}]

sleep 2
set last_seen [exec date "+%Y-%m-%d,%H:%M:%S"]

if {{$randomInt == 1}} {{
    puts -nonewline stderr "ExpectTimeout"; exit 255
}}
puts "{{\\"gw_number\\": \\"001\\", \\"gw_name\\": \\"$host\\", \\"host\\": \\"$host\\", \\"last_seen\\": \\"$last_seen\\", \\"commands\\": {{\\"show system\\": \\"location: 1\\", \\"show running-config\\": \\"location: 1\\"}}, \\"rtp_sessions\\": {{\\"2024-12-30,11:06:15,$host,0000$randomInt\\": \\"session 0000$randomInt\\"}}}}"
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