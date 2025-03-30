#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import re
from typing import AsyncIterator, Iterable, Iterator, Optional, Tuple, Union, TypeVar, Any, Dict, List, Set
from asyncio import Lock, Queue, Semaphore
from datetime import datetime

data ={
    "host": "192.168.111.111",
    "proto": "encrypted",
    "gw_name": "AvayaG450A",
    "gw_number": "001",
    "last_seen": "2025-03-21,08:49:27",
    
    "commands": {
        "show running-config": '''
        ! version 42.24.0
        Config info release 42.24.0 time "08:49:27 16 OCT 2024 " serial_number 10IS41452851
        !
        encrypted-username /6uCADuD2GZ7GGjZ2jGkbg== password cTV1Osm73kZMwAPq/E55vGir27ynys7m/YgbZZbsaX8= access-type 9os8uRcP3F
        lbMEqSff81ew==
        !
        encrypted-username N1uDac4hxp2ssYrs+tjY2A== password xDfcwOLBsCkmdlht+IJRcUFp6vBqHw0CAFhpioBeZ0E= access-type NETEZ/WGjk
        uL84gOKeBsww==
        hostname "AvayaG450A"
        no ip telnet
        ip tftp-server file-system-size 2288
        set port redundancy 10/5 10/4 on red1
        !
        ds-mode t1
        !
        interface Vlan 1
        icc-vlan
        server-blade-vlan 5
        ip address 192.168.111.111     255.255.255.0
        pmi
        exit
        !
        interface FastEthernet 10/3
        exit
        !
        interface FastEthernet 10/4
        exit
        !
        interface Console
        speed 9600
        exit
        !
        interface USB-Modem
        description "Default Modem Setup"
        timeout absolute 10
        ppp authentication ras
        no shutdown
        ip address 10.3.248.253    255.255.255.252
        exit
        !
        capture max-frame-size 1500
        login authentication min-password-length 8
        !
        login authentication lockout 0 attempt 0
        ! Avaya Login Confirmation Received.
        EASGManage enableEASG
        product-id 8c2ae2eead3e6cca800be892bb6e3411
        !
        set logging file enable
        set logging file condition all Error
        set logging file condition BOOT Debug
        !
        no snmp-server community
        !
        encrypted-snmp-server community read-only aC02uV3t/hD2WRQ2KzJZuA== read-write tIWV4hWxJEarok2vUVEgc0dBcaOywSBPgPnkHU0qOuo=
        snmp-server group v3ReadISO v3 priv read iso
        snmp-server host 10.62.17.5 traps v3 priv bbysnmpv3trap
        !
        ip default-gateway 10.10.48.254    1 low
        !
        rtp-stat-service
        rtp-stat qos-trap
        no rtp-stat fault
        analog-test
        exit
        !
        set sla-monitor enable
        set sla-server-ip-address 10.10.48.198
        set mgc list 10.10.48.240
        set mediaserver 10.10.48.240 10.10.48.240 23 telnet
        set mediaserver 10.10.48.240 10.10.48.240 5023 sat
        !#
        !# End of configuration file. Press Enter to continue.
        ''',

        "show system2": '''
        System Name             : cityhall
        System Location         : CityHall
        System Contact          :
        Uptime (d,h:m:s)        : 108,18:21:26
        Call Controller Time    : 17:32:47 29 MAR 2025
        Serial No               : 22TN07201536
        Model                   : G450v4
        Chassis HW Vintage      : 4
        Chassis HW Suffix       : A
        Mainboard HW Vintage    : 4
        Mainboard HW Suffix     : A
        Mainboard HW CS         : 4.0.0
        Mainboard FW Vintage    : 42.32.0
        LAN MAC Address         : c8:1f:ea:d5:cf:40
        WAN1 MAC Address        : c8:1f:ea:d5:cf:41
        WAN2 MAC Address        : c8:1f:ea:d5:cf:42
        SERVICES MAC address    : c8:1f:ea:d5:cf:43
        Memory #1               : 1GB
        Compact Flash Memory    : 1.0 GB
        PSU #1                  : AC 400W
        PSU #2                  : AC 400W
        Media Socket #1         : MP160 VoIP DSP Module
        Media Socket #2         : MP160 VoIP DSP Module

        Media Socket #3         : Not present
        Media Socket #4         : Not present
        FAN Tray                : Present
        '''

        "show system": '''
        System Name :
        System Location : townhall
        System Contact :
        Uptime (d,h:m:s) : 8,00:23:27
        Call Controller Time : 11:11:22 22 JUL 2020
        Serial No : 09IS48315342
        Model : G450v3
        Chassis HW Vintage : 1
        Chassis HW Suffix : A
        Mainboard HW Vintage : 3
        Mainboard HW Suffix : A
        Mainboard HW CS : 3.0.2
        Mainboard FW Vintage : 41.31.0
        LAN MAC Address : 34:75:c7:64:ef:08
        WAN1 MAC Address : 34:75:c7:64:ef:09
        WAN2 MAC Address : 34:75:c7:64:ef:0a
        SERVICES MAC address : 34:75:c7:64:ef:0b
        Memory #1 : 256MB
        Memory #2 : 256MB
        Compact Flash Memory : No CompactFlash card is installed
        PSU #1 : Not present
        PSU #2 : AC 400W
        Media Socket #1 : MP80 VoIP DSP Module
        Media Socket #2 : MP80 VoIP DSP Module
        Media Socket #3 : MP80 VoIP DSP Module
        Media Socket #4 : MP80 VoIP DSP Module
        FAN Tray #1 : Present
        ''',

        "show faults": '''
        CURRENTLY ACTIVE FAULTS
        -------------------------------------------------------------------
        -- Hardware Faults --
                + Multiple fans outage, 01/01-18:26:35.00
                + PSU fan brief outage, 01/01-18:26:35.00
        -- MGP Faults --
                + No controller found, 01/01-00:00:01.00
        ''',

        "show capture": '''
        The sniffing service is enabled and active
        Capturing started at:
        21:22:01, February 21, 2010 / 7,9:55:55 (uptime)
        stopped at: not-stopped
        Buffer size: 1000 KB
        Buffer mode is cyclic
        Maximum number of bytes captured from
        each frame: 128
        Packet filter: Capture List 503
        Number of frames in buffer: 200
        Size of capture file: 50 KB (5%)
        ''',

        "show voip-dsp": '''
        DSP #1 PARAMETERS
        --------------------------------------------------------------
        Board type     : MP160
        Hw Vintage     : 0 B
        Fw Vintage     : 182

        DSP#1 CURRENT STATE
        --------------------------------------------------------------
        In Use         : 0 of 160 channels, 0 of 4800 points (0.0% used)
        State          : Idle
        Admin State    : Release

        Core# Channels Admin     State
            In Use   State
        ----- -------- --------- -------
            1  0 of 40   Release Idle
            2  0 of 40   Release Idle
            3  0 of 40   Release Idle
            4  0 of 40   Release Idle

        DSP #2 PARAMETERS
        --------------------------------------------------------------
        Board type     : MP160

        Hw Vintage     : 0 B
        Fw Vintage     : 182

        DSP#2 CURRENT STATE
        --------------------------------------------------------------
        In Use         : 0 of 160 channels, 0 of 4800 points (0.0% used)
        State          : Idle
        Admin State    : Release

        Core# Channels Admin     State
            In Use   State
        ----- -------- --------- -------
            1  0 of 40   Release Idle
            2  0 of 40   Release Idle
            3  0 of 40   Release Idle
            4  0 of 40   Release Idle


        DSP #3 Not Present


        DSP #4 Not Present


        Done!
        ''',

        "show sla-monitor": '''
        show sla-monitor
        SLA Monitor: Disabled
        Server Address: 0.0.0.0
        Registered Server IP Address: 0.0.0.0
        Server Port: 50010
        Capture Mode: With Payload
        Version: 1.3.4
        ''',

        "show rtp-stat summary": '''
        Total QoS traps: 2
        QoS traps Drop : 0
        Qos Clear
        Engine                            Active   Total    Mean      Tx
        ID   Description     Uptime       Session  Session  Duration  TTL
        ---  --------------  -----------  -------  -------  --------  ----
        010        internal  53,05:23:06   123/12   332442/1443   00:05:17    64
        ''',

        "show lldp config": '''
        Lldp Configuration
        -------------------
        Application status: disable
        Tx interval: 30 seconds
        Tx hold multiplier: 4 seconds
        Tx delay: 2 seconds
        Reinit delay: 2 seconds
        ''',

        "show port": '''
        Port   Name             Status    Vlan Level  Neg     Dup. Spd. Type
        ------ ---------------- --------- ---- ------ ------- ---- ---- ----------------
        10/5   NO NAME          connected 1     0     enable  full 1G   Avaya Inc., G450 Media Gateway 10/100/1000BaseTx Port 10/5

        10/6   NO NAME          no link   1     0     enable  full 1G   Avaya Inc., G450 Media Gateway 10/100/1000BaseTx Port 10/6
        ''',

        "show mg list": '''
        G430-5-005(super)# show mg l
        SLOT   TYPE         CODE        SUFFIX  HW VINTAGE  FW VINTAGE
        ----   --------     ----------  ------  ----------  -----------
        v1     S8300        ICC         E       1           0
        v2     Analog       MM714       B       31          104
        v3     -- Not Installed --
        v5     -- Not Installed --
        v6     -- Not Installed --
        v7     -- Not Installed --
        v8     -- Not Installed --
        v10    Mainboard    G430        A       3           42.32.0(A)
        ''',

        "show_temp": '''
        Ambient
        -------
        Temperature : 22C (72F)
        High Warning: 42C (108F)
        Low Warning : -5C (23F)

        Devices
        -------
        CPU     : 38C (100F)
        FPGA    : 29C (84F)
        ''',

        "show announcements files": '''
        ID      File               Description    Size (Bytes)      Date
        ---- ------------------ ------------------ ------------ -------------------
        101   moh_upbeat.wav     announcement file     1268110    2022-08-15,8:48:48
        102   moh_sooth.wav      announcement file      239798    2022-08-15,8:48:48
        103   Fire_Main_Grtg.wa  announcement file      162186    2022-08-25,13:59:00
        104   3441_P&D_Main_Grt  announcement file      179642    2023-02-11,10:48:18
        105   6400_Fire_Main_Gr  announcement file      306098    2023-06-16,8:42:56
        106   3070_HR_ABH_Grtg.  announcement file      203898    2022-11-29,9:16:40
        107   3070_HR_Main_Grtg  announcement file      162058    2022-11-29,9:16:02
        108   3441_P&D_Inspect_  announcement file      240050    2023-02-11,11:00:48
        109   3441_P&D_FlrPl_Sr  announcement file      326826    2023-02-11,11:05:50
        110   3441_P&D_Agents_U  announcement file      296458    2023-05-17,9:49:16
        111   3430_P&D_LandZone  announcement file      375482    2023-02-23,14:23:34
        112   3400_BldgPmt_Cons  announcement file      158594    2022-10-24,11:38:42
        113   6027_PoirierSport  announcement file      186770    2023-05-18,10:05:52
        114   3930_PRCF_Facilit  announcement file      169362    2022-11-29,8:00:50
        115   3930_PRCF_Facilit  announcement file      228666    2022-11-29,7:59:32
        116   3441_P&D_Menu_Opt  announcement file      193842    2023-02-11,10:59:28
        117   3939_PRCF_AC_Clk_  announcement file      116634    2022-11-28,13:31:58
        118   3939_PRCF_AC_Clk_  announcement file      106074    2022-11-28,13:32:24
        119   3939_PRCF_AC_Clk_  announcement file       61314    2022-11-28,13:34:16
        120   Wait_To_Be_Connec  announcement file       42042    2023-02-14,14:11:36
        121   3040_Finance_AP_H  announcement file      115154    2023-02-24,10:56:38
        122   3040_Finance_AP_A  announcement file       85266    2023-02-24,10:56:56
        123   3040_Finance_AP_N  announcement file       72898    2023-02-24,10:57:16
        124   3430_P&D_LndZnSig  announcement file      225666    2023-02-24,10:52:28
        125   3430_P&D_ABH.wav   announcement file      278658    2023-02-24,10:54:16
        126   3441_P&D_ABH_Grtg  announcement file      297834    2023-03-02,14:34:18
        127   3636_EPW_WaterCon  announcement file      100474    2023-03-30,14:12:46
        128   3636_EPW_WaterCon  announcement file       78058    2023-03-30,14:13:10
        129   3636_EPW_WaterCon  announcement file       45378    2023-03-30,14:13:44
        130   3660_EPQ_UrbanWil  announcement file       92530    2023-03-30,14:31:20
        131   3660_EPW_UrbanWil  announcement file       79850    2023-03-30,14:31:38
        132   3660_EPW_UrbanWil  announcement file       43178    2023-03-30,14:31:52
        133   3550_EPQ_PWL&CDP_  announcement file       98978    2023-03-30,14:38:46
        134   3550_EPW_PWL&CDP_  announcement file       88018    2023-03-30,14:39:04
        135   3550_EPW_PWL&CDP_  announcement file       48242    2023-03-30,14:39:20
        136   3010_Clerks_Hol.w  announcement file       99122    2023-04-03,13:13:08
        137   3010_Clerks_ABH.w  announcement file       78754    2023-04-03,13:13:28
        138   3010_Clerks_NotAv  announcement file       71898    2023-04-03,13:13:46
        139   6070_CulturalSvcs  announcement file       65626    2023-04-10,11:35:00
        140   6070_CulturalSvcs  announcement file      112626    2023-04-10,11:34:42
        141   6070_CulturalSvcs  announcement file      122802    2023-04-10,11:34:18
        142   3482_UrbanForestr  announcement file      112762    2023-04-10,11:23:36
        143   3482_UrbanForestr  announcement file      110010    2023-04-10,11:24:00
        144   3482_UrbanForestr  announcement file       72274    2023-04-10,11:24:16
        145   3571_CmtyGrantCoo  announcement file       69626    2023-04-11,14:11:22
        146   3571_CmtyGrantCoo  announcement file      112538    2023-04-10,11:44:38
        147   3571_CmtyGrantCoo  announcement file      116146    2023-04-11,14:11:02
        148   6016_PRCF_FAC_Boo  announcement file      137738    2023-04-11,8:26:50
        149   6016_PRCF_FAC_Boo  announcement file      125538    2023-04-11,8:27:12
        150   6016_PRCF_FAC_Boo  announcement file       71882    2023-04-11,8:27:28
        151   6020_RobinsonMemP  announcement file      121346    2023-04-11,14:12:28
        152   6020_RobinsonMemP  announcement file      112610    2023-04-11,14:12:50
        153   6020_RobinsonMemP  announcement file      115090    2023-10-11,14:31:08
        154   6778_DepCityMgr_H  announcement file      150634    2024-12-17,7:44:36
        155   6778_DepCityMgr_A  announcement file      130866    2024-12-17,7:45:54
        156   6778_DepCityMgr_A  announcement file      104634    2024-12-17,7:46:16
        157   6777_CityMgrOfc_H  announcement file      138674    2024-12-17,7:49:20
        158   6777_CityMgrOfc_A  announcement file      124298    2024-12-17,7:49:44
        159   6777_CityMgrOfc_A  announcement file      103802    2024-12-17,7:50:06
        160   3001_MayorOfc_Hol  announcement file      114194    2023-04-25,7:52:50
        161   3001_MayorOfc_ABH  announcement file      103506    2023-04-25,7:53:32
        162   3001_MayorOfc_Agt  announcement file       76258    2023-04-25,7:53:50
        163   6076_CmtySvce_Hol  announcement file      122898    2023-04-25,8:09:58
        164   6076_CmtySvce_ABH  announcement file      108170    2023-04-25,8:10:20
        165   6076_CmtySvce_Agt  announcement file       71082    2023-04-25,8:10:44
        166   3900_Archives_Hol  announcement file      116538    2023-04-25,8:25:14
        167   3900_Archives_ABH  announcement file       71810    2023-04-25,8:25:52
        168   3905_EconomicDev_  announcement file      120370    2023-04-25,8:32:24
        169   3905_EconomicDev_  announcement file      119042    2023-04-25,8:32:48
        170   3905_EconomicDev_  announcement file       79202    2023-04-25,8:33:06
        171   3912_Tourism_Hol.  announcement file      116594    2023-04-25,8:39:22
        172   3912_Tourism_ABH.  announcement file      103378    2023-04-25,8:39:42
        173   3912_Tourism_Agt_  announcement file       73418    2023-04-25,8:40:00
        174   3548_FilmOfc_Hol.  announcement file      110282    2023-04-25,8:49:18
        175   3548_FilmOfc_ABH.  announcement file      100194    2023-04-25,8:49:38
        176   3548_FilmOfc_Agt_  announcement file       71922    2023-04-25,8:50:04
        177   4390_FOI_Privacy_  announcement file      134194    2023-04-25,10:30:16
        178   4390_FOI_Privacy_  announcement file      124450    2023-04-25,10:30:40
        179   4390_FOI_Privacy_  announcement file       97250    2023-04-25,10:31:02
        180   3575_FacCS_ABH.wa  announcement file      231066    2023-04-25,10:45:22
        181   3575_FacCS_Hol.wa  announcement file      172794    2023-04-25,10:45:56
        182   3575_FacCS_Agt_NA  announcement file       95242    2023-04-25,10:46:22
        183   6027_PoirierSport  announcement file      129266    2023-07-10,12:51:56
        184   6027_PoirierSport  announcement file      205754    2023-05-16,14:34:28
        185   Audio_Ext_3004.wa  announcement file      118394    2023-06-01,11:10:56
        186   6027_PoirierSport  announcement file      113914    2023-08-18,11:28:46
        187   4386_ProgActRegLi  announcement file      132914    2023-06-07,10:41:38
        188   6999_CityCntrAqua  announcement file      194474    2023-05-19,8:31:36
        189   6999_CityCntrAqua  announcement file      117434    2023-07-10,12:53:00
        190   6999_CityCntrAqua  announcement file      116162    2023-08-18,11:29:10
        191   6940_GlenPinePavP  announcement file      174154    2023-05-19,8:38:02
        192   6940_GlenPinePavH  announcement file      105570    2023-07-10,12:50:56
        193   6940_GlenPinePavR  announcement file      100034    2023-08-18,11:28:20
        194   6098_DogwoodPavPr  announcement file      170794    2023-05-19,8:42:18
        195   6098_DogwoodPavHr  announcement file      110938    2023-07-10,12:50:04
        196   6098_DogwoodPavRA  announcement file      100842    2023-08-18,11:27:58
        197   6960_PinetreeCmty  announcement file      179514    2023-05-19,8:47:42
        198   6960_PinetreeCmty  announcement file      117114    2023-07-10,12:45:06
        199   6960_PinetreeCmty  announcement file      104290    2023-08-18,11:27:16
        200   6760_Maillardvill  announcement file      186914    2023-06-07,10:40:44
        201   6760_Maillardvill  announcement file      125322    2023-07-10,12:48:38
        202   6760_Maillardvill  announcement file      105618    2023-08-18,11:26:16
        203   2207_PoirierCmtyC  announcement file      175162    2023-05-19,9:03:40
        204   2207_PoirierCmtyC  announcement file      109202    2023-07-10,12:46:12
        205   2207_PoirierCmtyC  announcement file      101226    2023-08-18,11:25:26
        206   6300_ParksService  announcement file      134610    2023-05-19,11:16:42
        207   6300_ParksService  announcement file      215354    2023-05-19,11:17:36
        208   6300_ParksService  announcement file       76562    2023-05-19,11:17:54
        209   6329_ParksSpark_H  announcement file      118418    2023-05-19,12:56:08
        210   6329_ParksSpark_A  announcement file      111154    2023-05-19,12:56:32
        211   6329_ParksSpark_A  announcement file       65282    2023-05-19,12:56:48
        212   3000_City_Hall_Ma  announcement file      349538    2023-08-28,13:06:40
        213   3000_ByLaw_AmlPet  announcement file      121738    2023-08-28,12:59:54
        214   3000_BldgPrmt_Lan  announcement file      107474    2023-08-28,13:03:04
        215   6433_FirePreventi  announcement file      108946    2023-06-12,9:53:12
        216   6433_FirePreventi  announcement file      103306    2023-06-12,9:53:34
        217   6433_FirePreventi  announcement file       75210    2023-06-12,9:53:52
        218   6400_Fire_Hol.wav  announcement file      328114    2023-06-16,8:42:04
        219   6400_Fire_Agt_NA.  announcement file      329706    2023-06-26,7:38:30
        220   3000_COQ_Receptio  announcement file       38050    2023-08-24,9:50:44
        221   3000_COQ_Receptio  announcement file      240474    2024-01-17,10:15:16
        222   6200_AWY_Receptio  announcement file      195986    2023-08-18,10:36:58
        223   6200_AWY_Receptio  announcement file      194162    2023-08-18,10:38:22
        224   6200_AWY_Receptio  announcement file      196538    2023-08-18,10:39:34
        225   3430_P&D_DevInfo_  announcement file      364578    2023-08-22,13:15:22
        226   3037_Purchasing_A  announcement file       93170    2023-08-22,13:23:46
        227   3037_Purchasing_H  announcement file      119866    2023-08-22,13:24:12
        228   3900_Archives_Agt  announcement file       82554    2023-08-22,13:53:50
        229   3070_HR_Hol.wav    announcement file      245474    2023-08-23,13:47:58
        230   3000_COQ_Receptio  announcement file      238306    2023-08-28,13:05:48
        231   3000_COQ_Recept_D  announcement file      218354    2023-08-29,8:13:10
        232   3000_COQ_Recept_N  announcement file      317786    2023-12-22,10:06:42
        233   3575_FacCS_Christ  announcement file      217370    2023-09-21,14:50:40
        234   6950_TCPCCProgA.w  announcement file      240738    2024-04-08,8:33:32
        235   3030_Finance_Dept  announcement file      120082    2023-10-31,13:33:36
        236   3030_Finance_Dept  announcement file       91226    2023-10-31,13:33:56
        237   3030_Finance_Dept  announcement file       73410    2023-10-31,13:34:14
        238   6211_Garage_Hol.w  announcement file      145490    2023-12-07,12:26:20
        239   6211_Garage_ABH.w  announcement file      133562    2023-12-07,12:27:10
        240   6211_Garage_Agt_N  announcement file       92930    2023-12-07,12:27:30
        241   6950_TCPCCHrsLoc.  announcement file      154146    2024-04-08,8:34:34
        242   6950_TCPCC_ABH.wa  announcement file      129050    2024-04-08,8:35:04
        243   Test.wav           announcement file      119866    2024-05-23,8:51:04
        244   4357_Emergency_Ca  announcement file      191850    2024-12-10,16:25:36
        245   6778_DepCityMgr_D  announcement file      141338    2024-12-17,7:46:44
        246   6777_CityMgrOfc_D  announcement file      153690    2024-12-17,7:50:34
        247   3070_HR_Dec_Grtg.  announcement file      243802    2024-12-17,7:53:40
        248   3548_FilmOfc_Dec_  announcement file      133938    2024-12-17,7:55:06
        249   3905_EconomicDev_  announcement file      123490    2024-12-17,8:08:54
        250   3912_Tourism_Dec_  announcement file      130130    2024-12-17,8:10:10
        251   3660_EPQ_UrbanWil  announcement file      107154    2024-12-17,8:11:58
        252   3636_EPW_WaterCon  announcement file      105282    2024-12-17,8:13:00
        253   3550_EPQ_PWL&CDP_  announcement file      103890    2024-12-17,8:15:16
        254   6200_AWY_Recept_D  announcement file      278786    2024-12-17,8:18:16
        255   3040_Finance_AP_D  announcement file      132922    2024-12-17,8:19:44
        256   3037_Purchasing_D  announcement file      136834    2024-12-17,8:21:26
        257   3030_Finance_Dept  announcement file      140042    2024-12-17,8:22:46
        258   3010_Clerks_Dec_G  announcement file      113058    2024-12-17,9:36:32
        259   3000_COQ_Recept_D  announcement file      261954    2024-12-17,9:39:00
        260   4390_FOI_Privacy_  announcement file      158842    2024-12-17,9:40:54
        261   3900_Archives_Dec  announcement file      119898    2024-12-17,9:42:00
        262   3001_MayorOfc_Dec  announcement file      129170    2024-12-17,9:43:04
        263   6016_PRCF_FAC_Boo  announcement file      157474    2024-12-17,9:45:06
        264   3939_PRCF_AC_Clk_  announcement file      136690    2024-12-17,9:46:26
        265   6070_CulturalSvcs  announcement file      133034    2024-12-17,9:47:38
        266   6076_CmtySvce_Dec  announcement file      161626    2024-12-17,9:48:48
        267   3482_UrbanForestr  announcement file      155578    2024-12-17,9:50:26
        268   3571_CmtyGrantCoo  announcement file      157562    2024-12-17,9:53:28
        269   6329_ParksSpark_D  announcement file      154426    2024-12-17,9:54:48
        270   6020_RobinMemPkCe  announcement file      162034    2024-12-17,9:56:18
        271   6300_ParksService  announcement file      165034    2024-12-17,9:58:14
        272   3430_P&D_Dec_Grtg  announcement file      363154    2024-12-17,10:00:20
        273   3441_P&D_Dec_Grtg  announcement file      279722    2024-12-17,10:02:22

        Compact-Flash:
        Total bytes used             : 26423808
        Total bytes free             : 96049152
        Total bytes capacity (fixed) : 122472960
        ''',

        '''show utilization''': '''

        Mod   CPU      CPU     RAM      RAM
            5sec     60sec   used(%)  Total(Kb)
        ---   ------   -----  -------  ----------
        10      21%       4%    47%     447489 Kb
        
        '''
        },
    "rtp_sessions": {
        "2004-10-20,11:09:07,001,00001": '''
        Session-ID: 1
        Status: Terminated, QOS: Ok, EngineId: 10
        Start-Time: 2024-10-04,14:32:07, End-Time: 2024-10-04,14:32:19
        Duration: 00:00:12
        CName: gwp@10.10.48.58
        Phone:
        Local-Address: 10.10.48.58:2054 SSRC 1910942191
        Remote-Address: 10.10.48.192:35000 SSRC 1073745424 (0)
        Samples: 2 (5 sec)

        Codec:
        G711U 200B 20mS srtpAesCm128HmacSha180, Silence-suppression(Tx/Rx) Disabled/Disabled, Play-Time 15.010sec, Loss 0.3% #0, Avg-Loss 0.3%, RTT 0mS #0, Avg-RTT 0mS, JBuf-under/overruns
        0.0%/0.0%, Jbuf-Delay 15mS, Max-Jbuf-Delay 15mS

        Received-RTP:
        Packets 846, Loss 0.0% #0, Avg-Loss 0.0%, RTT 0mS #0, Avg-RTT 0mS, Jitter 1mS #0, Avg-Jitter 0mS, TTL(last/min/max) 56/56/56, Duplicates 0, Seq-Fall 0, DSCP 0, L2Pri 0, RTCP 0, Flow
        -Label 0

        Transmitted-RTP:
        VLAN 0, DSCP 46, L2Pri 0, RTCP 12, Flow-Label 0


        Remote-Statistics:
        Loss 0.0% #0, Avg-Loss 0.0%, Jitter 0mS #0, Avg-Jitter 0mS

        Echo-Cancellation:
        Loss 0dB #4, Len 0mS

        RSVP:
        Status Unused, Failures 0

        Done!'''
    },
}

