# FRA — Reality Fracture: prerelease draft & Sealed guide

**Set:** Reality Fracture (`FRA`) · **Release:** 2026-10-02 · **Prerelease weekend:** 2026-09-25 → 09-27
**Sources:** card evaluations come from the two podcast set reviews, **Limited Resources 872**
(Marshall Sutcliffe + LSV, 2026-09-21) and **Limited Level-Ups** (Alex + Mark, 2026-09-22; blue not
yet transcribed). Counts come from the Wizards prerelease guide, LimitedMTG's study guide and Scryfall
`set:fra` (285 unique cards: 86 common, 109 uncommon, 64 rare, 26 mythic). Rewritten 2026-09-22 to
drop the Draftsim and MTG Arena Zone grades.

---

## ⚠ Evidence tier

Prerelease sources are the **weakest tier in the repo** — every grade below is a prediction made
before a single game. See [`README.md`](./README.md). Retire this file once 17Lands GIH WR lands
after the Arena release.

Two things in here are stronger than the grades, and worth separating:

- **Counts** (removal per color, mechanic distribution, per-pair two-drop and removal density) come
  from full set data — Scryfall directly, cross-checked against LimitedMTG's independent count.
  These are facts about the set.
- **Two independent podcast reviews** grade every common and uncommon (LR: [`limited-resources/FRA.md`](../limited-resources/FRA.md),
  LLU: [`limited-level-ups/FRA.md`](../limited-level-ups/FRA.md)). **Where both agree, that's the
  strongest card read in this file.** Where they split, both grades are shown.
- **Neither has graded rares and mythics yet.** LLU's rares video is due Thursday 2026-09-24,
  the day before the prerelease; LR's (#873) comes after it. Until then, judge a rare yourself with
  the rule in *Rares* below.

---

## Format in one line

**Ten two-color archetypes sharing one Jace token and one cheap-answer pool — black and red hold
most of the removal, blue-green is the trap, and every pair has a common dual land that enters
untapped if you control a planeswalker.**

---

## The eleven format principles

1. **All ten pairs are real archetypes.** Allied pairs are the Hexhaven colleges; enemy pairs are
   the Echoverse characters. Wizards documents all ten with signposts.
2. **Every pair has a dual land at common** — ten of them — and each enters untapped if you
   control a planeswalker. **A Jace token counts.** Fixing is abundant and splashing is cheap.
3. **Black and red hold the removal.** LimitedMTG's count: black 14, red 11, white 7, blue 5,
   green 5, gold/colorless 18. B/R is the consensus best pair.
4. **Blue-green is the consensus trap.** Fewest removal spells of any pair, and the Jace cards it
   wants are the ones every other drafter is taking anyway.
5. **The Jace token is the shared engine.** 35 cards empower, 11 at common, in every color. All
   sources feed one token.
6. **Prepared is the other engine**, and it's a *common* cycle — each allied pair's plan in
   miniature, on ten common creatures.
7. **The format plays at normal speed.** Average mana value 3.2, 68% of spells cost ≤3, 3 damage
   kills 68% of creatures. Nothing pushes it fast.
8. **Echoed pairs mean legends are everywhere.** 32 characters appear twice, usually in different
   colors. Cards that check for "a legendary creature" turn on constantly.
9. **Cheap answers, so hold your removal.** 28 removal spells cost one or two mana, 22 are
   instants. Both players have interaction; play around it.
10. **Four toughness is the magic number** (LLU). It blocks the two- and three-drops and dodges
    red's 3-damage spells and black's −3/−3. Three-toughness four-drops with no ETB are traps.
11. **Sealed will be wild.** Only 71 commons, and a pack can hold up to six rares. LLU expects a
    typical deck to be mostly uncommons and rares, so **card quality beats synergy** and "fine"
    filler bodies often don't make the cut.

---

## Mechanics

### Empower Jace N — the set's spine

> *Put N loyalty counters on a Jace token you control. If you don't control one, first create a
> blue Jace planeswalker token with "[−1]: Surveil 1" and "[−3]: Draw a card."*

**35 cards, 11 at common, in all five colors.** You only ever have one Jace token and every
empower card feeds it, so unrelated cards combine. Five cards reading "Empower Jace 2" make one
10-loyalty planeswalker.

