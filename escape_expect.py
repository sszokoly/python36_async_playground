import sys

def main(file):
    out = []
    with open(file) as fd:
        data = fd.read().splitlines()
    for line in data:
        line = line.replace("{", "{{").replace("}", "}}")
        out.append(repr(line).strip("'"))
    print('\n'.join(out))

if __name__ == "__main__":
    sys.argv.append('rtpstats.exp')
    sys.exit(main(sys.argv[1]))