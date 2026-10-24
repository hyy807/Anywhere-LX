# LX Native v0.2.0 integration

## Scope

Integrated protocol and original adaptive UI repairs from LX-TIMEOUT-AUDIT.md and LX-UI-AUDIT.md without replacing Home/Launchpad/Dashboard layouts. Public upstream main remains 89905e0e3641bcbd958a66fcb6f027a2bdecec90; there are no omitted upstream commits at this integration point.

Local checks passed: four resource/theme tests, source contract checks, eleven real Swift import/auth assertions, and production H2 receive logic rejecting local TLS/H2 403 and delivering 200 DATA. CI now requires these actual Swift seam executions before the macOS unsigned app build. They are not iOS TLSClient or packet-tunnel end-to-end tests.

## Importing provider nodes

A 32-hex password without an LX marker still selects **standard AnyTLS**. Importing the original plain provider configuration without conversion therefore remains incompatible with LX authentication. Do not guess from password shape.

For a known, trusted LX provider only:

```sh
python3 scripts/convert_trusted_lx.py /private/provider.yaml /private/LX-trusted-nodes.txt --trusted-lx-provider
```

The converter emits explicit `anytls://...?...lx-auth=1` URLs. Only nodes with an explicit LX XHTTP transport also receive `transport=lx-xhttp`, obfuscation/path and independent download settings. It does not force XHTTP onto TLS-only nodes. Output is mode 0600, must be outside the repository, and must never be uploaded as a release asset.

The supplied local provider file yielded 171 AnyTLS URLs: 4 LX-XHTTP and 167 LX-auth-over-TLS. The non-AnyTLS node is intentionally not converted. Import the private text as node links using the app's existing URL/clipboard import flow. Conversion verifies syntax/field mapping, not server availability.

The provider's `skip-cert-verify` flag has no corresponding native URL parser option; conversion does not pretend to preserve it. Certificate requirements may therefore differ from the original client. This is an explicit remaining compatibility boundary.

## Remaining boundaries

- No physical device install, user-server connectivity, throughput, packet-tunnel, or light/dark interaction validation was performed on this Linux host.
- Offering h2 still lacks an explicit selected-ALPN guard in the LX dial path.
- LX H2 setup lacks a dedicated bounded native socket deadline.
- Private bundled Rules.db remains unavailable; rule imports are separate.
- Widget/watch/iCloud remain excluded for portable app + NE self-signing.
- The IPA is unsigned, without an Apple team or provisioning profile; installation requires appropriate re-signing and network-extension entitlements. Deployment target override alone does not prove iOS 18 runtime compatibility.
