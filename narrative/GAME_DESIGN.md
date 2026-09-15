# Game design

How field knowledge about lantana and fire becomes an evening a room can play.

This is the index board for the whole thing. Read it top to bottom and you get
the arc in order. Every section points at the code and the notes that build that
piece. Nothing here is a plan for the future. It describes what is built.

---

## 1. The problem we are solving

Ecologists know things that do not travel. A person who has spent ten years
watching lantana take a forest can tell you that the dangerous moment is not
when there is a lot of it. It is when the separate patches join up. They can
tell you that clearing a patch and walking away leaves bare ground that gets
taken again. They can tell you that fire is a symptom and that the cheap moment
to act passed years ago.

Say that from a stage and people nod. Nothing sticks.

The bet here is that a room will keep a thing it worked out for itself under
mild pressure with other people watching. So we do not explain the ecology. We
build a landscape that behaves like the real one and let a room push on it until
it pushes back.

## 2. The one idea

**Fire is not the problem. Connected fuel is the problem. By the time the fuel
is connected your options have got expensive.**

Everything below exists to deliver that one sentence, and to deliver it as
something a room did rather than something they were told.

A second idea rides along with it. **You cannot act on what you did not take the
time to see.** That one belongs to the single player game at the end.

## 3. The arc

Five pieces, in the order a room meets them. Roughly two hours end to end.

| | Piece | Where | What the room does | What they end up knowing |
|---|---|---|---|---|
| 1 | Hidden lantana | `stage2/` at `--stage 1` | Plays Mafia with ecological roles | Their votes changed a landscape they were not watching |
| 2 | Ignition | `stage2/` at `--stage 2` | Same game plus fire and one choice a night | Separate patches joined up and then it was too late to hunt |
| 3 | The lab | `stage2/simulation/claude/lab/` | Watches their own board burned by real fire models | The game was not lying, and a plan would have changed it |
| 4 | The films | `stage2/simulation/codex/` | Watches real remote sensing of real forests | This is how anyone would know any of it |
| 5 | The online game | `web/`, `terminal/`, `engine/` | Plays alone with satellite and drone | Seeing costs time and time is the thing you do not have |

Pieces 1 and 2 are the same program in the same room on the same map. Piece 3 is
that room's own map handed to science. Piece 4 leaves the game entirely and goes
to measured data. Piece 5 sends them home with something to play.

The arc widens the whole way. One room, then one landscape, then one real fire,
then one real forest, then one player. Each step is allowed to be harder than
the last because the room has already earned the step before it.

---

## 4. Piece one: hidden lantana

**Run it:** `python3 -m stage2.server --stage 1`
**Docs:** [`stage2/README.md`](../stage2/README.md)

Plain Mafia with the names changed. Lantana instead of mafia. Ranger instead of
angel. Ecologist instead of sheriff. Native trees instead of villagers.

Nobody is asked to learn anything. People already know this game or pick it up in
a minute. The room argues about who is lying. That is the whole activity.

Behind them a map is on the projector and it is changing. Every lantana player
who survives a night spreads. Every native player voted out loses their stand to
lantana. Every lantana player voted out leaves bare ground that either comes back
as forest or gets taken again. The game master presses **Continue** each round
and the board updates without stopping the room.

### The reveal

When the game ends the game master presses **Replay the map** and walks the
evening forward one night at a time. The room watches the forest they were not
looking at. A faint dashed boundary shows the ground each player started with, so
a shape they can recognise changes hands in front of them. The name of whoever
went out that night sits on their patch. Teal if the room voted them out. Purple
if lantana took them in the dark.

The forest usually starts around 92 percent and ends somewhere in the forties.
Nobody was trying to wreck it.

### Why this piece exists

It buys attention for free. The room has fun for twenty minutes and then finds
out the fun had a cost. Every later piece spends the credit this one earns.

It also teaches two mechanics without naming them. Clearing lantana leaves bare
ground. Bare ground next to lantana gets taken again. People see that happen to a
patch with a name on it.

---

## 5. Piece two: ignition

**Run it:** press **Start stage 2** on the console when stage 1 ends
**Docs:** [`stage2/README.md`](../stage2/README.md), [`stages/STAGE_2.md`](../stages/STAGE_2.md), [`stages/STAGE_2_5.md`](../stages/STAGE_2_5.md)

Same people. Same names. Same phones. Same forest. Roles dealt again so nobody
carries over what they learned about who was lantana.

