#!/usr/bin/env python3

# generate-crops.py
#
# Copyright (C) 2023 Baylibre 
#
# SPDX-License-Identifier: GPL-2.0-only
#

import sys

import os
import shutil
import subprocess


import argparse
from pathlib import Path

bindir = os.path.dirname(__file__)
topdir = os.path.dirname(bindir)
sys.path[0:0] = [os.path.join(topdir, 'lib')]


if __name__ == "__main__":
    from crops import crops
    parser = argparse.ArgumentParser(
                        prog='crops_generator.py',
                        description='A generator tool from CROPS')

    parser.add_argument("--kconf", \
                        help="Name of .config to transform into CROPS Dockerfile", \
                        default=".config", \
                        type=str, required=True)
    parser.add_argument("--docker", help="Docker Container Context", type=str, required=True)
    args = parser.parse_args()

    crps=crops(args.kconf, args.docker, topdir)
    crps.MakeDockerDir()
    crps.SetUseradd()
    crps.SetHostOS()
    crps.UnpackTC()
    crps.SetTC()
    crps.SetEnvs()
    crps.SetPackages()
    crps.SetEntrypoints()
    crps.SetRepo()
    crps.SetTemplate()
    crps.WriteDockerFile()
