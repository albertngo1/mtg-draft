# FRA — Reality Fracture: prerelease draft & Sealed guide

**Set:** Reality Fracture (`FRA`) · **Release:** 2026-10-02 · **Prerelease weekend:** 2026-09-25 → 09-27
**Sources captured:** 2026-09-21 — Wizards official prerelease guide, Draftsim full set review
(Andrew Quinn, 0–10), LimitedMTG draft & sealed study guide, MTG Arena Zone color reviews (J2SJosh),
plus Scryfall `set:fra` (285 unique cards: 86 common, 109 uncommon, 64 rare, 26 mythic).

---

## ⚠ Evidence tier

Prerelease sources are the **weakest tier in the repo** — every grade below is a prediction made
before a single game. See [`README.md`](./README.md). Retire this file once 17Lands GIH WR lands
after the Arena release.

Two things in here are stronger than the grades, and worth separating:

- **Counts** (removal per color, mechanic distribution, per-pair two-drop and removal density) come
  from full set data — Scryfall directly, cross-checked against LimitedMTG's independent count.
  These are facts about the set.
- **Draftsim's 0–10 grades** are captured in full at [`grades/draftsim_FRA.json`](../../grades/draftsim_FRA.json)
  (converted to /5, all 280 non-basic cards) and drive the bomb list below.

---

## Format in one line

**Ten two-color archetypes sharing one Jace token and one cheap-answer pool — black and red hold
most of the removal, blue-green is the trap, and every pair has a common dual land that enters
untapped if you control a planeswalker.**

---

