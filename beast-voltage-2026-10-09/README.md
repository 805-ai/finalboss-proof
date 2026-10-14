# BEAST inside a VoltageGPU Confidential VM, 9 October 2026

Final Boss Technology ran BEAST, its red-team engine for AI systems, end to end inside a VoltageGPU confidential VM: one Intel TDX guest with one NVIDIA H100. Every receipt the run wrote is signed, chained, and sealed inside an Intel TDX quote.

Write-up: https://finalbosstech.com/beast-voltage

## Run it yourself

```
git clone https://github.com/805-ai/finalboss-proof
cd finalboss-proof/beast-voltage-2026-10-09
pip install cryptography voltage-verify
python verify.py --hardware
```

`python verify.py` alone runs every check below except the hardware re-verification, with no network. `--hardware` adds VoltageGPU's open-source verifier (voltage-verify, MIT) on all 115 bundles, offline, from the Intel and NVIDIA collateral each bundle carries. A run ends with `RESULT: ALL CHECKS PASSED` and exit code 0.

## What the checks prove

1. **The receipts.** `RUN_KEY_CHAIN.jsonl` holds 4,215 receipts. Every one is Ed25519-signed by one run key, and every one carries the SHA-256 of the receipt before it, from genesis to `RUN_CLOSE`. Change, drop, or reorder one and the chain breaks.
2. **The run key was bound at admission.** `HARDWARE_ACCEPTED.json` is the VM's admission record. It names the same run key, and the first attestation link points at its hash.
3. **The receipts were sealed in the hardware, every two minutes.** `attestation/CHAIN.jsonl` holds 115 links. Each link is a fresh Intel TDX quote and NVIDIA H100 attestation over a manifest that carries an off-box challenge, the previous link, and the SHA-256 of the receipt chain as it stood at that moment. The quote's report data is SHA-512 of that manifest. All 115 chain prefixes match the published chain byte for byte.
4. **The last quote seals all of it.** Link 115 was taken after the run closed. Its manifest carries the SHA-256 of the full chain, `8354759f7d2dc1aa6b71a97284c949fbfce4a4a62ffd0f495c601edb0443cb4a`.
5. **One machine.** All 115 quotes carry one set of TDX measurements and one H100, `GPU-6d81b7ed-136f-b8b3-98b0-f129388fe0c6`.
6. **The numbers.** The totals on the write-up come from the signed `RUN_CLOSE` receipt: 1,052 campaigns verified, 0 failed, 25,248 gate decisions (24 per campaign), 26,688 inference calls, 19,173,230 tokens through the gate, 7,914 bypass effects caught, 34,310 model bypass attempts caught, 0 unattributed.

## What it does not prove

The quotes prove every receipt existed inside that genuine TDX guest, on that H100, when it was sealed, and that none changed afterward. They do not prove which program wrote the receipts: the VM boots VoltageGPU's stock image and the tenant has root.

## Files

| File | What it is |
|---|---|
| `RUN_KEY_CHAIN.jsonl` | 4,215 signed receipts |
| `RUN_KEY_PUBLIC.json` | the run's Ed25519 public key |
| `HARDWARE_ACCEPTED.json` | the VM admission record |
| `attestation/CHAIN.jsonl` | the 115 attestation links, with each off-box challenge |
| `attestation/link-NNNN.bundle.json` | each Intel TDX quote + NVIDIA H100 attestation bundle (voltage-verify format) |
| `verify.py` | the checks above |
| `SHA256SUMS.txt` | SHA-256 of every file here |

Final Boss Technology Inc. · Oxnard, California · abraham@finalbosstech.com · No receipt, no run.
