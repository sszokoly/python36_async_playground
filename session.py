#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import re
from typing import Dict, Iterator, List, Tuple, Union

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
        'color': 'normal',
        'format_spec': '',
        'ypos': 1,
        'xpos': 1
    },
    {
        'text': 'session_id',
        'color': 'standout',
        'format_spec': '',
        'ypos': 1,
        'xpos': 13
    },
    {
        'text': 'Status:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 1,
        'xpos': 21
    },
        {
        'text': 'status',
        'color': 'standout',
        'format_spec': '',
        'ypos': 1,
        'xpos': 29
    },
    {
        'text': 'QoS:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 1,
        'xpos': 43
    },
    {
        'text': 'qos',
        'color': 'standout',
        'format_spec': '',
        'ypos': 1,
        'xpos': 48
    },
    {
        'text': 'Samples:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 1,
        'xpos': 58
    },
    {
        'text': 'samples',
        'color': 'standout',
        'format_spec': '',
        'ypos': 1,
        'xpos': 67
    },
    {
        'text': 'Start:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 2,
        'xpos': 1
    },
    {
        'text': 'start_time',
        'color': 'standout',
        'format_spec': '',
        'ypos': 2,
        'xpos': 8
    },
    {
        'text': 'End:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 2,
        'xpos': 30
    },
    {
        'text': 'end_time',
        'color': 'standout',
        'format_spec': '',
        'ypos': 2,
        'xpos': 35
    },
    {
        'text': 'Duration:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 2,
        'xpos': 57
    },
    {
        'text': 'duration',
        'color': 'standout',
        'format_spec': '',
        'ypos': 2,
        'xpos': 67
    },
    {
        'text': 'LOCAL',
        'color': 'title',
        'format_spec': '^36',
        'ypos': 4,
        'xpos': 1
    },
    {
        'text': 'REMOTE',
        'color': 'title',
        'format_spec': '^36',
        'ypos': 4,
        'xpos': 40
    },
    {
        'text': 'local_addr',
        'color': 'address',
        'format_spec': '>15',
        'ypos': 5,
        'xpos': 5
    },
    {
        'text': ':',
        'color': 'normal',
        'format_spec': '',
        'ypos': 5,
        'xpos': 20
    },
    {
        'text': 'local_port',
        'color': 'port',
        'format_spec': '<5',
        'ypos': 5,
        'xpos': 21
    },
    {
        'text': '<',
        'color': 'normal',
        'format_spec': '',
        'ypos': 5,
        'xpos': 27
    },
    {
        'text': '-',
        'color': 'normal',
        'format_spec': '-^20',
        'ypos': 5,
        'xpos': 28
    },
    {
        'text': 'codec',
        'color': 'codec',
        'format_spec': '^7',
        'ypos': 5,
        'xpos': 35
    },
    {
        'text': '>',
        'color': 'normal',
        'format_spec': '',
        'ypos': 5,
        'xpos': 48
    },
    {
        'text': 'remote_port',
        'color': 'port',
        'format_spec': '>5',
        'ypos': 5,
        'xpos': 50
    },
    {
        'text': ':',
        'color': 'normal',
        'format_spec': '',
        'ypos': 5,
        'xpos': 55
    },
    {
        'text': 'remote_addr',
        'color': 'address',
        'format_spec': '<15',
        'ypos': 5,
        'xpos': 56
    },
    {
        'text': 'SSRC',
        'color': 'normal',
        'format_spec': '',
        'ypos': 6,
        'xpos': 7
    },
    {
        'text': 'local_ssrc',
        'color': 'standout',
        'format_spec': '',
        'ypos': 6,
        'xpos': 12
    },
    {
        'text': 'Enc:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 6,
        'xpos': 25
    },
    {
        'text': 'codec_enc',
        'color': 'standout',
        'format_spec': '^22',
        'ypos': 6,
        'xpos': 29
    },
    {
        'text': 'SSRC',
        'color': 'normal',
        'format_spec': '',
        'ypos': 6,
        'xpos': 54
    },
    {
        'text': 'local_ssrc',
        'color': 'standout',
        'format_spec': '',
        'ypos': 6,
        'xpos': 59
    },
    {
        'text': 'remote_ssrc_change',
        'color': 'standout',
        'format_spec': '',
        'ypos': 6,
        'xpos': 70
    },
    {
        'text': 'RTP/RTCP',
        'color': 'title',
        'format_spec': '^36',
        'ypos': 8,
        'xpos': 1
    },
    {
        'text': 'CODEC',
        'color': 'title',
        'format_spec': '^36',
        'ypos': 8,
        'xpos': 40
    },
    {
        'text': 'RTP Packets (Rx/Tx):',
        'color': 'normal',
        'format_spec': '',
        'ypos': 9,
        'xpos': 2
    },
    {
        'text': 'rx_rtp_packets',
        'color': 'standout',
        'format_spec': '>7',
        'ypos': 9,
        'xpos': 22
    },
    {
        'text': '/',
        'color': 'normal',
        'format_spec': '',
        'ypos': 9,
        'xpos': 30
    },
    {
        'text': 'NA',
        'color': 'dimmmed',
        'format_spec': '>5',
        'ypos': 9,
        'xpos': 32
    },
    {
        'text': 'Psize/',
        'color': 'normal',
        'format_spec': '',
        'ypos': 9,
        'xpos': 46
    },
    {
        'text': 'Ptime:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 9,
        'xpos': 52
    },
    {
        'text': 'codec_psize',
        'color': 'standout',
        'format_spec': '>5',
        'ypos': 9,
        'xpos': 59
    },
    {
        'text': '/',
        'color': 'normal',
        'format_spec': '',
        'ypos': 9,
        'xpos': 64
    },
    {
        'text': 'codec_ptime',
        'color': 'standout',
        'format_spec': '',
        'ypos': 9,
        'xpos': 65
    },
    {
        'text': 'RTCP Packets (Rx/Tx):',
        'color': 'normal',
        'format_spec': '',
        'ypos': 10,
        'xpos': 1
    },
    {
        'text': 'rx_rtp_rtcp',
        'color': 'standout',
        'format_spec': '>7',
        'ypos': 10,
        'xpos': 22
    },
    {
        'text': '/',
        'color': 'normal',
        'format_spec': '',
        'ypos': 10,
        'xpos': 30
    },
    {
        'text': 'tx_rtp_rtcp',
        'color': 'standout',
        'format_spec': '>5',
        'ypos': 10,
        'xpos': 32
    },
    {
        'text': 'Play-Time:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 10,
        'xpos': 48
    },
    {
        'text': 'codec_play_time',
        'color': 'standout',
        'format_spec': '',
        'ypos': 10,
        'xpos': 60
    },
    {
        'text': 'DSCP (Rx/Tx):',
        'color': 'normal',
        'format_spec': '',
        'ypos': 11,
        'xpos': 9
    },
    {
        'text': 'rx_rtp_dscp',
        'color': 'standout',
        'format_spec': '>7',
        'ypos': 11,
        'xpos': 22
    },
    {
        'text': '/',
        'color': 'normal',
        'format_spec': '',
        'ypos': 11,
        'xpos': 30
    },
    {
        'text': 'tx_rtp_dscp',
        'color': 'standout',
        'format_spec': '>5',
        'ypos': 11,
        'xpos': 32
    },
    {
        'text': 'Avg-Loss:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 11,
        'xpos': 49
    },
    {
        'text': 'codec_avg_loss',
        'color': 'standout',
        'format_spec': '>6',
        'ypos': 11,
        'xpos': 59
    },
    {
        'text': 'L2Pri (Rx/Tx):',
        'color': 'normal',
        'format_spec': '',
        'ypos': 12,
        'xpos': 8
    },
    {
        'text': 'rx_rtp_l2pri',
        'color': 'standout',
        'format_spec': '>7',
        'ypos': 12,
        'xpos': 22
    },
    {
        'text': '/',
        'color': 'normal',
        'format_spec': '',
        'ypos': 12,
        'xpos': 30
    },
    {
        'text': 'tx_rtp_l2pri',
        'color': 'standout',
        'format_spec': '>5',
        'ypos': 12,
        'xpos': 32
    },
    {
        'text': 'Avg-RTT:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 12,
        'xpos': 50
    },
    {
        'text': 'codec_avg_rtt',
        'color': 'standout',
        'format_spec': '>7',
        'ypos': 12,
        'xpos': 58
    },
    {
        'text': 'Duplicates (Rx):',
        'color': 'normal',
        'format_spec': '',
        'ypos': 13,
        'xpos': 6
    },
    {
        'text': 'rx_rtp_duplicates',
        'color': 'standout',
        'format_spec': '>7',
        'ypos': 13,
        'xpos': 22
    },
    {
        'text': 'Max-Jbuf-Delay:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 13,
        'xpos': 43
    },
    {
        'text': 'codec_max_jbuf_delay',
        'color': 'standout',
        'format_spec': '>7',
        'ypos': 13,
        'xpos': 58
    },
    {
        'text': 'Seq-Fall (Rx):',
        'color': 'normal',
        'format_spec': '',
        'ypos': 14,
        'xpos': 8
    },
    {
        'text': 'rx_rtp_seqfall',
        'color': 'standout',
        'format_spec': '>7',
        'ypos': 14,
        'xpos': 22
    },
    {
        'text': 'JBuf-und/overruns:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 14,
        'xpos': 40
    },
    {
        'text': 'codec_jbuf_underruns',
        'color': 'standout',
        'format_spec': '>6',
        'ypos': 14,
        'xpos': 59
    },
    {
        'text': '/',
        'color': 'normal',
        'format_spec': '',
        'ypos': 14,
        'xpos': 65
    },
    {
        'text': 'codec_jbuf_overruns',
        'color': 'standout',
        'format_spec': '',
        'ypos': 14,
        'xpos': 66
    },
    {
        'text': 'LOCAL RTP STATISTICS',
        'color': 'title',
        'format_spec': '^36',
        'ypos': 16,
        'xpos': 1
    },
    {
        'text': 'REMOTE RTP STATISTICS',
        'color': 'title',
        'format_spec': '^36',
        'ypos': 16,
        'xpos': 40
    },
    {
        'text': 'Avg-Loss:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 17,
        'xpos': 13
    },
    {
        'text': 'rx_rtp_avg_loss',
        'color': 'standout',
        'format_spec': '>7',
        'ypos': 17,
        'xpos': 22
    },
    {
        'text': 'Avg-Loss:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 17,
        'xpos': 49
    },
    {
        'text': 'rem_avg_loss',
        'color': 'standout',
        'format_spec': '>6',
        'ypos': 17,
        'xpos': 59
    },
    {
        'text': 'Avg-Jitter:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 18,
        'xpos': 11
    },
    {
        'text': 'rx_rtp_avg_jitter',
        'color': 'standout',
        'format_spec': '>7',
        'ypos': 18,
        'xpos': 22
    },
    {
        'text': 'Avg-Jitter:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 18,
        'xpos': 47
    },
    {
        'text': 'rem_avg_jitter',
        'color': 'standout',
        'format_spec': '>7',
        'ypos': 18,
        'xpos': 58
    },
    {
        'text': 'Avg-RTT:',
        'color': 'normal',
        'format_spec': '',
        'ypos': 19,
        'xpos': 14
    },
    {
        'text': 'rx_rtp_avg_rtt',
        'color': 'standout',
        'format_spec': '>7',
        'ypos': 19,
        'xpos': 22
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

def cmds_to_session_dicts(cmds: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """
    Take the output of stdout_to_cmds and convert it into a dictionary of RTPSession objects.

    :param cmds: A dictionary of commands and their output, as returned by stdout_to_cmds
    :return: A dictionary of RTPSession objects, keyed by the 'id' attribute of each RTPSession
    """
    session_dicts = {}
    for cmd, output in cmds.items():
        if 'show rtp-stat detailed' not in cmd:
            continue
        try:
            session_dict = reDetailed.match(output).groupdict()
        except:
            continue
        id = '_'.join((
            session_dict['start_time'],
            session_dict['local_addr'],
            session_dict['session_id'].zfill(5)
        ))
        session_dict.update({'id': id})
        session_dicts.update({id: session_dict})
    return session_dicts

def iter_session_detailed_attrs(
    session_dict: Dict[str, str],
    detailed_attrs: List[Dict[str, Union[int, str]]] = DETAILED_ATTRS,
    yoffset: int = 0,
    xoffset: int = 1
    ) -> Iterator[Tuple[int, int, str, str]]:
    """
    Iterate over the attributes of a session dictionary and yield a tuple of 4 values:

    - `ypos`: The y position of the attribute
    - `xpos`: The x position of the attribute
    - `text`: The text of the attribute, formatted according to the `format_spec`
    - `color`: The color of the attribute

    :param session_dict: A dictionary of key-value pairs of the attributes of the session
    :param detailed_attrs: A list of dictionaries of the detailed attributes of the session
    :param yoffset: The offset of ypos
    :param xoffset: The offset of xpos
    :return: An iterator of tuples of 4 values
    """
    for attrs in detailed_attrs:
        text = session_dict.get(attrs['text'], attrs['text'])
        text = f'{text:{attrs["format_spec"]}}'
        yield attrs['ypos'] + yoffset, attrs['xpos'] + xoffset, text, attrs['color']

if __name__ == '__main__':
    stdout = '''#BEGIN\nshow rtp-stat detailed 00001\r\n\r\nSession-ID: 1\r\nStatus: Terminated, QOS: Ok, EngineId: 10\r\nStart-Time: 2024-11-04,10:06:07, End-Time: 2024-11-04,10:07:07\r\nDuration: 00:00:00\r\nCName: gwp@10.10.48.58\r\nPhone: \r\nLocal-Address: 192.168.110.110:2052 SSRC 1653399062\r\nRemote-Address: 10.10.48.192:35000 SSRC 2704961869 (0)\r\nSamples: 0 (5 sec)\r\n\r\nCodec:\r\nG711U 200B 20mS srtpAesCm128HmacSha180, Silence-suppression(Tx/Rx) Disabled/Disabled, Play-Time 4.720sec, Loss 0.8% #0, Avg-Loss 0.8%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 22mS, Max-Jbuf-Delay 22mS\r\n\r\nReceived-RTP:\r\nPackets 245, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, Jitter 2mS #0, Avg-Jitter 2mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 0, Flow-Label 2\r\n\r\nTransmitted-RTP:\r\nVLAN 0, DSCP 46, L2Pri 0, RTCP 10, Flow-Label 0\r\n\r\nRemote-Statistics:\r\nLoss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS\r\n\r\nEcho-Cancellation:\r\nLoss 0dB #2, Len 0mS\r\n\r\nRSVP:\r\nStatus Unused, Failures 0\n#END'''
    stdout += '''#BEGIN\nshow rtp-stat detailed 00002\r\n\r\nSession-ID: 1\r\nStatus: Terminated, QOS: Faulted, EngineId: 10\r\nStart-Time: 2024-11-04,10:06:10, End-Time: 2024-11-04,10:07:10\r\nDuration: 00:00:00\r\nCName: gwp@10.10.48.58\r\nPhone: \r\nLocal-Address: 192.168.110.111:2052 SSRC 1653399062\r\nRemote-Address: 192.168.110.112:35000 SSRC 2704961869 (0)\r\nSamples: 0 (5 sec)\r\n\r\nCodec:\r\nG711U 200B 20mS Off, Silence-suppression(Tx/Rx) Disabled/Not-Supported, Play-Time 4.720sec, Loss 0.8% #0, Avg-Loss 0.8%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 22mS, Max-Jbuf-Delay 22mS\r\n\r\nReceived-RTP:\r\nPackets 245, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, Jitter 2mS #0, Avg-Jitter 2mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 0, Flow-Label 2\r\n\r\nTransmitted-RTP:\r\nVLAN 0, DSCP 46, L2Pri 0, RTCP 10, Flow-Label 0\r\n\r\nRemote-Statistics:\r\nLoss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS\r\n\r\nEcho-Cancellation:\r\nLoss 0dB #2, Len 0mS\r\n\r\nRSVP:\r\nStatus Unused, Failures 0\n#END'''
    print(stdout)
    session_dicts = cmds_to_session_dicts(stdout_to_cmds(stdout))
    for id, session_dict in session_dicts.items():
        print(session_dict)
        for y, x, text, attrs in iter_session_detailed_attrs(session_dict):
            print(y, x, text, attrs)