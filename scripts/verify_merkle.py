#!/usr/bin/env python3
# Minimal placeholder verifier: recompute bundle hash and list file hashes.
# Extend to full merkle verification as needed.
import hashlib, sys, re

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    manifest = "manifest.txt" if len(sys.argv) < 2 else sys.argv[1]
    with open(manifest, 'r', encoding='utf-8') as f:
        txt = f.read()
    m = re.search(r"Bundle-Hash:\s*([0-9a-fA-F]{64})", txt)
    stated = m.group(1) if m else None
    actual = sha256_file(manifest)
    print(f"Stated Bundle-Hash: {stated}")
    print(f"Actual  Bundle-Hash: {actual}")
    if stated == actual:
        print("OK: Bundle-Hash matches file content.")
        sys.exit(0)
    else:
        print("MISMATCH: Bundle-Hash differs!")
        sys.exit(1)

if __name__ == "__main__":
    main()
