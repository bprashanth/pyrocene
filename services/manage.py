#!/usr/bin/env python3
"""Manage only repository-owned Pyrocene event units; never stop shared cloudflared."""
import argparse
import os
from pathlib import Path
import secrets
import subprocess
import time
import urllib.request
import urllib.error

HERE=Path(__file__).resolve().parent
TARGET='pyrocene-games.target'
UNITS=[TARGET]+['pyrocene-'+n+'.service' for n in ['room','films','cinematic','gateway']]

def ctl(*args,check=True):
    return subprocess.run(['systemctl','--user',*args],check=check)

def ready():
    deadline=time.monotonic()+20
    paths=['/start','/stage4/health','/films/','/stage3/']
    while time.monotonic()<deadline:
        try:
            for path in paths:
                with urllib.request.urlopen('http://127.0.0.1:8030'+path,timeout=2) as r:
                    if r.status!=200: raise OSError('Unexpected response')
            print('Ready: http://127.0.0.1:8030/start')
            return
        except (OSError,urllib.error.URLError): time.sleep(.25)
    raise SystemExit('Services started but readiness checks failed. Run: python3 services/manage.py logs')

def install():
    # Refuse duplicate ownership rather than silently overwriting another unit.
    destination=Path.home()/'.config/systemd/user'
    destination.mkdir(parents=True,exist_ok=True)
    for unit in UNITS:
        link=destination/unit
        if (link.exists() or link.is_symlink()) and link.resolve()!=HERE/unit:
            raise SystemExit(f'{link} belongs to another installation. Resolve it first.')
    secret=Path.home()/'.config/pyrocene/gm-credentials'
    secret.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    if not secret.exists():
        fd=os.open(secret,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f: f.write('gm:'+secrets.token_urlsafe(24)+'\n')
    for unit in UNITS:
        link=destination/unit
        if not link.is_symlink(): link.symlink_to(HERE/unit)
    ctl('daemon-reload');ctl('enable',TARGET)
    print('Installed and enabled. Use start after checking that ports 8020/21/22/30 are free.')
    print(f'Organiser credentials: {secret} (not printed or stored in git).')

def uninstall():
    ctl('disable','--now',TARGET)
    destination=Path.home()/'.config/systemd/user'
    for unit in UNITS:
        link=destination/unit
        if link.is_symlink() and link.resolve()==HERE/unit: link.unlink()
    ctl('daemon-reload')
    print('Event units removed. Lore, cloudflared, repository, assets and organiser credentials retained.')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=['install','uninstall','start','stop','restart','status','logs','disable'])
    ap.add_argument('service',nargs='?',choices=['room','films','cinematic','gateway','lore'])
    args=ap.parse_args()
    unit='pyrocene-'+args.service+'.service' if args.service else TARGET
    if args.action=='install': install()
    elif args.action=='uninstall': uninstall()
    elif args.action=='logs':
        units=[unit] if args.service else UNITS[1:]
        subprocess.run(['journalctl','--user',*[a for u in units for a in ['-u',u]],'-n','60','--no-pager'],check=True)
    elif args.action=='disable': ctl('disable','--now',TARGET)
    elif args.action=='status': ctl('status',*([unit] if args.service else UNITS), '--no-pager',check=False)
    else:
        if args.action=='restart': ctl('daemon-reload')
        ctl(args.action,unit)
        if args.action in {'start','restart'} and not args.service: ready()

if __name__=='__main__': main()
