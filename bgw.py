
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import os
import re
from typing import Dict, Iterator, List, Tuple, Union
from session import cmds_to_session_dicts, stdout_to_cmds

MAIN_ATTRS = [
    {'xpos':  1, 'text': 'start_time', 'format_spec': '', 'color': 'normal'},
    {'xpos': 10, 'text': 'end_time', 'format_spec': '', 'color': 'normal'},
    {'xpos': 19, 'text': 'bgw_num', 'format_spec': '0>3', 'color': 'normal'},
    {'xpos': 23, 'text': 'local_ip', 'format_spec': '>15', 'color': 'address'},
    {'xpos': 39, 'text': 'local_port', 'format_spec': '>5', 'color': 'port'},
    {'xpos': 46, 'text': 'remote_ip', 'format_spec': '>15', 'color': 'address'},
    {'xpos': 61, 'text': 'remote_port', 'format_spec': '>5', 'color': 'port'},
    {'xpos': 67, 'text': 'status', 'format_spec': '^6', 'color': 'active'},
    {'xpos': 74, 'text': 'qos', 'format_spec': '^3', 'color': 'ok'},
]

BGW_ATTRS = [
    {'xpos':  1, 'text': 'number', 'format_spec': '', 'color': 'normal'},
    {'xpos':  5, 'text': 'model', 'format_spec': '>6', 'color': 'normal'},
    {'xpos': 12, 'text': 'firmware', 'format_spec': '>8', 'color': 'normal'},
    {'xpos': 21, 'text': 'ip', 'format_spec': '>15', 'color': 'address'},
    {'xpos': 37, 'text': 'serial', 'format_spec': '>12', 'color': 'normal'},
    {'xpos': 50, 'text': 'snmp', 'format_spec': '^4', 'color': 'normal'},
    {'xpos': 55, 'text': 'rtp_stat', 'format_spec': '>8', 'color': 'normal'},
    {'xpos': 64, 'text': 'capture', 'format_spec': '>7', 'color': 'normal'},
    {'xpos': 72, 'text': 'fault', 'format_spec': '>5', 'color': 'normal'},
]

def connected_bgws() -> Dict[str, str]:
    """Return a dictionary of connected branch media-gateways

    The dictionary has the bgw ip as the key and the protocol
    'encrypted' or 'unencrypted' as the value.

    Returns:
        dict: A dictionary of connected bgws
    """
    bgws: Dict[str, str] = {}
    output: str = os.popen('netstat -tan | grep ESTABLISHED').read()
    for line in output.splitlines():
        m = re.search(r'([0-9.]+):(1039|2945)\s+([0-9.]+):([0-9]+)', line)
        if not m:
            continue
        proto: str = 'encrypted' if m.group(2) == '1039' else 'unencrypted'
        bgws[m.group(3)] = proto
    return bgws

class BGW():
    def __init__(self,
        ip: str,
        config: str = '',
        system: str = '',
        faults: str = '',
        capture: str = '',
    ) -> None:   
        self.ip = ip
        self.config = config
        self.system = system
        self.capture = capture
        self.faults = faults
        self._fault = None
        self._capture_service = None
        self._number = None
        self._model = None
        self._firmware = None
        self._serial = None
        self._snmp = None
        self._rtp_stat = None
        self._capture = None
        self._fault = None

    @property
    def number(self):
        if not self._number:
            m = re.search(r'.*-([0-9]*)\(\S+\)#\s?', self.config)
            self._number = m.group(1) if m else '???'
        return self._number

    @property
    def model(self):
        if not self._model:
            m = re.search(r'Model\s+:\s+(\S+)', self.system)
            self._model = m.group(1) if m else '???'
        return self._model

    @property
    def firmware(self):
        if not self._firmware:
            m = re.search(r'Mainboard FW Vintags\s+:\s+(\S+)', self.system)
            self._firmware = m.group(1) if m else '??.??.??'
        return self._firmware
    
    @property
    def serial(self):
        if not self._serial:
            m = re.search(r'Serial No\s+:\s+(\S+)', self.system)
            self._serial = m.group(1) if m else '????????????'
        return self._serial

    @property
    def snmp(self):
        if not self._snmp:
            m = re.search(r'snmp.*?', self.config)
            self._snmp = m.group(1) if m else '??'
        return self._snmp

    @property
    def rtp_stat(self):
        if not self._rtp_stat:
            m = re.search(r'rtp-stat.*?', self.config)
            self._rtp_stat = m.group(1) if m else '??????'
        return m.group(1) if m else ''

    @property
    def capture_service(self):
        if not self._capture_service:
            m = re.search(r'capture(.*?)\)# $', self.capture)
            self._capture_service = m.group(1) if m else 'inactive'
        return self._capture_service

    @property
    def fault(self):
        if not self._fault:
            m = re.search(r'fault.*?', self.faults)
            self._faults = m.group(1) if m else '?????'
        return m.group(1) if m else '????'