| Ability | Effect | Cost |
|---|---|---|
| −1 | Surveil 1 | Use it most turns |
| −3 | Draw a card | 3 loyalty per card |

**Three interactions that matter more than the token's own text:**

- **It turns on the common duals.** All ten enter untapped if you control a planeswalker. A turn-one
  Jace fixes your mana for the rest of the game.
- **`Compel Brutality` turns it into removal.** Its second mode has a planeswalker you control deal
  damage equal to its loyalty. A Jace that `Protege's Awakening` just built kills almost anything.
- **`Silence the Echo` can eat a spent token.** It needs a creature or planeswalker sacrificed — a
  drained Jace is the ideal fodder.

**Cheapest loyalty:** `Arcane Amphisbaena` and `Academic Ascent` at two mana, `Campus Crier` from
the graveyard for one, `Protege's Awakening` for six loyalty at four mana, `Jace's Machinations`
for eight.

**Playing against it:** attack the Jace. LimitedMTG's read is that *a Jace token left alone decides
more games than a two-drop does*, and most opponents will let yours sit.

### Prepared — a common cycle, not a rare curiosity

> *While it's prepared, you may cast a copy of its spell. Doing so unprepares it.*

**24 cards, 10 at common.** Each allied pair owns one spell, and that spell is the pair's whole
plan in miniature:

| Spell | Pair | Effect |
|---|---|---|
| `Peer Review` | W/U | Make a 2/2 Cadet and surveil |
| `Omit Variables` | U/B | Mill three |
| `Vicious Verse` | B/R | 1 damage to an opponent |
| `Soul Tether` | R/G | Make a Heartwood token (taps for R or G) |
| `Seed Suture` | G/W | +1/+1 counter and 1 life |

**The commons enter prepared and fire once.** `Fatehold Chronologist`, `Semester Foreseer`,
`Theorix Metamage`, `Void Extrapolator`, `Hallway Heckler`, `Whiplash Wordsmith`, `Konstrari
Improviser`, `Emergency Phytomedic`, `Blossom-Blessed Angel`.

**Three uncommons re-prepare at your upkeep, so they fire every turn, forever:** `Stingerquill
Voxmancer` (B/R), `Paradox Shaper` (U/B), `Woodwork Prodigy` (R/G). The podcasts are lukewarm on
all three: Voxmancer LR B / LLU D+–C−, Paradox Shaper C+ / C–D+, Woodwork Prodigy C+ / C+–C.
They're good in a long game, but the free spells are small. Play them on-plan; don't build around them.

`Codie, Ravenous Codex` copies every prepared spell, but it needs a critical mass of prepared
creatures that a Sealed pool won't reliably have.

### Heartwood tokens

Red-green artifacts that tap for {R} or {G}. Made by `Soul Tether`, `Konstrari Improviser`,
`Woodwork Prodigy`, `Tenured Tethermage`, `Hungering Puppetbeast`, `Aerid Konstrari`. They're the
R/G ramp plan and they turn on `Pia, Determined Rebuilder` and `Craterclaw Colossus`.

### Returning mechanics

