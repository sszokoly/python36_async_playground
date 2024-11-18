#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import re
from typing import Dict

SESSION_DETAILED = (
        r'.*?Session-ID: (?P<session_id>\d+)',
        r'.*?Status: (?P<status>\S+), QOS: (?P<qos>\S+), EngineId: (?P<engineid>\d+)',
        r'.*?Start-Time: (?P<start_time>\S+),',
        r'.*?End-Time: (?P<end_time>\S+)',
        r'.*?Duration: (?P<duration>\S+)',
        r'.*?CName: (?P<cname>\S+)',
        r'.*?Phone: (?P<phone>.*?)\s+',
        r'.*?Local-Address: (?P<local_addr>\S+):(?P<local_port>\d+) SSRC (?P<local_ssrc>\d+)',
        r'.*?Remote-Address: (?P<remote_addr>\S+):(?P<remote_port>\d+) SSRC (?P<remote_ssrc>\d+) (?P<ssrc_change>\S+)',
        r'.*?Samples: (?P<samples>\d+) (?P<sampling_interval>\(.*?\))',
        r'.*?Codec:\s+(?P<codec>\S+) (?P<pkt_size>\S+) (?P<ptime>\S+)',
        r'.*?(?P<enc>\S+),',
        r'.*?Silence-suppression\(Tx/Rx\) (?P<codec_silence_suppr_tx>\S+)/(?P<codec_silence_suppr_rx>\S+),',
        r'.*?Play-Time (?P<play_time>\S+),',
        r'.*?Loss (?P<codec_loss>\S+) #(?P<codec_loss_events>\d+),',
        r'.*?Avg-Loss (?P<codec_avg_loss>\S+),',
        r'.*?RTT (?P<codec_rtt>\S+) #(?P<codec_rtt_events>\d+),'
        r'.*?Avg-RTT (?P<codec_avg_rtt>\S+),'
        r'.*?JBuf-under/overruns (?P<codec_jbuf_underruns>\S+)/(?P<codec_jbuf_overruns>\S+),',
        r'.*?Jbuf-Delay (?P<codec_jbuf_delay>\S+),',
        r'.*?Max-Jbuf-Delay (?P<codec_max_jbuf_delay>\S+)',
        r'.*?Packets (?P<rx_rtp_packets>\d+),',
        r'.*?Loss (?P<rx_rtp_loss>\S+) #(?P<rx_rtp_loss_events>\d+),',
        r'.*?Avg-Loss (?P<rx_rtp_avg_loss>\S+),',
        r'.*?RTT (?P<rx_rtp_rtt>\S+) #(?P<rx_rtp_rtt_events>\d+),'
        r'.*?Avg-RTT (?P<rx_rtp_avg_rtt>\S+),'
        r'.*?Jitter (?P<rx_rtp_jitter>\S+) #(?P<rx_rtp_jitter_events>\d+),'
        r'.*?Avg-Jitter (?P<rx_rtp_avg_jitter>\S+),'
        r'.*?TTL\(last/min/max\) (?P<rx_rtp_ttl_last>\d+)/(?P<rx_rtp_ttl_min>\d+)/(?P<rx_rtp_ttl_max>\d+),'
        r'.*?Duplicates (?P<rx_rtp_duplicates>\d+),',
        r'.*?Seq-Fall (?P<rx_rtp_seqfall>\d+),',
        r'.*?DSCP (?P<rx_rtp_dscp>\d+),',
        r'.*?L2Pri (?P<rx_rtp_l2pri>\d+),',
        r'.*?RTCP (?P<rx_rtp_rtcp>\d+),',
        r'.*?Flow-Label (?P<rx_rtp_flow_label>\d+)',
        r'.*?VLAN (?P<tx_rtp_vlan>\d+),',
        r'.*?DSCP (?P<tx_rtp_dscp>\d+),',
        r'.*?L2Pri (?P<tx_rtp_l2pri>\d+),',
        r'.*?RTCP (?P<rtp_tx_rtcp>\d+),',
        r'.*?Flow-Label (?P<tx_rtp_flow_label>\d+)',
        r'.*?Loss (?P<rem_loss>\S+) #(?P<rem_loss_events>\S+),',
        r'.*?Avg-Loss (?P<rem_avg_loss>\S+),',
        r'.*?Jitter (?P<rem_jitter>\S+) #(?P<rem_jitter_events>\S+),',
        r'.*?Avg-Jitter (?P<rem_avg_jitter>\S+)',
        r'.*?Loss (?P<ec_loss>\S+) #(?P<ec_loss_events>\S+),',
        r'.*?Len (?P<ec_len>\S+)',
        r'.*?Status (?P<rsvp_status>\S+),',
        r'.*?Failures (?P<rsvp_failures>\d+)',
)

