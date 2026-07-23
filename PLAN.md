# ASH & INTUITION: A Simulation of Ecological Resilience

---

## Part I: Lore 

### The Philosophy of the Flame

For over a century, humanity treated the forest as a museum - a static gallery of green to be rigidly preserved, policed, and locked behind glass. We believed that peace meant the total absence of fire. We were wrong.

By suffocating the flame, we starved the soil. By extinguishing every column of smoke, we allowed dead wood, dense brush, and opportunistic invasive species to accumulate into a catastrophic powder keg. Nature’s fury is not a malfunction of the system; it is a feature. Fire is the forest's great exhalation, a necessary disturbance that clears the old to make way for the resilient. When we deny the small, necessary fires, we inadvertently summon the megafire.

In *Ash & Intuition*, you do not play to conquer nature, nor do you play to preserve it in a fragile, artificial stasis. You play to cultivate **Resilience**: the capacity of an ecosystem to absorb a burning disruption, survive it, and regenerate.

You will face an AI that acts not merely as a destructive force, but as an unforgiving teacher. It will exploit your blind spots, punish your reactive panic, and drain your resources if you treat the landscape like a battleground instead of a living relationship.

* **The Ecologist** must look backward to see forward, decoding the whispers of the community, the history of the soil, and the hidden vulnerabilities of the grid.
* **The Ranger** must act decisively, balancing the urgent, expensive cry of human preservation against the quiet, systemic need for long-term ecological health.

The fire is coming. You cannot stop it. You can only learn to dance with the spark.

---

## Part II: The 10-Minute Onboarding Guide 

If you want to skip the deep theory and ignite your first simulation immediately, read this section. You can learn the nuanced strategies as the forest burns around you.

### 1. The Core Objective

You win or lose as a team based on your **Ecological Health Score (EHS)**, which starts at **75**:

* **How to Win:** Maintain an EHS of **90 or above for 3 consecutive turns**.
* **How to Lose:** Allow the EHS to drop **below 50** at any point.

### 2. Setup the Board

The landscape is a grid of hidden squares. While the AI knows the exact variables of every square, they are hidden from the players. You must spend your shared budget to uncover them.

### 3. The Anatomy of a Square

Each square contains hidden environmental variables that dictate how it behaves when ignited:

* **Fuel Load:** The volume of dead trees, leaves, and brush. High fuel = explosive spread.
* **Vegetation Status:** Can be **Native Patch** (resistant, high health) or **Invasive Colonization** (highly volatile, quick to ignite).
* **Human Assets:** Contains villages, infrastructure, or community borders. Burning these inflicts a massive, immediate penalty to your EHS.

### 4. The Game Loop

Each game round represents a cycle of seasons, split into three distinct phases:

```
[ Phase 1: Day Phase ] --------> [ Phase 2: Night Phase ] --------> [ Phase 3: The Dawn Debrief ]
  Players spend Budget;            AI simulates nature's fury;        EHS is calculated;
  Ecologist scans/flags;           Fires spread based on             Turn Counter advances.
  Ranger deploys actions.          hidden variables & player actions.

```

* **Phase 1: The Day Phase - Player Actions**
* The Ecologist and Ranger receive a shared Turn Budget.
* The Ecologist deploys monitoring strategies, places danger flags, or studies history.
* The Ranger builds firelines, clears invasives, or restores land based on the Ecologist's guidance.


* **Phase 2: The Night Phase - The AI Simulation**
* The AI evaluates the board's hidden states, triggers ignitions, and simulates fire spread based on weather (possibly wind/rain) and fuel.


* **Phase 3: The Dawn Debrief**
* The players observe where the fire spread, calculate the new EHS, and check win/loss conditions.

---

## Part III: Roles, Abilities, and Limitations

The fundamental tension of the game rests on a communication barrier: **The Ecologist can see the problems but cannot fix them; the Ranger can fix the problems but cannot see them.** ---

### The Ecologist - The Learning Mind

Your goal is to build deep situational awareness. You look at the landscape through data, history, and human lore.

#### 1. Bounded Data Strategies

* **Satellite Imagery (Low Cost):** Reveals broad, vague risk zones across a wide quadrant (e.g., "This $4\times4$ area is High Risk").
* **Drone Reconnaissance (Medium Cost):** Uncovers precise data (Fuel Load, Vegetation Status) for a small, targeted cluster of squares.
* **Forest Surveys (High Cost):** Completely uncovers every variable, asset, and environmental factor of a single square with perfect clarity.

#### 2. Community Qualitative Clues (Wildcard Action)

Once per turn, you can interview local communities. They provide cryptic, non-linear insights that direct sensors miss:

* *Example Clue:* "The five ridge-lines always catch fire first when the north wind blows." You must deduce which five squares share this hidden trait.
* *The Language Risk:* Rarely, the community speaks an ancient dialect your current tools cannot translate. The turn is spent, the budget is lost, and you receive no data.

#### 3. Danger Flags & The Communication Quirk

* **Flagging Danger:** The Ecologist can place or remove **Danger Flags** on any square during their turn to warn the Ranger.
* **The Quirk:** Flags are silent. The Ranger sees *where* the danger is, but **not why**.
* **Radio Consultation:** To find out *why* a square is flagged (e.g., "Is it high fuel, or an invasive species?"), the Ranger must spend an action point to communicate with the Ecologist.

#### 4. The Deep Hindcast

