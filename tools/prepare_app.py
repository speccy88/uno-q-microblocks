#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Capture actual LED triggers before the FIRST App start; no MCU operations."""
import argparse,importlib.util,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('app_dir',type=Path);a=p.parse_args();app=a.app_dir.resolve();state=app/'data/led_original.json'
if state.exists():raise SystemExit('Existing original LED snapshot preserved; preparation already done.')
s=importlib.util.spec_from_file_location('led_backend',app/'bricks/microblocks_bridge/leds.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
backend=m.LinuxLEDs(state);print(json.dumps({'saved':True,'channels':list(backend.original),'instruction':'Keep data/led_original.json private and persistent. App restarts reuse it.'}))
