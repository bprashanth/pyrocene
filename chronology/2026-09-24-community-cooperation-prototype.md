# Community cooperation, isolated first prototype

User approved prototyping three roles on Cooperation's A/B/C, with a compact
qualitative Community panel and land-use disagreement that the room must resolve.
Do not drop Negligence or alter Combined before reviewing this experiment.

Baseline: `67ee3fb`. Work lives in `stage4/community_cooperation/` and is exposed
at `/community-cooperation/`. Current preview is port 8036; a fresh normal run.sh
serves it on 8024 too. The existing 8024 process was not interrupted.

The default host can play all roles through the dropdown. Teams provides private
links for ecologist, removal and community plus the shared-room link. Each team
chooses one of the same three patches. After reveal, proposals can change until
the host commits a funded and land-compatible plan. The server rejects both
pasture/restoration C and cupuaçu/native-restoration B conflicts.

Community choices:

- A: nursery supply for A, high return only with an order for restoration A.
- B: cupuaçu beneath mixed shade, expensive, delayed return dependent on shelter.
- C: pasture preparation by burning, low investment, avoided bought-feed costs.

No numerical returns or health in Community survey. Investment remains numeric.
No leases, cattle trading, livelihood submenus or additional main-game level.

Fire no longer uses the accepted model's narrow ellipse in this prototype.
An irregular interpolated invasion field drives both low vegetation tint and
surface-fire spread. C has damp, non-invaded flanks which can be inspected. Its
connection to openings farther north matters. Bright fire cools to a muted scar.
Recovery age changes spread. The shared score now falls as area burns. This is
an authored scenario on measured scan geometry, not inferred historical fuels.

UI play found and fixed concurrent-proposal retries, stale responses, baseline
narration claiming shelter that was absent, and a stale fruit-income assessment
after fire reached the crop plot. Local Pokedex dispersal uses the same inventory
as the prototype; accepted-game species modules were not modified.

Evidence, exact assumptions, test commands, sample plan outcomes and screenshot
names are in [the prototype README](../stage4/community_cooperation/README.md).
Verification: 24 Python tests and 4 JavaScript model tests passed, including
seven browser playthrough/layout/software-rendering checks. The browser suite
was rerun after the final compact-layout pass. Server readiness and direct-script
startup checks also passed. Screenshots were opened and visually inspected.
Screenshots are under `/mnt/seagate/models/pyrocene/stage4/qa-community-cooperation/`,
not in git. Test the experience with a real room next; automated UI play does not
establish workshop fun or learning outcomes.

Preserved user files: `stage4/v2_recap.md`, `narrative/RECAP.md`,
`narrative/CONCEPT_NOTE.md`, `stage4/partner_note.md`.

Next review: does the grazing/restoration conflict prompt negotiation without
blaming the community? Are qualitative opportunities sufficiently informative?
Only after review decide which pieces to move into Cooperation and whether to
remove the separate Negligence level. The main game's current flow is unchanged.
