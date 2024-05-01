"""garak entry point wrapper"""

import sys

from garak import cli


def main():
    cli.main(sys.argv[1:])


if __name__ == "__main__":
    main()