The Ecologist can look backward in time at a single square's historical data:

* Reveals previous burn cycles and ancient vegetation.
* **ANR Breakthrough:** If a square is flagged as risky due to invasive species, using Hindcast reveals the exact native species that historically thrived there. Passing this data to the Ranger unlocks the **Assisted Natural Regeneration (ANR)** action.

---

### The Ranger (The Decisive Hand)

Your goal is intervention. You are inherently action-focused, protecting immediate human life while attempting to executing systemic fixes.

```
       RANGER ACTION MATRIX
+-----------------------------------+-----------------------------------+
|         REACTIVE ACTIONS          |         SYSTEMIC ACTIONS          |
|  (High Cost, Short-Term Safety)   |    (Low Cost, Long-Term Health)   |
+-----------------------------------+-----------------------------------+
| * Digging Fire Lines              | * Controlled Prescribed Burns     |
| * Reactive Fire Suppression       | * Targeted Invasive Clearing      |
| * Community Relocation            | * ANR Restoration (With History)  |
+-----------------------------------+-----------------------------------+

```

#### 1. Reactive Emergency Interventions (High Cost)

* **Digging Fire Lines:** Completely cuts off fire spread into a square, but costs heavy budget and protects only immediate borders.
* **Reactive Suppression / Evacuation:** Protects villages and human assets from an active fire, saving the EHS from crashing, but consumes massive financial resources.

#### 2. Systemic Ecological Interventions (Low Cost)

* **Targeted Invasive Clearing:** Removes volatile weeds from a square, lowering its ignition rate permanently. Requires the Ecologist to have identified the invasive first.
* **Controlled / Prescribed Burns:** The Ranger intentionally burns a high-fuel square under managed conditions.
* *The Mechanic:* If a fire is safely contained within fire lines and burns off dangerous fuel, **it is declared a "Good Fire."** Instead of costing money, the community rewards the players with a **Budget Bonus** next turn, and the regional EHS increases.


* **ANR Restoration (Requires Ecologist's Hindcast):** If the Ecologist discovered the historical native profile of a degraded, invasive-ridden square via Hindcast, the Ranger can execute an ANR action. Over two turns, this square transforms into a **Resilient Native Patch**, drastically boosting the global EHS.

---

## Part IV: The AI's Hidden Mandate & The Fire Engine

The AI does not play to "win" in a traditional competitive sense. It is programmed to act as a **systemic provocateur**. Its goal is to create high-stakes scenarios that force you out of short-term thinking.

### 1. The Night Simulation

Every turn, after players exhaust their actions, the AI calculates the hidden state of the board:

* It checks hidden fuel accumulation, moisture levels, and random weather triggers (like lightning strikes or shifting wind vectors).
* It ignites fires in high-risk zones, spreading them across the grid using a deterministic calculation:

$$\text{Fire Spread Probability} = \text{Fuel Load} + \text{Invasive Volatility} + \text{Wind Direction} - \text{Ranger Firebreaks}$$



### 2. The Trap of Reactive Suppression

If players play purely reactively-blindly clearing invasives without scanning, or endlessly dumping money into fire lines around villages-the AI will deliberately ignite fires in other unmonitored sectors. You will rapidly deplete your budget, the invasives will aggressively return, and a massive megafire will eventually overwhelm your unmanaged borders, causing an immediate loss.

---

## Part V: Scoring, Resilience, and The "Turning Point" Debrief

### The Ecological Health Score (EHS) Impact Matrix

| Event / Outcome | Immediate EHS Impact | Economic Consequence |
| --- | --- | --- |
| **Wildfire Consumes Village / Asset** | Heavy Decrease (-20) | High emergency costs next turn. |
| **Wildfire Consumes Native Patch** | Moderate Decrease (-10) | Land becomes vulnerable to invasives. |
| **Unmanaged Invasive Spread** | Slow, Continuous Decrease (-2/turn) | Increases future fire spread risk. |
| **Successfully Managed "Good Fire"** | **Increase (+10)** | **Financial Budget Bonus Granted.** |
| **Completed ANR Restoration** | **Heavy Increase (+15)** | Permanently secures the sector. |

---

### The "Turning Point" Debrief (The History Lesson)

When the simulation concludes-whether in triumphant Resilience or devastating Collapse-the AI generates a retrospective timeline analysis.

Rather than forcing a rigid historical template onto your creative gameplay, the AI uses your specific board movements to teach a real-world land management lesson. The debrief focuses on **Turning Points**:

> ### SYSTEM DEBRIEF: The Ridge Sector Cascade (Turn 4)
> 
> 
> **What Happened:** On Turn 4, a major fire broke out in Sector E7, threatens the local township. The Ranger opted for an emergency evacuation and suppression strategy, spending 80% of the turn's budget.
> **The Real-World Reflection:** This mirrors the historic **2018 Camp Fire** dynamics. When resources are entirely consumed by emergency suppression, long-term mitigation halts.
> **The Divergence Analysis:** Two turns prior, the Ecologist flagged Sector E7 as a high-risk invasive fuel bed, but the team skipped a *Radio Consultation* to save time. Had the Ranger utilized a **Controlled Burn** on Turn 2, the fuel would have been safely removed. The wildfire on Turn 4 would have run out of energy naturally, saving the village and preserving your budget.
> **The Lesson:** Total fire suppression is a temporary illusion. Embracing small, proactive disturbances is the only path to true ecosystem survival.