def iter_session_main_attrs(
    session_dict: Dict[str, str],
    main_attrs: List[Dict[str, Union[int, str]]] = MAIN_ATTRS,
    xoffset: int = 0
) -> Iterator[Tuple[int, str, str]]:
    """
    Iterate over the main attributes of a session dictionary and yield a tuple of 3 values:

    - `ypos`: The y position of the attribute
    - `text`: The text of the attribute, formatted according to the `format_spec`
    - `color`: The color of the attribute

    :param session_dict: A dictionary of key-value pairs of the attributes of the session
    :param main_attrs: A list of dictionaries of the main attributes of the session
    :param xoffset: The offset of xpos
    :return: An iterator of tuples of 3 values
    """
    for attrs in main_attrs:
        text = session_dict.get(attrs['text'], attrs['text'])
        color = attrs['color']
        if attrs['text'] == 'status':
            text = 'active' if text == 'Active' else 'ended'
            color = 'active' if text == 'Active' else 'ended'
        if attrs['text'] == 'qos':
            text = '✔' if text == 'OK' else '✘'
            color = 'ok' if text == 'OK' else 'fault'
        text = f'{text:{attrs["format_spec"]}}'
        yield attrs['xpos'] + xoffset, text, color

def iter_bgw_attrs(
    bgw: BGW,
    bgw_attrs: List[Dict[str, Union[int, str]]] = BGW_ATTRS
) -> Iterator[Tuple[int, str, str]]:
    """
    Iterate over the attributes of a BGW object and yield a tuple of 3 values:

    - `xpos`: The x position of the attribute
    - `text`: The text of the attribute, formatted according to the `format_spec`
    - `color`: The color of the attribute

    :param bgw: A BGW object
    :param bgw_attrs: A list of dictionaries of the attributes of the BGW
    :return: An iterator of tuples of 3 values
    """
    for attrs in bgw_attrs:
        text = getattr(bgw, attrs['text'])
        text = f'{text:{attrs["format_spec"]}}'
        yield attrs['xpos'], text, attrs['color']


if __name__ == '__main__':
    print(connected_bgws())
    stdout = '''#BEGIN\nshow rtp-stat detailed 00001\r\n\r\nSession-ID: 1\r\nStatus: Terminated, QOS: Faulted, EngineId: 10\r\nStart-Time: 2024-11-20,16:07:30, End-Time: 2024-11-21,07:17:48\r\nDuration: 15:10:18\r\nCName: gwp@10.10.48.58\r\nPhone: \r\nLocal-Address: 192.168.110.110:2052 SSRC 1653399062\r\nRemote-Address: 10.10.48.192:35000 SSRC 3718873098 (0)\r\nSamples: 10923 (5 sec)\r\n\r\nCodec:\r\nG711U 200B 20mS srtpAesCm128HmacSha180, Silence-suppression(Tx/Rx) Disabled/Disabled, Play-Time 54626.390sec, Loss 0.8% #0, Avg-Loss 0.8%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns 0.0%/0.0%, Jbuf-Delay 22mS, Max-Jbuf-Delay 22mS\r\n\r\nReceived-RTP:\r\nPackets 2731505, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, Jitter 2mS #0, Avg-Jitter 2mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 41, DSCP 0, L2Pri 0, RTCP 10910, Flow-Label 2\r\n\r\nTransmitted-RTP:\r\nVLAN 0, DSCP 46, L2Pri 0, RTCP 10927, Flow-Label 0\r\n\r\nRemote-Statistics:\r\nLoss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS\r\n\r\nEcho-Cancellation:\r\nLoss 0dB #10902, Len 0mS\r\n\r\nRSVP:\r\nStatus Unused, Failures 0\n#END'''
    session_dicts = cmds_to_session_dicts(stdout_to_cmds(stdout))
    for id, session_dict in session_dicts.items():
        print(session_dict)
        for x, text, attrs in iter_session_main_attrs(session_dict):
            print(x, text, attrs)
    
    bgw = BGW(ip='192.168.111.111', config='blabla\r\n\g430-few2-001(super)#')
    for x, text, attrs in iter_bgw_attrs(bgw):
        print(x, text, attrs)