rtp_stat = {
    "start_time": "10:10:10",
    "end_time": "11:11:11",
    "gw_number": "001",
    "local_addr": "10.10.10.10",
    "local_port": "55555",
    "remote_addr": "11.11.11.11",
    "remote_port": "55556",
    "codec": "G711U",
    "qos": "ok",
}

#System
#+---+--------+---------------+-----------------+-------------+-----+--+--------+
#│BGW│  Name  |     LAN IP    │     LAN MAC     |   Uptime    |Model│HW│Firmware│
#+---+--------+---------------+-----------------+-------------+-----+--+--------+
#|001|        |192.168.111.111|34:75:c7:64:ef:08|153d05h23m06s| g430│1A│43.11.12│
#+---+--------+---------------+-----------------+-------------+-----+--+--------+

SYSTEM_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 1,
    },
    {
        'column_attr': 'gw_name',
        'column_name': 'Name',
        'color': 'base',
        'fmt': '>8',
        'xpos': 5,
    },
    {
        'column_attr': 'host',
        'column_name': 'LAN IP',
        'color': 'base',
        'fmt': '>15',
        'xpos': 14,
    },
    {
        'column_attr': 'mac',
        'column_name': 'LAN MAC',
        'color': 'base',
        'fmt': '>17',
        'xpos': 30,
    },
    {
        'column_attr': 'uptime',
        'column_name': 'Uptime',
        'color': 'base',
        'fmt': '>13',
        'xpos': 48,
    },
    {
        'column_attr': 'model',
        'column_name': 'Model',
        'color': 'base',
        'fmt': '>5',
        'xpos': 62,
    },
    {
        'column_attr': 'hw',
        'column_name': 'HW',
        'color': 'base',
        'fmt': '>2',
        'xpos': 68,
    },
    {
        'column_attr': 'fw',
        'column_name': 'Firmware',
        'color': 'base',
        'fmt': '>8',
        'xpos': 71,
    },
]

