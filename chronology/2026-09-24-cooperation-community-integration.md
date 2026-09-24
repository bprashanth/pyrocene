# Three-team Cooperation enters the main game

Baseline / rollback checkpoint: `f45226e`. User approved integrating Community,
hiding Negligence and preserving the main map/fire look. Do not integrate these
mechanics into Combined until the next discussion.

## Changes

- Main `/round.html` now offers Removal, Ecologist and Community. Community
  chooses nursery A, shade-grown coffee B or pasture grazing C. Investment is
  numeric; community returns and forest health remain qualitative.
- Coffee replaces cupuaçu as a familiar example. Generic game copy, with
  [WeForest/IDESAM's coffee-and-native-tree work](https://www.weforest.org/programmes/special-projects/apui/)
  in Sources. Prices, crop shelter effects and harvest timing are game assumptions.
- Three private proposals, shared finances and land-use conflicts use the tested
  prototype store. The room resolves coffee/native-restoration or pasture/native-
  restoration conflicts before committing. Teams can revise during discussion.
- Survey any active square. Inventory, dispersal records and survey clues use
  the tested fuel composition: damp invasive-free flanks beside C, grass in C
  and the openings ahead. Height colour is not a fuel classification.
- Only fire arrival data and survey contents were brought over. Main rendering
  uses `RoundForest` directly. No changes to `round-render.mjs`, its height
  palette or fire shaders/blending. The prototype's darker scar rendering is
  NOT used in the main game. The forward-biased 20-minute propagation uses
  continuous fuel/treatment edges rather than square-shaped fuel caps.
- Existing Hazel role modal, structure lab, species records, Recap and camera
  views remain. A/B/C recovery previews in discussion do not change proposals.
- Expedition links include three teams. Entering Cooperation retains their
  capabilities. A host return to Expedition resets the shared proposals and
  carries connected team tabs back; tokens remain valid. A team cannot reset
  other teams' work. Combined saves are not touched.
- Negligence is absent from default menus. `/round.html?negligence=1` explicitly
  restores the old two-team Cooperation -> Negligence sequence. Flagged links
  stay flagged. Old modules and the two-role store remain intact.
- Combined mechanics and rendering remain unchanged. Its menu entry is still
  direct and carries a return link to the shared game.

## Files and boundaries

`round-entry.mjs` chooses current Cooperation or archived `round.mjs`.
`cooperation.mjs` supplies the shell, `cooperation-briefing.mjs` the editable
copy, `community_cooperation/app.mjs` the controller and `game-features.mjs`
the archive flag. The controller selects the original renderer in the main
shell. Do not replace it with CommunityForest when refactoring.

New modules are included in both server and portable-package allowlists.
Old two-role room links are not converted into three-role plans: start a fresh
`/round.html`. Rooms expire on server restart. Prototype routes remain pending
review and can later be retired. No Combined save migration is needed.

## Verification

Real UI playthroughs cover role introductions, nursery/coffee/grazing, conflicts,
private team links, revision/commit/reload, A/B/C previews, young versus mature
recovery, paired fire, Expedition entry/reset, species dispersal, structure,
arbitrary flank inspection, Recap and unchanged Combined entry. The integration
suite also runs with WebGL disabled. The archive flag is played through old
Cooperation into Negligence, not merely checked for a visible menu item.

Screenshots outside git:
`/mnt/seagate/models/pyrocene/stage4/qa-cooperation-integrated/`.
See `community-briefing.png`, `community-coffee.png`, `C-close-fuel.png`,
`survey-flank.png`, `C-structure.png`, `without-plan-original-fire.png`,
`restored-C-original-fire.png`, `laptop-small-ignition.png` and
`laptop-grazing-spread.png`. Software captures have a `software-` prefix.

```
python3 -m unittest stage4.test_cooperation -v
python3 -m unittest stage4.community_cooperation.test_store stage4.community_cooperation.test_play -v
node --test stage4/community_cooperation/test_model.mjs stage4/test_round_model.mjs
python3 -m unittest stage4.test_delivery stage4.test_shared_round -v
python3 -m stage4.serve --check
```

Scoped revert of the integration checkpoint returns to `f45226e`. Do not reset
unrelated recap/concept/partner notes. Large scan assets and QA images remain
outside git. Restart only Stage 4 to load new allowlists; other stages need not
be stopped. Existing in-memory test rooms will expire on that restart.

Deployment: refreshed Stage 4 on 8024 and its comparison preview on 8036. No
other stage processes were stopped. Played all three roles on live 8024 through
commit and fire, confirmed the RoundForest renderer, coffee copy and hidden
Negligence, and captured `live-8024-coffee.png` / `live-8024-fire.png` without
browser page errors. A normal `run.sh` start includes the latest integration.
The automated integration suite passed 13 WebGL/software playthroughs; the final
survey-note consistency change also passed in both renderers. Prototype suite:
18 passing store/browser tests. Model suites: 11 passing tests. Delivery,
archived room rules and an archived browser playthrough: 12 passing tests.
