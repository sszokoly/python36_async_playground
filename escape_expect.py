import sys

def escape_expect(file):
    out = []
    with open(file) as fd:
        data = fd.read().splitlines()
    for line in data:
        line = line.replace("{", "{{").replace("}", "}}")
        out.append(repr(line).strip("'"))
    return "\n".join(out)

if __name__ == "__main__":
    sys.argv.append('g4xx_cmd_runner.exp')
    sys.exit(print(escape_expect(sys.argv[1])))