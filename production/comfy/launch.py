"""Launch an existing ComfyUI checkout on loopback with paid/custom nodes disabled."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def command(root, python, cpu=False, port=8188):
    root = Path(root).resolve()
    if not (root / 'main.py').is_file():
        raise ValueError('No ComfyUI main.py at the supplied path; install the open-source core first')
    if not 1 <= port <= 65535:
        raise ValueError('port must be 1-65535')
    # Read flags without importing torch or starting a server.
    flags = (root / 'comfy/cli_args.py').read_text()
    if '--offline' in flags:
        offline = '--offline'
    elif '--disable-api-nodes' in flags:
        offline = '--disable-api-nodes'
    else:
        raise ValueError('This checkout has no recognized flag to disable paid API nodes')
    if '--disable-all-custom-nodes' not in flags:
        raise ValueError('This checkout cannot disable unreviewed custom nodes')
    args = [python, str(root / 'main.py'), '--listen', '127.0.0.1', '--port', str(port),
            offline, '--disable-all-custom-nodes']
    if cpu:
        args.append('--cpu')
    return args


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--comfy-root', required=True)
    p.add_argument('--python', default=sys.executable)
    p.add_argument('--port', type=int, default=8188)
    p.add_argument('--cpu', action='store_true')
    p.add_argument('--print-only', action='store_true')
    a = p.parse_args()
    try:
        args = command(a.comfy_root, a.python, a.cpu, a.port)
    except (ValueError, OSError) as exc:
        p.exit(2, str(exc) + '\n')
    if a.print_only:
        print(json.dumps(args))
    else:
        # No shell, manager, model downloads, provider failover or restart loop.
        raise SystemExit(subprocess.call(args, cwd=Path(a.comfy_root).resolve()))

if __name__ == '__main__':
    main()
