import re

def cmds_to_expect_array(cmds):
    if cmds:
        cmds = [cmds] if isinstance(cmds, str) else list(cmds)
        cmds = [re.split(';|,|\|', c) for c in cmds]
        cmds = [c for cs in cmds for c in cs]
        return " ".join(f'"{c}"' for c in cmds)
    return ""

if __name__ == "__main__":
    print(cmds_to_expect_array(None))
    print(cmds_to_expect_array('show system|show version'))
    print(cmds_to_expect_array('show system'))
    print(cmds_to_expect_array(['show system|show version', 'show running-config']))