Now fire is in the game, and the room gets one choice a night.

| Choice | What happens |
|---|---|
| Hunt lantana | The room votes somebody out, as before |
| Work against fire | No vote. The crew prepares instead |

That is the entire decision. One thing per night. It is the whole tension because
the room cannot do both and the clock does not stop.

### The corridor

This is the piece the rest of the evening is built around.

Fire severity does not come from how much lantana there is. It comes from the
largest **connected band** of it. Three separate stands of ten squares are three
small fires. The same thirty squares joined into one band is a single run that
carries end to end, and the ground it crosses on the way is where the loss comes
from.

Lantana is pushed to join up the way it does in the field. Fastest along roads.
Fastest into the gaps between stands that are already close. It crosses bare
ground that an earlier removal left behind, which is how a job half done turns
into a corridor. It cannot cross water, because a creeping front cannot and
neither can a creeping fire.

The evening is shaped to deliver the turn:

| Nights | What the room sees | What they should work out |
|---|---|---|
| 1 to 2 | Small fires, a few squares, wherever they start | Hunting now is cheap and it works |
| 3 to 4 | The patches meet. One card says so, once | Removing one player no longer breaks the chain |
| 5 on | One fire running the length of the band into forest or houses | From here it is fire work and fire work is expensive |

Over 120 scripted games the joined-up card appears in 116 of them, median night
three. The biggest fire of a game is a median of 55 of the 264 squares.

### Resilience without a lecture

There are three things a crew can do. A fire line. Water. An early warning.

**The room never picks which one.** They choose *whether* to work against fire.
The game picks what the crew does, based on the board.

This is deliberate and it is the design decision most likely to be undone by
somebody trying to be helpful. Making the room learn three options before their
first real decision costs five minutes of rules and buys nothing. The lesson is
that preparing for fire competes with fixing the cause. That lesson survives
perfectly well if a crew chief picks the method. They still see the trench get
dug. They still see it hold or fail to hold. They just do not have to hold three
option cards in their head to get there.

The picker used to reach for water as soon as severity hit three, on the
reasoning that a fire that big runs past any single break. That is defensible and
it was wrong here. Water holds tonight's fire to a few squares. So the one night
the room would have watched a connected band carry a fire across the map, the
game's own helper hid it. It digs a trench now. If it holds, a break works. If
the fire goes round it, one trench is not a strategy. Either way they see the
run.

### One press a round

Stage 2 does not stop the room. Finish night shows nothing at all. The room
wakes, hears no verdict, goes straight to the vote. Then the game master presses
**Show what happened** once and the whole night runs in order. The removal, the
spread, the crew's work, the fire. Twelve to seventeen seconds, ending on the
board they are about to argue over.

Stage 1 stops at every change because there the map is the lesson. Stage 2 is a
game being played. Stopping it four times a night to read a card about ground
nobody can act on gets in the way of the thing the room is doing. The explaining
happens in the replay, where there is time.

### The one dial

The game master can move the last night in or out while the game runs.

Bring it down to the night you are on and lantana makes its run across whatever
is between the patches, then one fire carries the length of it. Push it out and
the next fire is a smaller one that starts in the thickest fuel and works through
it, leaving bare ground where the lantana was.

Both are real fire behaviour. A room that only ever sees fire as the enemy has
learnt half of it. The dial exists because a room is not a simulation, and the
person running it can see whether they need the hard ending or the hopeful one.

---

## 6. Piece three: the lab

**Run it:** `/simulation/claude/lab/?run=sample` on the stage 2 server
**Docs:** [`stage2/simulation/claude/lab/README.md`](../stage2/simulation/claude/lab/README.md), [`chronology/2026-09-13T1630-fire-lab.md`](../chronology/2026-09-13T1630-fire-lab.md)

The room has just watched a fire cross their map. Fair question: was that real or
did the game make it up?

The lab answers it with their own board. It takes the board as it stood when
their biggest fire started and hands it to fire models that exist outside this
project. ForeFire. A cell to cell automaton in the style of Cell2Fire. One square
is thirty metres. Every cover becomes a fuel class with published spread
parameters.

Six panels and one slider. The top row is the board as played and the two models
burning it. The bottom row is the same board with a plan applied. Clear the
largest thick stand. Dig a line along the downwind edge of what is left. Then the
same two models burn that.

