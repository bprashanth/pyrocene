#!/usr/bin/env python3
"""Prepare measured leaf/wood fragments for a fictional forest neighbourhood.

Run with the rendering venv (NumPy). This never edits the source scans.
The runtime repeats fragments; the resulting forest is not a measured plot.
"""
import hashlib
import json
from pathlib import Path
import numpy as np


def prepare(output=Path('/mnt/seagate/models/pyrocene/stage4/assets')):
    root=Path('/mnt/seagate/videos/pyrocene/lidar/artifacts')
    source=root/'paracou-fg6c2-tls-175-segmented.npz'
    d=np.load(source)
    rng=np.random.default_rng(170926)
    selected=[]
    for label,limit in [(0,14000),(1,74603),(3,31397)]:
        indices=np.flatnonzero(d['classification']==label)
        selected.extend(rng.choice(indices,min(limit,len(indices)),replace=False))
    indices=np.sort(selected)
    xyz=d['xyz'][indices];height=np.maximum(0,d['height'][indices])
    points=np.column_stack((xyz[:,0],height,-xyz[:,1],d['classification'][indices]==3)).astype('<f4')
    output.mkdir(parents=True,exist_ok=True)
    binary=output/'forest-fragment-wood.bin';points.tofile(binary)
    manifest={
        'schema':'pyrocene-forest-fragments/1',
        'file':binary.name,'stride':4,'tuple':'x,height,z,wood','count':len(indices),
        'bounds':{'x':[float(points[:,0].min()),float(points[:,0].max())],
                  'z':[float(points[:,2].min()),float(points[:,2].max())]},
        'source':json.loads((root/'paracou-fg6c2-tls-175-segmented.manifest.json').read_text())['source'],
        'sourceArtifact':source.name,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
        'selection':'Deterministic sample by measured structural class. All 31397 wood returns retained.',
        'limits':'Wood is the source structural class, not a species. Repeated runtime fragments form a fictional forest, not a tree census or an estimate of fuel load.'
    }
    # Keep source attribution portable, without build-machine paths.
    for key in ['source_file','ground_file']:
        if key in manifest['source']:manifest['source'][key]=Path(manifest['source'][key]).name
    (output/'forest-fragments.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'{len(indices)} measured returns -> {binary}')


if __name__=='__main__':prepare()
