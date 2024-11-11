#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import re
from datetime import datetime

detailed_fields = r''.join((
    r'.*?Session-ID: (?P<id>\d+)',
    r'.*?Status: (?P<status>\w+)',
    r'.*?QOS: (?P<qos>\w+)',
    r'.*?Start-Time: (?P<starttime>\S+), End-Time: (?P<endtime>\S+)',
    r'.*?Duration: (?P<duration>\S+)',
    r'.*?Phone: (?P<phone>.*?)\s+',
    r'.*?Local-Address: (?P<srcip>\S+):(?P<srcport>\d+) SSRC (?P<srcssrc>\d+)',
    r'.*?Remote-Address: (?P<dstip>\S+):(?P<dstport>\d+) SSRC (?P<dstssrc>\d+)',
    r'.*?Samples: (?P<samples>\d+)',
    r'.*?Codec:\s+(?P<codec>\S+)',
    r'.*?mS (?P<enc>\S+),',
    r'.*?Play-Time (?P<playtime>\S+),',
    r'.*?Avg-Loss (?P<codec_avgloss>\S+),',
    r'.*?Avg-RTT (?P<codec_avgrtt>\S+),',
    r'.*?Max-Jbuf-Delay (?P<codec_maxjbufdelay>\S+)',
    r'.*?Packets (?P<rtp_rx_pkts>\d+),',
    r'.*?Avg-Loss (?P<rtp_rx_avgloss>\S+)',
    r'.*?Avg-RTT (?P<rtp_rx_avgrtt>\S+),',
    r'.*?Avg-Jitter (?P<rtp_rx_avgjitter>\S+),',
    r'.*?Duplicates (?P<rtp_rx_dup>\d+),',
    r'.*?Seq-Fall (?P<rtp_rx_seqfall>\d+),',
    r'.*?DSCP (?P<rtp_rx_dscp>\d+),',
    r'.*?L2Pri (?P<rtp_rx_l2pri>\d+),',
    r'.*?RTCP (?P<rtp_rx_rtcp>\d+),',
    r'.*?VLAN (?P<rtp_tx_vlan>\d+),',
    r'.*?DSCP (?P<rtp_tx_dscp>\d+),',
    r'.*?L2Pri (?P<rtp_tx_l2pri>\d+),',
    r'.*?RTCP (?P<rtp_tx_rtcp>\d+),',
    r'.*?Avg-Loss (?P<rem_avgloss>\S+),',
    r'.*?Avg-Jitter (?P<rem_avgjitter>\S+)',
))


def detailed_to_dict(detailed, pattern=detailed_fields):
    try:
        d = re.match(pattern, detailed.strip(), re.M|re.S|re.I).groupdict()
        d['starttime'] = datetime.strptime(d['starttime'], '%Y-%m-%d,%H:%M:%S')
        d['endtime'] = datetime.strptime(d['endtime'], '%Y-%m-%d,%H:%M:%S')
        d['duration'] = d['endtime'] - d['starttime']
        return d
    except:
        return {}


if __name__ == '__main__':
    DETAILED = '''show rtp-stat detailed 00022\r\n\r\nSession-ID: 22\r\nStatus: Terminated, QOS: Ok, EngineId: 10\r\nStart-Time: 2024-06-24,10:03:06, End-Time: 2024-06-24,10:04:29\r\nDuration: 00:01:23\r\nCName:
    gwp@10.10.48.58\r\nPhone: \r\nLocal-Address: 10.10.48.58:2050 SSRC 2100011765\r\nRemote-Address: 10.10.48.160:2048 SSRC 24089228 (0)\r\nSamples: 16 (5 sec)\r\n\r\nCodec:\r\nG711U 200B 20mS srtpAesCm128HmacSha
    180, Silence-suppression(Tx/Rx) Disabled/Disabled, Play-Time 84.980sec, Loss 0.1% #0, Avg-Loss 0.2%, RTT 62mS #0, Avg-RTT 61mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 13mS, Max-Jbuf-Delay 18mS\r\n\r\nReceiv
    ed-RTP:\r\nPackets 4394, Loss 0.0% #0, Avg-Loss 0.0%, RTT 9mS #0, Avg-RTT 8mS, Jitter 0mS #0, Avg-Jitter 0mS, TTL(last/min/max) 64/64/64, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 18, Flow-Label 0\r\n\r\
    nTransmitted-RTP:\r\nVLAN 0, DSCP 46, L2Pri 0, RTCP 26, Flow-Label 0\r\n\r\nRemote-Statistics:\r\nLoss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS\r\n\r\nEcho-Cancellation:\r\nLoss 0dB #18, Len 0mS\r
    \n\r\nRSVP:\r\nStatus Unused, Failures 0\r\n\r\nDone!\r\nAvayaG450A-001(super)# END show rtp-stat detailed 00022\n\n'''
    print(f'\n{detailed_to_dict(DETAILED)}')