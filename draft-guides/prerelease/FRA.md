# FRA — Reality Fracture: prerelease draft & Sealed guide

**Set:** Reality Fracture (`FRA`) · **Release:** 2026-10-02 · **Prerelease weekend:** 2026-09-25 → 09-27
**Card data:** Scryfall `set:fra`, fetched 2026-09-21 — 285 unique cards (86 common, 109 uncommon, 64 rare, 26 mythic)

---

## ⚠ What this document is, and how much to trust it

This is the **weakest evidence tier in the repo**, by construction. See
[`README.md`](./README.md). No games of FRA Limited have been played anywhere. There is no
17Lands data, no Limited Resources set review, no Lords of Limited crash course.

**Where the HOB guide differed:** that one synthesized five published expert reviews. This one
does not, because at the time of writing none exist for FRA. Every evaluation below is derived
from **the card text itself** — full set data pulled from Scryfall and analyzed directly. That is
a genuinely different evidence basis, and it cuts both ways:

- **Better than prerelease punditry at:** counting. Removal density per color, curve shape,
  mechanic distribution, archetype support — these are facts about the set, not predictions.
- **Worse than expert review at:** knowing which cards overperform. Card evaluation from text
  alone misses speed, misses which bombs are actually beatable, misses the traps.

**Treat the counting as reliable and the grades as a starting point.** Retire this file once
17Lands GIH WR lands after the Arena release.

---

## Format in one line

**A five-faction set built on a shared planeswalker token, where black is the only color that
reliably kills things and blue does not kill anything at all.**

---

## The eight format principles

1. **Black is the removal color.** By a wide margin — see the removal table below. Any deck that
   wants to interact should have a serious reason not to be in black.
2. **Blue has zero unconditional removal** at common or uncommon. It has bounce, a soft counter,
   and a Pacifism aura. Never build blue as your *only* interactive color.
3. **Empower Jace is free value in every color.** It appears on commons in all five colors. The
   loyalty accumulates on one shared token, so unrelated cards combine.
4. **But the Jace token is a liability too.** It's a permanent your opponent can attack. Loyalty
   you never spend is loyalty you wasted.
5. **Five allied factions, and the set only supports allied pairs.** Charms, dual lands, and the
   Prepared hybrids are all allied-only. Enemy pairs exist but are unsupported.
6. **Legendary creatures are commons-tier abundant.** 60+ legendary uncommons. Several cards
   check for "a legendary creature" or "a legendary card" — this turns on far more often than
   your instincts say.
7. **A lot of removal is color-hosed.** Five separate cards only kill specific colors. Check
   before you maindeck.
8. **Prepared creatures are recurring free spells.** Three of them re-prepare every upkeep with
   no input. In a grindy Sealed game that is the strongest engine in the set.

---

## Mechanics

### Empower Jace N — the set's spine

> *Put N loyalty counters on a Jace token you control. If you don't control one, first create a
> blue Jace planeswalker token with "[−1]: Surveil 1" and "[−3]: Draw a card."*

**36 cards in the set reference Jace. 19 of them empower.** They appear at common in all five
colors, which is unusual and important: this is not a blue mechanic, it is a colorless one wearing
blue clothes.

The critical rule is **you only ever have one Jace token**, and every empower card feeds it.
Five cards that each say "Empower Jace 2" make a single 10-loyalty planeswalker, not five small
ones. That is what makes the mechanic build-aroundable in Sealed — you don't need a payoff card,
you just need volume.

**What the token actually does:**

| Ability | Effect | Real cost |
|---|---|---|
| −1 | Surveil 1 | Cheap filtering, use it most turns |
| −3 | Draw a card | 3 loyalty per card |

So a Jace at 12 loyalty is **four cards**, spread over four turns, that your opponent can attack
down. Compare to a 4-mana "draw two" — the Jace is slower but free, because the loyalty came
attached to cards you were casting anyway.

