# Strategy: private practice after the shared game

The accepted Cooperation / Negligence baseline is tagged
`stage4-before-strategy` (`f9b7511`). The pre-change record is
[the checkpoint chronology](../chronology/2026-09-21-stage4-before-strategy.md).
The shared round engine and its costs have not been replaced.

## Open it

Finish and commit Negligence, then select **Strategy** in the stage dropdown.
The planting, crew choice and remaining credits seed a private experiment.
Its actions never write back to the shared room. **Back to shared game** returns
to that room. Each browser tab keeps its own replay trace for refresh recovery.

For a fresh independent trial, open `strategy.html` on the Stage 4 server.
The development instance is <http://100.82.28.38:8033/strategy.html>.
The existing 8024 process is deliberately not restarted: it holds live room
state in memory. Its dropdown detects whether it can serve Strategy and uses
8033 if necessary. A newly started or portable server serves both on one port.

## The small loop

Choose a patch. Remove or restore. Six months pass, weeds return, trees grow
and a fire may spread. Looking around or opening a field record takes no time.
**Let six months pass** allows waiting without spending credits, but does not
pause those risks.

Removal opens a ledger entry. Restoring plants young trees. Remove on a young
planting means careful weeding, not another profitable harvest. Five open
entries prevent starting another clearing, not caring for an existing one.
An entry ends with canopy closure or reinvasion; these are recorded separately.
The fill in each ledger block means canopy progress, not remaining time.

The three advice cards change no rules or random probabilities:

- Rush opens and plants new ground quickly, leaving older work vulnerable.
- One at a time tends a planting while other fuel remains in the landscape.
- Anchor uses neighbouring forest to shelter planting and then spreads.

The experimental target is three restored canopies in 24 six-month actions.
The result also records burned plots and credits. There is no combined health
score and no claim that a closed canopy is fireproof. Replaying the same seed
keeps the same underlying weather and random draws. Changed vegetation can
change which fires catch and where they spread.

## Boundaries and evidence

Measured scan fragments provide the point-cloud material. Species locations,
plot states, growth, shelter effects, financial returns and fire probabilities
are authored game assumptions. The animated front inside a burned plot is
illustrative. Burned **plots**, not a falsely precise scar area, are shown to
players. This does not reproduce the 2023 burn scar or predict a real fire.

The ecological relationships have research support, but that does not validate
the numbers or six-month pace used here:

- [Silvério et al. 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3638439/):
  grass invasion, canopy opening and repeated fire interact.
- [Balch et al. 2015](https://doi.org/10.1093/biosci/biv106): repeated fire and
  drought can damage Amazon forest; closed canopy is not absolute protection.
- [Forest proximity and restoration at former Amazon mines](https://pmc.ncbi.nlm.nih.gov/articles/PMC9661946/):
  forest context and site conditions matter. This is a different setting,
  not a numerical calibration for our patches.

The native/invasive field guide and dispersal/germination panels are retained.
Their sources and illustrative habitat bands keep the accepted disclosures.
The dispersal inventory is a survey reference, not a measured seed-tracking
system or a new simulated animal population.

## Files and tests

All new gameplay is isolated in `strategy-model.mjs`. `strategy-render.mjs`
extends the existing point-cloud renderer without replacing its source arrays.
`strategy.mjs`, `strategy.html` and `strategy.css` own the private interface.
The only shared integration is navigation and the server/package allowlists.
Cooperation and Negligence retain their shared authority and proposal mechanics.

```sh
node --test stage4/test_strategy_model.mjs
node stage4/strategy-evaluate.mjs 100 1
node stage4/strategy-play.mjs 113 remove:C2 restore:C2 wait
python3 -m unittest stage4.test_strategy -v
```

See [strategy-trials](strategy-trials/README.md) for scripted calibration and
lower-model CLI play evidence. Scripted runs are balance probes. They are not
human enjoyment evidence. Browser tests cover the actual controls, Close view,
field records, structure, fire, replay, CPU rendering and private handoff.

To back out, revert the Strategy feature commit while retaining the checkpoint
commit. Do not reset the whole repository or delete the user's untracked
`v2_strategies.md`. Live room state is not in Git and disappears on server
restart, regardless of which code revision is checked out.