SESSION_FORMAT = '''
Session-ID: {WHITE}{session_id}{END}
    Status: {WHITE}{status}{END}
       QoS: {WHITE}{qos}{END}
Start-Time: {WHITE}{start_time}{END}
  End-Time: {WHITE}{end_time}{END}
  Duration: {WHITE}{duration}{END}
   Samples: {WHITE}{samples} {sampling_interval}{END}

  LOCAL-ADDRESS                                REMOTE-ADDRESS
{YELLOW}{local_addr:>15}{END}:{BLUE}{local_port:5}{END} <{codec:-^19}> {BLUE}{remote_port}{END}:{YELLOW}{remote_addr}{END}
SSRC {local_ssrc:38}  SSRC {remote_ssrc} {ssrc_change}

        RTP  Packets (Rx/Tx): {rx_rtp_packets:>6} / NA
        RTCP Packets (Rx/Tx): {rx_rtp_rtcp:>6} / {rtp_tx_rtcp}
                DSCP (Rx/Tx): {rx_rtp_dscp:>6} / {tx_rtp_dscp}
               L2Pri (Rx/Tx): {rx_rtp_l2pri:>6} / {tx_rtp_l2pri}
             Duplicates (Rx): {rx_rtp_duplicates:>6}
               Seq-Fall (Rx): {rx_rtp_seqfall:>6}

  LOCAL RTP STATISTICS (Rx)       REMOTE RTP STATISTICS (Rx)
       Loss: {rx_rtp_loss:>6} #{rx_rtp_loss_events:3}               Loss: {rem_loss:>6} #{rem_loss_events}
   Avg-Loss: {rx_rtp_avg_loss:>6}                Avg-Loss: {rem_avg_loss:>6}
     Jitter: {rx_rtp_jitter:>6} #{rx_rtp_jitter_events:3}             Jitter: {rem_jitter:>6} #{rem_jitter_events}
 Avg-Jitter: {rx_rtp_avg_jitter:>6}              Avg-Jitter: {rem_avg_jitter:>6}
        RTT: {rx_rtp_rtt:>6} #{rx_rtp_rtt_events:3}       
    Avg-RTT: {rx_rtp_avg_rtt:>6}

  LOCAL CODEC STATISTICS
      Encryption: {enc}
       Play-Time: {play_time}
            Loss: {codec_loss} #{codec_loss_events}
        Avg-Loss: {codec_avg_loss}
             RTT: {codec_rtt} #{codec_rtt_events}
         Avg-RTT: {codec_avg_rtt}
  Jbuf-underruns: {codec_jbuf_underruns}
   Jbuf-overruns: {codec_jbuf_overruns}
      Jbuf-Delay: {codec_jbuf_delay}
  Max-Jbuf-Delay: {codec_max_jbuf_delay}
Silence-Sup (Tx): {codec_silence_suppr_tx}
Silence-Sup (Rx): {codec_silence_suppr_rx}

  ECHO CANCELATION
            Loss: {ec_loss} #{ec_loss_events}
             Len: {ec_len}
'''

