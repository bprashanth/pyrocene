"""One scene, handed to every style.

The renderers never touch the game. They get this, and nothing else, so a new
style is a new file and no change anywhere upstream.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Scene:
    cols: int
    rows: int
    round: int = 0
    max_rounds: int = 8
    health: int = 100
    cover: dict = field(default_factory=dict)      # index -> forest|lantana|bare|water|village
    stage: dict = field(default_factory=dict)      # index -> 1..3 for lantana
    fireline: set = field(default_factory=set)
    hill: set = field(default_factory=set)
    road: set = field(default_factory=set)
    fire: set = field(default_factory=set)         # burning right now
    focus: set = field(default_factory=set)        # squares the room should watch
    halo: set = field(default_factory=set)         # ground lantana is pressing on
    held: set = field(default_factory=set)         # trench cells the fire ran into
    haze: bool = False                             # push everything but focus back
    title: str = ""
    note: str = ""

    def of(self, kind: str) -> set:
        return {i for i, k in self.cover.items() if k == kind}

    @property
    def land(self) -> set:
        return {i for i, k in self.cover.items() if k != "water"}

    def rc(self, i: int):
        return divmod(i, self.cols)


def from_view(view: dict, **overlay) -> Scene:
    """Build a scene from the game's own view plus one frame's overlays."""
    cover, stage, fl, hill, road = {}, {}, set(), set(), set()
    for c in view["cells"]:
        i = c["index"]
        cov = c.get("cover")
        cover[i] = {"native": "forest", "invasive": "lantana", "bare": "bare",
                    "water": "water", "village": "village"}.get(cov, "forest")
        if cov == "invasive":
            stage[i] = c.get("stage", 1)
        if c.get("fireline"):
            fl.add(i)
        if c.get("hill"):
            hill.add(i)
        if c.get("road"):
            road.add(i)
    return Scene(
        cols=view["cols"], rows=view["rows"],
        round=view.get("round", 0), max_rounds=view.get("max_rounds", 8),
        health=view.get("health", 100),
        cover=cover, stage=stage, fireline=fl, hill=hill, road=road,
        fire=set(overlay.get("fire") or []),
        focus=set(overlay.get("focus") or []),
        halo=set(overlay.get("halo") or []),
        held=set(overlay.get("held") or []),
        haze=bool(overlay.get("haze")),
        title=overlay.get("title", ""), note=overlay.get("note", ""),
    )