Surveil (43 cards, 14 common — the set's most-used keyword), prowess (8), threshold (5),
flashback (5), basic landcycling (4 commons, and the key to splashing), landfall (3).

---

## The ten archetypes

LimitedMTG's per-pair counts, with the official name and signpost. **Removal** is that pair's
total castable removal; **2-drops** is depth at two mana.

| Pair | Name | Plan | Signpost | Removal | 2-drops | Avg MV |
|---|---|---|---|---|---|---|
| **B/R** | Stingerquill | Face burn / noncombat damage | `Grim Repriser` | **26** | 12 | 3.10 |
| **W/B** | Liliana's Attrition | Small creatures dying for value | `Twisted Fates` | 23 | 11 | 3.10 |
| **B/G** | Garruk's Bestiary | Deathtouch trades, value creatures | `Primal Witchstalker` | 21 | 11 | 3.28 |
| **U/B** | Theorix | Graveyard math, threshold at 7 | `Recursive Recruitment` | 20 | **14** | **3.01** |
| **R/W** | Ajani's Army | Go-wide, +1/+1 counters, Cadets | `Warrior's Blades` | 20 | 13 | 3.23 |
| **R/G** | Konstrari | Heartwood ramp into fatties | `Craftwork Crusher` | 18 | 15 | **3.39** |
| **U/R** | Chandra's Prowess | Noncreature spells matter | `Clash of Elements` | 17 | 15 | 3.11 |
| **G/W** | Vigorbloom | Lifegain → counters and cards | `Bloombrute` | 13 | 15 | 3.35 |
| **W/U** | Fatehold | Surveil aggro, cheap fliers | `Desperate Futurescribe` | 13 | **16** | 3.07 |
| **G/U** | Jace's Mastery | Empower Jace, planeswalker value | `Mind Meanderer` | **11** | 16 | 3.27 |

**LimitedMTG's pick is B/R.** No color has more removal at common than black or red, and the pair
has the most overall.

**LimitedMTG's trap is G/U**, and the reasoning is sound: least removal of any pair, its signpost
is a six-mana flier, and the loyalty it needs comes from cards every other deck wants too. *Take
the Jace pieces for whatever you end up in and leave the pair alone.*

Three worth a note beyond the table:

- **W/B is a removal deck with a sacrifice angle, not the reverse.** Draft it as black removal
  with white bodies. Don't expect to race — few pairs are lighter on two-drops.
- **U/B is the cheapest pair and the deepest at two mana**, and its enablers feed its payoffs more
  directly than any other. The cost is the wait: before the seventh card in the graveyard, none of
  the threshold bonuses are on.
- **R/G has the highest curve in the set** and gets away with it only because of Heartwood ramp
  plus basic landcycling on its big commons.

**What the two podcasts add to the counts:**

- **B/R: keep the removal, drop the face-burn plan.** Both podcasts doubt the pinging deck most.
  LLU's Mark: "the school I doubt most." Red has one good two-drop (`Skilled Battlecarver`), and
  both reviews say B/R plays as **grindy removal midrange**, not burn-out. The removal count
  still stands.
- **G/U: both podcasts agree it's fragile.** LR: "the fancier the deck, the likelier it does
  nothing." LLU calls `Kiora of Salt and Sand` an "upside trap." This matches the removal count.
- **R/G is the easy deck.** Wizards designed it to be simple, to offset the set's complexity (LLU,
  citing designer Ben White), and `Craftwork Crusher` is both podcasts' top C/U. LR doubts the
  Heartwood ramp; LLU likes it.
- **G/W: LR's favourite, LLU's middle.** It rests on `Bloombrute`, the card the podcasts split on
  hardest (A− vs B−/C).
- **Colours:** neither podcast calls a colour bad. LLU's Mark ranks black worst and white
  second-worst, "but not by much." LR is highest on black and red removal.

---

## Removal

LimitedMTG counts **60 removal spells** in the set. By color:

| Color | Count | Notes |
|---|---|---|
| **Black** | **14** | `Last Gasp` and `Extended Absence` at common are the workhorses |
| **Red** | **11** | `No Admittance` and `Wrath of the Bloodmane` at common |
| White | 7 | `Your Fate Ends Here` is the best (LR B, LLU B−/B). `Prophesied End` is only good against attackers (LR C, LLU C+/C) |
| Blue | 5 | `Unsummon` and `Infinite Coursework`. Blue does not kill things, it delays them |
| Green | 5 | Mostly fight effects — they need a body and they're card disadvantage into removal |
| Gold/colorless | 18 | The Charms and the gold uncommons |

At common the split is tighter than the totals suggest: red 4, black 3, green 3, white 2, blue 2.

**Five color-hosed spells** only answer specific colors — premium rates, punishing conditions:

| Card | Cost | Hits only |
|---|---|---|
| `Refute Destiny` | {1}{W} | Green or blue |
| `Terminal Criticism` | {1}{B} | Blue or red |
| `Essence Burn` | {1}{R} | Black or green |
| `Flourishing Grapple` | {G} | Red or white |
| `Precise Redaction` | {1}{U} | White or black |

Against the right half of the field these are the best cards in your deck. Sideboard them in
aggressively after game one.

**What to play around** (28 spells cost one or two mana, 22 are instants): white has `Prophesied
End` at two for anything; blue holds `Unsummon` for one and `Icy Reception` for two; black has
`Last Gasp`; red has `Wrath of the Bloodmane` at instant speed; green has `Compel Brutality`.

---

## What to take — the two podcasts' top commons and uncommons

Both reviews graded all 180-odd commons and uncommons (LLU minus blue). **Both** means both
podcasts put the card at B− or better. Grades are shown as **LR / LLU**, with LLU split as Alex/Mark.

| Card | Colors | Rarity | What it is | LR / LLU |
|---|---|---|---|---|
| `Craftwork Crusher` | R/G | U | 7-mana 7/5 trample, two of: 4 dmg / 2/2 / draw | B+–B / **A−** |
| `Twisted Fates` | W/B | U | Destroy any nonland permanent + team counters | **A−** / B |
| `Hapatra, the Desert Fang` | B/G | U | ETB −1/−1 counters = biggest MV in your yard | B+–A− / B–B+ |
| `Way of the Healer` | W | U | Empower 5; every Jace −2 makes a 2/2 and surveils | B / **A−–B+** |
| `Stingerquill Charm` | B/R | U | Bolt any target, or deathtouch+first strike, or a hasty 2/2 | B+ / B−–B |
| `Multiply by Zero` | B | U | 2-mana instant, base 0/0 | B / B |
| `Violent Echoes` | R | U | 4-mana instant, 6 dmg, excess empowers | B / B−–B+ |
| `Break Under Pressure` | B | U | Instant edict of their biggest, gain 2 | B+ / B− |
| `Your Fate Ends Here` | W | U | Instant kill MV 3+ creature or walker, surveil | B / B−–B |
| `Clash of Elements` | U/R | U | 3-mana instant, answers any nonland permanent | B / B−–B |
| `Fulminous Forte` | R | U | Instant: 5 dmg, or 1 to each of theirs | B / B− |
| `Desperate Futurescribe` | W/U | U | 4-mana 3/4 flier, grows the team on surveil | B / B−–B |
| `Fblthp, Knows the Way` | G | U | X-mana domain land fetcher | B+ / B–A− |
| `Jiang Yanggu, Never Alone` | G | U | 2/2 + 3/3 for four | B+ / B−–B |
| `Kiora of Fire and Ashes` | R | U | 2/2 + 5/5 flying Dragon for six | B+ / B–B+ |
| `Vigorbloom Charm` | G/W | U | Protect / draw + gain 3 / counter + fight | B+ / B− |
| `Teyo, Lightshield Expert` | W | U | Flash hexproof + counter, or +loyalty | B− / B |
| `Last Gasp` | B | C | 2-mana −3/−3 instant | B / B−–C+ |
| `No Admittance` | R | C | 2-mana sorcery, 3 dmg anywhere + empower | B / B−–C+ |

**Commons are thin at the top.** Only `Last Gasp` and `No Admittance` reach B from both podcasts.
Next tier: `Extended Absence` (B / C+–B−), `Surgical Precision` (C / B−–C+), `Memory Trap` (B /
B−–C+), `Hexhaven Battalion` (C+–B− / B−–C+), `Awaken the Inferno` (B− / C+),
`Compel Brutality` (C+ / C+). In Sealed that means **your uncommons and rares decide your colors;
the commons fill the curve.**

**Where the two podcasts split hard.** Weigh these as uncertain:

| Card | LR | LLU | The argument |
|---|---|---|---|
| `Bloombrute` | **A−** | B− / C | LR: "busted." LLU (Mark): you don't get the card every turn, and Seed Suture cards are fewer than they look |
| `Saheeli, Jewel of Avishkar` | B+ | C | LLU: fewer spells than Strixhaven, where the Murmuring Mystic comparison finished C+ |
| `Mabel, Valley Hero` | B–B+ | B− / C | LLU: only creatures that entered *this turn* get counters |
| `Thalia, the Survivor` | B | C | LR rates the 3/4 lifelink body higher |
| `Koth of the Homestead` | B | C+ / D+ | Needs ~11 Plains |
| `Wrath of the Bloodmane` | B | C+ / C | With ~3 legends per pack the discount is real. Both podcasts still play it |
| `Traxos, Scourge Eternal` | B–C+ | C− / C+ | Colorless 5/4 trampler; plays in any deck either way |

### Rares — no podcast grades yet

LLU's rares video lands **Thursday 2026-09-24**; ingest it the night before the prerelease. Until
then, use the rule both reviews applied to every uncommon: **a rare is a bomb if it removes
something or makes a threat the turn it lands, and survives three damage.** Seven-plus-mana cards
and "does nothing the turn it lands" enchantments were marked down by both podcasts no matter the
payoff.

---

## Sealed: building your 40

Wizards' own template, which is a fine baseline:

| MV | Cards |
|---|---|
| 1 | 1–2 |
| 2 | 7–8 |
| 3 | 5–6 |
| 4 | 3–4 |
| 5 | 2–3 |
| 6 | 0–1 |

Plus **17 lands**. Order of operations: find your bombs first, then your removal, then let those
two pick your colors.

**Splashing is unusually easy in this format** and you should be readier than normal to do it.
Ten common dual lands, all untapped with any planeswalker out; basic landcycling on big commons in
four colors; `Room of Refuge` and `Murmuring Volume` colorless. A third color for one removal spell
is affordable.

**If you're blue,** you need a second color that kills things. Blue's five "removal" spells bounce
or tap. That is not a deck on its own.

**Deckbuilding rules both podcasts applied:**

- **Play the duals.** Both grade all ten C+, and Alex (LLU) wants about **two fixing lands per
  deck** even with no splash. `Room of Refuge` is C+ from both too.
- **Land cyclers are free slots.** `Hexhaven Battalion`, `Awaken the Inferno`, `Undulating
  Witness`, `Vinelasher Adept` and `Apex Witchstalker` graded C+ to B−. They're a threat late
  and a land early.
- **Cap pure card draw at one or two.** So many cards empower Jace that `Protege's Awakening`,
  `Sphinx's Approach` and `Way of the Mind Sculptor` crowd each other out (LR).
- **Big Ways yes, cheap Ways no.** `Way of the Healer`, `Way of the Wildspeaker` and `Way of the
  Warlord` are fine. The 2–3-mana Ways (Mentor, Necromancer, Cryomancer, Paradox) don't touch the
  board, and both podcasts graded them D to C.
- **Colour hosers are sideboard cards** (both podcasts, all five). Bring them in for games 2–3.
- **Cut "fine" bodies without a reason.** LR marked down Budding Insurgent, Shatterwing Pegasus,
  both Yargles and Rampart Hunter; LLU agreed on most. This is a synergy set, and the rare-dense
  pool gives you better options.
- **Respect Unsummon.** LLU calls it "a shadow hanging over" token makers and big green creatures.
  Don't stack auras or counters onto one body against blue.

---

## Trios / Team Sealed

**Format:** three prerelease kits opened together, **18 boosters, one shared pool**, three decks
built collectively. Not official 12-booster Team Sealed. **Confirm on the day.**

**Match structure:** three seats play simultaneously. **You need 2 of 3 seat wins, not 3.**

### What 18 packs gives you

Approximate Play Booster math — planning numbers, not guarantees:

| Slot | × 18 | Notes |
|---|---|---|
| Commons | ~126 | From 81 non-basic commons → ~25 per color |
| Uncommons | ~54 | From 109 |
| Rare/mythic | ~18 + 3 kit promos = **~21** | Against 90 rares+mythics → expect **4–7 real bombs** |
| Common duals | ~15 across all ten pairs | Fixing is not a constraint |

### 🔒 Recommended configuration: **B/R + B/G + W/U**

With all ten pairs live the choice is wide open, so the constraints that actually bind are: take
the consensus best pair, avoid the consensus trap, cover all five colors, and double the color
with the most removal to split between two seats.

- **Lock B/R** — most removal in the format. Both podcasts doubt its ping plan but rate its
  removal highly (`Stingerquill Charm`, `Multiply by Zero`, `Violent Echoes`, `Fulminous Forte`,
  `Last Gasp`, `No Admittance`), so **build it as removal midrange**.
- **Never build G/U** — the trap. Take its Jace pieces for whichever decks want them.
- **B/G and W/U** complete the five colors with one doubled color (black) and no Simic.

Total castable removal across the three: **26 + 21 + 13 = 60**.

| Seat | Pair | Role | Plan |
|---|---|---|---|
| **Albert** | **B/G Garruk's Bestiary** | **Decider** | Deathtouch trades, grindy value, wins the long game one trade at a time. The most blocking decisions on the table |
| **Kyle** | **B/R Stingerquill** | **Scribe** + contested-card pass | The removal deck. Kill everything, win with whatever's left — not a burn-out deck. Hardest sequencing, most rewarding |
| **Andy** | **W/U Fatehold** | **Clock** | Cheap fliers, surveil, curve out and attack. Deepest two-drop pair in the set and the cheapest |

**Why W/U for the newest player even though it has the least removal of the three:** that's the
point. Holding removal correctly — use it now or save it? — is the decision new Limited players
get wrong most often. A deck with little removal has few of those decisions. W/U is also the
cheapest pair in the set with the most two-drops, so "curve out and attack" is a plan that
survives misplay. LLU's Mark adds that W/U "may be one of the strongest decks" because its cards
all push the same way.

**Re-checked against the podcasts (2026-09-22): the configuration holds.** Both podcasts agree on
the two load-bearing calls: black/red removal is the format's best, and G/U is fragile. One
alternative worth knowing: **if the pool has `Craftwork Crusher` plus 3+ Heartwood makers, R/G
can replace W/U as the newest player's deck.** It was designed to be the easy deck, and Crusher
is both podcasts' top uncommon.

### Runner-up: **B/R + W/B + U/G**

Higher raw removal (26+23+11 = 60) but it forces someone into Simic. Only take it if the pool's
green and white are both empty and the blue is deep.

### The census gate — before anyone sorts into decks

1. **Which top cards appeared?** Check the *What to take* table: `Craftwork Crusher`,
   `Twisted Fates`, `Hapatra, the Desert Fang`, `Way of the Healer` and any rare that passes the
   bomb rule. Two or more in one pair locks a seat, even if the pair isn't in the plan above.
2. **How many black removal spells are there?** Two black seats need roughly 7+ between them.
   Under 5 → drop to one black seat and move the third pair to R/W or U/R.
3. **How many common duals?** Expect ~15. If you got unlucky, splashes come off the table and the
   configuration tightens.
4. **Are there 2+ of the self-preparing uncommons?** (`Stingerquill Voxmancer`, `Paradox Shaper`,
   `Woodwork Prodigy`.) Put them where they're on-plan, but don't bend a seat for them. Both
   podcasts graded them C-range.

### Build choreography — ~75 minutes, six phases

| Phase | Time | What happens |
|---|---|---|
| **1. Open + stage** | 10 min | Open six each. **Photograph each player's own pulls before merging** — the only way a split-back is possible later |
| **2. Sort silently, in parallel** | 12 min | Split by color. **No reading.** Piles only |
| **3. Census + lock config** | 8 min | Run the four gate questions. Lock the three pairs and the pilots. Everything after depends on this |
| **4. Read only your two colors** | 15 min | Each pilot reads only their pair. Nobody reads 285 cards |
| **5. Build three 40s in parallel** | 20 min | Uncontested cards go straight in |
| **6. Contested zone + lands + cross-check** | 10 min | Resolve the shared pile together, add lands, sleeve, and have someone other than the pilot count each deck |

**FRA-specific additions to phase 3:** call out the **color-hosed removal** aloud — whether it's
maindeck or sideboard depends on the field, not on the deck it sits in. And **count the common
duals** before anyone plans a splash.

### The contested-card rule

**A contested card goes to whichever deck has the worse alternative — not the deck that uses it
best.** You need 2 of 3 seat wins, so you are maximizing the floor across three decks, not the
ceiling of one.

In FRA this bites hardest on **black removal** with two black seats. Split it roughly evenly and
give tiebreakers to whichever deck's curve has the bigger hole.

### The split rule — agree in writing, before the event

> *Everyone keeps what they personally opened. We photograph each person's six packs before
> merging. Cards go into a shared pool for the event only. Afterwards we split back by photo. If
> anyone wants to trade or buy a card out of someone else's pulls, that's a separate conversation
> after the split, not part of the build.*

---

## Reading your colors at the table

| Seat | Scryfall query | Cards |
|---|---|---|
| B/G | `set:fra ci<=bg -ci:c` | 88 |
| B/R | `set:fra ci<=br -ci:c` | 88 |
| W/U | `set:fra ci<=wu -ci:c` | 88 |
| Everyone, night before | `set:fra rarity:common` | 86 (81 + 5 basics) |

**Do the commons the night before** — 81 cards, about 25 minutes in Scryfall's Images view. It
removes most of the reading load at the table.

---

## Playing the games

- **Play first.**
- **Attack the Jace.** Most opponents won't expect it and won't defend it.
- **Track your own Jace's loyalty out loud.** One token, many sources.
- **A big Jace is a removal spell** with `Compel Brutality`, and sacrifice fodder for
  `Silence the Echo` once it's spent.
- **Check your prepared creatures at upkeep**, before you draw. A missed free spell every turn is
  how these games get lost.
- **Your common duals want a planeswalker out.** Sequencing a cheap empower spell before you play
  the land is often worth a whole turn.
- **3 damage kills 68% of creatures**; the step to 4 buys 19 points more. Worth knowing when
  choosing between burn spells.
- **32% of creatures have toughness 4+**, which is why `Surgical Precision` is live more often
  than it reads.
- **Aim one attacker at their Jace, the rest at face** (LLU's Mark). Send the attacker that's
  hardest to block at the Jace. Pushing it to zero is "functional life gain," but don't swing 15
  power into a 2-loyalty Jace.
- **Early, −3 to draw. Late, −1 to surveil.** Once you don't need lands, surveil is as good as
  the card (LLU).
- **One activation per turn.** Empowering a Jace that still has loyalty gives no second
  activation. Empowering after it died does, because the new token is a fresh planeswalker (LLU).
- **Cast spells before combat** when the opponent might hold `Countersculpt`. It makes them a Jace,
  and you want your attackers still untapped to hit it (LR).
- **With `Way of the Healer` out, every Jace activation is the −2** for a 2/2 and a surveil (LLU).

---

## Where the sources disagree

- **B/R: the count and the podcasts.** LimitedMTG picks B/R on removal density. Both podcasts doubt
  its ping plan. Both are right: take the removal, skip the face-burn build.
- **G/U.** LimitedMTG calls it the trap, and both podcasts agree it's fragile. Wizards presents
  "Jace's Mastery" as a normal archetype. Three sources to one.
- **The gold uncommons, LR versus LLU.** LR is much higher on `Bloombrute` (A− vs B−/C),
  `Saheeli, Jewel of Avishkar` (B+ vs C) and `Mabel, Valley Hero` (B/B+ vs B−/C). If one of these
  decides a seat, LLU's objection is concrete and worth checking against your pool: Bloombrute
  needs a lifegain trigger every turn, and Mabel only counters creatures that entered this turn.
- **Prepared's ceiling.** LimitedMTG treats the self-preparing uncommons as major engines. Both
  podcasts grade them C-range. Strong in a long game, mediocre in a short one.
- **Coverage gap.** Nobody has play data, and neither podcast has graded rares yet.

---

## Sources

- **Wizards of the Coast** — [Reality Fracture Prerelease Guide](https://magic.wizards.com/en/news/feature/reality-fracture-prerelease-guide),
  Jubilee Finnegan, 2026-09-18. Authoritative on the ten archetypes and pack contents.
- **LimitedMTG** — [Reality Fracture draft & sealed guide](https://limitedmtg.com/reality-fracture/).
  Per-pair removal and curve counts, format speed, the B/R pick and the G/U trap call. The
  strongest source here; it counts rather than predicts.
- **Limited Resources 872** — Reality Fracture Set Review: Commons and Uncommons, Marshall
  Sutcliffe + LSV, 2026-09-21. Distilled in [`limited-resources/FRA.md`](../limited-resources/FRA.md).
- **Limited Level-Ups** — Reality Fracture set review (6 parts; blue not yet transcribed) plus
  First Impressions #261, Alex + Mark, 2026-09-18 → 09-22. Distilled in
  [`limited-level-ups/FRA.md`](../limited-level-ups/FRA.md).
- **Not used:** Draftsim's and MTG Arena Zone's reviews were dropped 2026-09-22. Their captures stay
  on disk (`grades/draftsim_FRA.json`, `draft-guides/draftsim/`, `draft-guides/mtgazone/`).
- **Scryfall** — `set:fra`, 285 unique cards, fetched 2026-09-21.
- **Prior art:** [`HOB.md`](./HOB.md) — the trio choreography, contested-card rule and split rule
  are carried over from there, where they were tested at a real event.
- **17Lands GIH WR supersedes everything here** once FRA hits Arena.
