# LX Native UI audit (2026-10-24)

## Upstream baseline

Live `git ls-remote` and fetch of NodePassProject/Anywhere main returned
`89905e0e3641bcbd958a66fcb6f027a2bdecec90` (Update README).
`git merge-base HEAD upstream/main` returns that same commit and
`git rev-list --count HEAD..upstream/main` returns 0. No newer public upstream
feature commits were omitted from this fork at audit time.

The upstream Git tree/API does **not** include an asset catalog, original
VoyagerMemberCard/VoyagerCardBackground/voyagerCover implementations, or the
ToolbarOverflowMenu implementation. These cannot be restored verbatim from
public main. README explicitly excludes upstream names/icons/brand resources
from its source license. The LX replacements are original and must not be
represented as pixel-identical official assets.

## Confirmed regressions and changes

- `configure_lx.py` generated the same dark-only RGB triplets in light and dark
  appearance; no AccentColor existed. Added checked-in original light/dark
  background, card and accent catalogs. Configure regenerates the same bytes
  rather than overwriting them with the previous single-appearance colors.
- Theme editor retained the full upstream light/dark background/card pickers,
  previews and reset logic, but all pickers were blocked by StoreKit membership
  unavailable to this bundle. Made local personalization independent of that
  publisher entitlement without pretending to grant upstream membership.
- Icon picker advertised absent upstream alternate icons while configure cleared
  their build setting. Added three original LX icons, matching previews and
  matching alternate icon names; retained upstream selection/error flow.
- Launchpad tab/capsule referenced absent `anywhere` / `anywhere.fill` images.
  Added original template LX vector resources and changed these references.
- Certificate and Telegram custom images were missing. Replaced them with native
  system symbols while preserving their surrounding layouts and actions.
- Service icons can be absent for imported rule sets. Added a native fallback to
  AppIconView rather than displaying an empty image.
- Replaced one-line local card/sheet placeholders with an adaptive detailed card
  and build-information sheet linking to actual theme/icon settings. The card
  visibility preference is now reachable without publisher StoreKit membership.

## Preserved / still different

- Main HomeView, LaunchpadView, DashboardView navigation/layout implementations
  remain upstream code, not rewritten stubs. Only the capsule mark changed.
- Local-only storage and iCloud disabling are retained for portable self-signing.
  No Apple team, CloudKit or StoreKit entitlement was introduced.
- Watch/widget embedding remains disabled by earlier LX commits; not restored
  because that changes packaging/signing scope beyond the phone app theme.
- Private AnywhereRules/Rules.db is still unavailable. This audit does not claim
  bundled service/ad-block/country rules work. Imported rules remain separate.
- Project-level iOS minimum is 26.6; app and NE target overrides are 18.0;
  tests are 26.0. Existing CI overrides iOS minimum to 18.0. This audit does not
  claim iOS 18 compatibility based on that override, nor an iOS 27 UI test.
- All protocol/parser implementation files remain untouched by this UI work.

## Verification

`python3 scripts/test_lx_theme.py`: 4 tests passed, including distinct light/dark
variants, all icon/preview files, membership-independent theme editing and two
runs of configure in an isolated temporary fixture producing identical resource
bytes. The initial regression run failed on absent catalogs and gated editing.

`python3 scripts/test_lx_contract.py`: passed (source contracts only).
`git diff --check`: passed.
All six PNG files passed PNG chunk CRC checks and have 1024x1024 RGB/no-alpha
headers. Catalog contains 21 files. No CI was dispatched and no commit created.

This Linux environment has no swift/swiftc/xcodebuild, so these are static/resource
checks, **not** Swift compilation, actool validation, signed install, screenshots,
or iOS 18/26/27 runtime validation. Parent integration must run the actual Xcode
build and light/dark simulator/device interaction checks before release.