**How to value it in deckbuilding:**

- An empower rider on a card you'd already play is **pure profit**. Take it every time.
- A card that *only* empowers (`Protege's Awakening`, {3}{U} sorcery, Empower Jace 6) is a real
  card but a slow one — two cards for four mana, delivered over two later turns. Playable filler,
  not a build-around.
- `Jace's Machinations` ({2}{U} instant, Empower Jace 8, plus lets you activate loyalty at instant
  speed) is the single biggest empower card in the set.
- `Sanctum Lurker` ({2}{B} rare) is the true build-around: **planeswalkers you control don't die
  at 0 loyalty**, and they gain "[+2]: deal 1 damage to each opponent and gain 1 life." With any
  Jace on board that is an inevitable win condition that never runs out.

**Playing against it:** attack the Jace. Most players will let it sit because it doesn't threaten
the board. A Jace that resolves four draws has won the long game on its own.

### Prepared — recurring free spells

> *While it's prepared, you may cast a copy of its spell. Doing so unprepares it.*
> *(Only creatures with prepare spells can become prepared.)*

Prepared lives on **split-faced cards** — a creature on the front, a small spell on the back.
When the creature is prepared, you may cast a **copy** of its spell for free. Casting it
unprepares the creature.

Three of the five allied hybrids **re-prepare themselves at the beginning of your upkeep**, with
no cost and no condition:

| Card | Colors | Free spell, every turn |
|---|---|---|
| `Paradox Shaper // Omit Variables` | U/B | Mill three |
| `Stingerquill Voxmancer // Vicious Verse` | B/R | 1 damage to target opponent |
| `Woodwork Prodigy // Soul Tether` | R/G | Create a Heartwood token (R/G mana artifact) |

Several rares instead **enter prepared** — a one-shot, not an engine: `Diviner of Victory //
Unwind`, `Variable Chaser // Arc of Fortune`, `Pompous Battlemage // Improv`, `Pyre Rhymer //
Molten Tide`, `Carnivorous Cultivator // Entrench`.

**Two ways to break it open:**

- `Codie, Ravenous Codex` ({3} rare artifact creature) — **copies every prepared spell you cast.**
  Doubles the engine.
- `Hexhaven Dueling Arena` (uncommon land) — {4},{T}: make a creature prepared. Re-arms a card
  that entered prepared and already fired. A colorless land slot that does real work.

**In Sealed this is stronger than it looks.** A B/R deck with `Stingerquill Voxmancer` on turn one
is dealing a free damage every single turn for the rest of the game, unanswerable except by
killing a 1-mana creature. Games go long in Sealed. Take these highly.

### Returning mechanics

| Mechanic | Count | Notes |
|---|---|---|
| **Surveil** | ~40 cards reference it | The most common keyword in the set. `Denzilore Fatehold` and `Proft, Consulting Detective` pay you for it |
| **Prowess** | 8 | Mostly U/R. `Ruric Thar, Biomagus` has *prowess twice* |
| **Threshold** | 5 | Seven cards in graveyard. Enabled by the heavy mill/surveil |
| **Flashback** | 5 | `Predictive Preparations` and `Bestial Incursion` are both fine commons |
| **Basic landcycling** | 4 commons (U/B/R/G) | {2}, discard: fetch a basic. Free mana-smoothing on real cards |
| **Landfall** | 3 | Minor |
| **Domain, Convoke, Behold, Exhaust** | 1–2 each | Effectively flavor |

---

## The five factions

All five are **allied pairs**, and the set supports them three ways each — a Charm at uncommon, a
dual land at rare, and a Prepared hybrid at uncommon. Enemy pairs have gold cards but none of
this scaffolding.

