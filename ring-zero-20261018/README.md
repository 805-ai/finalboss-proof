# Ring Zero: kernel network enforcement on attested H100 hardware

FinalBoss Technology Inc. | Run date: 2026-10-18 | Hardware: VoltageGPU H100, Intel TDX confidential VM, kernel 6.8.0-110-generic

## What this run shows

Three FinalBoss eBPF cgroup hooks (connect4, sendmsg4, sock_create) were loaded into the Linux kernel inside an attested confidential VM. Network actions without a valid gate permit were denied in the kernel.

## Results

Phase 1, bounded test
- 3,000 of 3,000 unpermitted socket calls denied. 0 allowed.
- Median deny time: 10.94 microseconds.
- Permitted calls: 3,000 of 3,000 went through, 0 failures.

Phase 2, long run (41 minutes, 21 cycles, one every 2 minutes)
- 21 of 21 cycles passed. 0 failed.
- Hardware attestation succeeded on all 21 cycles.
- All 3 hooks attached on all 21 cycles.
- Deny check passed on all 21 cycles.
- The permit in this phase came from a signed gate receipt, verified and bound to the TDX attestation.
- Hooks detached cleanly at the end.

## Scope

This run proves kernel network enforcement. It does not cover BPF-LSM (file and program-launch blocking), and it makes no AMD SEV-SNP claim.

## Verify it yourself

Evidence bundle: GUEST_EVIDENCE_PHASE2.tar.gz
SHA-256: 6019ef19363e76ca1ea3cc0114c29d0b7afd9312cc0d363548b1bcaf10c66dc9

Inside: per-cycle attestation bundles and manifests, CYCLES.jsonl, LATENCY.json, MANIFEST.sha256, the gate public keys (Ed25519 and ML-DSA-87), and the signed gate receipt.

Check the bundle hash, then check every file against MANIFEST.sha256.

Contact: Abraham@finalbosstech.com
