import argparse
import sys

DEFAULTS = {
    "user": "",
    "passwd": "",
    "rtp_stat": True,
    "lastn_secs": 20,
    "timeout": 10,
    "debug": False,
    "log_file": "/dev/null"
}

def test(**kwargs):
    print(locals())
    print(kwargs)

def bgw_user():
    while True:
        user = input("Enter SSH username of BGWs: ")
        correct = input("Is this correct (Y/N)?: ")
        if correct.lower().startswith("y"):
            break
    return user.strip()

def get_passwd():
    while True:
        passwd = input("Enter SSH passwd of BGWs: ")
        correct = input("Is this correct (Y/N)?: ")
        if correct.lower().startswith("y"):
            break
    return passwd.strip()

def main(**kwargs):
    kwargs["user"] = kwargs["user"] if kwargs["user"] else bgw_user()
    kwargs["passwd"] = kwargs["passwd"] if kwargs["passwd"] else get_passwd()
    if kwargs["debug"]:
        kwargs["log_file"] = "bgw_debug.log"
    print(f"OLD: {DEFAULTS}")
    DEFAULTS.update(kwargs)
    print(f"NEW: {DEFAULTS}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-u', dest='user', type=str, default=DEFAULTS["user"], help='user')
    parser.add_argument('-p', dest='passwd', type=str, default=DEFAULTS["passwd"], help='password')
    parser.add_argument('-t', dest='timeout', default=DEFAULTS["timeout"], help='timeout in secs')
    parser.add_argument('-n', dest='lastn_secs', default=DEFAULTS["lastn_secs"], help='secs to look back in RTP statistics')
    parser.add_argument('-d', action='store_true', dest='debug', default=DEFAULTS["debug"], help='debug')
    parser.add_argument('-l', dest='log_file', default=DEFAULTS["log_file"], help='log file')
    sys.exit(main(**vars(parser.parse_args())))