#Hardware
#+---+---------------+------------+-------+---------+------+---+------+---------+
#│BGW│    Location   | Serial Num |Chassis|Mainboard|Memory│DSP│Announ| C.Flash |
#+---+---------------+------------+-------+---------+------+---+------+---------+
#|001|               |13TG01116522|     1A|       3A| 256MB│160│   999|installed|
#+---+---------------+------------+-------+---------+------+---+------+---------+

HARDWARE_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 1,
    },
    {
        'column_attr': 'location',
        'column_name': 'Location',
        'color': 'base',
        'fmt': '>15',
        'xpos': 5,
    },
    {
        'column_attr': 'serial',
        'column_name': 'Serial',
        'color': 'base',
        'fmt': '>12',
        'xpos': 21,
    },
    {
        'column_attr': 'chassis_hw',
        'column_name': 'Chassis',
        'color': 'base',
        'fmt': '>9',
        'xpos': 34,
    },
    {
        'column_attr': 'mainboard_hw',
        'column_name': 'Mainboard',
        'color': 'base',
        'fmt': '>7',
        'xpos': 42,
    },
    {
        'column_attr': 'memory',
        'column_name': 'Memory',
        'color': 'base',
        'fmt': '>6',
        'xpos': 52,
    },
    {
        'column_attr': 'dsp',
        'column_name': 'DSP',
        'color': 'base',
        'fmt': '>3',
        'xpos': 59,
    },
    {
        'column_attr': 'announcements',
        'column_name': 'Announ',
        'color': 'base',
        'fmt': '>6',
        'xpos': 63,
    },
    {
        'column_attr': 'comp_flash',
        'column_name': 'C.Flash',
        'color': 'base',
        'fmt': '>9',
        'xpos': 70,
    },
]

