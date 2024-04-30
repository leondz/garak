"""garak entry point wrapper"""

import sys

sys.path.append("/home/sda/tianhaoli/garak")
from garak import cli


def main():
    cli.main(sys.argv[1:])


if __name__ == "__main__":
    main()
