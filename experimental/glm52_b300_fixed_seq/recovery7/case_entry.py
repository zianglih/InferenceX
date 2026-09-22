#!/usr/bin/env python3
import argparse
import os
import sys
import cli

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--case-from-environment", action="store_true", required=True)
    p.add_argument("--activation", required=True)
    a = p.parse_args()
    sys.argv = [
        sys.argv[0],
        "case",
        "--lock",
        a.activation,
        "--lock-sha",
        os.environ["R7_EXECUTION_LOCK_SHA256"],
    ]
    raise SystemExit(cli.main())
