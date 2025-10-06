#!/usr/bin/env python3
import argparse, re, hashlib, sys, json, os
from datetime import datetime

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def replace_once(text, pattern, repl):
    return re.sub(pattern, repl, text, count=1, flags=re.MULTILINE)

def main():
    p = argparse.ArgumentParser(description="Update manifest.txt with blockchain anchors and bundle hash")
    p.add_argument("--manifest", required=True)
    p.add_argument("--bundle-hash", required=False)
    p.add_argument("--ots-proof", required=False)
    p.add_argument("--btc-tx", required=False)
    p.add_argument("--eth-tx", required=False)
    p.add_argument("--eth-block", required=False)
    args = p.parse_args()

    with open(args.manifest, 'r', encoding='utf-8') as f:
        txt = f.read()

    # Update Bundle-Hash (recompute to be safe if not provided)
    bundle_hash = args.bundle_hash or sha256_file(args.manifest)
    txt = re.sub(r"^Bundle-Hash:\s*.*$", f"Bundle-Hash: {bundle_hash}", txt, flags=re.MULTILINE)

    # Update OTS proof and Bitcoin TxID if provided
    if args.ots_proof:
        # Insert or replace OTS-Proof-File line
        txt = re.sub(r"(OTS-Proof-File:\s*).*$", r"\1{}".format(args.ots_proof), txt, flags=re.MULTILINE)
        # Mark Proof-Status under Bitcoin as Confirmed if btc tx present else Pending
        status = "Confirmed" if args.btc_tx else "Pending"
        # Only update the Bitcoin block's Proof-Status (first occurrence after 'Bitcoin-OTS:')
        txt = re.sub(r"(Bitcoin-OTS:\n(?:.*\n)*?\s*Proof-Status:\s*).*$", r"\1{}".format(status), txt, count=1, flags=re.MULTILINE)

    if args.btc_tx:
        txt = re.sub(r"(Bitcoin-TxID:\s*).*$", r"\1{}".format(args.btc_tx), txt, flags=re.MULTILINE)

    # Update Ethereum fields
    if args.eth_tx:
        txt = re.sub(r"(Ethereum:\n(?:.*\n)*?\s*TxID:\s*).*$", r"\1{}".format(args.eth_tx), txt, count=1, flags=re.MULTILINE)
        # Also update DataField with bundle-hash
        txt = re.sub(r"(DataField:\s*)0x\{\{Bundle-Hash\}\}", r"\1" + "0x" + bundle_hash, txt, flags=re.MULTILINE)
        # Proof status confirmed if block present
        status = "Confirmed" if args.eth_block else "Pending"
        txt = re.sub(r"(Ethereum:\n(?:.*\n)*?\s*Proof-Status:\s*).*$", r"\1{}".format(status), txt, count=1, flags=re.MULTILINE)
    if args.eth_block:
        txt = re.sub(r"(Block-Number:\s*).*$", r"\1{}".format(args.eth_block), txt, flags=re.MULTILINE)

    with open(args.manifest, 'w', encoding='utf-8') as f:
        f.write(txt)

    # Touch README-Notarization.txt to reflect latest anchor state (optional no-op here)
    if os.path.exists("README-Notarization.txt"):
        # Ensure there's at least a line that references the latest ETH TxID for human readers
        with open("README-Notarization.txt", 'a', encoding='utf-8') as rf:
            rf.write(f"\n\n# Auto-Update {datetime.utcnow().isoformat()}Z\n")
            if args.eth_tx:
                rf.write(f"Ethereum TxID: {args.eth_tx}\n")
            if args.ots_proof:
                rf.write(f"OTS Proof: {args.ots_proof}\n")

    print("✅ manifest.txt updated with anchors.")

if __name__ == "__main__":
    main()
