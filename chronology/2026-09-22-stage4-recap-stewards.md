# Recap: livelihood fires, connectivity and Forest Stewards

Starting checkpoint: `b030523`. This replaces the two-screen Hazel prelude's
presentation, not any game mechanics.

The user asked to remove Hazel's picture, call the sequence Recap, expand the
livelihood examples, replace the narrow-link emphasis with fuel connectivity,
and end with Forest Stewards. The final community mission is deferred.

## Changes

- Three pages with the existing green point-cloud presentation, no portrait.
- "The last stage" replaces "Combined" in the opening paragraph.
- Page one includes the roughly 95% human-caused estimate, Mahua, tendu/beedi
  collection, and Amazon pasture management.
- Page two connects invasive fuel structure to what players saw in Close view.
  Yellow, dark-outlined dashed connections follow the authored Cooperation
  corridor over its simulated scar. This is a connectivity annotation, not an
  instruction to clear that whole route or a new fire simulation.
- Page three introduces forest livelihoods, agroforestry, Aadhimalai and Last
  Forest. Finish returns to Combined. No enterprise-choice screen follows.
- Each page has a Sources disclosure with claim-specific links and limitations.
- Existing Community gameplay remains at `/community/#prototype=1`. Replay URLs
  retain that flag. Recap visits cannot overwrite the prototype's saved run.

## Source checks that affected the supplied draft

The argument is retained, with corrections announced to the user before editing:

- [NIDM's 2013 report](https://nidm.gov.in/PDF/pubs/Forest%20Fire%202013.pdf)
  supports the commonly cited roughly 95% human-caused estimate and describes
  livelihood uses of fire. It does not establish a national numeric share for
  livelihood-related ignitions. Copy says "many", not "most", and Sources notes
  the historical nature of the estimate.
- [Farmers for Forests](https://wb-v2.farmersforforests.in/forest-protection)
  describes community fire prevention in Maharashtra. Its
  [public updates](https://www.linkedin.com/company/farmersforforests)
  describe paid fire-free Mahua collection work. It is not presented as promoting
  "good fires". [Telangana's report to the NGT](https://www.greentribunal.gov.in/sites/default/files/news_updates/OA%20205%20of%202024%20Report%20by%20R1.pdf)
  documents Mahua, tendu and grazing-related ignitions.
- Litter fire is not automatically safe under closed canopy, nor is an invaded
  plot guaranteed to produce a large fire. The text describes fuel and moisture
  changing the outcome, consistent with the cited ATREE and NASA material.
- [World Agroforestry](https://apps.worldagroforestry.org/Units/Library/Books/Book%2082/imperata%20grassland/html/3.3_grass.htm?n=16)
  describes maintained, productive greenbreaks and their limits. Agroforestry is
  not intrinsically fireproof. Fire lines can help stop spread, not guarantee it.
- NTFPs and agroforestry share a livelihood-and-care idea but are not identical
  practices. Recurring income depends on replenishment, rather than being
  promised "forever".
- [Aadhimalai](https://aadhimalai.in/) confirms its 2013 formation with Keystone
  support. [Last Forest](https://lastforest.in/pages/about-us) describes itself as
  a social enterprise connecting producers with markets, not a multinational
  corporation. No unsupported occupational breakdown was added.

## Verification

Desktop and small-screen screenshots checked in
`/mnt/seagate/models/pyrocene/stage4/qa-community/recap-live-{1,2,3}.png`
and `recap-stewards-small.png` (outside git). Browser tests cover all three
screens, Sources, Back, Finish, unchanged gameplay, and preserving a parked
prototype save even when the recap opens with another seed.

All eight Community browser tests passed. A separate live run checked typed
text and Sources with WebGL disabled. No browser JavaScript errors were reported.

The existing recap notes in `stage4/v2_recap.md` and `narrative/RECAP.md` belong
to the user and remain untouched. No shared-room server restart or model change
was required.
