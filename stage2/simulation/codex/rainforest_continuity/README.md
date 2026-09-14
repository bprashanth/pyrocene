# Rainforest continuity film studies

These two silent candidates continue the frozen 56 second LiDAR film without
changing biome or visual language. They use near black space, measured returns,
height colors, slow camera movement, one sentence and one typed location. No
generated forest imagery is used.

## Candidates

- `liana-structure.mp4` compares two real 2019 Nouragues airborne LiDAR tiles.
  About one percent of one tile and about 72 percent of the other overlap the
  liana zone mapped in 2012. It then moves to a published terrestrial LiDAR
  classifier image in which model-labelled liana stems are recolored magenta.
- `invasive-identity.mp4` uses published terrestrial LiDAR cross-sections from
  wet Hawaiian rainforest grouped by measured strawberry guava abundance. It
  then enters three co-registered panels from one published 53 hectare Hawaiian
  forest stand: LiDAR height, spectral composition, and invasive tree detection.
  The footprint and crop remain fixed so spatial features can be followed.

These are edit modules rather than finals. The old dry-forest hyperspectral set
and the unsupported gap-light experiment are retired and absent from the active
gallery.

## Edit every word on screen

All renderer-added words are in [`captions.json`](captions.json). The renderer
rejects periods, em dashes, arrows and middle dots. Edit the JSON and run
[`rerender.sh`](rerender.sh). The frozen LiDAR master is never an output target.

## Source chain

The new raw sources are stored under
`/mnt/seagate/videos/pyrocene/data/rainforest-continuity/` and render artifacts
under `/mnt/seagate/videos/pyrocene/rainforest-continuity/artifacts/`.

- Nouragues intact TLS: Zenodo record 4661301, CC BY 4.0.
- Nouragues liana zone and 2012 canopy-height model: Dryad DOI
  `10.5061/dryad.1pc19`, CC0.
- Nouragues 2019 ALS: CEDA DOI `10.5285/7bdc5bfc06264802be34f918597150e8`,
  CC BY 4.0.
- Liana stem extraction: Krishnamoorthy et al 2019, published classifier figure.
- Hawaiian invasive structure: Seely et al 2025, CC BY 4.0 figure.
- Hawaiian invasive imaging spectroscopy: Asner et al 2008 Figure 3, published
  LiDAR and AVIRIS processing layers for one 53 hectare stand.

The exact source and claim limits are in
[`EVIDENCE_BOUNDARIES.md`](EVIDENCE_BOUNDARIES.md). The Asner 2008 figure is for
internal editorial review. Confirm public-performance or figure-reuse permission
before promoting that module.

## Reproduce

The environment needs Python 3 with NumPy, Pillow, laspy and lazrs, plus FFmpeg.

```bash
PYROCENE_RAINFOREST_PYTHON=/path/to/python ./rerender.sh
```

Outputs are deterministic 1920 by 1080 H.264 at 24 frames per second with no
audio. `prepare_sources.py` samples only source returns and records hashes and
transforms in sibling manifests. `render_candidates.py` pipes fixed-time RGB
frames directly to FFmpeg.

## Scientific boundaries

- The 2019 airborne tiles are compared against a liana zone mapped in 2012.
  They are not point-level liana labels and are not a controlled time series.
- The liana stem close-up is a recolored published classifier result. It is not
  an open raw point cloud.
- The Seely structural transects and the Asner fused-data sequence are separate
  Hawaiian studies. The transition between those studies is conceptual.
- Within the Asner sequence, the LiDAR height, spectral composition, and final
  invasive detection panels are co-registered views of the same 53 hectare
  stand. A common crop excludes publication labels without inventing pixels.
- Lianas are a structural rainforest example. They are not presented as
  non-native plants or as proof of fuel.
- LiDAR geometry does not measure fuel chemistry, moisture or flammability.
- The Asner map panels are enlarged from the best available published figure.
  No generative upscaling or fabricated spatial detail is used.
