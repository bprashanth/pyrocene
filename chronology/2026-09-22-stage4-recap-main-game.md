# Recap enters the main game; the stewardship mission waits

Baseline: `355dae3`. User asked to mark the forest edge, shorten Forest Stewards,
use India and Amazon examples without an advertisement-like company biography,
and integrate Recap into the accepted game.

The last page now has three paragraphs: a short question, combined NTFP and
agroforestry explanation, and the shared livelihood challenge illustrated by
Aadhimalai/Keystone and IDESAM/WeForest. Last Forest's line and source are removed.
A dashed yellow forest-edge annotation marks the exposed transition on the last
point-cloud map. It is illustrative, not a surveyed vegetation boundary.

Sources checked: [Aadhimalai coffee](https://aadhimalai.in/coffee/) describes
tribal-grown coffee with shade trees and mixed crops;
[WeForest's Apuí account](https://www.weforest.org/blog/special-projects/coffee-helping-reforest-amazon/)
documents its coffee-agroforestry partnership with IDESAM in Amazonas. These
examples do not establish a measured fire-prevention rate.

Recap is now a stage-menu option in Expedition, Cooperation, Negligence and
Combined. It opens in place and Finish returns to the exact current map. The
shared-room state, private run, funds, actions and view are not replaced. It
does not load the prototype or navigate to another server.

Canonical module moved into the already-served `stage4/play-briefing.mjs`, beside
the existing BRIEFINGS export. Recap CSS moved to `play-flow.css`. The old
`community/prelude.mjs` only re-exports for compatibility. This avoids restarting
8024/8033 and losing live in-memory rooms. Do not introduce new static paths on
those running servers without considering their frozen allowlists.

The final community/stewardship mission remains explicitly deferred. The old
prototype at `/community/#prototype=1` is unchanged and remains a disposable
experiment. Later discussion may replace Finish with a last-stage transition.
`narrative/GAME_DESIGN.md` and `.prompt/stage4_handoff.md` record that boundary.

Verification includes live browser entry/exit on 8033 Combined and 8024 shared
views, screenshot review of the marked edge, and an automated unchanged-state
test. A Cursor low-model CLI review was attempted but timed out without output;
no independent review result is claimed.

Validation: 17 existing Community/Combined browser tests passed, plus the new
main Recap unchanged-state test. Live entry/exit checks on 8033 Combined and
8024 shared/expedition pages reported no JavaScript errors. The forest-edge
screenshot was inspected. The handoff is intentionally force-added because
`.prompt/` is normally ignored; no other ignored prompt files are staged.
