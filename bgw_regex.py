#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import re
from typing import Dict

SESSION_DETAILED = (
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
        r'.*?RTCP (?P<rtp_tx_rtcp>\d+),',
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

SESSION = {
    'session_id': {
        'regex': r'.*?Session-ID: (?P<session_id>\d+)',
        'title:': 'Session-ID',
        'title_color': Color.WHITE,
        'value_attr': 'session_id',
        'value_color': Color.WHITE,
        'value_format_spec': '>2',
        'ypos': 0,
        'xpos': 3,
    },
    'status': {
        'regex': r'.*?Status: (?P<status>\S+),',
        'title:': 'Status',
        'title_color': Color.WHITE,
        'value_attr': 'status',
        'value_color': Color.WHITE,
        'value_format_spec': '>6',
        'ypos': 0,
        'xpos': 10,

    },
    'qos': {
        'regex': r'.*?QOS: (?P<qos>\S+),',
        'title:': 'QoS',
        'title_color': Color.WHITE,
        'value_attr': 'qos',
        'value_color': Color.WHITE,
        'value_format_spec': '>2',
        'ypos': 0,
        'xpos': 13,
    },
    'engineid': {
        'regex': r'.*?EngineId: (?P<engineid>\d+)',
        'title:': 'EngineId',
        'title_color': Color.WHITE,
        'value_attr': 'engineid',
        'value_color': Color.WHITE,
        'value_format_spec': '>2',
        'ypos': None,
        'xpos': None,
    },
    'start_time': {
        'regex': r'.*?Start-Time: (?P<start_time>\S+),',
        'title:': 'Start',
        'title_color': Color.WHITE,
        'value_attr': 'start_time',
        'value_color': Color.WHITE,
        'value_format_spec': '>10',
        'ypos': 1,
        'xpos': 1,
    },
    'end_time': {
        'regex': r'.*?End-Time: (?P<end_time>\S+)',
        'title:': 'End',
        'title_color': Color.WHITE,
        'value_attr': 'end_time',
        'value_color': Color.WHITE,
        'value_format_spec': '>10',
        'ypos': 1,
        'xpos': 11,
    },
    'duration': {
        'regex': r'.*?Duration: (?P<duration>\S+)',
        'title:': 'Duration',
        'title_color': Color.WHITE,
        'value_attr': 'duration',
        'value_color': Color.WHITE,
        'value_format_spec': '>10',
        'ypos': 1,
        'xpos': 22,

    },
    'cname': {
        'regex': r'.*?CName: (?P<cname>\S+)',
        'title:': 'CName',
        'title_color': Color.WHITE,
        'value_attr': 'cname',
        'value_color': Color.WHITE,
        'value_format_spec': '>10',
        'ypos': None,
        'xpos': None,
    },
    'phone': {
        'regex': r'.*?Phone: (?P<phone>.*?)\s+',
        'title:': 'Phone',
        'title_color': Color.WHITE,
        'value_attr': 'phone',
        'value_color': Color.WHITE,
        'value_format_spec': '>10',
        'ypos': None,
        'xpos': None,
    },
    'local_addr': {
        'regex': r'.*?Local-Address: (?P<local_addr>\S+):',
        'title:': 'Local-Address',
        'title_color': Color.WHITE,
        'value_attr': 'local_addr',
        'value_color': Color.WHITE,
        'value_format_spec': '>15',
        'ypos': 2,
        'xpos': 1,
    },
    'local_port': {
        'regex': r'.*?(?P<local_port>\d+)',
        'title:': '',
        'title_color': None,
        'value_attr': 'local_port',
        'value_color': Color.WHITE,
        'value_format_spec': '>5',
        'ypos': 2,
        'xpos': 16,
    },
    'local_ssrc': {
        'regex': r'.*?SSRC (?P<local_ssrc>\d+)',
        'title:': 'Local SSRC',
        'title_color': Color.WHITE,
        'value_attr': 'local_ssrc',
        'value_color': Color.WHITE,
        'value_format_spec': '>8',
        'ypos': 2,
        'xpos': 16,
    },
    'remote_addr': {
        'regex': r'.*?Remote-Address: (?P<remote_addr>\S+):',

    },
    'remote_port': {
        'regex': r'.*?(?P<remote_port>\d+)',

    },
    'remote_ssrc': {
        'regex': r'.*?SSRC (?P<remote_ssrc>\d+)',

    },
    'remote_ssrc_change': {
        'regex': r'.*?(?P<remote_ssrc_change>\S+)',

    },
    'samples': {
        'regex': r'.*?Samples: (?P<samples>\d+)',

    },
    'sampling_interval': {
        'regex': r'.*?(?P<sampling_interval>\(.*?\))',

    },
    'codec': {
        'regex': r'.*?Codec:\s+(?P<codec>\S+)',

    },
    'codec_psize': {
        'regex': r'.*?(?P<codec_psize>\S+)',

    },
    'codec_ptime': {
        'regex': r'.*?(?P<codec_ptime>\S+)',

    },
    'codec_enc': {
        'regex': r'.*?(?P<codec_enc>\S+),',

    },
    'codec_silence_suppr_tx': {
        'regex': r'.*?Silence-suppression\(Tx/Rx\) (?P<codec_silence_suppr_tx>\S+)/',

    },
    'codec_silence_suppr_rx': {
        'regex': r'.*?(?P<codec_silence_suppr_rx>\S+),',

    },
    'codec_play_time': {
        'regex': r'.*?Play-Time (?P<codec_play_time>\S+),',

    },
    'codec_loss': {
        'regex': r'.*?Loss (?P<codec_loss>\S+)',

    },
    'codec_loss_events': {
        'regex': r'.*?#(?P<codec_loss_events>\d+),',

    },
    'codec_avg_loss': {
        'regex': r'.*?Avg-Loss (?P<codec_avg_loss>\S+),',

    },
    'codec_rtt': {
        'regex': r'.*?RTT (?P<codec_rtt>\S+)',

    },
    'codec_rtt_events': {
        'regex': r'.*?#(?P<codec_rtt_events>\d+),',

    },
    'codec_avg_rtt': {
        'regex': r'.*?Avg-RTT (?P<codec_avg_rtt>\S+),',

    },
    'codec_jbuf_underruns': {
        'regex': r'.*?JBuf-under/overruns (?P<codec_jbuf_underruns>\S+)/',

    },
    'codec_jbuf_overruns': {
        'regex': r'.*?(?P<codec_jbuf_overruns>\S+),',

    },
    'codec_jbuf_delay': {
        'regex': r'.*?Jbuf-Delay (?P<codec_jbuf_delay>\S+),',

    },
    'codec_max_jbuf_delay': {
        'regex': r'.*?Max-Jbuf-Delay (?P<codec_max_jbuf_delay>\S+)',

    },
    'rx_rtp_packets': {
        'regex': r'.*?Packets (?P<rx_rtp_packets>\d+),',

    },
    'rx_rtp_loss': {
        'regex': r'.*?Loss (?P<rx_rtp_loss>\S+)',

    },
    'rx_rtp_loss_events': {
        'regex': r'.*?#(?P<rx_rtp_loss_events>\d+),',

    },
    'rx_rtp_avg_loss': {
        'regex': r'.*?Avg-Loss (?P<rx_rtp_avg_loss>\S+),',

    },
    'rx_rtp_rtt': {
        'regex': r'.*?RTT (?P<rx_rtp_rtt>\S+)',

    },
    'rx_rtp_rtt_events': {
        'regex': r'.*?#(?P<rx_rtp_rtt_events>\d+),',

    },
    'rx_rtp_avg_rtt': {
        'regex': r'.*?Avg-RTT (?P<rx_rtp_avg_rtt>\S+),',

    },
    'rx_rtp_jitter': {
        'regex': r'.*?Jitter (?P<rx_rtp_jitter>\S+)',

    },
    'rx_rtp_jitter_events': {
        'regex': r'.*?#(?P<rx_rtp_jitter_events>\d+),',

    },
    'rx_rtp_avg_jitter': {
        'regex': r'.*?Avg-Jitter (?P<rx_rtp_avg_jitter>\S+),',

    },
    'rx_rtp_ttl_last': {
        'regex': r'.*?TTL\(last/min/max\) (?P<rx_rtp_ttl_last>\d+)/',

    },
    'rx_rtp_ttl_min': {
        'regex': r'.*?(?P<rx_rtp_ttl_min>\d+)/',

    },
    'rx_rtp_ttl_max': {
        'regex': r'.*?(?P<rx_rtp_ttl_max>\d+),',

    },
    'rx_rtp_duplicates': {
        'regex': r'.*?Duplicates (?P<rx_rtp_duplicates>\d+),',

    },
    'rx_rtp_seqfall': {
        'regex': r'.*?Seq-Fall (?P<rx_rtp_seqfall>\d+),',

    },
    'rx_rtp_dscp': {
        'regex': r'.*?DSCP (?P<rx_rtp_dscp>\d+),',

    },
    'rx_rtp_l2pri': {
        'regex': r'.*?L2Pri (?P<rx_rtp_l2pri>\d+),',

    },
    'rx_rtp_rtcp': {
        'regex': r'.*?RTCP (?P<rx_rtp_rtcp>\d+),',

    },
    'rx_rtp_flow_label': {
        'regex': r'.*?Flow-Label (?P<rx_rtp_flow_label>\d+)',

    },
    'tx_rtp_vlan': {
        'regex': r'.*?VLAN (?P<tx_rtp_vlan>\d+),',

    },
    'tx_rtp_dscp': {
        'regex': r'.*?DSCP (?P<tx_rtp_dscp>\d+),',

    },
    'tx_rtp_l2pri': {
        'regex': r'.*?L2Pri (?P<tx_rtp_l2pri>\d+),',

    },
    'rtp_tx_rtcp': {
        'regex': r'.*?RTCP (?P<rtp_tx_rtcp>\d+),',

    },
    'tx_rtp_flow_label': {
        'regex': r'.*?Flow-Label (?P<tx_rtp_flow_label>\d+)',

    },
    'rem_loss': {
        'regex': r'.*?Loss (?P<rem_loss>\S+)',

    },
    'rem_loss_events': {
        'regex': r'.*#(?P<rem_loss_events>\S+),',

    },
    'rem_avg_loss': {
        'regex': r'.*?Avg-Loss (?P<rem_avg_loss>\S+),',

    },
    'rem_jitter': {
        'regex': r'.*?Jitter (?P<rem_jitter>\S+)',

    },
    'rem_jitter_events': {
        'regex': r'.*?#(?P<rem_jitter_events>\S+),',

    },
    'rem_avg_jitter': {
        'regex': r'.*?Avg-Jitter (?P<rem_avg_jitter>\S+)',

    },
    'ec_loss': {
        'regex': r'.*?Loss (?P<ec_loss>\S+)',

    },
    'ec_loss_events': {
        'regex': r'.*?#(?P<ec_loss_events>\S+),',

    },

    'ec_len': {
        'regex': r'.*?Len (?P<ec_len>\S+)',

    },
    'rsvp_status': {
        'regex': r'.*?Status (?P<rsvp_status>\S+),',

    },
    'rsvp_failures': {
        'regex': r'.*?Failures (?P<rsvp_failures>\d+)',

    },
}

LAYOUT = '''
Session-ID: 35    Status: Terminated     QOS: Faulted    Samples: 54 (5 sec)
Start: 2004-10-20,11:09:07   End: 2004-10-20,11:13:40   Duration: 00:04:33

     LOCAL ADDRESS                                         REMOTE ADDRESS
   192.168.111.111:20544 <----------G711U----------> 20544:192.168.111.112
   SSRC 2704961869	     Enc:srtpAesCm128HmacSha180		 SSRC 2704961869 (0)
	    
			RTP/RTCP							              CODEC
	RTP Packets (Rx/Tx): 180000 /    NA             Psize/Ptime: 200B/30ms
   RTCP Packets (Rx/Tx):    120 /   134               Play-Time: 272.610sec
           DSCP (Rx/Tx):     46 /    46                Avg-Loss: 0.1%
          L2Pri (Rx/Tx):      6 /     6                 Avg-RTT: 570mS
        Duplicates (Rx):      0                  Max-Jbuf-Delay: 60mS
          Seq-Fall (Rx):      6             JBuf-under/overruns: 66.1%/43.0%

   LOCAL RTP STATISTICS                             REMOTE RTP STATISTICS
		Loss: 0.0% #0							          Loss: 0.0% #0
    Avg-Loss: 0.1%			                  		  Avg-Loss: 0.0%
	  Jitter: 0mS #0									Jitter: 0mS #0
  Avg-Jitter: 0mS									Avg-Jitter: 0mS
		 RTT: 604mS      
	 Avg-RTT: 376mS
'''

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
            print(d)
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
