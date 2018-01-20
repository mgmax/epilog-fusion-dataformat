#!/usr/bin/python3
import sys
import os

# Dump the contents of a raw print file resulting from "Print to File" with the Epilog Lasercutter print driver
# LICENSE: GPLv3 (or do whatever you want, I don't care)


def dump(filename):
    f=open(filename,  'rb')
    output=''
    for cmd in f.read().split(b'\x1b'):
        output += '\\x1b' + str(cmd)[2:-1] + '\r\n'
    return output


if len(sys.argv) > 1:
    filename = sys.argv[1]
    if filename == "--all":
        for f in os.listdir("."):
            if os.path.isfile(f) and f.endswith(".prn"):
                dump_file = open(f + ".dump",  'w')
                dump_file.write(dump(f))
                dump_file.close()
    else:
        print(dump(filename))
else:
    print("please provide the filename of the raw print dump as commandline argument")
    sys.exit(1)