| Faction | Colors | What it does | Charm | Dual land | Mythic |
|---|---|---|---|---|---|
| **Fatehold** | W/U | Scry/surveil → +1/+1 counters, fliers | `Fatehold Charm` | `Deserted Beach` | `Denzilore Fatehold` |
| **Theorix** | U/B | Graveyard, mill, threshold, Cadet tokens | `Theorix Charm` | `Shipwreck Marsh` | `Uldaros Theorix` |
| **Stingerquill** | B/R | Noncombat damage, sacrifice, prowess, aggro | `Stingerquill Charm` | `Haunted Ridge` | `Ingris Stingerquill` |
| **Konstrari** | R/G | Artifacts (Heartwood tokens), big trampling creatures | `Konstrari Charm` | `Rockfall Vale` | `Aerid Konstrari` |
| **Vigorbloom** | G/W | Lifegain → draw and counters | `Vigorbloom Charm` | `Overgrown Farmland` | `Kwia Vigorbloom` |

### The Elder Sphinx mythic cycle

One per faction, and they are **not** close to equal. This matters enormously for a shared pool —
opening one of these largely decides a seat.

| Card | Cost | Body | Verdict |
|---|---|---|---|
| `Kwia Vigorbloom` | {3}{G}{W} | 6/6 flying, vigilance, lifelink, ward {2} | **Best card in the set.** Five mana, wins the game unanswered, and ward {2} beats most removal |
| `Aerid Konstrari` | {1}{R}{G} | 5/4 flying | **Absurd rate.** A 5/4 flier on turn three ends games before anything matters |
| `Uldaros Theorix` | {3}{U}{B} | 5/5 flying + huge graveyard ETB | Bomb, but the ETB needs a stocked graveyard to be more than a 5/5 flier |
| `Denzilore Fatehold` | {1}{W}{U} | 3/4 flash flying, pumps team on scry/surveil | Very strong, not a bomb. Needs a board |
| `Ingris Stingerquill` | {B}{R}{R} | 1/4 flying, pings on attack | **The weak one.** A 1/4 body for three. Good in a wide deck, unplayable in a bad one |

**Build rule:** `Kwia` or `Aerid` in the pool is reason enough to lock that seat's colors. The
other three are strong cards you build toward, not around.

---

## Removal — the most important table in this document

Counting every card at common and uncommon that kills, exiles, or permanently neutralizes a
creature:

| Color | Common | Uncommon | **Unconditional total** | The spells |
|---|---|---|---|---|
| **Black** | 3 | 6 | **9** | `Last Gasp`, `Silence the Echo`, `Extended Absence`, `Break Under Pressure`, `Multiply by Zero`, `Winter, Tormented Loner`, `Proft, Sinister Mastermind`, `Loot, the Anomaly`, + `Terminal Criticism` (hosed) |
| **Red** | 3 | 2 | **5** | `No Admittance`, `Wrath of the Bloodmane`, `Awaken the Inferno`, `Fulminous Forte`, `Violent Echoes`, + `Essence Burn` (hosed) |
| **White** | 1 | 2 | **3** | `Surgical Precision` (toughness 4+ only), `Prophesied End`, `Your Fate Ends Here`, + `Refute Destiny` (hosed) |
| **Green** | 2 | 1 | **3** | `Sureshot Sower` (fliers only), `Compel Brutality`, `Yoshimaru, Scrappy Stray` — all fight effects, all need a creature |
| **Blue** | 0 | 0 | **0** | `Unsummon` (bounce), `Icy Reception` (soft counter), `Infinite Coursework` (aura) — nothing dies |

**Three consequences, and they drive everything below:**

1. **Black is not a preference, it's close to a requirement** for any deck that needs to answer a
   bomb. In a shared-pool trio, black is the color you fight over.
2. **A blue deck must be paired with black or red.** W/U is the trap archetype of this format on
   paper — it has the second-worst removal color paired with the worst.
3. **Green's "removal" is three fight effects.** They are card disadvantage against a removal
   spell and blanks when you're behind on board. Do not count them as removal when you're
   building a curve.

### The color-hosed removal — read this before maindecking

