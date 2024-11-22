#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import re
from typing import Dict, Iterator, List, Tuple

DETAILED_PATTERNS = (
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

DETAILED_ATTRS = [
    {
        'text': 'Session-ID:',
        'color': 'white',
        'format_spec': '',
        'ypos': 1,
        'xpos': 0
    },
    {
        'text': 'session_id',
        'color': 'white_standout',
        'format_spec': '>5',
        'ypos': 1,
        'xpos': 12
    },
    {
        'text': 'Status:',
        'color': 'white',
        'format_spec': '',
        'ypos': 1,
        'xpos': 20
    },
        {
        'text': 'status',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 1,
        'xpos': 28
    },
    {
        'text': 'QoS:',
        'color': 'white',
        'format_spec': '',
        'ypos': 1,
        'xpos': 41
    },
    {
        'text': 'qos',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 1,
        'xpos': 46
    },
    {
        'text': 'Samples:',
        'color': 'white',
        'format_spec': '',
        'ypos': 1,
        'xpos': 56
    },
    {
        'text': 'samples',
        'color': 'white_standout',
        'format_spec': '>4',
        'ypos': 1,
        'xpos': 65
    },
    {
        'text': 'sampling_interval',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 1,
        'xpos': 70
    },
    {
        'text': 'Start:',
        'color': 'white',
        'format_spec': '',
        'ypos': 2,
        'xpos': 0
    },
    {
        'text': 'start_time',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 2,
        'xpos': 7
    },
    {
        'text': 'End:',
        'color': 'white',
        'format_spec': '',
        'ypos': 2,
        'xpos': 29
    },
    {
        'text': 'end_time',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 2,
        'xpos': 34
    },
    {
        'text': 'Duration:',
        'color': 'white',
        'format_spec': '',
        'ypos': 2,
        'xpos': 56
    },
    {
        'text': 'duration',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 2,
        'xpos': 66
    },
    {
        'text': 'LOCAL ADDRESS',
        'color': 'white',
        'format_spec': '',
        'ypos': 4,
        'xpos': 5
    },
    {
        'text': 'REMOTE ADDRESS',
        'color': 'white',
        'format_spec': '',
        'ypos': 4,
        'xpos': 59
    },
    {
        'text': 'local_addr',
        'color': 'yellow',
        'format_spec': '>15',
        'ypos': 4,
        'xpos': 3
    },
    {
        'text': 'local_port',
        'color': 'cyan',
        'format_spec': '',
        'ypos': 4,
        'xpos': 19
    },
    {
        'text': '-',
        'color': 'white',
        'format_spec': '-^27',
        'ypos': 4,
        'xpos': 25
    },
    {
        'text': 'codec',
        'color': 'green',
        'format_spec': '^7',
        'ypos': 4,
        'xpos': 36
    },
    {
        'text': 'remote_port',
        'color': 'cyan',
        'format_spec': '>5',
        'ypos': 4,
        'xpos': 53
    },
    {
        'text': 'remote_addr',
        'color': 'yellow',
        'format_spec': '',
        'ypos': 4,
        'xpos': 59
    },
    {
        'text': 'SSRC',
        'color': 'white',
        'format_spec': '',
        'ypos': 5,
        'xpos': 3
    },
    {
        'text': 'local_ssrc',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 5,
        'xpos': 7
    },
    {
        'text': 'Enc:',
        'color': 'white',
        'format_spec': '',
        'ypos': 5,
        'xpos': 25
    },
    {
        'text': 'codec_enc',
        'color': 'white_standout',
        'format_spec': '^22',
        'ypos': 5,
        'xpos': 30
    },
    {
        'text': 'SSRC',
        'color': 'white',
        'format_spec': '',
        'ypos': 5,
        'xpos': 58
    },
    {
        'text': 'local_ssrc',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 5,
        'xpos': 63
    },
    {
        'text': 'remote_ssrc_change',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 5,
        'xpos': 74
    },
    {
        'text': 'RTP/RTCP',
        'color': 'white',
        'format_spec': '',
        'ypos': 7,
        'xpos': 12
    },
    {
        'text': 'CODEC',
        'color': 'white',
        'format_spec': '',
        'ypos': 7,
        'xpos': 62
    },
    {
        'text': 'RTP Packets (Rx/Tx):',
        'color': 'white',
        'format_spec': '',
        'ypos': 8,
        'xpos': 4
    },
    {
        'text': 'rx_rtp_packets',
        'color': 'white_standout',
        'format_spec': '>7',
        'ypos': 8,
        'xpos': 25
    },
    {
        'text': '/',
        'color': 'white',
        'format_spec': '',
        'ypos': 8,
        'xpos': 33
    },
    {
        'text': 'NA',
        'color': 'white',
        'format_spec': '',
        'ypos': 8,
        'xpos': 38
    },
    {
        'text': 'Psize/',
        'color': 'white',
        'format_spec': '',
        'ypos': 8,
        'xpos': 50
    },
    {
        'text': 'Ptime:',
        'color': 'white',
        'format_spec': '',
        'ypos': 8,
        'xpos': 56
    },
    {
        'text': 'codec_psize',
        'color': 'white_standout',
        'format_spec': '>4',
        'ypos': 8,
        'xpos': 63
    },
    {
        'text': '/',
        'color': 'white',
        'format_spec': '',
        'ypos': 8,
        'xpos': 67
    },
    {
        'text': 'codec_ptime',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 8,
        'xpos': 68
    },
    {
        'text': 'RTCP Packets (Rx/Tx):',
        'color': 'white',
        'format_spec': '',
        'ypos': 9,
        'xpos': 3
    },
    {
        'text': 'rx_rtp_rtcp',
        'color': 'white_standout',
        'format_spec': '>7',
        'ypos': 9,
        'xpos': 25
    },
    {
        'text': '/',
        'color': 'white',
        'format_spec': '',
        'ypos': 9,
        'xpos': 33
    },
    {
        'text': 'tx_rtp_rtcp',
        'color': 'white_standout',
        'format_spec': '>5',
        'ypos': 9,
        'xpos': 35
    },
    {
        'text': 'Play-Time:',
        'color': 'white',
        'format_spec': '',
        'ypos': 9,
        'xpos': 52
    },
    {
        'text': 'codec_play_time',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 9,
        'xpos': 63
    },
    {
        'text': 'DSCP (Rx/Tx):',
        'color': 'white',
        'format_spec': '',
        'ypos': 10,
        'xpos': 11
    },
    {
        'text': 'rx_rtp_dscp',
        'color': 'white_standout',
        'format_spec': '>7',
        'ypos': 10,
        'xpos': 25
    },
    {
        'text': '/',
        'color': 'white',
        'format_spec': '',
        'ypos': 10,
        'xpos': 33
    },
    {
        'text': 'tx_rtp_dscp',
        'color': 'white_standout',
        'format_spec': '>5',
        'ypos': 10,
        'xpos': 25
    },
    {
        'text': 'Avg-Loss:',
        'color': 'white',
        'format_spec': '',
        'ypos': 10,
        'xpos': 53
    },
    {
        'text': 'codec_avg_loss',
        'color': 'white_standout',
        'format_spec': '>5',
        'ypos': 10,
        'xpos': 63
    },
    {
        'text': 'L2Pri (Rx/Tx):',
        'color': 'white',
        'format_spec': '',
        'ypos': 11,
        'xpos': 10
    },
    {
        'text': 'rx_rtp_l2pri',
        'color': 'white_standout',
        'format_spec': '>7',
        'ypos': 11,
        'xpos': 25
    },
    {
        'text': '/',
        'color': 'white',
        'format_spec': '',
        'ypos': 11,
        'xpos': 33
    },
    {
        'text': 'tx_rtp_l2pri',
        'color': 'white_standout',
        'format_spec': '>5',
        'ypos': 11,
        'xpos': 35
    },
    {
        'text': 'Avg-RTT:',
        'color': 'white',
        'format_spec': '',
        'ypos': 11,
        'xpos': 54
    },
    {
        'text': 'codec_avg_rtt',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 11,
        'xpos': 63
    },
    {
        'text': 'Duplicates (Rx):',
        'color': 'white',
        'format_spec': '',
        'ypos': 12,
        'xpos': 8
    },
    {
        'text': 'rx_rtp_duplicates',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 12,
        'xpos': 25
    },
    {
        'text': 'Max-Jbuf-Delay:',
        'color': 'white',
        'format_spec': '',
        'ypos': 12,
        'xpos':47
    },
    {
        'text': 'codec_max_jbuf_delay',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 12,
        'xpos': 63
    },
    {
        'text': 'Seq-Fall (Rx):',
        'color': 'white',
        'format_spec': '',
        'ypos': 13,
        'xpos': 10
    },
    {
        'text': 'rx_rtp_seqfall',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 13,
        'xpos': 25
    },
    {
        'text': 'JBuf-under/overruns:',
        'color': 'white',
        'format_spec': '',
        'ypos': 13,
        'xpos': 42
    },
    {
        'text': 'codec_jbuf_underruns',
        'color': 'white_standout',
        'format_spec': '>5',
        'ypos': 13,
        'xpos': 63
    },
    {
        'text': '/',
        'color': 'white',
        'format_spec': '',
        'ypos': 13,
        'xpos': 68
    },
    {
        'text': 'codec_jbuf_overruns',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 13,
        'xpos': 69
    },
    {
        'text': 'LOCAL RTP STATISTICS',
        'color': 'white',
        'format_spec': '',
        'ypos': 15,
        'xpos': 3
    },
    {
        'text': 'REMOTE RTP STATISTICS',
        'color': 'white',
        'format_spec': '',
        'ypos': 15,
        'xpos': 52
    },
    {
        'text': 'Loss:',
        'color': 'white',
        'format_spec': '',
        'ypos': 16,
        'xpos': 8
    },
    {
        'text': 'Loss:',
        'color': 'white',
        'format_spec': '',
        'ypos': 16,
        'xpos': 8
    },
    {
        'text': 'rx_rtp_loss',
        'color': 'white_standout',
        'format_spec': '>6',
        'ypos': 16,
        'xpos': 14
    },
    {
        'text': 'rx_rtp_loss_events',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 16,
        'xpos': 21
    },
    {
        'text': 'Loss:',
        'color': 'white',
        'format_spec': '',
        'ypos': 16,
        'xpos': 57
    },
    {
        'text': 'rem_loss',
        'color': 'white_standout',
        'format_spec': '>6',
        'ypos': 16,
        'xpos': 63
    },
    {
        'text': 'rem_loss_events',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 16,
        'xpos': 70
    },
    {
        'text': 'Avg-Loss:',
        'color': 'white',
        'format_spec': '',
        'ypos': 17,
        'xpos': 4
    },
    {
        'text': 'rx_rtp_avg_loss',
        'color': 'white_standout',
        'format_spec': '>6',
        'ypos': 17,
        'xpos': 14
    },
    {
        'text': 'Avg-Loss',
        'color': 'white',
        'format_spec': '',
        'ypos': 17,
        'xpos': 57
    },
    {
        'text': 'rem_avg_loss',
        'color': 'white_standout',
        'format_spec': '>6',
        'ypos': 17,
        'xpos': 63
    },
    {
        'text': 'Jitter:',
        'color': 'white',
        'format_spec': '',
        'ypos': 18,
        'xpos': 6
    },
    {
        'text': 'rx_rtp_jitter',
        'color': 'white_standout',
        'format_spec': '>6',
        'ypos': 18,
        'xpos': 14
    },
    {
        'text': 'rx_rtp_jitter_events',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 18,
        'xpos': 21
    },
    {
        'text': 'Jitter:',
        'color': 'white',
        'format_spec': '',
        'ypos': 18,
        'xpos': 55
    },
    {
        'text': 'rem_jitter',
        'color': 'white_standout',
        'format_spec': '>6',
        'ypos': 18,
        'xpos': 14
    },
    {
        'text': 'rem_jitter_events',
        'color': 'white_standout',
        'format_spec': '',
        'ypos': 18,
        'xpos': 70
    },
    {
        'text': 'Avg-Jitter:',
        'color': 'white',
        'format_spec': '',
        'ypos': 19,
        'xpos': 4
    },
    {
        'text': 'rx_rtp_avg_jitter',
        'color': 'white_standout',
        'format_spec': '>6',
        'ypos': 19,
        'xpos': 14
    },
    {
        'text': 'Avg-Jitter:',
        'color': 'white',
        'format_spec': '',
        'ypos': 19,
        'xpos': 51
    },
    {
        'text': 'rem_avg_jitter',
        'color': 'white_standout',
        'format_spec': '>6',
        'ypos': 19,
        'xpos': 63
    },
    {
        'text': 'RTT:',
        'color': 'white',
        'format_spec': '',
        'ypos': 20,
        'xpos': 9
    },
    {
        'text': 'rx_rtp_rtt',
        'color': 'white_standout',
        'format_spec': '>6',
        'ypos': 20,
        'xpos': 14
    },
    {
        'text': 'Avg-RTT:',
        'color': 'white',
        'format_spec': '',
        'ypos': 21,
        'xpos': 5
    },
    {
        'text': 'rx_rtp_avg_rtt',
        'color': 'white_standout',
        'format_spec': '>6',
        'ypos': 21,
        'xpos': 14
    },
]

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
        self.id = '_'.join((
            params['start_time'],
            params['local_addr'],
            params['session_id'].zfill(5)
        ))

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

reDetailed = re.compile(r''.join(DETAILED_PATTERNS), re.M|re.S|re.I)
reFindall = re.compile(r'#BEGIN(.*?)\s+?#END', re.M|re.S|re.I)

def stdout_to_cmds(stdout: str) -> Dict[str, str]:
    """
    Take expect script output andd split it into a dictionary of commands and their output.

    :param stdout: The output of expect script as a string
    :return: A dictionary of commands and their output as strings
    """
    cmds = {}
    commands = [x for x in reFindall.split(stdout) if x.strip()]
    for c in commands:
        command, output = c.split("\r\n", 1)
        cmds[command.strip()] = output.strip()
    return cmds

def cmds_to_rtpsessions(cmds: Dict[str, str]) -> Dict[str, RTPSession]:
    """
    Take the output of stdout_to_cmds and convert it into a dictionary of RTPSession objects.

    :param cmds: A dictionary of commands and their output, as returned by stdout_to_cmds
    :return: A dictionary of RTPSession objects, keyed by the 'id' attribute of each RTPSession
    """
    rtpsessions = {}
    for cmd, output in cmds.items():
        if 'show rtp-stat detailed' not in cmd:
            continue
        try:
            d = reDetailed.match(output).groupdict()
            print(d)
        except:
            continue
        id = '_'.join((
            d['start_time'],
            d['local_addr'],
            d['session_id'].zfill(5)
        ))
        d.update({'id': id})
        rtpsessions.update({id: d})
    return rtpsessions

def iter_session_attrs(
    session_dict: Dict[str, str],
    detailed_attrs: List[Dict[str, str]] = DETAILED_ATTRS
    ) -> Iterator[Tuple[int, int, str, str]]:
    """
    Iterate over the attributes of a session dictionary and yield a tuple of 4 values:
    - The y position of the attribute
    - The x position of the attribute
    - The text of the attribute, formatted according to the format_spec
    - The color of the attribute

    :param session_dict: A dictionary of key-value pairs of the attributes of the session
    :param detailed_attrs: A list of dictionaries of the detailed attributes of the session
    :return: An iterator of tuples of 4 values
    """
    for attrs in detailed_attrs:
        text = session_dict.get(attrs['text'], attrs['text'])
        text = f'{text:{attrs["format_spec"]}}'
        yield attrs['ypos'], attrs['xpos'], text, attrs['color']

if __name__ == '__main__':
    stdout = '''#BEGIN\nshow rtp-stat detailed 00001\r\n\r\nSession-ID: 1\r\nStatus: Terminated, QOS: Ok, EngineId: 10\r\nStart-Time: 2024-11-04,10:06:07, End-Time: 2024-11-04,10:07:07\r\nDuration: 00:00:00\r\nCName: gwp@10.10.48.58\r\nPhone: \r\nLocal-Address: 192.168.110.110:2052 SSRC 1653399062\r\nRemote-Address: 10.10.48.192:35000 SSRC 2704961869 (0)\r\nSamples: 0 (5 sec)\r\n\r\nCodec:\r\nG711U 200B 20mS srtpAesCm128HmacSha180, Silence-suppression(Tx/Rx) Disabled/Disabled, Play-Time 4.720sec, Loss 0.8% #0, Avg-Loss 0.8%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 22mS, Max-Jbuf-Delay 22mS\r\n\r\nReceived-RTP:\r\nPackets 245, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, Jitter 2mS #0, Avg-Jitter 2mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 0, Flow-Label 2\r\n\r\nTransmitted-RTP:\r\nVLAN 0, DSCP 46, L2Pri 0, RTCP 10, Flow-Label 0\r\n\r\nRemote-Statistics:\r\nLoss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS\r\n\r\nEcho-Cancellation:\r\nLoss 0dB #2, Len 0mS\r\n\r\nRSVP:\r\nStatus Unused, Failures 0\n#END'''
    stdout += '''#BEGIN\nshow rtp-stat detailed 00002\r\n\r\nSession-ID: 1\r\nStatus: Terminated, QOS: Faulted, EngineId: 10\r\nStart-Time: 2024-11-04,10:06:10, End-Time: 2024-11-04,10:07:10\r\nDuration: 00:00:00\r\nCName: gwp@10.10.48.58\r\nPhone: \r\nLocal-Address: 192.168.110.111:2052 SSRC 1653399062\r\nRemote-Address: 192.168.110.112:35000 SSRC 2704961869 (0)\r\nSamples: 0 (5 sec)\r\n\r\nCodec:\r\nG711U 200B 20mS Off, Silence-suppression(Tx/Rx) Disabled/Not-Supported, Play-Time 4.720sec, Loss 0.8% #0, Avg-Loss 0.8%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 22mS, Max-Jbuf-Delay 22mS\r\n\r\nReceived-RTP:\r\nPackets 245, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, Jitter 2mS #0, Avg-Jitter 2mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 0, Flow-Label 2\r\n\r\nTransmitted-RTP:\r\nVLAN 0, DSCP 46, L2Pri 0, RTCP 10, Flow-Label 0\r\n\r\nRemote-Statistics:\r\nLoss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS\r\n\r\nEcho-Cancellation:\r\nLoss 0dB #2, Len 0mS\r\n\r\nRSVP:\r\nStatus Unused, Failures 0\n#END'''
    print(stdout)
    rtpsessions = cmds_to_rtpsessions(stdout_to_cmds(stdout))
    for id, rtpsession in rtpsessions.items():
        print(str(rtpsession))
        for y, x, text, attrs in iter_session_attrs(rtpsession):
            print(y, x, text, attrs)