### Why it is built this way

**The board is the bridge.** The room is not shown a fire model interface. They
are shown the map they spent an hour with, in the same colours, burning. The only
new thing on screen is that it burns differently. Everything else they already
know how to read.

**One interaction.** A slider for time. That is all. Nothing to configure. The
point is not to teach anyone to run a fire model. The point is to show that the
thing they played has a serious version and the serious version agrees.

**The counterfactual is the payload.** The bottom row is the evening they did not
have. Same board, same ignition, same wind, with the work done. This is where a
room gets to see what their resilience nights would have bought if they had spent
them earlier. Nobody has to say it.

**Real fires sit alongside.** `cases.py` lays documented invasive-fuel fires on
the same board in the same words. Lahaina 2023 with guinea grass. Bandipur 2019
with lantana under dry forest. Same map, same models, real event.

---

## 7. Piece four: the films

**Docs:** [`stage2/simulation/codex/NOTES.md`](../stage2/simulation/codex/NOTES.md), [`stage2/simulation/codex/VNEXT.md`](../stage2/simulation/codex/VNEXT.md), [`lidar/README.md`](../stage2/simulation/codex/lidar/README.md), [`rainforest_continuity/README.md`](../stage2/simulation/codex/rainforest_continuity/README.md), [`hyperspectral/README.md`](../stage2/simulation/codex/hyperspectral/README.md)

The films for the event are the ones under `codex/`. The `claude/` directory holds
an earlier parallel attempt and the lab. It is not the film source.

By now the room believes the landscape. The open question is how anybody knows
any of this about a real forest. Nobody walks 300,000 square kilometres of tiger
range counting bushes.

These are short silent films made from measured data. No generated imagery.

- **Structure.** Real airborne and terrestrial LiDAR of tropical forest. Point
  colour means measured height above ground. You can see the canopy, the gaps
  and the understorey as shapes rather than as a claim.
- **Continuity of scale.** One continuous camera move from a fine spectral
  signature out to a satellite footprint and back. This is the piece that earns
  the next section. It shows the same thing measured at three resolutions and
  why each one loses something.
- **Identity.** Published work detecting lantana and other invasives from the air
  in Mudumalai, and strawberry guava in Hawaiian forest.

### The rule these follow

Every shot declares what kind of thing it is. Recorded game. Modelled scenario.
Documented real fire. Atmospheric reconstruction. A generated flame may make a
recorded fire look better. It may not stand in for one. A beautiful plate may
establish a forest. It may not be captioned as the board.

That rule costs effort and it is the reason any of this can be shown to people
who work in the field.

---

## 8. Piece five: the online game

