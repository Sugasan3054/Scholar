import os
import site

packages = site.getsitepackages()
gradio_path = ""
for p in packages:
    candidate = os.path.join(p, 'gradio')
    if os.path.exists(candidate):
        gradio_path = candidate
        break

if not gradio_path:
    print("Gradio not found")
    exit(1)

frontend_path = os.path.join(gradio_path, 'templates', 'frontend')
if not os.path.exists(frontend_path):
    print(f"Frontend path not found: {frontend_path}")
    exit(1)

import glob
assets_path = os.path.join(frontend_path, 'assets', '*.js')
files = glob.glob(assets_path)

found = []
for f in files:
    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
        if '.flatMap' in content:
            found.append(f)

print(f"File count with .flatMap: {len(found)}")
for f in found:
    print(os.path.basename(f))
    # Extract surrounding text
    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
        idx = content.find('.flatMap')
        while idx != -1:
            start = max(0, idx - 50)
            end = min(len(content), idx + 50)
            snippet = content[start:end]
            print(f"  ... {snippet.replace(chr(10), ' ')} ...")
            idx = content.find('.flatMap', idx + 1)
