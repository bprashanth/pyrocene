# Cooperation: direct room editing and quieter projection

Baseline: `506e5ac`. Main Cooperation only; Combined, archived Negligence and
the prototype's comparison controls remain unchanged.

- Ecologist A now describes healthy natives and arriving invasives, with careful
  clearing before restoration. B describes degraded open land mixed with both.
- Recap I keeps the first sentence about removal, drops the returning-crews
  sentence, and uses four bullets for restoration, coffee, nursery buyers and
  debt. The “game estimates” footer wording is removed.
- Dots still represent ten-year earnings/health, not year-zero balances. The
  caption now says plans are **chosen at the start**, projected without wildfire
  destruction. This preserves the intended explanation without mislabelling the
  chart's existing time horizon. Debt repayment is explained, not automated;
  no interest/default mechanic was added.
- Room opens directly with one editable dropdown per role. Empty choices say
  Choose. No Reveal/Edit gate. Commit stays disabled for missing choices or
  conflicting land use. Host can commit a complete compatible plan directly
  from survey; the old reveal API remains for the prototype. Private teams still
  cannot inspect other proposals before commitment, unless explicitly revealed.
- Commit opens Recap I then the projection; Revise reopens the same dropdowns.
  Main With/Without plan buttons are removed, not just hidden. Old prototype
  comparison buttons still function through guarded shared-controller bindings.
- Returning weeds use a continuous cosine fade: cleared at year 0, fullest at
  year 4, cleared again by year 8, returning by year 10. There is no year-boundary
  flash. The fuel field uses the same curve. The recap counts one completed
  later clearance, not the previous three, so income/native-damage accounting
  agrees with the slower displayed cadence. This is an illustrative cycle,
  not a claim that physical removal takes four years. Sources is updated.

Verification uses real browser clicks and keyboard sliders with read-only
diagnostics. The browser skill found no available in-app browser; repo Python
Playwright is the fallback. Tests cover direct empty-room selection, conflicts,
debt, commit/revise/recommit, four recap bullets, missing comparison controls,
continuous weed/fuel cover, private team links, and WebGL-disabled rendering.

Screenshots outside git:
`/mnt/seagate/models/pyrocene/stage4/qa-cooperation-integrated/`:
`direct-room-edit.png`, `debt-recap.png`, `joint-projection-year-four.png`,
`joint-projection-year-eight.png`, plus software variants.

Rollback: revert this scoped checkpoint; never reset the user's unrelated notes.
The backend commit rule needs a Stage 4 process restart, not just a page refresh.

Verification completed: 17 main browser tests passed with WebGL and software
rendering; eight JS model tests and 19 store/delivery/archived-room tests passed.
The prototype suite caught a disabled Reveal button on conflicting plans. Fixed
that prototype-only gate and reran its conflict-resolution playthrough to a pass;
the other ten prototype browser cases passed. Live 8024 was also played with
direct Room commitment and an actual 100-step mouse drag across Projection, with
no browser errors. Laptop Recap screenshot was inspected at 1280 x 800.

Stage 4 ports 8024 and 8036 were restarted for the backend rule. Existing room
links expired. Other stages were left running. `run.sh` includes these changes.