**Run it:** [pyrocene.netlify.app](https://pyrocene.netlify.app), or `python3 -m terminal.play`
**Docs:** [`README.md`](../README.md), [`ENGINE_SPEC.md`](../ENGINE_SPEC.md), [`ROADMAP.md`](../ROADMAP.md), [`ux.md`](../ux.md), [`DESIGN.md`](../DESIGN.md)

The room has seen what satellites and drones and airborne sensors can do. Now
they get to be the person holding them, alone, at home.

One action a night. Look or act, never both.

| Look | Act |
|---|---|
| `sat` wide and coarse, misses seedlings | `remove` clear a patch |
| `drone D4` sharp and local | `restore` plant the bare ground so it does not come back |
| `survey D4` slow and certain | |
| `ask D4` local knowledge about what keeps coming back | |

The campaign is built to lose on purpose.

| Level | You get | What happens |
|---|---|---|
| 1 | satellite only | You lose. You can see the shape of it and not the thing itself |
| 2 | plus drone and survey | You lose by less |
| 3 | plus local knowledge | You lose by less again |
| 4 | plus a decision support system | You win |
| 5 | plus telegraphed disasters | The real test |

Losing three times is the design. Each loss is a different data layer missing,
and the player feels the specific shape of not being able to see. Level four is
where the tool arrives and the game becomes winnable.

This closes the loop. The films showed real instruments. The game makes the
player pay for them in the only currency it has, which is nights.

The front end is deliberately a terminal. A polished web build was made and
rejected for reading like a casual puzzle game. See [`ux.md`](../ux.md). The
browser version runs the same Python unchanged through Pyodide.

---

## 9. The pieces that carry all this

What the room actually touches, and why each one is the way it is.

### The site

One address, read out loud. People type their name and nothing else. No accounts,
no install, no app store. It runs on a laptop on the room's wifi and needs no
internet.

### The phone

Shows one thing. Your role, and whether you are in or out. That is the whole
interface. A phone that shows the map would kill the room, because everyone would
look down.

### The game master console

The only complicated screen, and only one person sees it. It holds the player
list, the two buttons that end a night, the one choice, the season dial and the
replay. The design rule is that the game master should be able to run the evening
while mostly looking at the room.

### The map

The one thing everybody looks at. Six cartographic styles exist and the default
is a hand drawn one. The thing that made it readable was not the rendering. It
was dissolving the grid. The board is 264 squares and drawn as squares it reads
as a spreadsheet. Traced as outlines and smoothed it reads as land. Same data,
different comprehension.

Legends change by stage. Stage 1 does not name fire or fire lines because neither
can happen there.

### The event log

Every round writes itself to disk as it happens. Who went out, every square that
changed and what it changed from and to, the crew's work, and the fire with its
ignition square, cause, severity, wave by wave spread, burned squares and the
trench edges it pushed against. Plus the full terrain and the player list.

This is the spine of the whole back half. The lab reads it. The films read it.
The replay reads it. Nothing downstream needs any game code, only the log.
See [`stage2/simulation/SPEC.md`](../stage2/simulation/SPEC.md).

### The replay

The evening again, one night per press, with no cards. Each press runs the same
transition the game used live. In stage 2 the fire starts where it started,
spreads the way it spread and hits whatever trench it hit. This is where the
explaining happens, because now there is time for it.

---

## 10. Rules we hold to

These are the ones worth defending when somebody tries to improve them.

**The lesson is a mechanic, never a caption.** If a thing has to be said on a
card it has failed. The card says what happened. The room supplies why.

**Never make the room learn a rule to receive a lesson.** The system picks the
resilience action for this reason.

**One thing per night.** One choice, one press, one animation.

**Do not balance the strategies into parity.** Hunting lantana beats sheltering
because source control beats suppression. That is the point. Over 250 games the
strategies land within two points of each other on win rate and differ completely
in how they lose, which is the honest outcome.

**Water is a break for everything or for nothing.** If the river stops fire and
stops a trench it stops lantana too.

**Declare what kind of thing every picture is.** See section 7.

**Never name a player during play.** Names appear in the replay only. In Mafia
the not knowing is the game.

---

## 11. Index of documents

### The arc

| Doc | What is in it |
|---|---|
| [`stages/STAGE_2.md`](../stages/STAGE_2.md) | The original brief for the room game |
| [`stages/STAGE_2_5.md`](../stages/STAGE_2_5.md) | The connectivity lesson, written as a target |
| [`stage2/README.md`](../stage2/README.md) | How to run an evening, every rule, every tunable |
| [`stage2/maps/README.md`](../stage2/maps/README.md) | The six map styles |
| [`stage2/simulation/SPEC.md`](../stage2/simulation/SPEC.md) | The event log contract |
| [`stage2/simulation/claude/lab/README.md`](../stage2/simulation/claude/lab/README.md) | The fire lab |
| [`stage2/simulation/codex/VNEXT.md`](../stage2/simulation/codex/VNEXT.md) | The film plan and the evidence lanes |

### The online game

| Doc | What is in it |
|---|---|
| [`README.md`](../README.md) | What it is and how to run it |
| [`ENGINE_SPEC.md`](../ENGINE_SPEC.md) | The engine to front end contract |
| [`ROADMAP.md`](../ROADMAP.md) | The level arc and the field note sources |
| [`ux.md`](../ux.md) | Why the front end is a terminal |
| [`DESIGN.md`](../DESIGN.md) | The earlier fire first framing, kept for the philosophy |

### What actually happened

[`chronology/`](../chronology/) is dated notes on what was built, what went
wrong and what is still untested. Written to be appended to, never rewritten.
Start at [`chronology/README.md`](../chronology/README.md).

---

## 12. What has not been tested

Worth saying plainly at the end of a document this confident.

No room has played stage 2. Every balance number here comes from scripted play
against a model of a room that does not argue, get suspicious of the quiet
person, or vote badly on purpose. No projector has shown these maps to an
audience at ten metres. No fleet of phones has joined at once. The game master
console has only ever been driven by the person who wrote it.

The next useful thing is one evening with real people and somebody taking notes.
