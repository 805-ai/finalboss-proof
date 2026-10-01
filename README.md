# FinalBoss public proofs

Don't trust us. Check it yourself.

Download both ZIPs from the Release: https://github.com/805-ai/finalboss-proof/releases/latest

Check the hash first:

- Windows: `certutil -hashfile FILE.zip SHA256`
- macOS / Linux: `shasum -a 256 FILE.zip`

## 1. Fail-closed proof capsule V2

`FINALBOSS_PUBLIC_PROOF_CAPSULE_20260927_V2.zip`

SHA-256 `26810aee448859cfbe28ba461d71079ea439bf21e12a4c29a680e9467556ce83`

Extract it, open a terminal in the folder, and run:

```
py VERIFY_PUBLIC.py        (Windows)
python3 VERIFY_PUBLIC.py   (macOS / Linux)
```

Expected last line: `FINAL PASS 4/4 PUBLIC FAIL-CLOSED PROOFS VERIFIED`

Standard library only. Nothing to install.

## 2. V3.11 AMD SEV-SNP proof

`FINALBOSS_V311_PUBLIC_PROOF_20260824_R1.zip`

SHA-256 `14801b9cf6a7edabea3589f21f65a7793b2fe07e54f8a307d007ceca09c5f04b`

Path-scrubbed evidence text (v1.1). Cryptographic material unchanged from the original packet. Prior digests remain on the [v1.0 release](https://github.com/805-ai/finalboss-proof/releases/tag/v1.0).

Linux x86-64, Python 3.12, `python3-venv`. In the extracted folder:

```
python3 -m venv /tmp/fb-proof
/tmp/fb-proof/bin/pip install -r REQUIREMENTS.txt
/tmp/fb-proof/bin/python tools/VERIFY_PUBLIC_PROOF.py
```

Expected: JSON with `"status": "PASS"`

No private keys. No credentials. No engine source.

FinalBoss Technology Inc. | finalbosstech.com
