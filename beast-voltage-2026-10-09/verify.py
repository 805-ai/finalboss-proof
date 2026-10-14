#!/usr/bin/env python3
"""Check the BEAST run on a VoltageGPU confidential VM (Intel TDX + one NVIDIA H100), 9 October 2026.

    pip install cryptography voltage-verify
    python verify.py              receipts, attestation chain and bindings (no network)
    python verify.py --hardware   also re-verify all 115 Intel TDX quotes and NVIDIA H100 attestations
                                  with VoltageGPU's open-source voltage-verify, offline, from the collateral
                                  each bundle carries

Every check prints PASS or FAIL. Exit code 0 means every check passed.
"""
import argparse, base64, hashlib, json, subprocess, sys
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:
    sys.exit('needs: pip install cryptography')

D = Path(__file__).resolve().parent
A = D / 'attestation'
OK = True


def sha(b):
    return hashlib.sha256(b).hexdigest()


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':')).encode()


def check(name, cond, detail=''):
    global OK
    print(('PASS  ' if cond else 'FAIL  ') + name + (('   ' + detail) if detail else ''))
    OK = OK and bool(cond)


ap = argparse.ArgumentParser()
ap.add_argument('--hardware', action='store_true', help='also run voltage-verify on all 115 bundles')
args = ap.parse_args()

# 1. The receipt chain: every receipt signed by the run key, each pointing at the one before it.
chain = (D / 'RUN_KEY_CHAIN.jsonl').read_bytes()
raw = chain.splitlines(keepends=True)
run_public = json.loads((D / 'RUN_KEY_PUBLIC.json').read_text())['run_public']
key = Ed25519PublicKey.from_public_bytes(base64.b64decode(run_public))
prev, sig_ok, link_ok, recs = '0' * 64, True, True, []
for n, row in enumerate(raw):
    line = json.loads(row)
    rec = line['record']
    try:
        assert line['run_public'] == run_public
        key.verify(base64.b64decode(line['signature']), canon(rec))
    except Exception:
        sig_ok = False
    if rec['prev_sha256'] != prev or rec['seq'] != n:
        link_ok = False
    prev = sha(canon(line))
    recs.append(rec)
print('Receipt chain  RUN_KEY_CHAIN.jsonl  sha256 %s' % sha(chain))
check('%d receipts, every one signed by run key %s' % (len(recs), run_public), sig_ok)
check('every receipt points at the one before it, genesis to tip', link_ok)
check('chain opens with RUN_OPEN and closes with RUN_CLOSE', recs[0]['kind'] == 'RUN_OPEN' and recs[-1]['kind'] == 'RUN_CLOSE')

# 2. The run key was bound when the VM was admitted.
admission_raw = (D / 'HARDWARE_ACCEPTED.json').read_bytes()
admission = json.loads(admission_raw)
check('admission record (sha256 %s...) names the same run key' % sha(admission_raw)[:16],
      admission.get('run_public') == run_public and admission.get('status') == 'PASS')

# 3. The attestation chain: 115 links, every 2 minutes, each sealing the receipt chain as it stood.
links = [json.loads(x) for x in (A / 'CHAIN.jsonl').read_text().splitlines() if x.strip()]
prevlink, link_chain_ok, bundles_ok, prefix_ok, seal_ok = sha(admission_raw), True, True, True, True
measurements = set()
bad = []
for r in links:
    body = {k: v for k, v in r.items() if k != 'link_sha256'}
    if sha(canon(body)) != r['link_sha256'] or r['previous_link_sha256'] != prevlink:
        link_chain_ok = False
        bad.append(r['name'] + ' link')
    prevlink = r['link_sha256']
    braw = (A / (r['name'] + '.bundle.json')).read_bytes()
    bundle = json.loads(braw)
    m = bundle['manifest']
    ex = m['workload']['extra']
    # The Intel TDX quote's report_data (bytes 568-632) must be SHA-512 of this exact manifest.
    q = base64.b64decode(bundle['tdx']['quote_b64'])
    if q[568:632].hex() != hashlib.sha512(canon(m)).hexdigest():
        seal_ok = False
        bad.append(r['name'] + ' seal')
    measurements.add(q[184:232].hex() + q[376:568].hex())  # MRTD, RTMR0..RTMR3
    if (sha(braw) != r['bundle_sha256'] or m['challenge'] != r['nonce'] or r['status'] != 'PASS'
            or ex.get('previous_link_sha256') != r['previous_link_sha256'] or ex.get('run_public') != run_public):
        bundles_ok = False
        bad.append(r['name'] + ' bundle')
    art = {a['name']: a['sha256'] for a in m['workload']['artifacts']}
    if art.get('RUN_KEY_CHAIN.snapshot.jsonl') != sha(b''.join(raw[:r['run_key_chain_lines']])):
        prefix_ok = False
        bad.append(r['name'] + ' prefix')