#Module
#+---+------+------+------+------+------+------+------+------+--------+----+----+
#│BGW│  v1  |  v2  |  v3  |  v4  |  v5  |  v6  |  v7  |  v8  |   v10  |PSU1|PSU2|
#+---+------+------+------+------+------+------+------+------+--------+----+----+
#|001|S8300E│MM714B│MM714B│MM714B│MM714B│MM714B│S8300E│S8300E│Mainboar|400W│400W|
#+---+------+------+------+------+------+------+------+------+--------+----+----+

MODULE_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 1,
    },
    {
        'column_attr': 'mm_v1',
        'column_name': 'v1',
        'color': 'base',
        'fmt': '>6',
        'xpos': 5,
    },
    {
        'column_attr': 'mm_v2',
        'column_name': 'v2',
        'color': 'base',
        'fmt': '>6',
        'xpos': 12,
    },
    {
        'column_attr': 'mm_v3',
        'column_name': 'v3',
        'color': 'base',
        'fmt': '>6',
        'xpos': 19,
    },
    {
        'column_attr': 'mm_v4',
        'column_name': 'v4',
        'color': 'base',
        'fmt': '>6',
        'xpos': 27,
    },
    {
        'column_attr': 'mm_v5',
        'column_name': 'v5',
        'color': 'base',
        'fmt': '>6',
        'xpos': 33,
    },
    {
        'column_attr': 'mm_v6',
        'column_name': 'v6',
        'color': 'base',
        'fmt': '>6',
        'xpos': 40,
    },
    {
        'column_attr': 'mm_v7',
        'column_name': 'v7',
        'color': 'base',
        'fmt': '>6',
        'xpos': 47,
    },
    {
        'column_attr': 'mm_v8',
        'column_name': 'v8',
        'color': 'base',
        'fmt': '>6',
        'xpos': 54,
    },
    {
        'column_attr': 'mm_v10',
        'column_name': 'v10',
        'color': 'base',
        'fmt': '>6',
        'xpos': 61,
    },
    {
        'column_attr': 'psu1',
        'column_name': 'PSU1',
        'color': 'base',
        'fmt': '>4',
        'xpos': 70,
    },
    {
        'column_attr': 'psu2',
        'column_name': 'PSU2',
        'color': 'base',
        'fmt': '>4',
        'xpos': 75,
    },
]

