# Hazel before Community: local ignitions and a connected scar

Starting checkpoint: `c4e5ac5` / `stage4-community-v0`.

The user wanted to develop the explanation before revising Community itself.
Combined's sporadic fires interrupt work around exposed land. Cooperation's
larger fire demonstrates a connected route from outside into the forest and
the value of restoring its narrow link. These are two different lessons.

Clarification during work: "small" does not mean limited to one or two squares.
A fire may cross several plots while still remaining local rather than forming
Cooperation's long route into the interior. **No Combined, Cooperation or
Community mechanics were changed.** We did not make restoration at the edge
impossible or guarantee that interior planting always succeeds.

## Two screens

1. Hazel explains repeated disturbance at the edge and the use of fire in
   pasture management and preparing fields. Separate pulsing ignition marks
   appear over the lower part of the measured point-cloud footprint.
2. Hazel explains dry-fuel connectivity and weather. The picture uses the
   actual baseline `runFire()` result from Cooperation, with patch C outlined
   as the narrow link. It ends with who will care for the edge after the grant.

The existing `hazel.png` is unchanged. Green filtering and scan lines match the
existing briefings. Text types out, but reduced-motion mode displays it directly.
Next/Back/Continue are the only progression controls. Continue opens the
unchanged shade-crop / nursery introduction. Replaying Community itself does
not force the prelude again. `#prelude=1` explicitly reopens it.

The map is a lightweight Canvas drawing from already-loaded measured points.
No second WebGL scene, new raster asset or extra forest download is introduced.
The ignition marks are illustrative. The scar is simulated, not historical NBR
and not a reconstruction of an individual player's Combined run. Captions and
the small Sources disclosure distinguish these clearly.

## Evidence and restraint

Combined already weights ignition by exposed fuel, past disturbance and the
existing human-use flag. Growing canopy reduces transmission. Original closed
forest can receive an edge scorch, but does not relay that fire onward. Nearby
native cover also helps young planting grow. Those rules were inspected, not
retuned for this explanation.

The narration uses Amazon context rather than carrying the Indian percentages
and case studies from `stage4/v2_recap.md` across regions. It does not imply that
every fire is a livelihood fire or that the game diagnoses an ignition's cause.

- [NASA: From Forest to Field](https://science.nasa.gov/earth/earth-observatory/from-forest-to-field-how-fire-is-transforming-the-amazon/) describes agricultural and land-clearing fires escaping into neighbouring forest and the importance of canopy damage and drying.
- [IPAM: Amazon on Fire](https://ipam.org.br/bibliotecas/technical-note-amazon-on-fire/) distinguishes management, deforestation and forest fires and discusses drought conditions.

The prelude does not claim that a closed forest or agroforestry is fireproof.
It does not add a fire ban, a prescribed-burn mechanic or any community actions.
The nursery and shade-crop mechanics remain parked for the next discussion.

## Verification and rollback

Browser checks cover both screens, Back, passage to the existing enterprise
choice, unchanged turn/credits/plots, and all existing Community flows. Screenshots
are outside git in `/mnt/seagate/models/pyrocene/stage4/qa-community/`, named
`hazel-prelude-edge-live.png`, `hazel-prelude-scar-live.png` and
`hazel-prelude-small-screen.png`. The in-app browser was unavailable, so the
checked fallback was Python Playwright, including a normal-motion live run.

Validation: 7 Community browser tests, 6 delivery tests and 29 targeted model
tests passed. Screenshot review moved two initial illustration marks onto the
actual lower footprint and increased their contrast against the pink returns.

The change is confined to `stage4/community/prelude.mjs`, Community presentation
and its tests, plus static-file serving/packaging allowlists and these notes.
The private 8035 server was restarted to load the new file allowlist; shared-room
servers were left running. User recap edits remain outside this checkpoint.
Revert the prelude commit to return to `stage4-community-v0`; no saved game model
migration is required.
