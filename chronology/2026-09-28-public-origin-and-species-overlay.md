# Public stage navigation and fallback species map

Follow-up to [managed deployment](2026-09-28-managed-event-gateway.md).
Previous committed checkpoint: `ff26003`. No gameplay rules changed.

Two screenshots (`/tmp/found.png`, `/tmp/found2.png`) exposed gaps in the initial
deployment tests: species mapping with WebGL disabled, and browser action POSTs
over HTTPS rather than local HTTP.

## Species locations

The species query worked and counted matching patches, but ExpeditionForest's
CPU point-cloud drawing override never drew the match polygons. The parent
renderer had a fixed overhead-image overlay, unsuitable for the newer draggable
camera. The fallback now projects the same match polygons as the WebGL renderer
through the live camera, using the existing amber palette. Changing or clearing
the species selection invalidates the drawing cache even if the camera is still.
Close view continues to hide the overlay. No inventory or species placement changed.

## HTTPS stage entry

The gateway forwarded the browser's HTTPS Origin to the HTTP forest backend.
The backend intentionally compares Origin with `http://Host`, so creating a
room failed with `origin does not match this server`. Initial local HTTP browser
tests did not expose this.

The gateway now validates an exact HTTP/HTTPS same-host Origin before expressing
it in the internal HTTP transport. The backend retains its own check. Other
hosts, null origins, non-HTTP schemes and malformed origins remain rejected;
forwarded headers do not determine trust. Only the gateway was restarted, leaving
Lore and all shared game backends running. Stage 4 JS is served from disk.

An earlier route issue was diagnosed separately: the tunnel's plain `lore` regex
matched `explore.css` and `explore-render.mjs`. Tunnel logs and backend 404s showed
those prefixed requests bypassing the gateway. The required rule is
`^/lore(/.*)?$`. The service README now explicitly warns against the loose match.
Cloudflare configuration is user-owned; no Access or tunnel settings were changed.

## Checks

- Seven gateway checks pass, including real HTTPS-origin POST headers and
  rejection of unrelated origins and spoofed forwarded headers.
- Visible-control browser tests discover a plant in C2, find its locations,
  drag the map, and clear highlights with WebGL disabled. Both direct backend
  and `/stage4/` gateway paths pass. Pixel checks verify actual amber drawing,
  not merely the matching-place count.
- A temporary local TLS gateway and real HTTPS browser run enter The Players
  from Start Here and load its role briefing. No page errors occur. This tests
  the browser-generated HTTPS Origin without bypassing public Cloudflare login.
- Live gateway POST with Host `pyrocene.idli.cc` and its HTTPS Origin returns 200.
- Screenshots inspected: `/tmp/pyrocene-event-qa/species-matches-direct-no-webgl.png`,
  `species-matches-gateway-no-webgl.png` and `https-players-entry.png`.
- The full gateway/browser suite passed all 12 tests in 69 seconds. An earlier
  run hit a transient Chromium screenshot-capture error on the launcher; the
  two targeted regression tests passed independently and the full rerun passed.

Reload the page to receive the renderer fix; no browser acceleration setting
change is required. Existing discoveries and rooms are not reset by deployment.
