# Community: an isolated Stage 4 experiment

Live prototype: **http://100.82.28.38:8035/community/#fresh=1**.
Accepted Combined game: **http://100.82.28.38:8033/strategy.html**.

This asks a different question from Combined: can a locally maintained buffer
help unfinished native restoration survive at the exposed forest edge?
It does not change Cooperation, Negligence or Combined. Hazel's concluding
page is deferred. Nothing is imported from or written into a saved Combined run.

## Play

Choose Shade crops or Seed nursery, then Begin. The dashed outlines mark two
already-cleared buffer gaps. You can start a partnership there, plant native
forest instead, or spend the grant elsewhere. Keep the two young native plots
behind the buffer alive until their canopies close.

- Start with 18 project credits and four Unstable plots. Capacity is five.
- Each action takes six months. Close view and plant records are free.
- Partnership costs 5 per buffer. Weeding costs 1. Native restoration costs 6.
- Local income pays local tending. It never becomes extra project credits.
- Fire can cross, damage or destroy a buffer. Shade and tending reduce risk;
  they are not a guarantee.
- Replay keeps the same seed for comparisons. New weather chooses a new seed.
  Both targets closing offers an early finish. Keep exploring continues up to
  the 12-year limit without repeatedly interrupting you.

The fixed fixture is E10/F10 boundary fuel, E9/F9 buffer gaps, E8/F8 young
native planting, and E7/F7 standing forest. All other active squares remain
selectable. Only the two buffer gaps can start this prototype's partnership.
The two young targets are already planted, so their immediate care action is
**Weed**, not Restore. After fire kills planting, Restore becomes useful again.

## Two versions of the same idea

| Enterprise | First income | Tending per season | Shade limit | Tradeoff |
| --- | --- | --- | --- | --- |
| Seed nursery | First season | 1.15 local credits | 48% | Early income, less shelter |
| Cupuaçu under mixed shade | Third season | 1.35 local credits | 62% | Early care gap, stronger later shade |

Base seasonal earnings are 1.35 and 2.2 respectively, with seeded variation
of ±14%. These are balance parameters, not yield or income estimates.
The nursery represents a seed-collection and plant-raising enterprise with a
managed shaded buffer, not nursery structures measured by the point cloud.

The association pays as much tending as its reserve allows. More paid care
means less grass and better shade development. Surplus remains in its reserve.
If fire destroys a buffer, that reserve contributes first to rebuilding; the
project pays only the shortfall. There are no recurring grants or carbon
payments. Local revenue has buyers as an explicit scenario assumption.

Native canopy closure and an established managed buffer are different outcomes.
Only native closure counts toward the two-plot goal. Buffers leave Unstable
plots at 80% of their enterprise's shade limit. Their strip fill measures progress
toward that establishment threshold, while the selected-patch panel shows actual
shade cover. Fire damage below that threshold puts them back on the strip.

## What is real and what is simulated

The forest uses the existing point-cloud renderer, measured scan fragments,
species records and dispersal/germination panels. The new buffer's crop placement,
canopy development and accounts are simulated. This is not a scan of a cupuaçu
farm or seed nursery. Community planting is rendered as growing low vegetation,
not an instantly mature forest or a flat illustration.

The model reuses Combined's connected-fire and restoration rules. It adds a
seeded boundary ignition opportunity after two setup turns, alongside the
existing fire process. A season can contain both fires; the UI displays both.
This is not a historical burn-scar reconstruction or calibrated prediction.
Combined's simplified rule that closed restored canopy stops spread remains a
game rule, not a claim of fireproof rainforest.

Amazon references supporting the enterprise and management ideas:

