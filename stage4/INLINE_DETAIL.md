# Ground detail inside the map

The main expedition remains one map. Select a square and choose Close view.
The camera moves to the existing low close-view position. The airborne returns
inside that square sink and fade as measured ground-scan returns rise there.
All airborne geometry remains intact. The shader changes only the selected
sector. The surrounding cloud stays visible and retains its original colours.
Forest reverses the rise first, then moves back to the forest camera.

There is no separate TLS scene or scan/field-team confirmation. Species names
appear automatically. Selecting one records the discovery and opens a short
paragraph alongside the map. It covers native/invasive status, fallen-leaf
moisture, uses and frequency within this authored practice map. Frequency is
not a conservation-status claim. Uses are editable in `field-catalogue.json`
under `plainUse`, with the original longer records and sources retained.

Plot observations appear automatically as short paragraphs in the side panel.
The plot's scan, visit and displayed records are recorded together after the
detail loads. Reading a species note also records its displayed use. The
existing missions and paper recall remain reachable without the removed buttons.

## Display, not geographic registration

Airborne and TLS data are measured but come from different surveys. The former
horizontal-only stretch made plants unreadable and has been removed. The lower
eight metres of each crop now use a uniform 3x display scale. Three individual
ForestScan tree references supplement these narrow tiles, using uniform scales
to fit the square. Bright wood and softer leaves reveal branching. The original
files are unchanged. These are structural references, not species-identified
trees or a registered survey of the selected square. Their authored placement
must not be interpreted as an inventory. Eleven crops still vary the understorey.
`prepare_tree_structure.py` records source URLs, hashes and CC BY 4.0 attribution.
Species notes show independently identified reference photos through an in-app
green terminal treatment. Some photos depict a leaf, fruit or flower rather
than the whole plant. Species assignments and field observations remain authored.

## Animation and performance

Camera moves last 0.9 seconds. The detail rises over 1 second and sinks over
0.6 seconds. Reduced-motion mode skips both. A failed detail request leaves
the airborne map intact and allows a retry. Cached crops are reused. Temporary
display geometry is disposed on return. Automatic point reduction is ignored
while inspecting a square so it cannot remove surrounding dots mid-transition.

The non-WebGL expedition now projects measured points through the same camera
using Canvas2D. It samples approximately 22,000 airborne and up to 16,000 TLS
returns. Drag, zoom, selection, labels and the reversible detail still work.
It redraws only when the camera, selection or transition changes. It is less
dense than WebGL and still needs testing on the actual team laptops. The older
non-expedition routes keep their earlier fallback implementations.

## Verification

`test_inline.py` covers direct labels, plain notes, sink-before-pullback order,
revisits, a different square, reduced motion, failed-fetch retry and narrow
screens. A renderer test compares every airborne position before and after
detail and checks all transformed TLS returns stay inside the selected square.
The disabled-WebGL test verifies actual image change on drag and distance
change on scroll before opening and closing detail. It does not merely assert
that the fallback loads.

`test_expedition.py` follows the revised controls through field learning and
physical-map preparation. The memory and simulator rules are unchanged.