Five cards only answer specific colors:

| Card | Cost | Only hits | Rarity |
|---|---|---|---|
| `Refute Destiny` | {1}{W} | Green or blue | Uncommon |
| `Terminal Criticism` | {1}{B} | Blue or red | Uncommon |
| `Essence Burn` | {1}{R} | Black or green | Uncommon |
| `Flourishing Grapple` | {G} | Red or white | Uncommon |
| `Precise Redaction` | {1}{U} | White or black (counter) | Uncommon |

These are **premium rates for punishing costs** — `Essence Burn` is 5 damage and exile for two
mana. Against the right half of the field they're the best cards in your deck; against the wrong
half they're blank.

**In a trio specifically this is an information advantage.** You know what your two teammates are
playing, which tells you nothing about opponents — but it *does* mean your sideboard decisions are
free after game one. Board them in aggressively; these are sideboard cards that steal games.

---

## Rares & mythics worth building around

### The unconditional bombs

| Card | Colors | Why |
|---|---|---|
| `Kwia Vigorbloom` | G/W | 6/6 flier with lifelink and ward {2} for five |
| `Aerid Konstrari` | R/G | 5/4 flier for three |
| `Garruk, Veiled Butcher` | B | Exiles opposing creatures that would die, +2 shrinks, −2 makes a 4/4 |
| `Chandra, Torch of Defiance` | R | Card advantage, mana, and a −3 that kills |
| `Garruk, Curse Breaker` | G | Draws on every fat creature, −3 makes 4/4 tramplers |
| `Verdant Kraken` | G | 6/6 that makes a 3/3 land creature **every upkeep, both players'** |
| `Draconic Visitor` | R | 5/5 flier for five, upgrades artifact tokens into 5/5 Dragons |
| `Curse-Marred Demon` | R | 4/4 flying trample for four that tutors |
| `The Theorist, Jace Beleren` | U | Draws an extra card every opponent's draw step |

### The build-arounds that need the right pool

| Card | Needs | Payoff if you have it |
|---|---|---|
| `Sanctum Lurker` | Any Jace token | Planeswalkers stop dying at 0 loyalty and drain every turn. Wins alone |
| `Codie, Ravenous Codex` | 2+ Prepared creatures | Every free spell happens twice |
| `Omnipresence` | Seven mana and a wide board | Cast your hand for free. Game over, but seven mana in Sealed is real |
| `Return to the Light Realms` | Nine mana, full graveyard | The most unfair thing in the set if a game reaches nine mana |
| `Kindred Judgment` | A tribal-ish board | One-sided wrath for seven. Cadet tokens are all Wizard Soldiers — a real synergy |
| `Puppet Crafting` | Any artifact or enchantment | Two mana, turns a Heartwood token into a 5/5 |

### Traps — cards that read stronger than they play

- **`Tarmogoyf`** — yes, really. In Limited it's often a 2/3 or 3/4 for two. Fine, not a bomb.
- **`Hexhaven Invigorator`** — {G}{G}{G} 6/6 is a real cost; triple-pip on turn three is a
  fantasy in a two-color Sealed deck.
- **`Extrapolate the Impossible`** — a wish card. Dead unless you're sideboarding from outside
  the game, which is not how prerelease works.
- **`Face Yourself`** — seven mana, copies **their** board, and the copies die at end of turn
  unless you control a planeswalker. Too many conditions.
- **`Frostbite Pyromental`** — 4/4 trample haste that draws two, then **sacrifices itself**. It's
  a two-card Lava Spike. Fine, not the bomb the stat line suggests.

---

## Commons that carry decks

Ranked within color. These are the cards you're actually building 40 out of.

**White** — `Memory Trap` (unconditional exile at 3, the best white common), `Surgical Precision`,
`Shatterwing Pegasus`, `Hexhaven Battalion` (three 2/2s + empower for six), `Graft Surgeon`,
`Predictive Preparations`.