## The nine format principles

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
Voxmancer` (B/R), `Paradox Shaper` (U/B), `Woodwork Prodigy` (R/G). In a long Sealed game these
are the best engines in the format.

`Codie, Ravenous Codex` copies every prepared spell — but Draftsim rates it **2.0/5**, and that's
right: it needs a critical mass a Sealed pool won't reliably have.

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

---

## Removal

LimitedMTG counts **60 removal spells** in the set. By color:

| Color | Count | Notes |
|---|---|---|
| **Black** | **14** | `Last Gasp` and `Extended Absence` at common are the workhorses |
| **Red** | **11** | `No Admittance` and `Wrath of the Bloodmane` at common |
| White | 7 | `Prophesied End` is the best of them — two mana, instant, unconditional |
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

## Bombs — Draftsim's top of the set

Full grades for all 280 non-basic cards: [`grades/draftsim_FRA.json`](../../grades/draftsim_FRA.json).
Shown as Draftsim's original 0–10.

| Card | Colors | Cost | Body | DS |
|---|---|---|---|---|
| `Chandra, Torch of Defiance` | R | 4 | PW | **10** |
| `Ajani Unrelenting` | R | 6 | PW | **10** |
| `Craterclaw Colossus` | R | 7 | 5/5 haste | **10** |
| `Garruk, Curse Breaker` | G | 5 | PW | **10** |
| `Verdant Kraken` | G | 7 | 6/6 | **10** |
| `Kwia Vigorbloom` | G/W | 6 | 6/6 flying vig lifelink ward2 | **10** |
| `Denzilore Fatehold` | W/U | 4 | 3/4 flash flier | **10** |
| `The Theorist, Jace Beleren` | U | 4 | PW | **10** |
| `Lyra, Tolarian Archangel` | U | 3 | 3/3 flier | **10** |
| `Aerid Konstrari` | R/G | 4 | 5/4 flier | 9 |
| `Uldaros Theorix` | U/B | 6 | 5/5 flier | 9 |
| `Ingris Stingerquill` | B/R | 3 | 1/4 flier | 9 |
| `Garruk, Veiled Butcher` | B | 5 | PW | 9 |
| `Overwrite the Multiverse` | B | 6 | Exile all creatures | 9 |
| `Draconic Visitor` | R | 5 | 5/5 flier | 9 |
| `Guiding Hydra` | W | X+1 | Grows the team | 9 |
| `Hungering Puppetbeast` | G | 5 | 5/5 | 9 |

**Red and green are where the top end lives** — five of the nine perfect scores. If you open a red
or green mythic, that is your color.

### Where I disagreed with Draftsim, and lost

Recorded because the disagreements are the useful part:

- **`Ingris Stingerquill` (9/10).** A 1/4 body for three looked weak to me. Draftsim is right that
  the ping-on-attack plus the Cadet-and-haste activation *is* the B/R deck's engine, and a 4
  toughness flier blocks the format's two-drops all day.
- **`Denzilore Fatehold` (10/10).** I read it as strong-not-a-bomb. Flash, flying, and a
  team-wide counter on every scry or surveil in a set with 43 surveil cards is a bomb.
- **`Sanctum Lurker` (5/10).** I called it an inevitable win condition. It needs a planeswalker you
  already care about; in a Sealed pool that's a Jace token you were using anyway.
- **`Codie, Ravenous Codex` (4/10).** Needs a prepared critical mass Sealed won't give you.

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

- **Lock B/R** — most removal in the format, both sources agree.
- **Never build G/U** — the trap. Take its Jace pieces for whichever decks want them.
- **B/G and W/U** complete the five colors with one doubled color (black) and no Simic.

Total castable removal across the three: **26 + 21 + 13 = 60**.

| Seat | Pair | Role | Plan |
|---|---|---|---|
| **Albert** | **B/G Garruk's Bestiary** | **Decider** | Deathtouch trades, grindy value, wins the long game one trade at a time. The most blocking decisions on the table |
| **Kyle** | **B/R Stingerquill** | **Scribe** + contested-card pass | The best deck in the pool. Removal plus reach — hardest sequencing, most rewarding |
| **Andy** | **W/U Fatehold** | **Clock** | Cheap fliers, surveil, curve out and attack. Deepest two-drop pair in the set and the cheapest |

**Why W/U for the newest player even though it has the least removal of the three:** that's the
point. Holding removal correctly — use it now or save it? — is the decision new Limited players
get wrong most often. A deck with little removal has few of those decisions. W/U is also the
cheapest pair in the set with the most two-drops, so "curve out and attack" is a plan that
survives misplay.

### Runner-up: **B/R + W/B + U/G**

Higher raw removal (26+23+11 = 60) but it forces someone into Simic. Only take it if the pool's
green and white are both empty and the blue is deep.

### The census gate — before anyone sorts into decks

1. **Did a red or green mythic appear?** Five of Draftsim's nine perfect scores are red or green.
   That locks a seat.
2. **How many black removal spells are there?** Two black seats need roughly 7+ between them.
   Under 5 → drop to one black seat and move the third pair to R/W or U/R.
3. **How many common duals?** Expect ~15. If you got unlucky, splashes come off the table and the
   configuration tightens.
4. **Are there 2+ of the self-preparing uncommons?** (`Stingerquill Voxmancer`, `Paradox Shaper`,
   `Woodwork Prodigy`.) Those are engines; put them where they're on-plan.

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

---

## Where the sources disagree

- **Best pair.** LimitedMTG picks B/R on removal density. Wizards is neutral by design. Draftsim's
  top grades cluster in **red and green**, which argues R/G is underrated by the removal-first
  framing. If the pool hands you two red or green mythics, believe the bombs over the table above.
- **G/U.** LimitedMTG calls it the trap. Wizards presents "Jace's Mastery" as a normal archetype.
  Trust LimitedMTG here — it's counting, Wizards is describing.
- **Prepared's ceiling.** LimitedMTG treats the self-preparing uncommons as major engines;
  Draftsim grades them 6/10. Both can be right: strong in a long game, mediocre in a short one.
- **Coverage gap.** Neither source has play data, and neither has seen the format's actual speed.

---

## Sources

- **Wizards of the Coast** — [Reality Fracture Prerelease Guide](https://magic.wizards.com/en/news/feature/reality-fracture-prerelease-guide),
  Jubilee Finnegan, 2026-09-18. Authoritative on the ten archetypes and pack contents.
- **LimitedMTG** — [Reality Fracture draft & sealed guide](https://limitedmtg.com/reality-fracture/).
  Per-pair removal and curve counts, format speed, the B/R pick and the G/U trap call. The
  strongest source here; it counts rather than predicts.
- **Draftsim** — [The Ultimate Reality Fracture Limited Set Review](https://draftsim.com/mtg-fra-limited-set-review/),
  Andrew Quinn. 0–10 on every card; captured in full to `grades/draftsim_FRA.json`.
- **MTG Arena Zone** — [FRA Limited Set Review](https://mtgazone.com/reality-fracture-fra-limited-set-review-black/),
  J2SJosh, color by color.
- **Scryfall** — `set:fra`, 285 unique cards, fetched 2026-09-21.
- **Prior art:** [`HOB.md`](./HOB.md) — the trio choreography, contested-card rule and split rule
  are carried over from there, where they were tested at a real event.
- **17Lands GIH WR supersedes everything here** once FRA hits Arena.