- [Embrapa: Desenvolver sem devastar](https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/918498/1/FolderDesenvolversemdevastar.pdf): agroforestry options in the Transamazon, including cupuaçu and other shade-associated crops.
- [Xingu Seed Network: Muvuca de sementes](https://www.sementesdoxingu.org.br/muvuca-de-sementes/): seed collection linked to restoration demand and orders. This supports the livelihood idea, not the game's payment schedule.
- [Xingu Seed Network: O que é](https://www.sementesdoxingu.org.br/o-que-e/): community organisation and livelihoods, rather than treating residents as a free maintenance service.
- [IPAM: local fire-management strategies in Pará](https://ipam.org.br/workshops-strengthen-local-fire-management-strategies-in-para/): community participation, production and fire prevention.

These sources do **not** establish the numeric shade caps, risk reduction or
success rates used here. Secure access, community agreement, willing buyers and
available labour are assumed. Land rights, market failure, labour allocation,
benefit-sharing and changing climate would matter in a real intervention. They
are deliberately not extra game systems in this first test.

## Playtesting and findings

The default browser seed is **991**, selected to make the edge-care tradeoff
visible. It is not an unseen bonus for choosing a particular option.

Actual browser play used visible weed readings and enabled buttons, not future
fire outcomes. Fund both buffers, weed the young native plots when weeds reach
30%, and replant burned targets if affordable:

- Shade crops: both targets closed by year 3.5; 5 project credits remained.
  Local income had paid 12.15 credits of tending. 53 landscape plots had burned.
- Nursery: both targets closed by year 3.5; 5 project credits remained.
  Local income had paid 14.95 credits of tending. 53 landscape plots had burned.
- No buffers, with native care and affordable replanting: F8 burned repeatedly.
  At year 12 only one target was closed; 3 credits remained, with 69 plots burned.

That is one paired example, not proof of balance. Reproducible model probes use
a simpler policy: fund both buffers if applicable, weed young targets at 30%,
otherwise wait. This policy does not replant failed targets or raise extra cash.

| Policy | Both recovered, seeds 1–100 | Both recovered, held-out seeds 1001–1100 |
| --- | --- | --- |
| Wait throughout | 0/100 | 0/100 |
| Manual native care | 62/100 | 57/100 |
| Nursery + native care | 78/100 | 74/100 |
| Shade crops + native care | 74/100 | 71/100 |

These are simulated balance checks, not real-world restoration effectiveness.
Nursery currently has a small advantage under this simple policy. The variants
are not yet balanced as equally strong competitive choices. A buffer can still
fail; native care remains necessary; success at the two targets does not mean
the rest of the landscape was saved.

[Player findings](player-findings.md) separates early snapshots, Cursor's actual
low-model choices, deterministic policies and browser results. Claude Haiku
authenticated but play prompts timed out; no Claude match is claimed. No room
of participants has tested this prototype yet.

## Verify and run

From the repository root:

```sh
python3 -m stage4.serve --host 0.0.0.0 --port 8035
node --test stage4/community/test_model.mjs
node stage4/community/probes.mjs 100
node stage4/community/probes.mjs 100 1001
python3 -m unittest stage4.test_community stage4.test_strategy stage4.test_delivery -v
```

Browser tests exercise real clicks, replay, early completion, Close view, species
tabs, refresh persistence, disabled-WebGL fallback and preservation of the Combined
save. Screenshots live outside git at
`/mnt/seagate/models/pyrocene/stage4/qa-community/`. In particular compare
`play-991-shade-result.png`, `play-991-none-result.png` and
`play-991-shade-buffer-close.png`.

## Isolation, rollback and later migration

All new gameplay lives in this directory. `model.mjs` adapts the unchanged
`../strategy-model.mjs`; `render.mjs` subclasses its renderer. Shared changes are
only route and package allowlists. No main-menu entry has been added.

The live experiment has its own server on 8035, so shared-room servers did not
need to restart. On that port, Back to Combined points to the existing 8033
server. Portable/test deployments use their own origin. Community saves use
their own sessionStorage key, `pyrocene-community:community-1`.

Baseline tag: `stage4-before-community` at `b8f50f8`. Prototype checkpoint:
`stage4-community-v0`. The accepted game can be used directly without reverting
anything. If removing the experiment, revert its scoped commit rather than
resetting the worktree or discarding unrelated recap edits.

Candidates to move later, **after review**:

1. An opt-in partnership on already-degraded edge land.
2. A separate local care account that survives the initial project grant.
3. Managed shade affecting the same grass and fire variables as restoration.
4. A buffer returning to the ledger after damage and using reserves to rebuild.

Do not copy the fixed E/F fixture, selected seed, two-target goal or extra
boundary ignitions into Combined without a new balance test. A real continuation
needs an explicit snapshot import and appropriate buffer eligibility; this
prototype intentionally does neither.
