#!/usr/bin/env python3
"""
Construye la carpeta `deployment/package/` copiando los archivos necesarios
para llevar el modelo a otro proyecto.

Ejecutar desde la raíz del repo:
  python deployment/build_package.py
"""
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)

FILES = [
    'ml_model/model.py',
    'scripts/code_analyzer.py',
    'requirements.txt',
    'config.yml',
    'deployment/infer_example.py',
    'deployment/README.md',
    'ml_model/vulnerability_detector.pkl',
]

OUT_DIR = os.path.join('deployment', 'package')
os.makedirs(OUT_DIR, exist_ok=True)

copied = []
missing = []
for path in FILES:
    if os.path.exists(path):
        dest = os.path.join(OUT_DIR, os.path.basename(path))
        shutil.copy2(path, dest)
        copied.append(path)
        print(f'Copied: {path} -> {dest}')
    else:
        missing.append(path)
        print(f'Warning: not found {path}')

print('\nPackage assembled at:', OUT_DIR)
print('Files copied:', len(copied))
if missing:
    print('Missing files (please add manually if needed):')
    for m in missing:
        print(' -', m)