#Port
#+---+----+---------+--------+---------+----+---------+--------+----+----+------+
#|BGW|Port| Status  |  Neg.  |Spd.|Dup.|Port| Status  |  Neg.  |Spd.|Dup.|Redund|
#+---+----+---------+--------+----+----+----+---------+--------+----+----+------+
#|001|10/4|connected| enabled|100M|full|10/5|  no link| enabled|100M|half|   5/4|
#+---+----+---------+--------+----+----+----+---------+--------+----+----+------+

PORT_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 1,
    },
    {
        'column_attr': 'port1',
        'column_name': 'Port',
        'color': 'base',
        'fmt': '>4',
        'xpos': 5,
    },
    {
        'column_attr': 'port1_status',
        'column_name': 'Status',
        'color': 'base',
        'fmt': '>9',
        'xpos': 10,
    },
    {
        'column_attr': 'port1_neg',
        'column_name': 'Neg',
        'color': 'base',
        'fmt': '>8',
        'xpos': 20,
    },
    {
        'column_attr': 'port1_speed',
        'column_name': 'Spd.',
        'color': 'base',
        'fmt': '>4',
        'xpos': 29,
    },
    {
        'column_attr': 'port1_duplex',
        'column_name': 'Dup.',
        'color': 'base',
        'fmt': '>4',
        'xpos': 34,
    },
    {
        'column_attr': 'port2',
        'column_name': 'Port',
        'color': 'base',
        'fmt': '>4',
        'xpos': 39,
    },
    {
        'column_attr': 'port2_status',
        'column_name': 'Status',
        'color': 'base',
        'fmt': '>9',
        'xpos': 44,
    },
    {
        'column_attr': 'port2_neg',
        'column_name': 'Neg',
        'color': 'base',
        'fmt': '>8',
        'xpos': 54,
    },
    {
        'column_attr': 'port2_speed',
        'column_name': 'Spd.',
        'color': 'base',
        'fmt': '>4',
        'xpos': 63,
    },
    {
        'column_attr': 'port2_duplex',
        'column_name': 'Dup.',
        'color': 'base',
        'fmt': '>4',
        'xpos': 68,
    },
    {
        'column_attr': 'port_redu',
        'column_name': 'Redund',
        'color': 'base',
        'fmt': '>6',
        'xpos': 73,
    },
]

#Service
#+---+---------+---------------+----+---------+--------+---------------+--------+
#|BGW|rtp-stats|capture-service|snmp|snmp-trap| slamon | slamon server |  lldp  |
#+---+---------+---------------+----+---------+--------+---------------+--------+
#|001| disabled|       disabled|v2&3|  enabled| enabled|101.101.111.198|disabled|
#+---+---------+---------------+----+---------+--------+---------------+--------+