**Blue** — `Surveillance Phantasm` (2/3 flier that attacks the turn you surveil — excellent),
`Divining Duelist`, `Icy Reception`, `Undulating Witness`, `Mindseeker Oculus`, `Sphinx's Approach`.

**Black** — `Last Gasp` (best black common), `Extended Absence`, `Apex Witchstalker` (6/4 menace,
gains life twice, landcycles when you don't want it), `Silence the Echo`, `Rampart Hunter`,
`Theoretical Necromancer`.

**Red** — `No Admittance` (3 damage any target plus empower), `Wrath of the Bloodmane` (4 damage,
often for two mana in this legend-dense set), `Awaken the Inferno`, `Tether Technician`,
`Heartstring Puller`, `Chandra's Emberling`.

**Green** — `Bestial Incursion` (4/4 trample with flashback — two bodies from one card),
`Vinelasher Adept`, `Wrecking Gecko` (5/5 ward {2} for five), `Sureshot Sower`, `Budding
Insurgent`, `Compel Brutality`.

**Colorless** — `Medic's Kitesail` and `Murmuring Volume` are real playables in any deck.
`Afterthought Sentry` is filler that flies.

---

## Sealed: building your 40

Standard shape, with two FRA-specific adjustments.

**The baseline:** 17 lands, 23 spells, 15–17 creatures, curve topping around six.

**Adjustment 1 — you can go to 16 lands more comfortably than usual.** Four commons have basic
landcycling and several cards filter. But only do this if you actually have 3+ of those effects.

**Adjustment 2 — count your removal honestly.** Using the table above, not vibes. If your two
colors total fewer than four real answers, you are going to lose to a bomb you can't beat, and
you should seriously consider splashing black off a dual land or `Murmuring Volume`.

**Splashing** is well-supported: five allied dual lands at rare, `Room of Refuge` (colorless land,
any color), `Murmuring Volume` (3-mana any-color rock), `Heartwood` tokens in R/G, Treasures off
`Vraska, the Cutting Glare`. A single black splash for `Extended Absence` or a bomb is very
reasonable.

---

## Trios / Team Sealed — the part that isn't documented anywhere else

**Format:** three prerelease kits opened together, **18 boosters, one shared pool**, three decks
built collectively. This is *not* official 12-booster Team Sealed. Confirmed as the HOB format;
assumed unchanged for FRA.

**Match structure:** three seats play simultaneously against the opposing trio. **You need 2 of 3
seat wins**, not 3.

### What 18 packs actually gives you

Play Booster math, approximate — treat these as planning numbers, not guarantees:

| Slot | Per pack | × 18 | Notes |
|---|---|---|---|
| Commons | ~7 | **~126** | From 81 non-basic commons → ~25 per color |
| Uncommons | ~3 | **~54** | From 109 unique |
| Rare/mythic | 1 | **~18** | Plus 3 kit promos = **~21** |
| Wildcard slot | 1 | ~18 | Any rarity, skews common |

**The number that matters: roughly 7 copies of black removal in the pool.** (~25 black commons ×
3 removal commons ÷ 11 black commons.) Split across two black decks that's 3–4 each, plus
uncommons. Tight but workable — and it is the single strongest argument for the configuration
below.

**On rares:** ~21 rare/mythic slots against a 90-card rare+mythic pool means you should expect
**4–7 genuine bombs**, and roughly a coin flip on seeing at least one Elder Sphinx. Enough that
all three seats can have a real threat.

### Trio configuration — the ring math

FRA's five factions form a **closed ring**: W/U → U/B → B/R → R/G → G/W → back to W/U. Each color
appears in exactly two factions.

Pick any three factions from a five-cycle and you cannot avoid at least one shared color. You get
one of exactly two shapes:

- **One adjacency** — one doubled color, all five colors used. *This is what you want.*
- **Two adjacencies** — two doubled colors, only four colors used. Wasteful; you're leaving a
  whole color's cards in the box.

So the real question is only: **which color do you double?** And given the removal table, the
answer is black.

### 🔒 Recommended configuration: **U/B + B/R + G/W**

Doubles black. Uses all five colors. Exactly one adjacency. Mathematically clean and it doubles
the only color that reliably kills things.

| Seat | Faction | Role | Plan |
|---|---|---|---|
| **Albert** | **U/B Theorix** | **Decider** | Grindy control. Removal, surveil, threshold, Jace. Hardest deck to pilot, so it goes to the most experienced seat |
| **Kyle** | **B/R Stingerquill** | **Scribe** + contested-card pass | Aggro with the deepest removal in the pool. Prowess, noncombat damage, Cadet tokens |
| **Andy** | **G/W Vigorbloom** | **Clock** | Creatures, lifegain, +1/+1 counters, attack. Lowest decision density on the table, deliberately |

**Why G/W gets the newest player** even though it's the removal-poor seat: it's the deck whose
game plan survives misplay. Curve out, gain life, attack. It also has the best possible bomb if
`Kwia Vigorbloom` shows up. The two removal-rich decks go to the two players who'll sequence
removal correctly.

**Why not W/U anywhere:** worst removal color paired with the no-removal color. Avoid unless a
white *and* a blue bomb both appear.

### Runner-up configuration: **B/R + R/G + W/U**

Doubles red. Take this if the pool's black is genuinely shallow — which would be surprising — or
if two red bombs show up. Also all five colors, one adjacency.

### The census gate — run this before locking anything

Open everything, then answer these four questions **before** anyone starts sorting into decks:

1. **Did an Elder Sphinx appear?** `Kwia` or `Aerid` locks that seat's colors immediately.
2. **How many real black removal spells are there?** Under 5 total → the double-black plan is
   dead, fall back to the runner-up.
3. **Is there a `Sanctum Lurker` plus 4+ empower cards?** That's a deliberate Jace deck and it
   belongs in the U/B seat.
4. **Are there 2+ self-preparing hybrids?** (`Paradox Shaper`, `Stingerquill Voxmancer`,
   `Woodwork Prodigy`.) If yes, plus `Codie`, that's a real engine — build toward it.

### Build choreography — ~75 minutes, six phases

Carried over from HOB, which worked. One FRA-specific change is marked.

| Phase | Time | What happens |
|---|---|---|
| **1. Open + stage** | 10 min | Everyone opens their six packs. **Photograph each player's own pulls separately before merging** — this is the only way a split-back is possible later |
| **2. Sort silently, in parallel** | 12 min | Split the pool by color. **No reading.** Just piles. Three people, five piles plus gold plus colorless |
| **3. Census + lock config** | 8 min | Run the four gate questions above. Lock the three factions and who pilots what. **Do not skip this — everything after depends on it** |
| **4. Read only your two colors** | 15 min | Each pilot reads only their assigned pair. Nobody reads 285 cards. Scryfall links below |
| **5. Build three 40s in parallel** | 20 min | Each pilot builds their own deck. Uncontested cards go straight in |
| **6. Contested zone + lands + cross-check** | 10 min | Resolve the shared pile together, add lands, sleeve, and have someone other than the pilot count each deck |

**⚠ FRA-specific change to phase 4:** the **color-hosed removal must be read by everyone**, not
just the pilot whose color it's in. Five cards only kill certain colors, and whether they're
maindeck or sideboard depends on the field, not the deck. Call them out loud during phase 3.

### The contested-card rule

**A contested card goes to whichever deck has the worse alternative — not the deck that uses it
best.**

You need 2 of 3 seat wins. That means you are maximizing the *floor* across three decks, not the
ceiling of any one. A card that makes the strong deck slightly stronger, taken from the weak deck
that has nothing in that slot, actively loses matches.

In FRA this bites hardest on **black removal** with two black seats. Resist giving all of it to
the aggro deck because "removal is better in aggro." Split it roughly evenly and give the
tiebreakers to whichever deck's curve has the bigger hole.

### The split rule — agree on this before the event, in writing

The one thing that cannot be fixed at the table. Send it to your teammates the night before.
Suggested text:

> *Everyone keeps what they personally opened. We photograph each person's six packs before
> merging. Cards go into a shared pool for the event only. Afterwards we split back by photo. If
> anyone wants to trade or buy a card out of someone else's pulls, that's a separate conversation
> after the split, not part of the build.*

---

## Reading your colors at the table — Scryfall links

Each pilot opens only their own. Set the view to **Images** and scroll.

| Seat | Query | Approx. cards |
|---|---|---|
| U/B Theorix | `set:fra ci<=ub -ci:c` | 88 |
| B/R Stingerquill | `set:fra ci<=br -ci:c` | 88 |
| G/W Vigorbloom | `set:fra ci<=gw -ci:c` | 86 |
| Everyone, night before | `set:fra rarity:common` | 86 (81 + 5 basics) |

**Do the commons the night before.** 81 real cards, about 25 minutes, and it removes most of the
reading load at the table. This was the fix that saved the HOB build and it applies more here —
FRA has 285 cards to HOB's 193.

---

## Playing the games

- **Play first.** Almost never wrong in Limited.
- **Attack the Jace.** Opponents leave their own alone and expect you to as well. Four free cards
  is worth two turns of attacking a planeswalker instead of a player.
- **Track your own Jace's loyalty out loud.** One token, many sources, easy to lose count.
  −1 surveil most turns; save −3 for when you need gas.
- **Prepared creatures re-arm at your upkeep.** Set a habit of checking them before you draw. A
  missed free spell every turn is how these games get lost.
- **Assume opposing removal is black.** If they're not in black, they probably can't kill your
  creature — attack accordingly.
- **Ward {2} is everywhere** on the good creatures (`Kwia`, `Wrecking Gecko`, `Unflinching
  Hortimancer` at ward {1}). Hold removal until you can pay.
- **Cadet tokens are 2/2 Wizard Soldiers.** Colorless. They matter for `Kindred Judgment` and
  `Command the Stage`.

---

## Before you leave the house

1. Read all 81 non-basic commons on Scryfall — `set:fra rarity:common`, Images view. ~25 minutes.
2. Send teammates the split rule text above.
3. Confirm the trio config is only a *default* — it gets re-locked at phase 3 after the census.
4. Bring: sleeves, a token/loyalty counter for Jace (a die works), pen and paper for the Scribe.
5. Print or phone-load `FRA-onepager.html` for whoever isn't building.

---

## Where this guide is weakest

Stated plainly, so it's not mistaken for more than it is:

- **No play data.** Zero games. Format speed is unknown, and speed is what decides whether the
  grindy U/B seat is correct at all.
- **No expert consensus.** Every grade is one analyst reading card text.
- **Bomb ordering is the least reliable part.** Counting removal is a fact; ranking `Uldaros`
  against `Denzilore` is a guess.
- **Play Booster composition is assumed**, not verified against FRA's actual product spec. The
  pool math above could be off by 10–15%.
- **The trio config assumes the HOB format** (18 packs, shared pool). Confirm on the day.

---

## Sources

- **Scryfall** — `set:fra`, full card data, fetched 2026-09-21. 285 unique cards. This is the
  basis for every count in this document.
- **Prior art:** [`HOB.md`](./HOB.md) — the trio choreography, contested-card rule, split rule,
  and phase structure are carried over from there, where they were tested at a real event.
- **No expert reviews were available at time of writing.** When Limited Level-Ups, Limited
  Resources, or Lords of Limited publish FRA coverage, those supersede the card evaluations here.
- **17Lands GIH WR supersedes everything** once FRA hits Arena.
