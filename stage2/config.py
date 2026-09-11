"""Every tunable for Stage 2 in one place. See README.md for what each does."""

CONFIG = {
    # --- the room ---------------------------------------------------------
    "min_players": 6,          # 2 lantana + ecologist + ranger + 2 natives
    "lantana_ratio": 4,        # one lantana per this many players, minimum 2
    "max_rounds": 8,
    "team_loss": False,        # losing both ecologist and ranger ends stage 1, but here
                               # the room plays on blind: fire and time decide it           # reaching this is a loss: sheltering forever is not a win
    "loss_health": 35,
    "village_clearance": 5,    # keep homes this far from the starting infestation
    "village_defend_range": 8, # only trench around the homes if fuel is this close
    "village_loss": True,      # fire reaching the homes ends it: the one thing the room
                               # must spend a night defending rather than out-hunt         # forest health below this is a loss

    # --- the map ----------------------------------------------------------
    "owned_fraction": 0.66,    # share of land split into player patches; the rest is commons
    "native_loss_core": 4,     # cells of a lost native stand that lantana takes at once;
                               # the rest it has to grow into
    "lantana_core": 4,         # cells of a lantana player's territory that start infested;
                               # the rest is forest they have to grow into
    "initial_stage_age": (0, 1),   # staggers when each core goes dense

    # --- lantana growth (per neighbouring cell, per round) ----------------
    "growth_established": 0.16,
    "growth_dense": 0.24,
    "growth_wind_mult": 1.6,   # downwind neighbour
    "growth_bare_mult": 1.7,   # bare ground is taken fastest
    "orphan_mult": 0.6,        # lantana with no living owner grows slower
    "age_to_established": 1,
    "age_to_dense": 2,

    # --- bare ground after a removal or a burn -----------------------------
    "bare_on_removal": True,   # False: an eliminated lantana patch turns straight to native
    "reinvade_p": 0.55,        # bare cell next to lantana: chance it is retaken
    "regen_p": 0.22,            # bare cell with no lantana nearby: chance it regrows native

    # --- fire ---------------------------------------------------------------
    # severity comes from the size of the largest connected dense cluster
    "sev_t1": 7,               # below this: severity 1
    "sev_t2": 18,              # below this: severity 2, else 3
    "spark_p": 0.6,            # with no dense lantana at all, chance of a small fire anyway
    "fire_cells": {1: 3, 2: 12, 3: 38},
    "fire_round_ramp": 0.22,   # each round past the first adds this much to the cap:
                               # a dry season wearing on, so late fires run further   # max cells burned per severity
    "fire_iters": 12,
    "fire_p_invasive": 0.85,
    "fire_p_native": 0.40,
    "fire_p_bare": 0.55,
    "fire_wind_mult": 1.4,

    # --- resilience ---------------------------------------------------------
    "line_reach": 3,           # how far beyond a dense cluster a line looks for something to protect
    "line_gap": 1,
    "line_cells": 10,         # trench cells dug per resilience night, hugging the asset             # cells between the cluster edge and the line
    "early_warning_caps_next_fire": False,   # discuss before turning on

    # --- projector pacing (ms per beat kind); STAGE2_FAST=1 zeroes all of these
    "hold_ms": {
        "round": 1200, "elimination": 2200, "line": 2600, "water": 1800,
        "warn": 2600, "growth": 2000, "ignite": 900, "spread": 380, "burn": 1200, "blocked": 2800,
        "aftermath": 3200, "quiet": 2200, "forecast": 3200, "ending": 0,
    },

    # --- the copied engine's own knobs we override for this stage ---------
    "engine": {
        "n_hotspots": 0, "initial_infest_radius": 0, "villages": 2,
        "events_on": False, "hill_blobs": 2, "roads": 1,
        "age_to_established": 1, "age_to_dense": 2,
        "unlock_level": 0,
    },
}