SERVICE_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 1,
    },
    {
        'column_attr': 'rtp_stat_service',
        'column_name': 'RTP-Stats',
        'color': 'base',
        'fmt': '>9',
        'xpos': 5,
    },
    {
        'column_attr': 'capture_service',
        'column_name': 'Capture-Service',
        'color': 'base',
        'fmt': '>15',
        'xpos': 15,
    },
    {
        'column_attr': 'snmp',
        'column_name': 'SNMP',
        'color': 'base',
        'fmt': '>4',
        'xpos': 31,
    },
    {
        'column_attr': 'snmp_trap',
        'column_name': 'snmp-trap',
        'color': 'base',
        'fmt': '>9',
        'xpos': 36,
    },
    {
        'column_attr': 'slamon_service',
        'column_name': 'SLAMon',
        'color': 'base',
        'fmt': '>8',
        'xpos': 46,
    },
    {
        'column_attr': 'sla_server',
        'column_name': 'SLAMon Server',
        'color': 'base',
        'fmt': '>15',
        'xpos': 55,
    },
    {
        'column_attr': 'lldp',
        'column_name': 'LLDP',
        'color': 'base',
        'fmt': '>8',
        'xpos': 71,
    },
]

#Status
#+---+-----------+-----------+---------+--------+-----+--------+-------+--------+
#|BGW|Act.Session|Tot.Session|InUse DSP|  Temp  |Fault|PollSecs| Polls |LastSeen|
#+---+-----------+-----------+---------+--------+-----+--------+-------+--------+
#|001|        0/0| 32442/1443|      320|39C/104F|    3|  120.32|      3|11:02:11|
#+---+-----------+-----------+---------+--------+-----+--------+-------+--------+

STATUS_ATTRS = [
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 1,
    },
    {
        'column_attr': 'active_session',
        'column_name': 'Act.Session',
        'color': 'base',
        'fmt': '>11',
        'xpos': 5,
    },
    {
        'column_attr': 'total_session',
        'column_name': 'Tot.Session',
        'color': 'base',
        'fmt': '>12',
        'xpos': 17,
    },
    {
        'column_attr': 'voip_dsp',
        'column_name': 'InUse DSP',
        'color': 'base',
        'fmt': '>9',
        'xpos': 29,
    },
    {
        'column_attr': 'temp',
        'column_name': 'Temp',
        'color': 'base',
        'fmt': '>8',
        'xpos': 39,
    },
    {
        'column_attr': 'avg_poll_secs',
        'column_name': 'AvgPollSec',
        'color': 'base',
        'fmt': '>10',
        'xpos': 61,
    },
    {
        'column_attr': 'polls',
        'column_name': 'Polls',
        'color': 'base',
        'fmt': '>5',
        'xpos': 72,
    },
]

#RTP-Stat
#+--------+--------+---+---------------+-----+---------------+-----+--------+---+
#|  Start |   End  |BGW| Local-Address |LPort| Remote-Address|RPort|Codec/pt|QoS|
#+--------+--------+---+---------------+-----+---------------+-----+--------+---+
#|11:09:07|11:11:27|001|192.168.111.111|55555|100.100.100.100|55555|G711U/20| OK|
#+--------+--------+---+---------------+-----+---------------+-----+--------+---+

RTPSTAT_ATTRS = [
    {
        'column_attr': 'start_time',
        'column_name': 'Start',
        'color': 'base',
        'fmt': '>8',
        'xpos': 1,
    },
    {
        'column_attr': 'end_time',
        'column_name': 'End',
        'color': 'base',
        'fmt': '>8',
        'xpos': 10,
    },
    {
        'column_attr': 'gw_number',
        'column_name': 'BGW',
        'color': 'base',
        'fmt': '>3',
        'xpos': 19,
    },
    {
        'column_attr': 'local_addr',
        'column_name': 'Local-Address',
        'color': 'base',
        'fmt': '>15',
        'xpos': 23,
    },
    {
        'column_attr': 'local_port',
        'column_name': 'LPort',
        'color': 'base',
        'fmt': '>5',
        'xpos': 39,
    },
    {
        'column_attr': 'remote_addr',
        'column_name': 'Remote-Address',
        'color': 'base',
        'fmt': '>15',
        'xpos': 45,
    },
    {
        'column_attr': 'remote_port',
        'column_name': 'RPort',
        'color': 'base',
        'fmt': '>5',
        'xpos': 61,
    },
    {
        'column_attr': 'codec',
        'column_name': 'Codec',
        'color': 'base',
        'fmt': '>5',
        'xpos': 67,
    },
    {
        'column_attr': 'qos',
        'column_name': 'QoS',
        'color': 'base',
        'fmt': '^4',
        'xpos': 74,
    },
]


