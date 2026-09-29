# Event fixes: push checkpoint

The user confirmed the public game works after `b45e598` (HTTPS actions and
software-rendered species overlays). The preceding deployment is `ff26003`.
The tested game mechanics and layout are unchanged by this housekeeping step.

Added ignores for root `output/` (2.7 GB of generated marketing/media artifacts),
Cloudflare's local configuration directory, organiser credential files and HAR /
packet captures, which can contain authentication or private team links. Existing
rules already exclude raw scans, large media, delivery archives, private keys,
environment files and browser auth-state files. No local files were deleted.

The live organiser secret remains outside the repo in
`~/.config/pyrocene/gm-credentials`. Only its location, not its value, is documented.
New game/deployment commits contain source, tests and text documentation, not
new media. Existing deliberately tracked portraits and lab assets are unchanged;
ignore rules do not remove files already tracked by git.

Other-agent Lore work and narrative drafts were already uncommitted. They were
left untouched and are not part of this game-fix checkpoint. Pushing this branch
does not include those working-tree files. Runtime forest/media assets still live
outside git, so the checkout by itself is not a complete offline asset bundle.

Origin refs were refreshed for the audit. This local branch has no upstream yet;
publish it explicitly with `git push -u origin stage4_recap`. No push, force push,
history rewrite, service restart or Cloudflare change was made during this check.

Audit: all 234 unpublished Git blobs were checked, including earlier versions in
the unpushed commits. The largest was 47,990 bytes. Pattern checks found no private
keys, recognised API tokens, JWTs or credential-bearing HTTP URLs. This is a
targeted secret-pattern check, not a guarantee against every possible secret.
The live organiser credential has mode 0600. Ignore checks passed for generated
output, screenshots, Cloudflare configuration, organiser credentials, HAR files,
environment overrides and PEM keys. No files under `output/` or `stage4/assets/`
are tracked. The existing source/test checkpoint passed 12 regression tests;
this commit changes only ignore rules and documentation.