class RTPSession:
    color = {
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'PURPLE': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[1;97m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m',
        'END': '\033[0m',
    }

    def __init__(self, params: Dict[str, str], session_format: str = SESSION_FORMAT) -> None:
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
        self.session_format = session_format

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
        return self.session_format.format(**{
            **self.__dict__,
            **self.__class__.__dict__['color']
        })

reRTP_detailed = re.compile(r''.join(SESSION_DETAILED), re.M|re.S|re.I)
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
            d = reRTP_detailed.match(output).groupdict()
        except:
            continue
        id = '_'.join((
            d['start_time'],
            d['local_addr'],
            d['session_id'].zfill(5)
        ))
        d.update({'id': id})
        rtpsession = RTPSession(d)
        rtpsessions.update({id: rtpsession})
    return rtpsessions

if __name__ == '__main__':
    stdout = '''#BEGIN\nshow rtp-stat detailed 00001\r\n\r\nSession-ID: 1\r\nStatus: Terminated, QOS: Ok, EngineId: 10\r\nStart-Time: 2024-11-04,10:06:07, End-Time: 2024-11-04,10:07:07\r\nDuration: 00:00:00\r\nCName: gwp@10.10.48.58\r\nPhone: \r\nLocal-Address: 192.168.110.110:2052 SSRC 1653399062\r\nRemote-Address: 10.10.48.192:35000 SSRC 2704961869 (0)\r\nSamples: 0 (5 sec)\r\n\r\nCodec:\r\nG711U 200B 20mS srtpAesCm128HmacSha180, Silence-suppression(Tx/Rx) Disabled/Disabled, Play-Time 4.720sec, Loss 0.8% #0, Avg-Loss 0.8%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 22mS, Max-Jbuf-Delay 22mS\r\n\r\nReceived-RTP:\r\nPackets 245, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, Jitter 2mS #0, Avg-Jitter 2mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 0, Flow-Label 2\r\n\r\nTransmitted-RTP:\r\nVLAN 0, DSCP 46, L2Pri 0, RTCP 10, Flow-Label 0\r\n\r\nRemote-Statistics:\r\nLoss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS\r\n\r\nEcho-Cancellation:\r\nLoss 0dB #2, Len 0mS\r\n\r\nRSVP:\r\nStatus Unused, Failures 0\n#END'''
    stdout += '''#BEGIN\nshow rtp-stat detailed 00002\r\n\r\nSession-ID: 1\r\nStatus: Terminated, QOS: Faulted, EngineId: 10\r\nStart-Time: 2024-11-04,10:06:10, End-Time: 2024-11-04,10:07:10\r\nDuration: 00:00:00\r\nCName: gwp@10.10.48.58\r\nPhone: \r\nLocal-Address: 192.168.110.111:2052 SSRC 1653399062\r\nRemote-Address: 192.168.110.112:35000 SSRC 2704961869 (0)\r\nSamples: 0 (5 sec)\r\n\r\nCodec:\r\nG711U 200B 20mS Off, Silence-suppression(Tx/Rx) Disabled/Not-Supported, Play-Time 4.720sec, Loss 0.8% #0, Avg-Loss 0.8%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 22mS, Max-Jbuf-Delay 22mS\r\n\r\nReceived-RTP:\r\nPackets 245, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, Jitter 2mS #0, Avg-Jitter 2mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 0, Flow-Label 2\r\n\r\nTransmitted-RTP:\r\nVLAN 0, DSCP 46, L2Pri 0, RTCP 10, Flow-Label 0\r\n\r\nRemote-Statistics:\r\nLoss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS\r\n\r\nEcho-Cancellation:\r\nLoss 0dB #2, Len 0mS\r\n\r\nRSVP:\r\nStatus Unused, Failures 0\n#END'''
    print(stdout)
    rtpsessions = cmds_to_rtpsessions(stdout_to_cmds(stdout))
    for id, rtpsession in rtpsessions.items():
        print(str(rtpsession))
        print(rtpsession.is_ok)
