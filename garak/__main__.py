"""garak entry point script"""

import sys

import os
sys.path.append(os.getcwd())

from garak import cli


def main():
    cli.main(sys.argv[1:])


if __name__ == "__main__":
    main()
