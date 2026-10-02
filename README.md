# FinalBoss public proofs

Don't trust us. Check it yourself.

If you received a printed FinalBoss proof packet, use the **exact two verification bundles below**. Their filenames and SHA-256 values match the printed proof enclosure.

## Download the exact proof bundles

### 1. Fail-closed proof capsule V2

[Download FINALBOSS_PUBLIC_PROOF_CAPSULE_20260927_V2.zip](https://github.com/805-ai/finalboss-proof/releases/download/v1.0/FINALBOSS_PUBLIC_PROOF_CAPSULE_20260927_V2.zip)

SHA-256 `26810aee448859cfbe28ba461d71079ea439bf21e12a4c29a680e9467556ce83`

Extract it, open a terminal in the folder, and run:

```
py VERIFY_PUBLIC.py        (Windows)
python3 VERIFY_PUBLIC.py   (macOS / Linux)
```

Expected last line:

`FINAL PASS 4/4 PUBLIC FAIL-CLOSED PROOFS VERIFIED`

Standard library only. Nothing to install.

### 2. V3.11 AMD SEV-SNP public proof

[Download FINALBOSS_V311_PUBLIC_PROOF_20260824_R1.zip](https://github.com/805-ai/finalboss-proof/releases/download/v1.0/FINALBOSS_V311_PUBLIC_PROOF_20260824_R1.zip)

SHA-256 `0843262c04d1bc6b9dc66be15ac94515ad44e1a5627562b19d078cd6bbe22342`

Linux x86-64, Python 3.12, `python3-venv`. In the extracted folder:

```
python3 -m venv /tmp/fb-proof
/tmp/fb-proof/bin/pip install -r REQUIREMENTS.txt
/tmp/fb-proof/bin/python tools/VERIFY_PUBLIC_PROOF.py
```

Expected result: JSON ending with `"status": "PASS"`.

## Check the hash before running

- Windows: `certutil -hashfile FILE.zip SHA256`
- macOS / Linux: `shasum -a 256 FILE.zip`

The printed packet is the commitment. If a downloaded ZIP does not match the SHA-256 printed above and in the enclosure, do not use it as the referenced proof.

No private keys. No credentials. No engine source.

FinalBoss Technology Inc. | finalbosstech.com