print('Attestation chain  attestation/CHAIN.jsonl  %d links' % len(links))
check('every link re-hashes and points at the one before it; link 1 points at the admission record', link_chain_ok)
check('every bundle matches its link: file hash, off-box nonce, previous link, run key', bundles_ok)
check('every Intel TDX quote report_data equals SHA-512 of its manifest', seal_ok)
check('every quote sealed a byte-exact prefix of the published receipt chain', prefix_ok)
check('one set of TDX measurements (MRTD, RTMR0-3) across all %d quotes' % len(links), len(measurements) == 1)
last = links[-1]
lastm = json.loads((A / (last['name'] + '.bundle.json')).read_bytes())['manifest']
lastart = {a['name']: a['sha256'] for a in lastm['workload']['artifacts']}
check('the last quote (%s) seals the whole chain, all %d receipts, sha256 %s' % (last['name'], len(raw), sha(chain)),
      last['run_key_chain_lines'] == len(raw) and lastart.get('RUN_KEY_CHAIN.snapshot.jsonl') == sha(chain))
gpus = {r['gpu'].split(',')[1].strip() for r in links}
check('one H100 across all links', len(gpus) == 1, ', '.join(sorted(gpus)))
if bad:
    print('      problems: ' + ', '.join(bad[:20]))

# 4. The numbers on the page come from the signed RUN_CLOSE receipt.
t = recs[-1]['body']['totals']
nverified = sum(1 for r in recs if r['kind'] == 'CAMPAIGN_VERIFIED')
print('Signed totals (RUN_CLOSE, receipt %d)' % recs[-1]['seq'])
for k in ('campaigns_verified', 'gate_decisions', 'inference_calls', 'total_tokens', 'bypass_effects_caught',
          'model_bypass_attempts_caught', 'unattributed', 'in_doubt_unresolved'):
    print('      %-30s %s' % (k, '{:,}'.format(t[k])))
check('campaigns_verified equals the number of CAMPAIGN_VERIFIED receipts (%d)' % nverified, t['campaigns_verified'] == nverified)
check('gate_decisions = 24 per campaign', t['gate_decisions'] == 24 * t['campaigns_verified'])
around = t['provider_total_tokens'] - t['total_tokens']
print('      tokens at the model server %s = through the gate %s + around the gate %s' % (
    '{:,}'.format(t['provider_total_tokens']), '{:,}'.format(t['total_tokens']), '{:,}'.format(around)))
check('failed campaigns 0, unattributed 0, in-doubt 0',
      recs[-1]['body'].get('failed_campaigns') == 0 and t['unattributed'] == 0 and t['in_doubt_unresolved'] == 0)

# 5. Optional: the hardware itself, with VoltageGPU's own verifier.
if args.hardware:
    passed = 0
    for r in links:
        p = subprocess.run([sys.executable, '-m', 'voltage_verify', 'verify', str(A / (r['name'] + '.bundle.json')),
                            '--challenge', r['nonce'], '--gpus', '1', '--hwmodel', 'GH100', '--offline'],
                           capture_output=True, text=True)
        good = p.returncode == 0 and 'RESULT: VERIFIED' in p.stdout
        passed += good
        if not good:
            print('      %s: %s' % (r['name'], (p.stdout + p.stderr).strip().splitlines()[-1:]))
    check('voltage-verify: %d of %d Intel TDX quotes + NVIDIA H100 attestations VERIFIED' % (passed, len(links)), passed == len(links))

print('RESULT: ' + ('ALL CHECKS PASSED' if OK else 'FAILED'))
sys.exit(0 if OK else 1)