class BGW():
    def __init__(self,
        host: str,
        proto: str = '',
        polling_secs = 10,
        gw_name: str = '',
        gw_number: str = '',
        show_announcements_files = '',
        show_capture: str = '',
        show_faults: str = '',
        show_lldp_config: str = '',
        show_mg_list: str = '',
        show_port: str = '',
        show_rtp_stat_summary: str = '',
        show_running_config: str = '',
        show_sla_monitor: str = '',
        show_system: str = '',
        show_temp: str = '',
        show_voip_dsp: str = '',
        **kwargs,
    ) -> None:
        self.host = host
        self.proto = proto
        self.polling_secs = polling_secs
        self.gw_name = gw_name
        self.gw_number = gw_number
        self.polls = 0
        self.avg_poll_secs = 0
        self.last_seen = None
        self.show_announcements_files = show_announcements_files
        self.show_capture = show_capture
        self.show_faults = show_faults
        self.show_lldp_config = show_lldp_config
        self.show_mg_list = show_mg_list
        self.show_port = show_port
        self.show_rtp_stat_summary = show_rtp_stat_summary
        self.show_running_config = show_running_config
        self.show_sla_monitor = show_sla_monitor
        self.show_system = show_system
        self.show_temp = show_temp
        self.show_voip_dsp = show_voip_dsp
        self.queue = Queue()
        self._active_session = None
        self._announcements = None
        self._capture_service = None
        self._chassis_hw = None
        self._comp_flash = None
        self._dsp = None
        self._faults = None
        self._fw = None
        self._hw = None
        self._lldp = None
        self._location = None
        self._lsp = None
        self._mac = None
        self._mainboard_hw = None
        self._memory = None
        self._model = None
        self._port1 = None
        self._port1_status = None
        self._port1_neg = None
        self._port1_duplex = None
        self._port1_speed = None
        self._port2 = None
        self._port2_status = None
        self._port2_neg = None
        self._port2_duplex = None
        self._port2_speed = None
        self._port_redu = None
        self._psu = None
        self._psu1 = None
        self._psu2 = None
        self._rtp_stat_service = None
        self._serial = None
        self._slamon_service = None
        self._sla_server = None
        self._snmp = None
        self._total_session = None
        self._uptime = None
        self._voip_dsp = None

    @property
    def active_session(self):
        if self.show_rtp_stat_summary:
            m = re.search(r'nal\s+\S+\s+(\S+)', self.show_rtp_stat_summary)
            return m.group(1) if m else "?/?"
        return "NA"

    @property
    def announcements(self):
        if self.dir:
            if self._announcements is None:
                m = re.findall(r"Annc files", self.dir)
                self._announcements = len(m)
            return self._announcements
        return "NA"

    @property
    def capture_service(self):
        if self.show_capture:
            if self._capture_service is None:
                m = re.search(r' service is (\w+)', self.show_capture)
                self._capture_service = m.group(1) if m else "?"
            return self._capture_service
        return "NA"

    @property
    def chassis_hw(self):
        if self.show_system:
            if self._chassis_hw is None:
                v = re.search(r'Chassis HW Vintage\s+:\s+(\S+)', self.show_system)
                s = re.search(r"Chassis HW Suffix\s+:\s+(\S+)", self.show_system)
                self._chassis_hw = v.group(1) if v else "?" + s.group(1) if s else "?"
            return self._chassis_hw
        return "NA"

    @property
    def comp_flash(self):
        if self.show_system:
            if self._comp_flash is None:
                m = re.search(r'Flash Memory\s+:\s+(\S+)', self.show_system)
                if m and "Compact" in m.group(1):
                    self._comp_flash = "installed"
                else:
                    self._comp_flash = ""
            return self._comp_flash
        return "NA"

    @property
    def dsp(self):
        if self.show_system:
            if self._dsp is None:
                m = re.findall(r"Media Socket .*?: M?P?(\d+) ", self.show_system)
                self._dsp = sum(int(x) for x in m) if m else "?"
            return self._dsp
        return "NA"

    @property
    def faults(self):
        if self.show_faults:
            if self._faults is None:
                if "No Fault Messages" in self.show_faults:
                    self._faults = 0
                else:
                    m = re.findall(r"\s+\+ (\S+)", self.show_faults)
                    self._faults = len(m)
            return self._faults
        return "NA"

    @property
    def fw(self):
        if self.show_system:
            if self._fw is None:
                m = re.search(r'FW Vintage\s+:\s+(\S+)', self.show_system)
                self._fw = m.group(1) if m else "?"
            return self._fw
        return "NA"

    @property
    def hw(self):
        if self.show_system:
            if self._hw is None:
                m = re.search(r'HW Vintage\s+:\s+(\S+)', self.show_system)
                hw_vintage = m.group(1) if m else "?"
                m = re.search(r'HW Suffix\s+:\s+(\S+)', self.show_system)
                hw_suffix = m.group(1) if m else "?"
                self._hw = f"{hw_vintage}{hw_suffix}"
            return self._hw
        return "NA"

    @property
    def lldp(self):
        if self.show_lldp_config:
            if self._lldp is None:
                if "Application status: disable" in self.show_lldp_config:
                   self._lldp = "disabled"
                else:
                   self._lldp = "enabled"
            return self._lldp
        return "NA"

    @property
    def location(self):
        if self.show_system:
            if self._location is None:
                m = re.search(r'System Location\s+:\s+(\S+)', self.show_system)
                self._location = m.group(1) if m else ""
            return self._location
        return "NA"

    @property
    def lsp(self):
        if self.show_mg_list:
            if self._lsp is None:
                m = re.search(r'ICC\s+(\S)', self.show_mg_list)
                self._lsp = f"S8300{m.group(1)}" if m else ""
            return self._lsp
        return "NA"

    @property
    def mac(self):
        if self.show_system:
            if self._mac is None:
                m = re.search(r"LAN MAC Address\s+:\s+(\S+)", self.show_system)
                self._mac = m.group(1) if m else "?"
            return self._mac
        return "NA"

    @property
    def mainboard_hw(self):
        if self.show_system:
            if self._mainboard_hw is None:
                v = re.search(r'Mainboard HW Vintage\s+:\s+(\S+)', self.show_system)
                s = re.search(r"Mainboard HW Suffix\s+:\s+(\S+)", self.show_system)
                self._mainboard_hw = v.group(1) if v else "?" + s.group(1) if s else "?"
            return self._mainboard_hw
        return "NA"

    @property
    def memory(self):
        if self.show_system:
            if self._memory is None:
                m = re.findall(r"Memory #\d+\s+:\s+(\S+)", self.show_system)
                self._memory = f"{sum(self._to_mbyte(x) for x in m)}MB"
            return self._memory
        return "NA"

    @property
    def model(self):
        if self.show_system:
            if self._model is None:
                m = re.search(r'Model\s+:\s+(\S+)', self.show_system)
                self._model = m.group(1) if m else "?"
            return self._model
        return "NA"

    @property
    def port1(self):
        if self._port1 is None:
            pdict = self._port_groupdict(0)
            self._port1 = pdict.get("port", "?") if pdict else "NA"
        return self._port1

    @property
    def port1_status(self):
        if self._port1_status is None:
            pdict = self._port_groupdict(0)
            self._port1_status = pdict.get("status", "?") if pdict else "NA"
        return self._port1_status

    @property
    def port1_neg(self):
        if self._port1_neg is None:
            pdict = self._port_groupdict(0)
            self._port1_neg = pdict.get("neg", "?") if pdict else "NA"
        return self._port1_neg

    @property
    def port1_duplex(self):
        if self._port1_duplex is None:
            pdict = self._port_groupdict(0)
            self._port1_duplex = pdict.get("duplex", "?") if pdict else "NA"
        return self._port1_duplex

    @property
    def port1_speed(self):
        if self._port1_speed is None:
            pdict = self._port_groupdict(0)
            self._port1_speed = pdict.get("speed", "?") if pdict else "NA"
        return self._port1_speed

    @property
    def port2(self):
        if self._port2 is None:
            pdict = self._port_groupdict(1)
            self._port2 = pdict.get("port", "?") if pdict else "NA"
        return self._port2

    @property
    def port2_status(self):
        if self._port2_status is None:
            pdict = self._port_groupdict(1)
            self._port2_status = pdict.get("status", "?") if pdict else "NA"
        return self._port2_status

    @property
    def port2_neg(self):
        if self._port2_neg is None:
            pdict = self._port_groupdict(1)
            self._port2_neg = pdict.get("neg", "?") if pdict else "NA"
        return self._port2_neg

    @property
    def port2_duplex(self):
        if self._port2_duplex is None:
            pdict = self._port_groupdict(1)
            self._port2_duplex = pdict.get("duplex", "?") if pdict else "NA"
        return self._port2_duplex

    @property
    def port2_speed(self):
        if self._port2_speed is None:
            pdict = self._port_groupdict(1)
            self._port2_speed = pdict.get("speed", "?") if pdict else "NA"
        return self._port2_speed

    @property
    def port_redu(self):
        if self.show_running_config:
            if self._port_redu is None:
                m = re.search(r'port redundancy \d+/(\d+) \d+/(\d+)',
                    self.show_running_config)
                self._port_redu = f"{m.group(1)}/{m.group(2)}" if m else ""
            return self._port_redu
        return "NA"

    @property
    def psu(self):
        if self.show_system:
            if self._psu is None:
                m = re.findall(r"PSU #\d+", self.show_system)
                self._psu = len(m)
            return self._psu
        return "NA"

    @property
    def psu1(self):
        if self.show_system:
            if self._psu1 is None:
                m = re.search(r"PSU #1\s+:\s+\S+ (\S+)", self.show_system)
                self._psu1 = m.group(1) if m else ""
            return self._psu1
        return "NA"

    @property
    def psu2(self):
        if self.show_system:
            if self._psu2 is None:
                m = re.search(r"PSU #2\s+:\s+\S+ (\S+)", self.show_system)
                self._psu2 = m.group(1) if m else ""
            return self._psu2
        return "NA"

    @property
    def rtp_stat_service(self):
        if self._rtp_stat_service is None:
            m = re.search(r'rtp-stat-service', self.show_running_config)
            self._rtp_stat_service = "enabled" if m else "disabled"
        return self._rtp_stat_service

    @property
    def serial(self):
        if self.show_system:
            if self._serial is None:
                m = re.search(r'Serial No\s+:\s+(\S+)', self.show_system)
                self._serial = m.group(1) if m else "?"
            return self._serial
        return "NA"

    @property
    def slamon_service(self):
        if self.show_sla_monitor:
            if self._slamon_service is None:
                m = re.search(r'SLA Monitor:\s+(\S+)', self.show_sla_monitor)
                self._slamon_service = m.group(1).lower() if m else "?"
            return self._slamon_service
        return "NA"

    @property
    def sla_server(self):
        if self.show_sla_monitor:
            if self._sla_server is None:
                m = re.search(r'Registered Server IP Address:\s+(\S+)',
                              self.show_sla_monitor)
                self._sla_server = m.group(1) if m else ""
            return self._sla_server
        return "NA"

    @property
    def snmp(self):
        if self.show_running_config:
            if self._snmp is None:
                snmp = []
                if "snmp-server comm" in self.show_running_config:
                    snmp.append("2")
                if "encrypted-snmp-server comm" in self.show_running_config:
                    snmp.append("3")
                self._snmp = "v" + "&".join(snmp) if snmp else ""
            return self._snmp
        return "NA"

    @property
    def temp(self):
        if self.show_temp:
            m = re.search(r'Temp\s+:\s+(\S+)', self.show_temp)
            return self._snmp
        return "NA"

    @property
    def total_session(self):
        if self.show_rtp_stat_summary:
            m = re.search(r'nal\s+\S+\s+\S+\s+(\S+)',
                          self.show_rtp_stat_summary)
            return m.group(1) if m else "?/?"
        return "NA"

    @property
    def uptime(self):
        if self.show_system:
            if self._uptime is None:
                m = re.search(r'Uptime \(\S+\)\s+:\s+(\S+)', self.show_system)
                if m:
                    self._uptime = m.group(1).replace(",", "d")\
                                    .replace(":", "h", 1)\
                                    .replace(":", "m") + "s"
                else:
                    self._uptime = "?"
            return self._uptime
        return "NA"

    @property
    def voip_dsp(self):
        inuse, total = 0, 0
        dsps = re.findall(r"In Use\s+:\s+(\d+) of (\d+) channels",
                          self.show_voip_dsp)
        for dsp in dsps:
            try:
                dsp_inuse, dsp_total = dsp
                inuse += int(dsp_inuse)
                total += int(dsp_total)
            except:
                pass
        #total = total if total > 0 else "?"
        #inuse = inuse if inuse > 0 else "?"
        return f"{inuse}/{total}"

    def update(
        self,
        last_seen: Optional[str] = None,
        gw_name: Optional[str] = None,
        gw_number: Optional[str] = None,
        commands: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> None:
        """
        Updates the BGW instance with new data.

        Args:
            last_seen: The last time the BGW was seen, in the format
                "%Y-%m-%d,%H:%M:%S".
            gw_name: The name of the gateway.
            gw_number: The number of the gateway.
            commands: A dictionary of commands and their output.
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        if last_seen:
            last_seen = datetime.strptime(last_seen, "%Y-%m-%d,%H:%M:%S")
            if not self.last_seen:
                self.last_seen = last_seen

            delta = last_seen - self.last_seen
            if delta:
                self.avg_poll_secs = round((self.avg_poll_secs + delta) / 2, 1)
            else:
                self.avg_poll_secs = self.polling_secs

            if not self.gw_number and gw_number:
                self.gw_number = gw_number
            if not self.gw_name and gw_name:
                self.gw_name = gw_name

            self.polls += 1

        if commands:
            for cmd, value in commands.items():
                bgw_attr = cmd.replace(" ", "_").replace("-", "_")
                setattr(self, bgw_attr, value)

    def _port_groupdict(self, idx: int) -> Dict[str, str]:
        """
        Extract port information from the 'show_port' string.

        Args:
            idx: The index of the port information to extract.

        Returns:
            A dictionary containing port details.
        """
        if self.show_port:
            matches = re.findall(r'(.*Avaya Inc)', self.show_port)
            if matches:
                line = matches[idx] if idx < len(matches) else ""
                if line:
                    return re.search(r"".join((
                        r'.*?(?P<port>\d+/\d+)',
                        r'.*?(?P<name>.*)',
                        r'.*?(?P<status>(connected|no link))',
                        r'.*?(?P<vlan>\d+)',
                        r'.*?(?P<level>\d+)',
                        r'.*?(?P<neg>\S+)',
                        r'.*?(?P<duplex>\S+)',
                        r'.*?(?P<speed>\S+)')), line).groupdict()
        return {}

    def _mm_groupdict(self):
        if self.show_mg_list:
            return re.search(r'.*?(?P<mm>\S+)', self.show_mg_list).groupdict()
        return {}

    @staticmethod
    def _to_mbyte(str):
        m = re.search(r'(\d+)([MG]B)', str)
        if m:
            num, unit = int(m.group(1)), m.group(2)
            if unit == "MB":
                return num
            elif unit == "GB":
                return 1024 * num
        return 0

    def __str__(self):
        return f"BGW({self.host})"

    def __repr__(self):
        return f"BGW(host={self.host})"

    def properties_asdict(self) -> Dict[str, Any]:
        """
        Return a dictionary of this instance's properties.

        The dictionary will contain the names of the properties as keys and
        the values of the properties as values.

        Returns:
            A dictionary of the instance's properties.
        """
        properties = {}
        for name in dir(self.__class__):
            obj = getattr(self.__class__, name)
            if isinstance(obj, property):
                val = obj.__get__(self, self.__class__)
                properties[name] = val
        return properties   

    def asdict(self) -> Dict[str, Any]:
        """
        Return a dictionary of this instance's properties and attributes.

        The dictionary will contain the names of the properties and attributes
        as keys and the values of the properties and attributes as values.

        Returns:
            A dictionary of the instance's properties and attributes.
        """
        attrs = self.__dict__
        return {**self.properties_asdict(), **attrs}


def iter_attrs(
    obj: object,
    attrs: List[Dict[str, Any]],
    xoffset: int = 0
) -> Iterator[Tuple[int, str, str]]:

    for attr in attrs:
        if hasattr(obj, attr['column_attr']):
            _str = str(getattr(obj, attr['column_attr']))
        else:
            _str = str(obj.get(attr['column_attr'], attr['column_attr']))
        
        if attr['fmt']:
            _len = int(''.join(i for i in attr['fmt'] if i.isdigit()))
            _str = f"{_str[:_len]:{attr['fmt']}}"
        elif attr['column_name']:
            _len = len(attr['column_name'])
            _str = f"{_str[:_len]}"
        else:
            _len = len(attr['column_attr'])
            _str = f"{_str[:_len]}"
        
        color = attr['color']
        xpos = attr['xpos'] if attr['xpos'] else 0
        yield xpos + xoffset, _str, color

def main():
    bgw = BGW("192.168.111.111")
    bgw.update(**data)
    for xpos, str, color in iter_attrs(bgw, HARDWARE_ATTRS):
        print(f"{xpos:3} {str:20} {color}")
    for xpos, str, color in iter_attrs(rtp_stat, RTPSTAT_ATTRS):
        print(f"{xpos:3} {str:20} {color}")

if __name__ == '__main__':
    main()
