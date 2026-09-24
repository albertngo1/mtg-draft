# FRA — Reality Fracture: prerelease draft & Sealed guide

**Set:** Reality Fracture (`FRA`) · **Release:** 2026-10-02 · **Prerelease weekend:** 2026-09-25 → 09-27
**Sources:** card evaluations come from the two podcast set reviews, **Limited Resources 872**
(Marshall Sutcliffe + LSV, 2026-09-21) and **Limited Level-Ups** (Alex + Mark, 2026-09-22). Counts come from the Wizards prerelease guide, LimitedMTG's study guide and Scryfall
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

Both reviews graded all 180-odd commons and uncommons. **Both** means both
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

## Every card — what each expert said

All three expert sources, card by card, with the card image so you can read it in place. **🎧 LR** = Limited Resources 872 letter grade. **🎓 LLU** = Limited Level-Ups grade, `Alex / Mark` where they split. Both podcasts cover commons and uncommons only. **🎙 Numot** = Kenji's verdict in his words, from his read of the whole set; he gives verdicts, not grades. A line is left out when that source didn't cover the card. Within each colour: mythic, rare, uncommon, common, then alphabetical. The full reasoning is in the three channel guides linked under Sources.

**Jump to:** [White (38)](#white) · [Blue (38)](#blue) · [Black (37)](#black) · [Red (39)](#red) · [Green (36)](#green) · [Multicolor (60)](#multicolor) · [Colorless (11)](#colorless) · [Lands (5)](#lands)

### White

<table class="expertcards">
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/5/a5e1a7dd-8c49-4435-935c-bcc78704082b.jpg?1788329189" width="240" alt="Ajani Resolute" loading="lazy"></td><td><b>Ajani Resolute</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;crazy two drop, two mana planeswalker crazy.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/8/483fcc58-cc6e-4452-a696-7b38e117c837.jpg?1788329184" width="240" alt="Enlightened Confidant" loading="lazy"></td><td><b>Enlightened Confidant</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;the life gain dark confidant… This is just a good two drop.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/5/65e9f4df-02e5-4ac7-86da-795688bfb66f.jpg?1788878434" width="240" alt="Return to the Light Realms" loading="lazy"></td><td><b>Return to the Light Realms</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;very strong card, but nine mana is like turn 15&quot;. He generally won&#x27;t play it.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/8/686f3a25-305d-4f02-8972-eba7b8e9635f.jpg?1789470769" width="240" alt="Flickering Hound" loading="lazy"></td><td><b>Flickering Hound</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;probably not very good… when it is good, it&#x27;s crazy, but generally it&#x27;s not going to be worth it.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/b/1b5d7d19-b32a-4786-ae9a-00da5e6658ad.jpg?1789644810" width="240" alt="Germinate Recruits" loading="lazy"></td><td><b>Germinate Recruits</b> · Rare<br><br>🎙 <b>Numot:</b> build-around. &quot;more often than not it&#x27;s going to suck&quot;, but it has a very high upside in a lifegain deck.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/6/768c0e64-9907-417a-a763-c836fdf36883.jpg?1789127685" width="240" alt="Gideon&#x27;s Memorial" loading="lazy"></td><td><b>Gideon&#x27;s Memorial</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;solid… Yeah, it&#x27;s fine&quot; (use as Gideon&#x27;s Reproach with cadets).</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/5/a53eb840-039d-4c45-b701-d58cb26b1a6c.jpg?1789644816" width="240" alt="Guiding Hydra" loading="lazy"></td><td><b>Guiding Hydra</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Wow, that&#x27;s great.&quot; Good with counters and when going wide. Also fine as just a big creature.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/f/6f9f814b-8249-4e48-a05e-4c84060fe6fb.jpg?1789470776" width="240" alt="Kindred Judgment" loading="lazy"></td><td><b>Kindred Judgment</b> · Rare<br><br>🎙 <b>Numot:</b> 7-mana wrath, &quot;very expensive&quot; but &quot;I still think it&#x27;s very strong. So, would still play.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/0/70d8c400-87dc-4f15-808f-e54a95d779fc.jpg?1788329194" width="240" alt="Liliana the Faultless" loading="lazy"></td><td><b>Liliana the Faultless</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;a soul warden with upside, so just good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/9/490dae91-94ce-42a9-a11f-6c5e77c4e486.jpg?1788878096" width="240" alt="Loyal Tutor" loading="lazy"></td><td><b>Loyal Tutor</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;probably not playable… generally, this is just going to be bad… probably don&#x27;t want to play this card.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/6/86a3866e-68a8-402c-baf0-1908e98e3995.jpg?1789127693" width="240" alt="Lyra, Archangel of Dawn" loading="lazy"></td><td><b>Lyra, Archangel of Dawn</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;just great… Just very good.&quot; A 3-mana 3/3 flyer that grows with lifegain.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/5/35000e93-85d3-44f8-976a-5918ee4c71e0.jpg?1788878108" width="240" alt="Repurposed Enforcer" loading="lazy"></td><td><b>Repurposed Enforcer</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;going to be extremely annoying… games where your opponent plays this on turn two… and you just lose… Insane.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/5/d5cb9810-3c2d-4ae4-b8b6-0155ca3f47ad.jpg?1789127178" width="240" alt="Danitha, Sword of Hope" loading="lazy"></td><td><b>Danitha, Sword of Hope</b> · Uncommon<br><br>🎧 <b>LR C+/B− (LSV &quot;B− just flat&quot;).</b> 2/2 first strike that draws when you cast equipment or target your own creature.<br><br>🎓 <b>LLU Alex C+ / Mark C.</b> Draws off RW Blades, tricks and Seed Suture. A deathtouch counter trick both draws and wins the fight.<br><br>🎙 <b>Numot:</b> &quot;not bad… Solid enough&quot; (lots of targeting effects).</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/8/f82f181b-a43b-4cec-b8f6-f6c1dd4c64fd.jpg?1788433351" width="240" alt="Generous Revival" loading="lazy"></td><td><b>Generous Revival</b> · Uncommon<br><br>🎧 <b>LR C+.</b> Reanimate MV ≤3 with a counter, flashback 4. Wants 0–1 copies.<br><br>🎓 <b>LLU C−.</b> Its home is WB grind. It&#x27;s a card the grade scale &quot;lets down.&quot;<br><br>🎙 <b>Numot:</b> &quot;This is good. A lot of value for one card… if you&#x27;re playing white, you&#x27;re generally going to want to play one of these.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/9/a9f3aa55-908f-42db-8135-4201433df850.jpg?1789014423" width="240" alt="Ghalta the Immovable" loading="lazy"></td><td><b>Ghalta the Immovable</b> · Uncommon<br><br>🎧 <b>LR C−/D+.</b> 0/7 that costs 9 minus your greatest toughness. It&#x27;s stuck in hand without 4–5-toughness creatures.<br><br>🎓 <b>LLU Alex D+ / Mark D−.</b> Far worse than the green Ghalta; can rot in hand.<br><br>🎙 <b>Numot:</b> &quot;just a big dumb dork&quot;. The worst white card, but fine.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/2/920703fd-2a2f-454b-8829-af8f2afda4f4.jpg?1789568532" width="240" alt="Koth of the Homestead" loading="lazy"></td><td><b>Koth of the Homestead</b> · Uncommon<br><br>🎧 <b>LR B (maybe B+; the captions garble the final call).</b> 3-mana 2/3; landfall gains 1 life and Plains add +1/+1 counters. Enables several themes.<br><br>🎓 <b>LLU Alex C+ / Mark D+.</b> Needs about 11 Plains. Alex: &quot;I&#x27;m probably a little bit too high on it.&quot;<br><br>🎙 <b>Numot:</b> &quot;seems kind of insane for an uncommon… real good.&quot; Good even with minimal white.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/f/1f95399a-9766-4f3d-aa6a-ece55e0530d9.jpg?1788951920" width="240" alt="Prophesied End" loading="lazy"></td><td><b>Prophesied End</b> · Uncommon<br><br>🎧 <b>LR C.</b> 2-mana instant kill, but the controller draws unless the creature was attacking. It&#x27;s a solid C as &quot;kill an attacker&quot; and D−/F otherwise.<br><br>🎓 <b>LLU Alex C+ / Mark C.</b> Fine in UW flyers and for closing games, and walkers make even control opponents attack. Mark: &quot;I kind of like your grade more than mine.&quot;<br><br>🎙 <b>Numot:</b> &quot;Great, can always play that. Will splash for it most likely.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/c/2c588954-c6eb-4aae-a2fa-0651ccf2d90a.jpg?1789470778" width="240" alt="Refute Destiny" loading="lazy"></td><td><b>Refute Destiny</b> · Uncommon<br><br>🎧 <b>LR sideboard.</b> Exile a green or blue creature or walker. Don&#x27;t maindeck it in Bo1.<br><br>🎓 <b>LLU sideboard (no letter).</b> &quot;Sideboard. Move on.&quot;<br><br>🎙 <b>Numot:</b> &quot;very good sideboard card&quot;.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/9/699874e3-1ccf-4a6c-8371-61040de82d08.jpg?1789645598" width="240" alt="Rescue Girl, First Responder" loading="lazy"></td><td><b>Rescue Girl, First Responder</b> · Uncommon<br><br>🎧 <b>LR C/B− (LSV B−, build-around).</b> 1/3 flyer that bounces your own permanent on your turn, for ETB value or to replay a land.<br><br>🎓 <b>LLU Alex C+ / Mark C−.</b> A value engine for slow white decks with ETBs and Ways. Both call the grade &quot;a little fake&quot;: it&#x27;ll often be misused.<br><br>🎙 <b>Numot:</b> a 1/3 flyer for 3 &quot;is kind of bad&quot;, but good with enough ETB synergies.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/7/07572be0-6610-493c-a21e-14b78e9805c9.jpg?1789645608" width="240" alt="Saheeli, Consul of Oversight" loading="lazy"></td><td><b>Saheeli, Consul of Oversight</b> · Uncommon<br><br>🎧 <b>LR B.</b> 5-mana 4/4 flyer that makes a Thopter when you scry or surveil. Jace&#x27;s −1 triggers it immediately.<br><br>🎓 <b>LLU C−.</b> Good only if a Jace token is reliably out when you cast it (curve it off Way of the Healer); otherwise it&#x27;s &quot;an Air Elemental.&quot;<br><br>🎙 <b>Numot:</b> 5-mana 4/4 flyer baseline, and with thopters &quot;she&#x27;s just great.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/f/5f7521d7-9f1f-4f03-b2ea-dd2a1b1e4e5b.jpg?1789471515" width="240" alt="Teyo, Lightshield Expert" loading="lazy"></td><td><b>Teyo, Lightshield Expert</b> · Uncommon<br><br>🎧 <b>LR B−.</b> 2-mana flash 1/1: hexproof plus a +1/+1 counter (or a loyalty counter). Saves a creature and adds stats.<br><br>🎓 <b>LLU B.</b> Flash hexproof plus a counter, or loyalty onto a walker, which can push Jace to a draw. &quot;A lot of play to this card.&quot;<br><br>🎙 <b>Numot:</b> &quot;just really good uncommon… just great.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/0/80226231-9e70-430e-aabc-f262f70b9226.jpg?1789127700" width="240" alt="Thalia, the Survivor" loading="lazy"></td><td><b>Thalia, the Survivor</b> · Uncommon<br><br>🎧 <b>LR B.</b> 4-mana 3/4 lifelink that taxes opposing noncreature spells. It supports lifegain and counters.<br><br>🎓 <b>LLU C.</b> A 3/4 lifelink whose tax is &quot;potentially better than ward 1.&quot;<br><br>🎙 <b>Numot:</b> &quot;annoying… Yeah, that&#x27;s solid.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/c/7ca95235-6e54-4ff8-bc2e-6a3d483ff007.jpg?1789729766" width="240" alt="Tomik, Orzhov Lawmage" loading="lazy"></td><td><b>Tomik, Orzhov Lawmage</b> · Uncommon<br><br>🎧 <b>LR C+.</b> 2-mana 2/1 flyer that protects walkers (only one attacker at a time) with random upside.<br><br>🎓 <b>LLU B−.</b> A 2-mana 2/1 flyer; its one-attacker-per-walker clause is mostly upside. &quot;All around a very solid card.&quot;<br><br>🎙 <b>Numot:</b> &quot;2 mana 2/1 flying with multiple potential upsides. Solid.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/0/50326a2a-7e10-464b-a97e-e880bda0558c.jpg?1789729503" width="240" alt="Way of the Healer" loading="lazy"></td><td><b>Way of the Healer</b> · Uncommon<br><br>🎧 <b>LR B.</b> Empower Jace 5, and your walkers gain −2 to make a 2/2 Cadet and surveil 1. You usually make the 2/2 right away.<br><br>🎓 <b>LLU A− / B+.</b> &quot;The best of the Ways.&quot; With it out, &quot;every time you activate Jace, it should just be a minus two.&quot; The best white uncommon.<br><br>🎙 <b>Numot:</b> &quot;Excellent… just good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/a/1a59d5b1-12d6-486b-bd29-ca371359addd.jpg?1789729554" width="240" alt="Way of the Mentor" loading="lazy"></td><td><b>Way of the Mentor</b> · Uncommon<br><br>🎧 <b>LR build-around C.</b> Empower Jace 5, and lifegain adds loyalty. It doesn&#x27;t affect the board.<br><br>🎓 <b>LLU Alex D− / Mark D.</b> Lifegain decks want to beat down, not &quot;create Divinations.&quot;<br><br>🎙 <b>Numot:</b> &quot;totally reasonable… it&#x27;s good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/8/384f3b7d-8d7f-41bf-bebd-64e8babe7fca.jpg?1789470881" width="240" alt="Yoshimaru, Beloved Companion" loading="lazy"></td><td><b>Yoshimaru, Beloved Companion</b> · Uncommon<br><br>🎧 <b>LR build-around B.</b> Counter doubler that combos with Koth and Danitha. LSV thinks it&#x27;s fine in an average white deck too.<br><br>🎓 <b>LLU Alex D / Mark D+.</b> Weak on curve.<br><br>🎙 <b>Numot:</b> works well with the counter synergies. Positive.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/5/25000a17-b701-4d69-b2ef-2c74029199d3.jpg?1789729751" width="240" alt="Your Fate Ends Here" loading="lazy"></td><td><b>Your Fate Ends Here</b> · Uncommon<br><br>🎧 <b>LR B.</b> Instant: kill a creature or planeswalker with MV 3+, surveil 1. Because of the MV floor you always trade even or better.<br><br>🎓 <b>LLU Alex B− / Mark B.</b> Hits almost everything that matters, including mythic planeswalkers.<br><br>🎙 <b>Numot:</b> &quot;Great. Always play that. We&#x27;ll play multiple… that card&#x27;s amazing.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/c/ccbe92a5-42bc-4228-9d5a-212df2f5dc15.jpg?1789128047" width="240" alt="Yuriko, Blade of the Mighty" loading="lazy"></td><td><b>Yuriko, Blade of the Mighty</b> · Uncommon<br><br>🎧 <b>LR C.</b> High variance: it plays like D or B+ depending on the board. Beware best-case thinking.<br><br>🎓 <b>LLU Alex D+ / Mark D.</b> Small body, weak immediate impact.<br><br>🎙 <b>Numot:</b> &quot;not bad. That&#x27;s good… kind of sweet.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/3/730d8c28-1e58-4b8e-89e9-445d154d2e83.jpg?1788878081" width="240" alt="Academic Ascent" loading="lazy"></td><td><b>Academic Ascent</b> · Common<br><br>🎧 <b>LR C−.</b> +2/+2 flying trick plus Empower Jace 2.<br><br>🎓 <b>LLU C−.</b> Alex: &quot;I might be a little low on this.&quot;<br><br>🎙 <b>Numot:</b> a normal trick &quot;with a bonus mini planeswalker&quot;. Decent.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/0/6047b14c-91d5-4f8e-af3f-057a541e2546.jpg?1788878120" width="240" alt="Campus Crier" loading="lazy"></td><td><b>Campus Crier</b> · Common<br><br>🎧 <b>LR C.</b> 2-mana 3/1; exile it from the graveyard later for Empower Jace 2.<br><br>🎓 <b>LLU C+.</b> Don&#x27;t use its graveyard empower to save a Jace; let Jace die and empower at end of turn. &quot;Good common.&quot;<br><br>🎙 <b>Numot:</b> &quot;Just a solid solid two drop.&quot; Three power matters, with value later.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/0/f0c8400d-824f-4d79-84bc-7615a0deb831.jpg?1789556683" width="240" alt="Fateshaper Aspirant" loading="lazy"></td><td><b>Fateshaper Aspirant</b> · Common<br><br>🎧 <b>LR C (slides to D).</b> Returns a legendary card from the graveyard, or gives a counter plus indestructible. It&#x27;s a 23rd card without good legendary targets.<br><br>🎓 <b>LLU Alex C− / Mark D.</b> &quot;The definition of filler.&quot;<br><br>🎙 <b>Numot:</b> &quot;pretty solid common&quot;. Versatile 5-drop, but he doesn&#x27;t want multiples.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/2/32a7a905-11bf-4b66-a28e-1066a0e372b8.jpg?1789644811" width="240" alt="Graft Surgeon" loading="lazy"></td><td><b>Graft Surgeon</b> · Common<br><br>🎧 <b>LR C.</b> A 3/3 for 3 that passes its counters on when it dies.<br><br>🎓 <b>LLU C−.</b> &quot;Super perfect C− card.&quot;<br><br>🎙 <b>Numot:</b> &quot;Fine. Three. Drop filler.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/b/3b6ac80e-c726-4bd0-893a-e666041a04a6.jpg?1789556695" width="240" alt="Hexhaven Battalion" loading="lazy"></td><td><b>Hexhaven Battalion</b> · Common<br><br>🎧 <b>LR C → C+ (LSV B−).</b> Three 2/2 Cadets plus Empower Jace 2 for 6, or basic landcycling 2. Marshall first misread it as two tokens. LSV would happily play three.<br><br>🎓 <b>LLU Alex B− / Mark C+.</b> Three Cadets plus Empower Jace 2, with basic landcycling. &quot;One of the better land cyclers we&#x27;ve ever seen,&quot; but below Imperial Oath.<br><br>🎙 <b>Numot:</b> white landcycler. &quot;fantastic. That is very good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/f/2f5345ae-4489-4d05-b2d5-c71285254f05.jpg?1788866058" width="240" alt="Memory Trap" loading="lazy"></td><td><b>Memory Trap</b> · Common<br><br>🎧 <b>LR C+/B → B.</b> The 3-mana O-Ring-style reprint: &quot;these always play great.&quot;<br><br>🎓 <b>LLU Alex B− / Mark C+.</b> The standard O-Ring. &quot;Good removal spell.&quot;<br><br>🎙 <b>Numot:</b> &quot;Good. Just classic three mana O-ring style effect.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/0/50a0e5f0-3c39-4f16-9a73-eec8ef71f12e.jpg?1789556696" width="240" alt="Predictive Preparations" loading="lazy"></td><td><b>Predictive Preparations</b> · Common<br><br>🎧 <b>LR D+.</b> Two +1/+1 counters, flashback 4. Needs a counters payoff.<br><br>🎓 <b>LLU Alex D+ / Mark D−.</b> A worse Travel Preparations.<br><br>🎙 <b>Numot:</b> &quot;just travel preps. Good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/e/2/e29095de-59ec-4562-ba8e-73f952e457ae.jpg?1789385580" width="240" alt="Shatterwing Pegasus" loading="lazy"></td><td><b>Shatterwing Pegasus</b> · Common<br><br>🎧 <b>LR C−.</b> Fine 3-mana 2/3 flyer, but unclear where it fits in a synergy set.<br><br>🎓 <b>LLU Alex C− / Mark D+.</b> They&#x27;d like it far more if the pump cost 4.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s fine. It&#x27;s whatever.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/3/d3acf176-ef02-4729-88c4-0f0dfbfdada4.jpg?1789385570" width="240" alt="Surgical Precision" loading="lazy"></td><td><b>Surgical Precision</b> · Common<br><br>🎧 <b>LR C.</b> Sorcery: kill a toughness-4+ creature and gain life, or draw and gain 2. It has no losing case; sorcery speed keeps it off C+.<br><br>🎓 <b>LLU Alex B− / Mark C+.</b> Much better than Marvel&#x27;s Murdock&#x27;s Crusade because the fallback mode cycles. Alex: &quot;one of the best commons.&quot;<br><br>🎙 <b>Numot:</b> &quot;going to be one of the best white commons… It&#x27;s just great.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/3/63f82985-c9c2-4d0a-ac4f-560166bebd9f.jpg?1789556741" width="240" alt="Unflinching Hortimancer" loading="lazy"></td><td><b>Unflinching Hortimancer</b> · Common<br><br>🎧 <b>LR C.</b> 2/1 ward 1 that grows on lifegain; a good common payoff for GW.<br><br>🎓 <b>LLU Alex C+ / Mark C− (C+ graded only for GW; attribution inferred).</b> A ward-1 Ajani&#x27;s Pridemate; &quot;a pillar of green-white.&quot;<br><br>🎙 <b>Numot:</b> &quot;a very good common… for the life gain deck.&quot;</td></tr>
</table>

**Jump to:** [White (38)](#white) · [Blue (38)](#blue) · [Black (37)](#black) · [Red (39)](#red) · [Green (36)](#green) · [Multicolor (60)](#multicolor) · [Colorless (11)](#colorless) · [Lands (5)](#lands)

### Blue

<table class="expertcards">
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/4/240f58ab-944c-4f4c-9df9-5f40b132bf3e.jpg?1788329242" width="240" alt="Chandra, Chill of Compliance" loading="lazy"></td><td><b>Chandra, Chill of Compliance</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;it&#x27;s okay… not crazy like Jace.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/1/f1a15a83-2f74-4513-ae4b-4cdc17016a84.jpg?1789470965" width="240" alt="Seasoned Cryomancer" loading="lazy"></td><td><b>Seasoned Cryomancer</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;it&#x27;s just great.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/0/20bb8c55-4b0b-425f-8201-b54fa2fdde86.jpg?1788329228" width="240" alt="The Theorist, Jace Beleren" loading="lazy"></td><td><b>The Theorist, Jace Beleren</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;it&#x27;s insane… Card&#x27;s insane.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/7/f76c4d8e-3e1f-4264-99af-1b8adb9a06be.jpg?1789127482" width="240" alt="Cruel Calculations" loading="lazy"></td><td><b>Cruel Calculations</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;unplayable.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/8/0853bb80-8664-432a-8457-600139fd96d5.jpg?1788878145" width="240" alt="Diviner of Victory // Unwind History" loading="lazy"></td><td><b>Diviner of Victory // Unwind History</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;for a one drop, that&#x27;s just very good… As good of a one drop as you can get.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/8/282588b9-3656-453b-aa25-2419e078ddc1.jpg?1788878150" width="240" alt="Jace&#x27;s Machinations" loading="lazy"></td><td><b>Jace&#x27;s Machinations</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;that&#x27;s great… excellent, it&#x27;s just a better divination.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/4/74087795-0b38-4fd2-9841-147583baca41.jpg?1789644880" width="240" alt="Jace, Reality Sculptor" loading="lazy"></td><td><b>Jace, Reality Sculptor</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;it&#x27;s okay. It&#x27;s actually not crazy.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/5/a5183681-447b-4023-91f7-00e9338f4417.jpg?1789128032" width="240" alt="Lyra, Tolarian Archangel" loading="lazy"></td><td><b>Lyra, Tolarian Archangel</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;That card sweet… if it ever makes extra flyers you&#x27;re just winning.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/d/6d7d8fa7-ce69-4a8c-9af0-55571393a244.jpg?1789729644" width="240" alt="Samut, Tyrant of Naktamun" loading="lazy"></td><td><b>Samut, Tyrant of Naktamun</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Just an annoying two drop&quot;. Hoses the opponent&#x27;s pump spells.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/8/08ffbd51-2bd3-4262-8809-09576ce2b6f5.jpg?1789385594" width="240" alt="Sphinx of False Conclusions" loading="lazy"></td><td><b>Sphinx of False Conclusions</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Oh my god, Barf. I already hate that card. It&#x27;s too good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/1/710302ca-c4be-4069-8ce1-f531414c74e9.jpg?1788878151" width="240" alt="Theorist&#x27;s Proxy" loading="lazy"></td><td><b>Theorist&#x27;s Proxy</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Two mana 0/3 draw a card with flash. That&#x27;s good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/e/3/e3afedb1-bf9d-4e31-9700-433514cc29b1.jpg?1789470807" width="240" alt="Variable Chaser // Arc of Fortune" loading="lazy"></td><td><b>Variable Chaser // Arc of Fortune</b> · Rare<br><br>🎙 <b>Numot:</b> a 2/3 flying prowess for 3 &quot;is fine on its own&quot;, plus a weird Wheel of Fortune.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/e/8e3a2239-9348-4639-9318-e9e35b2cf86b.jpg?1789568409" width="240" alt="Arni, Humble Scribe" loading="lazy"></td><td><b>Arni, Humble Scribe</b> · Uncommon<br><br>🎧 <b>LR B+/B.</b> 3-mana 3/2 looter that untaps whenever another nontoken creature enters. The only knock is 2 toughness.<br><br>🎓 <b>LLU Alex C+ / Mark C− (Mark: &quot;I think I like your take&quot;).</b> A 3/2 looter for UB threshold and flashback.<br><br>🎙 <b>Numot:</b> &quot;Yeah, I&#x27;d play that.&quot; A 3/2 looter.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/4/145b928d-a7ff-4fe5-ae4d-bbae7b1d955b.jpg?1788878107" width="240" alt="Countersculpt" loading="lazy"></td><td><b>Countersculpt</b> · Uncommon<br><br>🎧 <b>LR C.</b> Cancel, or a 2-mana counter if you behold a Jace, plus Empower Jace 1. Its existence changes sequencing (see Format read).<br><br>🎓 <b>LLU B (Mark moved up from B− to Alex&#x27;s B).</b> &quot;A great set for Cancel&quot;: there are many good expensive things to counter, and at worst it&#x27;s a Dissolve plus Empower Jace 1.<br><br>🎙 <b>Numot:</b> a better Counterspell with a Jace, or Cancel plus empower. &quot;baseline, I think it&#x27;s not bad.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/3/a3a2edbb-d144-4670-acad-17316cea98d2.jpg?1789127697" width="240" alt="Fblthp, Impossibly Lost" loading="lazy"></td><td><b>Fblthp, Impossibly Lost</b> · Uncommon<br><br>🎧 <b>LR D− (joking &quot;build-around A+&quot; for the alt-win).</b> A cost-reduced Divination that needs combat damage.<br><br>🎓 <b>LLU D+.</b> Damaging a Jace doesn&#x27;t count toward its trigger. &quot;More interesting than good.&quot;<br><br>🎙 <b>Numot:</b> &quot;Oftentimes it&#x27;s a two mana draw two… like okay.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/c/9c334530-0880-46b5-a358-9603eee3cecf.jpg?1789128026" width="240" alt="Geist of Saint Thalia" loading="lazy"></td><td><b>Geist of Saint Thalia</b> · Uncommon<br><br>🎧 <b>LR build-around C+.</b> 2-mana 1/2 flyer that discounts your noncreature spells.<br><br>🎓 <b>LLU Alex C / Mark C−.</b> Mostly a UR card.<br><br>🎙 <b>Numot:</b> &quot;never going to want to play… I don&#x27;t like this type of card.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/5/85faaa9d-4656-4365-871d-7cba53ed0996.jpg?1789387113" width="240" alt="Hapatra, the Desert Frost" loading="lazy"></td><td><b>Hapatra, the Desert Frost</b> · Uncommon<br><br>🎧 <b>LR C+.</b> 4-mana 4/3; tap-and-stun on ETB. 3 toughness is shaky.<br><br>🎓 <b>LLU Alex C / Mark C−.</b> A &quot;big Frost Lynx&quot;; 3 toughness is rough here.<br><br>🎙 <b>Numot:</b> &quot;that&#x27;s fine. It&#x27;s a big Frost Lynx with an ability.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/0/d0ecae06-bc5a-4886-84df-c2900816f226.jpg?1788329222" width="240" alt="Perfected Theory" loading="lazy"></td><td><b>Perfected Theory</b> · Uncommon<br><br>🎧 <b>LR D.</b> 1-mana: base P/T becomes 1/1 or 4/5. It needs combat.<br><br>🎓 <b>LLU Alex C / Mark D+.</b> &quot;Seems pushed&quot; as a UR trick; Mark would cut it first.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s not bad. I&#x27;ll play that.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/4/c4effc17-0d0e-423a-b5f2-597ea6c71f67.jpg?1789576786" width="240" alt="Plan for All Outcomes" loading="lazy"></td><td><b>Plan for All Outcomes</b> · Uncommon<br><br>🎧 <b>LR B/C+.</b> 4-mana enchantment that tucks any nonland permanent. It&#x27;s real removal for blue, and empowers Jace on your first noncreature spell each turn.<br><br>🎓 <b>LLU B (Alex moved up from C+ to Mark&#x27;s B).</b> Sorcery-speed tuck removal; &quot;every spell is basically surveil 1 tacked on.&quot;<br><br>🎙 <b>Numot:</b> &quot;that card&#x27;s sweet… I like it a lot.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/2/9244efad-35ab-45c0-b173-4bc68276cb67.jpg?1789470790" width="240" alt="Precise Redaction" loading="lazy"></td><td><b>Precise Redaction</b> · Uncommon<br><br>🎧 <b>LR sideboard B.</b> Counter a white or black spell.<br><br>🎓 <b>LLU sideboard (no letter).</b> <br><br>🎙 <b>Numot:</b> &quot;good sideboard card&quot;. Main deck only with looting.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/8/b8466593-40fe-4557-89b2-760c1c92087b.jpg?1789127178" width="240" alt="Proft, Consulting Detective" loading="lazy"></td><td><b>Proft, Consulting Detective</b> · Uncommon<br><br>🎧 <b>LR no grade given.</b> Pay 2 on scry/surveil for a +1/+1 counter and a card. Wants about 4+ surveil sources, which most decks have. &quot;Sweet card.&quot;<br><br>🎓 <b>LLU C.</b> It can rarely be activated before turn 5 or so; &quot;a little bit worse than it reads.&quot;<br><br>🎙 <b>Numot:</b> &quot;that&#x27;s cool… it&#x27;s good two drop.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/0/00af4e87-5576-4a43-9422-4c35b2b66775.jpg?1789127229" width="240" alt="Ruric Thar, Biomagus" loading="lazy"></td><td><b>Ruric Thar, Biomagus</b> · Uncommon<br><br>🎧 <b>LR B−.</b> 6-mana 4/6 flyer with double prowess that draws when an opponent targets it.<br><br>🎓 <b>LLU Alex C− / Mark C.</b> Fine, but not a high pick. (Numot&#x27;s Sealed run disagrees: it won him two games.)<br><br>🎙 <b>Numot:</b> &quot;He&#x27;s big. He&#x27;s annoying… I&#x27;d play that at my top end.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/9/3983d71e-3c23-4b36-b331-08e0707d8245.jpg?1789127702" width="240" alt="Tetsuko Umezawa, Fugitive" loading="lazy"></td><td><b>Tetsuko Umezawa, Fugitive</b> · Uncommon<br><br>🎧 <b>LR B−.</b> Makes power-or-toughness ≤1 creatures unblockable. The Dominaria version overperformed.<br><br>🎓 <b>LLU Alex B− / Mark C+.</b> &quot;Deceptively good&quot;: it also makes Jace-pressuring small creatures unblockable.<br><br>🎙 <b>Numot:</b> reprint, &quot;probably fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/3/a349800f-b634-4e74-a9d9-185df37ad909.jpg?1789568451" width="240" alt="Traxos, Academy Guardian" loading="lazy"></td><td><b>Traxos, Academy Guardian</b> · Uncommon<br><br>🎧 <b>LR B.</b> 1/5 flying vigilance prowess that costs 2 less after a noncreature spell. It&#x27;s often a 2-mana wall that also attacks.<br><br>🎓 <b>LLU Alex B− / Mark C.</b> Alex says prepared spells make the discount reliable; it&#x27;s a great Jace protector.<br><br>🎙 <b>Numot:</b> &quot;a very annoying flyer… That&#x27;s cool.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/3/838b0efb-7398-4df9-8fdf-b8af43b47938.jpg?1789014637" width="240" alt="Way of the Cryomancer" loading="lazy"></td><td><b>Way of the Cryomancer</b> · Uncommon<br><br>🎧 <b>LR D.</b> Its −3 (copy your next instant or sorcery) is rarely better than Jace&#x27;s own −3 draw.<br><br>🎓 <b>LLU Alex C+ / Mark D+.</b> Alex: &quot;one of the scariest just sitting in play.&quot; Mark: awkward to time; it wants 7–8 empower cards.<br><br>🎙 <b>Numot:</b> &quot;I like it.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/8/5838af68-66c3-4fe8-ab89-0a1721b0cfeb.jpg?1789729565" width="240" alt="Way of the Mind Sculptor" loading="lazy"></td><td><b>Way of the Mind Sculptor</b> · Uncommon<br><br>🎧 <b>LR build-around B (&quot;B or B+&quot;).</b> Empower Jace 5, and Jace&#x27;s −2-or-more abilities draw a card. Watch your total card-draw count.<br><br>🎓 <b>LLU Alex D+ / Mark C− (?).</b> Either overkill card draw or what puts you over the top.<br><br>🎙 <b>Numot:</b> &quot;a little expensive. Five mana is actually quite a bit.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/4/f45ba926-6496-4bd4-96eb-663946d56bbf.jpg?1789128043" width="240" alt="Yargle, Goliath of Otaria" loading="lazy"></td><td><b>Yargle, Goliath of Otaria</b> · Uncommon<br><br>🎧 <b>LR sideboard C/C− vs R/G; D/F main.</b> Vanilla 3/9.<br><br>🎓 <b>LLU F (?).</b> The joke 3/9.<br><br>🎙 <b>Numot:</b> &quot;Pass.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/5/45e81487-8b8c-480b-922a-eaa9edc7201d.jpg?1789127717" width="240" alt="Yuriko, Hope from the Shadows" loading="lazy"></td><td><b>Yuriko, Hope from the Shadows</b> · Uncommon<br><br>🎧 <b>LR C−/C+ (?).</b> 1-mana flash 1/1: −X/−0 or surveil 2. Marshall was &quot;talked up to a C−&quot;. LSV is high on it and says it&#x27;s good to rebuy with Fateshaper Aspirant.<br><br>🎓 <b>LLU Alex C / Mark C+ (?).</b> Blanks a deathtouch attacker or saves yours.<br><br>🎙 <b>Numot:</b> &quot;that&#x27;s a solid one drop.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/b/9ba1f7ce-3404-4932-9795-22967707f762.jpg?1789556701" width="240" alt="Cryotheory Adept" loading="lazy"></td><td><b>Cryotheory Adept</b> · Common<br><br>🎧 <b>LR D/C−.</b> 2-mana 2/1 prowess with a graveyard tap/stun mode.<br><br>🎓 <b>LLU Alex D+ / Mark D−.</b> The prowess 2/1 doesn&#x27;t hold up.<br><br>🎙 <b>Numot:</b> &quot;fine filler, I guess.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/6/960c7335-331d-488b-be68-2ad1c1c695dc.jpg?1789556709" width="240" alt="Divining Duelist" loading="lazy"></td><td><b>Divining Duelist</b> · Common<br><br>🎧 <b>LR C.</b> 3-mana 3/2 flash with a Pestermite tap/untap or a loot.<br><br>🎓 <b>LLU C− / D+.</b> Flexible filler.<br><br>🎙 <b>Numot:</b> &quot;fine for three mana. Versatile enough… Playable.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/d/8d754b96-5e44-45af-9c7a-b0da59fbe4c3.jpg?1788779540" width="240" alt="Icy Reception" loading="lazy"></td><td><b>Icy Reception</b> · Common<br><br>🎧 <b>LR C/C+.</b> A soft Essence Scatter that also hits legendary spells, or −5/−0.<br><br>🎓 <b>LLU C+.</b> A Mana Leak for creatures, legends and Ways, or −5/−0, which matters with this much deathtouch.<br><br>🎙 <b>Numot:</b> &quot;probably a decent common&quot; (many legendary targets).</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/5/a5988272-faaa-463d-a0a1-a8e96b946bad.jpg?1789385916" width="240" alt="Infinite Coursework" loading="lazy"></td><td><b>Infinite Coursework</b> · Common<br><br>🎧 <b>LR C+/B.</b> 3-mana lockdown aura (tap, loses abilities, doesn&#x27;t untap). &quot;About as good as blue gets.&quot;<br><br>🎓 <b>LLU Alex C− / Mark C+.</b> Aura lockdown; weak to the green untap trick and Unsummon.<br><br>🎙 <b>Numot:</b> &quot;the classic blue tap down removal spell… that&#x27;s fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/5/f5324741-353a-4a70-adb2-b631b00806dd.jpg?1789556707" width="240" alt="Mindseeker Oculus" loading="lazy"></td><td><b>Mindseeker Oculus</b> · Common<br><br>🎧 <b>LR B.</b> 3-mana 2/1 plus Empower Jace 4: a creature, a card and a leftover walker. &quot;Absurd&quot; for a common.<br><br>🎓 <b>LLU B−.</b> &quot;Great card.&quot; Empower 4 is usually better than 3.<br><br>🎙 <b>Numot:</b> &quot;Wow. That&#x27;s a really good common… Very good one.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/0/a08c7ec2-4c6a-4db2-85a7-41afe8731523.jpg?1788878176" width="240" alt="Protege&#x27;s Awakening" loading="lazy"></td><td><b>Protege&#x27;s Awakening</b> · Common<br><br>🎧 <b>LR C.</b> Empower Jace 6 plus draw, which works out to draw 2 and a 3-loyalty Jace. You only want one.<br><br>🎓 <b>LLU Alex C / Mark C−.</b> Only good if you can spend loyalty in big chunks (UG, e.g. with Kiora).<br><br>🎙 <b>Numot:</b> &quot;four mana, empower J6, but also draw a card… That&#x27;s not bad.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/4/f49be090-c745-40e5-bc1c-605b8d98acdf.jpg?1789644816" width="240" alt="Sphinx&#x27;s Approach" loading="lazy"></td><td><b>Sphinx&#x27;s Approach</b> · Common<br><br>🎧 <b>LR D.</b> UU1 draw 2 is too expensive; the Sphinx-tutor mode needs multiple copies.<br><br>🎓 <b>LLU D.</b> The five-copy Sphinx tutor is a meme.<br><br>🎙 <b>Numot:</b> 3-mana draw two. The Sphinx clause is &quot;cool if you ever get that ability, but it&#x27;s not going to happen.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/d/9df8a06d-c7de-49af-8c01-06dca3dfef4b.jpg?1789385597" width="240" alt="Surveillance Phantasm" loading="lazy"></td><td><b>Surveillance Phantasm</b> · Common<br><br>🎧 <b>LR C/C+.</b> 2-mana 2/3 defender flyer that attacks after you surveil; &quot;looks pushed.&quot;<br><br>🎓 <b>LLU C+.</b> &quot;By far the best template like this&quot;: a vigilant flier that enables itself and defends Jace. Don&#x27;t attack after tapping out into the G/W +2/+2 reach/flying tricks.<br><br>🎙 <b>Numot:</b> &quot;probably plays a lot better than it looks… I like that.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/a/0adbb4b2-a142-48da-8f4b-fa91529dbac4.jpg?1789556706" width="240" alt="Undulating Witness" loading="lazy"></td><td><b>Undulating Witness</b> · Common<br><br>🎧 <b>LR C+.</b> 5-mana 3/5 flyer with basic landcycling 2.<br><br>🎓 <b>LLU Alex C− / Mark D+.</b> Probably the worst landcycler, but still some fixing.<br><br>🎙 <b>Numot:</b> blue landcycler. &quot;not that good… compare that to the white one and there&#x27;s no comparison.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/d/ddad9f16-52d5-49de-82b0-b1a5294a9c44.jpg?1789556722" width="240" alt="Unsummon" loading="lazy"></td><td><b>Unsummon</b> · Common<br><br>🎧 <b>LR C/C+.</b> Cheap bounce is good in a fast format and against tokens.<br><br>🎓 <b>LLU B−.</b> &quot;One of the best commons&quot;: the set&#x27;s 4/4 and 5/5 tokens and big creatures make bounce strong.<br><br>🎙 <b>Numot:</b> &quot;playable. Not amazing.&quot;</td></tr>
</table>

**Jump to:** [White (38)](#white) · [Blue (38)](#blue) · [Black (37)](#black) · [Red (39)](#red) · [Green (36)](#green) · [Multicolor (60)](#multicolor) · [Colorless (11)](#colorless) · [Lands (5)](#lands)

### Black

<table class="expertcards">
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/f/4fcc913e-f736-460a-b24b-022fa2e861b9.jpg?1788329264" width="240" alt="Bloodline Recollector // Ancestral Craving" loading="lazy"></td><td><b>Bloodline Recollector // Ancestral Craving</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;just a good two drop. High upside two drop&quot; (3 creatures dying is &quot;not as hard to get as you think&quot;).</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/6/16c5f0f3-2578-40d3-9012-6eaef17fa0b1.jpg?1789471442" width="240" alt="Darklight Phoenix" loading="lazy"></td><td><b>Darklight Phoenix</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;Yeah, that&#x27;s bad.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/4/d48bfb8a-d135-45f3-be99-4694b4b9ab93.jpg?1788329269" width="240" alt="Garruk, Veiled Butcher" loading="lazy"></td><td><b>Garruk, Veiled Butcher</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;That is very good. Yikes. Would play that.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/4/c4554f5b-791b-48f6-bf54-ad28699e1beb.jpg?1788952080" width="240" alt="Overwrite the Multiverse" loading="lazy"></td><td><b>Overwrite the Multiverse</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;Insane.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/e/4ec912d5-cbe7-4d07-9ece-b03ac02d3055.jpg?1789385959" width="240" alt="Dark Matter Manipulator" loading="lazy"></td><td><b>Dark Matter Manipulator</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;That seems bad.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/9/c985b0d1-25bd-4069-aab7-a566ff27a8f6.jpg?1789127990" width="240" alt="Gideon the Oathless" loading="lazy"></td><td><b>Gideon the Oathless</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;a good three drop. Very solid annoying three drop.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/1/b105511d-5022-4a84-b6ce-4bb433e93a62.jpg?1789644819" width="240" alt="Lich&#x27;s Relic" loading="lazy"></td><td><b>Lich&#x27;s Relic</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;That thing&#x27;s insane… That card&#x27;s absurd… take that if you see it. Splashable, too.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/e/1eb25a6c-d6b4-465d-990e-f1ab86b26b69.jpg?1788329273" width="240" alt="Liliana the Repentant" loading="lazy"></td><td><b>Liliana the Repentant</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;this is just good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/1/811719ad-b5a3-4d31-8c6f-5dbdfccf7c1f.jpg?1789470807" width="240" alt="Rise of the Deathbringer" loading="lazy"></td><td><b>Rise of the Deathbringer</b> · Rare<br><br>🎙 <b>Numot:</b> instant −3/−3 sweep &quot;kind of legit. Seems good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/1/2185c08f-bb4d-49d5-8b6c-c629a48bb61c.jpg?1789556729" width="240" alt="Sanctum Lurker" loading="lazy"></td><td><b>Sanctum Lurker</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;This thing is insane… That&#x27;s crazy.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/9/992bd991-7cfb-459f-bafd-9a44f3c925c5.jpg?1789699369" width="240" alt="Vraska&#x27;s Final Mercy" loading="lazy"></td><td><b>Vraska&#x27;s Final Mercy</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Just great. Excellent card.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/6/46974d94-e900-43e4-92b5-4fb9b9f7cf46.jpg?1789385622" width="240" alt="Break Under Pressure" loading="lazy"></td><td><b>Break Under Pressure</b> · Uncommon<br><br>🎧 <b>LR B+ (&quot;B, at least&quot;).</b> Instant edict of their highest-MV creature or walker, plus gain 2. It almost always hits what you want.<br><br>🎓 <b>LLU B−.</b> Mark started at B+ and tempered it. Alex: &quot;I think we&#x27;re too low on this card.&quot; It hits the intended target about 70% of the time.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s good… sacks their biggest thing.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/4/6489814b-3d10-423e-988c-324740d36748.jpg?1789127194" width="240" alt="Danitha, Spear of Agony" loading="lazy"></td><td><b>Danitha, Spear of Agony</b> · Uncommon<br><br>🎧 <b>LR B.</b> 2/2 first strike that grows when you target the opponent&#x27;s stuff. Black&#x27;s removal triggers it.<br><br>🎓 <b>LLU Alex C / Mark D → D+.</b> Mark had forgotten Vicious Verse triggers it.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/9/498fa810-8522-4020-b773-52ad404c9f65.jpg?1789385697" width="240" alt="Gallia, Tragic Host" loading="lazy"></td><td><b>Gallia, Tragic Host</b> · Uncommon<br><br>🎧 <b>LR B−.</b> 2-mana 2/1 menace that recurs from the graveyard (4B, exile another creature card).<br><br>🎓 <b>LLU C+.</b> Recurs with no finality counter. Good in UB.<br><br>🎙 <b>Numot:</b> &quot;Ah, good. Two drop.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/f/4f6fd2fa-8bc8-4743-bbc8-b56475d64eff.jpg?1789568430" width="240" alt="Loot, the Anomaly" loading="lazy"></td><td><b>Loot, the Anomaly</b> · Uncommon<br><br>🎧 <b>LR D.</b> The threshold-gated sac isn&#x27;t reliable, and there&#x27;s no real sacrifice archetype.<br><br>🎓 <b>LLU Alex D+ / Mark D.</b> Plays as a vanilla 2/4. A UB/Tetsuko curiosity.<br><br>🎙 <b>Numot:</b> &quot;It&#x27;s fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/2/b2a412b0-2ae4-4552-bc5e-70654b6b9b4e.jpg?1789385677" width="240" alt="Mabel, Bitter Recluse" loading="lazy"></td><td><b>Mabel, Bitter Recluse</b> · Uncommon<br><br>🎧 <b>LR B.</b> 1-mana 1/1 deathtouch that removes up to 3 counters, which kills a Jace.<br><br>🎓 <b>LLU C+.</b> Good even drawn late; removing counters matters most against walkers.<br><br>🎙 <b>Numot:</b> &quot;Oh that&#x27;s really good for a one drop… kill their Jace token.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/0/9028d31f-9c41-47e3-885b-6a869bca8178.jpg?1789644882" width="240" alt="Massacre Girl, Most Wanted" loading="lazy"></td><td><b>Massacre Girl, Most Wanted</b> · Uncommon<br><br>🎧 <b>LR B.</b> 5-mana 4/4 must-answer that drains on your deaths and grows on noncombat damage.<br><br>🎓 <b>LLU Alex D+ / Mark D.</b> &quot;Drain effects are very overrated.&quot;<br><br>🎙 <b>Numot:</b> &quot;the drainer that gets bigger. Not bad.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/0/90d684a4-9639-4792-8760-2011a7a85370.jpg?1789644823" width="240" alt="Multiply by Zero" loading="lazy"></td><td><b>Multiply by Zero</b> · Uncommon<br><br>🎧 <b>LR B.</b> 2-mana instant that sets base P/T to 0/0, killing anything without +1/+1 counters. Great against expensive threats.<br><br>🎓 <b>LLU B.</b> &quot;In the aggregate… still a great card.&quot;<br><br>🎙 <b>Numot:</b> &quot;Oh, that card&#x27;s amazing.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/3/d36b0e06-cb82-4c48-bf35-e76f109116f6.jpg?1789127196" width="240" alt="Proft, Sinister Mastermind" loading="lazy"></td><td><b>Proft, Sinister Mastermind</b> · Uncommon<br><br>🎧 <b>LR B.</b> A 3-mana 5/5 menace castable only at threshold, or discard it for −3/−1. Both halves are good.<br><br>🎓 <b>LLU Alex B− / Mark C.</b> Alex&#x27;s grade is a build-around grade for UB/BG turbo-mill, with an expected cast around turn 6.<br><br>🎙 <b>Numot:</b> &quot;This seems fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/5/453cfde7-c460-4b55-9472-b714e16f24bb.jpg?1788952087" width="240" alt="Rewrite Regrets" loading="lazy"></td><td><b>Rewrite Regrets</b> · Uncommon<br><br>🎧 <b>LR C+.</b> Reanimate MV ≤6 plus Empower Jace 2; better with the self-mill.<br><br>🎓 <b>LLU C (possibly higher ceiling).</b> Reanimation targets include the land cyclers and Kiora of Fire and Ashes.<br><br>🎙 <b>Numot:</b> &quot;strong for four mana.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/e/7ebd7e38-b27c-4c6e-aaea-e8ee5ba5e5df.jpg?1789470810" width="240" alt="Terminal Criticism" loading="lazy"></td><td><b>Terminal Criticism</b> · Uncommon<br><br>🎧 <b>LR sideboard B.</b> Destroy a blue or red creature or walker.<br><br>🎓 <b>LLU sideboard (no letter).</b> &quot;A smidge better to main deck, but not enough.&quot;<br><br>🎙 <b>Numot:</b> &quot;Good sideboard.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/0/100c3b67-0c92-4224-b5ed-67789c612df7.jpg?1789470892" width="240" alt="Teyo, Diamondblade Mage" loading="lazy"></td><td><b>Teyo, Diamondblade Mage</b> · Uncommon<br><br>🎧 <b>LR D (maybe D+).</b> The deathtouch and the counter overlap, and 1 toughness hurts.<br><br>🎓 <b>LLU C−.</b> Better as a trick than as a body.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/f/2f47ddf7-35b6-4205-8045-f057914c5f64.jpg?1788329294" width="240" alt="Tinybones, Pocket Nuisance" loading="lazy"></td><td><b>Tinybones, Pocket Nuisance</b> · Uncommon<br><br>🎧 <b>LR C (almost C+).</b> A slightly better Rank Rat because it&#x27;s more of a board piece.<br><br>🎓 <b>LLU C.</b> Pings on any discard, so it combos with Rank Rat and red rummagers.<br><br>🎙 <b>Numot:</b> &quot;maybe not good, but it&#x27;s very very playable.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/2/12dd46b2-e892-4660-b120-55766fd4d878.jpg?1789729576" width="240" alt="Way of the Deathbringer" loading="lazy"></td><td><b>Way of the Deathbringer</b> · Uncommon<br><br>🎧 <b>LR C.</b> Empower Jace 5 plus a −2 that sacs a creature for a 4/4 trampler. Only good with junk fodder.<br><br>🎓 <b>LLU Alex C / Mark C−.</b> Reads as &quot;draw a card, leave two loyalty&quot;; few good sac targets.<br><br>🎙 <b>Numot:</b> &quot;That seems really solid.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/0/a0ff9689-ea49-4fff-b37c-4abbaeb0f73d.jpg?1789729526" width="240" alt="Way of the Necromancer" loading="lazy"></td><td><b>Way of the Necromancer</b> · Uncommon<br><br>🎧 <b>LR D / build-around C.</b> Your creature deaths add loyalty.<br><br>🎓 <b>LLU Alex F / Mark D−.</b> &quot;If not the worst, I think tied for the worst.&quot;<br><br>🎙 <b>Numot:</b> &quot;Solid.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/6/9670f754-f41f-45ac-8e8b-025ad2c0f66b.jpg?1789127724" width="240" alt="Winter, Tormented Loner" loading="lazy"></td><td><b>Winter, Tormented Loner</b> · Uncommon<br><br>🎧 <b>LR C / build-around C+.</b> 0/3 whose ETB is an edict (it can sac itself). Needs fodder.<br><br>🎓 <b>LLU Alex C+ / Mark C− (&quot;maybe I&#x27;d meet you in the middle&quot;).</b> Sacrifice a 1-loyalty Jace to make them sacrifice a real creature. Alex: most black decks will have fodder.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s not bad at all.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/4/04c816fb-5951-4db1-8834-ed3f0b36bfe1.jpg?1789127722" width="240" alt="Yargle, Glutton of Urborg" loading="lazy"></td><td><b>Yargle, Glutton of Urborg</b> · Uncommon<br><br>🎧 <b>LR D/F.</b> &quot;It does not play well.&quot;<br><br>🎓 <b>LLU no grade heard (garbled in captions).</b> &quot;Just ain&#x27;t it.&quot;<br><br>🎙 <b>Numot:</b> &quot;Classic Yargle. Unplayable.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/d/cd56f047-6bdc-4e83-8a7c-923ebad26302.jpg?1789556710" width="240" alt="Apex Witchstalker" loading="lazy"></td><td><b>Apex Witchstalker</b> · Common<br><br>🎧 <b>LR C+/B−.</b> 6-mana 6/4 menace that gains 2 on ETB and death, with basic landcycling.<br><br>🎓 <b>LLU Alex C / Mark C−.</b> A land-cycling 6-drop; pairs with Rewrite Regrets.<br><br>🎙 <b>Numot:</b> black landcycler, 6/4 menace. &quot;Oh yeah, that&#x27;s good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/b/3b5b28a4-0abd-4dc2-9856-c9a8d27f6a2d.jpg?1788353191" width="240" alt="Cast Away Doubt" loading="lazy"></td><td><b>Cast Away Doubt</b> · Common<br><br>🎧 <b>LR C/C−.</b> Draw 2, 2 damage to each player. It&#x27;s good in BR and fine in BG/WB, but not wanted in UB.<br><br>🎓 <b>LLU Alex D / Mark D+.</b> &quot;We see these all the time. They&#x27;re never good.&quot;<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s fine… not excited about it.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/e/b/eb4b6ed8-782e-4473-abc9-d50bf2275c6a.jpg?1789556713" width="240" alt="Extended Absence" loading="lazy"></td><td><b>Extended Absence</b> · Common<br><br>🎧 <b>LR B+ → B.</b> 4-mana instant exile of a creature or walker plus drain 1.<br><br>🎓 <b>LLU Alex C+ / Mark B−.</b> The drain-1 lifts it from filler to &quot;actively good.&quot; Alex: &quot;I could be too low even.&quot;<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s good. Four mana instant. Solid.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/3/2381d123-d8c7-4822-98fe-b1c365beb5ed.jpg?1789127524" width="240" alt="Last Gasp" loading="lazy"></td><td><b>Last Gasp</b> · Common<br><br>🎧 <b>LR B.</b> &quot;Take it highly, play it often.&quot;<br><br>🎓 <b>LLU Alex B− / Mark C+.</b> &quot;Great rate, not much to say.&quot;<br><br>🎙 <b>Numot:</b> &quot;reprint. That&#x27;s good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/4/f4a80225-7459-4151-86bb-8fdea31c39a6.jpg?1789127211" width="240" alt="Rampart Hunter" loading="lazy"></td><td><b>Rampart Hunter</b> · Common<br><br>🎧 <b>LR D.</b> Looks classic, but it has no synergy.<br><br>🎓 <b>LLU Alex D / Mark C−.</b> Maybe only a 26th playable in a deep set.<br><br>🎙 <b>Numot:</b> an aggro 4-drop. &quot;It&#x27;s whatever.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/f/4ff6da82-d7dd-4b59-b7e6-30670cea7169.jpg?1789556727" width="240" alt="Rank Rat" loading="lazy"></td><td><b>Rank Rat</b> · Common<br><br>🎧 <b>LR C.</b> Ravenous Rats. There was a joke about C+ if the sac-fodder payoffs are real.<br><br>🎓 <b>LLU C.</b> Weak in this set: little sac payoff, and a 1/1 can&#x27;t pressure Jace.<br><br>🎙 <b>Numot:</b> &quot;the new ravenous rats… Probably fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/3/738667a1-c184-43ea-829f-49fbb69b6fc0.jpg?1789385960" width="240" alt="Screeching Soulbreaker" loading="lazy"></td><td><b>Screeching Soulbreaker</b> · Common<br><br>🎧 <b>LR C+.</b> 1/4 flyer that drains 1 on attack.<br><br>🎓 <b>LLU Alex C / Mark D+.</b> Alex sees a near-pillar of BR; Mark says it only pressures Jace for 1.<br><br>🎙 <b>Numot:</b> &quot;not bad. Very annoying. Big butt flyer&quot;. Triggers lifegain.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/1/f1d274db-751b-4414-a38d-762198168e91.jpg?1789385640" width="240" alt="Silence the Echo" loading="lazy"></td><td><b>Silence the Echo</b> · Common<br><br>🎧 <b>LR C.</b> Sac a creature or walker, or pay 3, to kill. Sacrificing a low-loyalty Jace is a nice wrinkle.<br><br>🎓 <b>LLU Alex C / Mark D+.</b> Play one copy; multiples get clunky.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s good. Solid common.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/b/7beaa8c9-1a2c-4c88-b579-91e371d8d9e3.jpg?1788878155" width="240" alt="Solve for Disappointment" loading="lazy"></td><td><b>Solve for Disappointment</b> · Common<br><br>🎧 <b>LR D− (started at D).</b> Missing is a disaster.<br><br>🎓 <b>LLU C−.</b> Weak as a late topdeck; Alex&#x27;s grade assumes the attrition plan works.<br><br>🎙 <b>Numot:</b> &quot;still good… seems really solid.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/e/3/e36a7908-1e22-494b-adb4-e72ac0974d62.jpg?1789556734" width="240" alt="Theoretical Necromancer" loading="lazy"></td><td><b>Theoretical Necromancer</b> · Common<br><br>🎧 <b>LR D+.</b> A 4/1 for 3 with an expensive late Raise Dead. &quot;Not pushed.&quot;<br><br>🎓 <b>LLU D+ (&quot;a theoretical D plus&quot;).</b> Four mana to do nothing to the board.<br><br>🎙 <b>Numot:</b> &quot;I hate this type of card. It&#x27;s like fine.&quot;</td></tr>
</table>

**Jump to:** [White (38)](#white) · [Blue (38)](#blue) · [Black (37)](#black) · [Red (39)](#red) · [Green (36)](#green) · [Multicolor (60)](#multicolor) · [Colorless (11)](#colorless) · [Lands (5)](#lands)

### Red

<table class="expertcards">
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/c/bc3c096f-7f6c-474c-a2c8-75d3e6ddd6f5.jpg?1788329317" width="240" alt="Ajani Unrelenting" loading="lazy"></td><td><b>Ajani Unrelenting</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;This card is dumb… it is insane.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/0/40cb22c8-cb03-45c9-bb0e-b8cabdcc43cd.jpg?1788329325" width="240" alt="Chandra, Torch of Defiance" loading="lazy"></td><td><b>Chandra, Torch of Defiance</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;reprint also just very good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/7/47793a51-08c6-4ad2-a7e5-a4484d83a5cd.jpg?1788329298" width="240" alt="Craterclaw Colossus" loading="lazy"></td><td><b>Craterclaw Colossus</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;real good with the heartwood tokens… not hard to just insta win.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/d/2d8e8e5f-3bf5-490d-aa9c-9df2b26f1460.jpg?1788329303" width="240" alt="Stingcaster Mage" loading="lazy"></td><td><b>Stingcaster Mage</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;Solid mythic as well&quot; (his wording).</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/9/d9039a58-2f17-4b8a-b714-3a2f0b46f057.jpg?1789470674" width="240" alt="Ajani&#x27;s Anguish" loading="lazy"></td><td><b>Ajani&#x27;s Anguish</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;This card&#x27;s nuts… just good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/f/8f827e50-0a08-4bc8-98b1-b26c9af15ef2.jpg?1789470818" width="240" alt="Curse-Marred Demon" loading="lazy"></td><td><b>Curse-Marred Demon</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;This is very good.&quot; A 4/4 flying trample for 4 is fine even without the tutor.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/1/112f8478-bd89-4a14-9721-8ab750613129.jpg?1789470842" width="240" alt="Draconic Visitor" loading="lazy"></td><td><b>Draconic Visitor</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;if this triggers once you basically win&quot;. Still a 5/5 flyer for 5.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/c/3ccf8f64-19bd-4fdf-b70a-30a042bacf2f.jpg?1789127528" width="240" alt="Face Yourself" loading="lazy"></td><td><b>Face Yourself</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;really cool… always going to want to play, but man, this one could be real bad.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/e/6/e600b33b-8916-43dd-95d3-d7cbf874933d.jpg?1789385968" width="240" alt="Identity Echo" loading="lazy"></td><td><b>Identity Echo</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;It&#x27;s bad, but it&#x27;s neat.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/4/4404d9d4-9cdd-4dad-a4f6-574d90db5052.jpg?1789127596" width="240" alt="Master of Barbs" loading="lazy"></td><td><b>Master of Barbs</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;I don&#x27;t feel like that extra ability is going to matter much, but whatever.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/a/aa0f77ac-741a-444a-8bf0-a42c644726bf.jpg?1788878186" width="240" alt="Pompous Battlemage // Improvised Act" loading="lazy"></td><td><b>Pompous Battlemage // Improvised Act</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;It&#x27;s fine. Not great. Fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/b/2b0ebea0-86de-4da4-9fe8-dacc1e75c161.jpg?1789470850" width="240" alt="Pyre Rhymer // Molten Tide" loading="lazy"></td><td><b>Pyre Rhymer // Molten Tide</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Fine… not exciting.&quot; He said Pyre Rhymer and Pompous Battlemage &quot;probably didn&#x27;t need to be rares.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/a/ba920f23-f05c-410e-8516-c93abedf1d4d.jpg?1789729662" width="240" alt="Samut, Hazoret&#x27;s Champion" loading="lazy"></td><td><b>Samut, Hazoret&#x27;s Champion</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s just good. Just a good two drop.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/d/bd8db649-1dba-457d-8327-e1f1da1aab36.jpg?1789557035" width="240" alt="Arni, Renowned Champion" loading="lazy"></td><td><b>Arni, Renowned Champion</b> · Uncommon<br><br>🎧 <b>LR C.</b> 1/5 trample that pumps when creatures enter; high variance.<br><br>🎓 <b>LLU D−.</b> &quot;Really really bad.&quot;<br><br>🎙 <b>Numot:</b> &quot;I hate this type of card. I have no doubt I will lose to it&quot;, but he personally rarely plays such cards.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/3/f3307da2-6dad-4ef2-9614-a7d34f38088e.jpg?1789644825" width="240" alt="Command the Stage" loading="lazy"></td><td><b>Command the Stage</b> · Uncommon<br><br>🎧 <b>LR build-around C+ (Marshall).</b> &quot;Looks like a D at face value.&quot; LSV is skeptical.<br><br>🎓 <b>LLU Alex C+ / Mark C.</b> &quot;Probably the best payoff for pinging,&quot; and it points to RB as grindy midrange.<br><br>🎙 <b>Numot:</b> &quot;deck dependent, but has the potential to be pretty good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/2/d2e958de-70de-4156-8f9b-b2c0c1ba704a.jpg?1789470825" width="240" alt="Essence Burn" loading="lazy"></td><td><b>Essence Burn</b> · Uncommon<br><br>🎧 <b>LR sideboard B.</b> 5 damage to a black or green creature or walker.<br><br>🎓 <b>LLU sideboard (no letter).</b> <br><br>🎙 <b>Numot:</b> &quot;Good sideboard.&quot; Main deck with rummage.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/9/19acb2b5-3b3e-43f0-bd81-8426ed3d9c55.jpg?1789614832" width="240" alt="Fulminous Forte" loading="lazy"></td><td><b>Fulminous Forte</b> · Uncommon<br><br>🎧 <b>LR B (maybe B+).</b> Instant: 5 damage, or 1 to each opposing creature and walker.<br><br>🎓 <b>LLU B−.</b> It meets Mark&#x27;s &quot;2 more damage than mana&quot; burn rule, and the instant sweep hits the set&#x27;s many 2/2 tokens.<br><br>🎙 <b>Numot:</b> &quot;Oh, this card&#x27;s nice… very solid three mana instant.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/2/f27d50f0-d76e-4ce1-a8d9-d997af6a5b41.jpg?1789385716" width="240" alt="Gallia, the Merrymaker" loading="lazy"></td><td><b>Gallia, the Merrymaker</b> · Uncommon<br><br>🎧 <b>LR C−/C.</b> The 1R activation prices it out.<br><br>🎓 <b>LLU C−.</b> The RW seeded uncommon; good with Mabel.<br><br>🎙 <b>Numot:</b> &quot;Yeah, fine. Two drop.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/e/8/e8c1ce21-b77d-40bf-9ed1-478604e71f5f.jpg?1789014416" width="240" alt="Jiang Yanggu, Alone" loading="lazy"></td><td><b>Jiang Yanggu, Alone</b> · Uncommon<br><br>🎧 <b>LR C+/B−.</b> 5-mana 4/4 menace that loots and adds counters when a creature attacks alone.<br><br>🎓 <b>LLU C+.</b> Triggers on itself and gives card quality plus stats.<br><br>🎙 <b>Numot:</b> &quot;okay. I&#x27;m not going to say it&#x27;s crazy. It&#x27;s like fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/8/08657053-86f9-4c52-abf0-d9cdd443ae3b.jpg?1789127995" width="240" alt="Kiora of Fire and Ashes" loading="lazy"></td><td><b>Kiora of Fire and Ashes</b> · Uncommon<br><br>🎧 <b>LR B+.</b> 6 mana: 2/2 plus a 5/5 flying Dragon, with an 8-mana mana sink.<br><br>🎓 <b>LLU Alex B / Mark B+.</b> Two must-kill threats, and a great RG ramp target, &quot;far better than the UG Kiora.&quot;<br><br>🎙 <b>Numot:</b> &quot;Just a great uncommon even without the eight mana ability.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/4/54f64e95-5a97-4d7c-9939-7f33a3165562.jpg?1789470892" width="240" alt="Koth, the Geomancer" loading="lazy"></td><td><b>Koth, the Geomancer</b> · Uncommon<br><br>🎧 <b>LR B−.</b> 3/2 reach; landfall pings and adds R off Mountains.<br><br>🎓 <b>LLU Alex C− / Mark D+.</b> Heartwood ramp doesn&#x27;t trigger landfall.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s kind of neat. Sure. Yeah. Play that.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/9/f93da73c-ca8b-438e-8387-6109dac3fc1a.jpg?1789644549" width="240" alt="Marwyn, the Clearcutter" loading="lazy"></td><td><b>Marwyn, the Clearcutter</b> · Uncommon<br><br>🎧 <b>LR C+ (started C).</b> 1-mana 2/1 that sacs an artifact or land to draw.<br><br>🎓 <b>LLU Alex C / Mark C+.</b> Good early stats and late card advantage.<br><br>🎙 <b>Numot:</b> &quot;Just solid one drop.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/d/dd3faaf4-45ca-4714-8dbe-37102ec131cf.jpg?1789385851" width="240" alt="Pia, Determined Rebuilder" loading="lazy"></td><td><b>Pia, Determined Rebuilder</b> · Uncommon<br><br>🎧 <b>LR B− → B.</b> A 2/2 plus a 1/1 flying Thopter for 3.<br><br>🎓 <b>LLU C+.</b> The floor is already good, and Heartwood tokens help its pump.<br><br>🎙 <b>Numot:</b> &quot;a classic solid card.&quot; Good with Heartwood tokens.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/f/df818900-ce5e-4b0d-a927-c975cbef7eda.jpg?1789128002" width="240" alt="Tetsuko Umezawa, Pursuer" loading="lazy"></td><td><b>Tetsuko Umezawa, Pursuer</b> · Uncommon<br><br>🎧 <b>LR C+.</b> 2/4 double strike with prowess.<br><br>🎓 <b>LLU Alex C− / Mark D.</b> Boom or bust; great with trample from Konstrari Charm.<br><br>🎙 <b>Numot:</b> &quot;That card&#x27;s annoying.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/c/5c5afd5f-6f37-4c3e-83f0-68fdcea98810.jpg?1789729773" width="240" alt="Tomik, Izzet Sparkmage" loading="lazy"></td><td><b>Tomik, Izzet Sparkmage</b> · Uncommon<br><br>🎧 <b>LR build-around B.</b> +1 to your noncombat damage, so it pairs with the BR ping spells and sweepers.<br><br>🎓 <b>LLU Alex D+ / Mark C−.</b> A &quot;dorky stat line&quot;; combos with Fulminous Forte.<br><br>🎙 <b>Numot:</b> &quot;You&#x27;re going to need a handful of ways to make that relevant… I don&#x27;t think I would normally want to play.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/d/ad03ba90-2442-4a71-94df-2088b5b63662.jpg?1789127599" width="240" alt="Violent Echoes" loading="lazy"></td><td><b>Violent Echoes</b> · Uncommon<br><br>🎧 <b>LR B.</b> 4-mana instant, 6 damage; the excess empowers Jace, so it&#x27;s often a 2-for-1.<br><br>🎓 <b>LLU Alex B− / Mark B+ (Mark nearly gave A−).</b> &quot;Kill a 3-toughness creature, draw a card.&quot; It often won&#x27;t cantrip against 4+ toughness.<br><br>🎙 <b>Numot:</b> &quot;Yeah, great… Seems excellent.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/1/c1a00020-7c14-4503-a057-5763704bb83e.jpg?1788878311" width="240" alt="Way of the Pyromancer" loading="lazy"></td><td><b>Way of the Pyromancer</b> · Uncommon<br><br>🎧 <b>LR C+/B (LSV B).</b> Empower Jace 2, and walkers gain &quot;+1: add R&quot;, which ramps turn 2 into turn 4. Marshall worries about drawing it late.<br><br>🎓 <b>LLU Alex D+ → C / Mark C.</b> On turn 2 it lets you cast a 4-drop on turn 3, and an up-ticking Jace demands an answer.<br><br>🎙 <b>Numot:</b> &quot;real nice… it&#x27;s very good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/d/6d86e410-20c4-4248-96bf-5780ece6274a.jpg?1789729585" width="240" alt="Way of the Warlord" loading="lazy"></td><td><b>Way of the Warlord</b> · Uncommon<br><br>🎧 <b>LR B/B+ (LSV B+).</b> Empower Jace 5; the walker −4 deals 2 to a creature and 2 to a player. It&#x27;s 3-mana removal that leaves a Jace.<br><br>🎓 <b>LLU Alex C+ / Mark D+ (the biggest red split).</b> Alex later said &quot;C plus is probably a little bit high.&quot;<br><br>🎙 <b>Numot:</b> &quot;Card&#x27;s great. Excellent card.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/f/df8713cd-3f4b-43ef-adbd-e37c2617c617.jpg?1789128020" width="240" alt="Winter, Team Player" loading="lazy"></td><td><b>Winter, Team Player</b> · Uncommon<br><br>🎧 <b>LR C (build-around lean).</b> Convoke conflicts with attacking.<br><br>🎓 <b>LLU Alex D+ / Mark D.</b> Needs too many things to line up.<br><br>🎙 <b>Numot:</b> &quot;That doesn&#x27;t seem good to me.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/d/7d3b720d-f27c-462a-8f80-15748e5086e1.jpg?1789729762" width="240" alt="Artifist Acumen" loading="lazy"></td><td><b>Artifist Acumen</b> · Common<br><br>🎧 <b>LR no grade given.</b> Team first strike plus draw; at best a prowess playable.<br><br>🎓 <b>LLU Alex D+ / Mark D.</b> Only for UR spells.<br><br>🎙 <b>Numot:</b> a cantrip that doesn&#x27;t need a creature target. &quot;I&#x27;m not saying it&#x27;s good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/5/c596c4ec-8480-4be9-a45d-700398a126f6.jpg?1789556812" width="240" alt="Awaken the Inferno" loading="lazy"></td><td><b>Awaken the Inferno</b> · Common<br><br>🎧 <b>LR B−.</b> 5-mana: 6 damage plus a +1/+1 counter, or basic landcycling.<br><br>🎓 <b>LLU C+.</b> Playable even if never cycled; a &quot;premium top common&quot; like WOE&#x27;s Cut In. Alex expects it to be overlooked early.<br><br>🎙 <b>Numot:</b> red landcycler. &quot;Still solid enough to play basically always&quot;, but below the white and black cyclers.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/4/8414a98c-0c79-4884-bc9b-061a6456b392.jpg?1789060147" width="240" alt="Blazing Crescendo" loading="lazy"></td><td><b>Blazing Crescendo</b> · Common<br><br>🎧 <b>LR C−/D.</b> Reprint from Phyrexia: All Will Be One; mostly for prowess.<br><br>🎓 <b>LLU Alex C / Mark C−.</b> A clean 2-for-1 in low-curve red.<br><br>🎙 <b>Numot:</b> &quot;I like this card. I don&#x27;t know how good it is.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/a/3a64c5f4-9cfc-4d19-bd99-13d619b1aa9d.jpg?1789385708" width="240" alt="Chandra&#x27;s Emberling" loading="lazy"></td><td><b>Chandra&#x27;s Emberling</b> · Common<br><br>🎧 <b>LR C (optimistic; &quot;probably a D&quot;).</b> The prowess archetype&#x27;s inflection point.<br><br>🎓 <b>LLU Alex D / Mark D+.</b> Starts too small; Mark wanted trample.<br><br>🎙 <b>Numot:</b> &quot;Spellgorger Weird with haste… cool card.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/f/5f8771f9-8128-4818-a11d-41ea368cf697.jpg?1789127173" width="240" alt="Eardrum Rattler" loading="lazy"></td><td><b>Eardrum Rattler</b> · Common<br><br>🎧 <b>LR D → D+/C−.</b> Moved up because it pushes damage into Jaces.<br><br>🎓 <b>LLU Alex D+ / Mark D−.</b> The 1-mana activation &quot;kills it.&quot; Its weakness is a big reason RB and UR look worse.<br><br>🎙 <b>Numot:</b> &quot;Okay, it&#x27;s a two drop.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/b/cbfe3354-7ced-4773-9a4e-a937ae9f94f8.jpg?1789556808" width="240" alt="Heartstring Puller" loading="lazy"></td><td><b>Heartstring Puller</b> · Common<br><br>🎧 <b>LR C+/B−.</b> A 3/1 trample plus a 2/2 Cadet for 4. &quot;Not even going to be the best common.&quot;<br><br>🎓 <b>LLU C+ (Mark nearly B−).</b> Mixed body sizes; a good target for the deathtouch hybrid trick.<br><br>🎙 <b>Numot:</b> &quot;This is a great common… just a good common.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/1/11ba4fdd-cc03-4bb6-a493-91a9785771d0.jpg?1788878170" width="240" alt="No Admittance" loading="lazy"></td><td><b>No Admittance</b> · Common<br><br>🎧 <b>LR B.</b> 2-mana sorcery: 3 to any target plus Empower Jace 1.<br><br>🎓 <b>LLU Alex B− / Mark C+.</b> The top-graded red common.<br><br>🎙 <b>Numot:</b> &quot;Good… you&#x27;re not going to do much better for two mana.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/e/0e44f959-1322-4abd-b6eb-dea992307c0c.jpg?1789556811" width="240" alt="Skilled Battlecarver" loading="lazy"></td><td><b>Skilled Battlecarver</b> · Common<br><br>🎧 <b>LR C−.</b> A potent attacker, but only in a truly aggressive deck.<br><br>🎓 <b>LLU C.</b> Possibly red&#x27;s only good 2-drop attacker.<br><br>🎙 <b>Numot:</b> (?) &quot;Very annoying aggro card.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/7/b75bbf46-a421-467a-9433-6cf22398a3a5.jpg?1789556839" width="240" alt="Tether Technician" loading="lazy"></td><td><b>Tether Technician</b> · Common<br><br>🎧 <b>LR C.</b> 5-mana 4/5 reach; discard a card to deal 2.<br><br>🎓 <b>LLU Alex C / Mark D+.</b> They agreed to disagree; Mark says it&#x27;s worse than DSK&#x27;s Boilerbilges Ripper.<br><br>🎙 <b>Numot:</b> &quot;the classically good big red creature.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/5/b5b55617-684a-4036-be9b-a3b24fc9cd5a.jpg?1789385820" width="240" alt="Wrath of the Bloodmane" loading="lazy"></td><td><b>Wrath of the Bloodmane</b> · Common<br><br>🎧 <b>LR B.</b> Instant, 4 damage, costs 1 less with a legendary creature (there are many).<br><br>🎓 <b>LLU Alex C+ / Mark C.</b> With about 3 legends per pack it&#x27;s often 2 mana; Mark said he should have joined Alex at C+.<br><br>🎙 <b>Numot:</b> &quot;that&#x27;s just really good… Good common.&quot;</td></tr>
</table>

**Jump to:** [White (38)](#white) · [Blue (38)](#blue) · [Black (37)](#black) · [Red (39)](#red) · [Green (36)](#green) · [Multicolor (60)](#multicolor) · [Colorless (11)](#colorless) · [Lands (5)](#lands)

### Green

<table class="expertcards">
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/0/90ca5812-ceb5-46bd-b049-aed7ff10e6af.jpg?1788329370" width="240" alt="Garruk, Curse Breaker" loading="lazy"></td><td><b>Garruk, Curse Breaker</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;Seems good… You could do worse.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/a/9a446cae-e93c-4574-8ffd-7688f9729a8a.jpg?1788878191" width="240" alt="Hexhaven Invigorator" loading="lazy"></td><td><b>Hexhaven Invigorator</b> · Mythic<br><br>🎙 <b>Numot:</b> the GGGG cost is prohibitive, &quot;But even if you&#x27;re not playing this until like turn six. That&#x27;s pretty good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/1/91e787cb-a9b0-4353-86b4-a4340122fd2f.jpg?1789471487" width="240" alt="Omnipresence" loading="lazy"></td><td><b>Omnipresence</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;Unplayable.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/b/8be5ee47-8f8a-4e3c-b1a1-9ca0e1fdec7f.jpg?1789127270" width="240" alt="Tarmogoyf" loading="lazy"></td><td><b>Tarmogoyf</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;not unplayable… This is like a common, maybe uncommonish in power level.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/9/79dd5c54-5ea5-47b5-8f9b-50ed57a5ea45.jpg?1789385967" width="240" alt="Carnivorous Cultivator // Enroot" loading="lazy"></td><td><b>Carnivorous Cultivator // Enroot</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;already good… Real good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/3/930b89c3-4433-48de-829f-20fc3dbfced9.jpg?1789644837" width="240" alt="Gardenize" loading="lazy"></td><td><b>Gardenize</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;unplayable&quot;.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/d/3db2da7a-8088-4117-916b-f9c905d1b45b.jpg?1789127646" width="240" alt="Hungering Puppetbeast" loading="lazy"></td><td><b>Hungering Puppetbeast</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;that thing&#x27;s insane… Wow, that thing&#x27;s nuts.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/b/6b8789a6-3b63-4198-af5f-c2f2f49fafd9.jpg?1789470736" width="240" alt="Puppet Crafting" loading="lazy"></td><td><b>Puppet Crafting</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Probably bad though.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/c/7c725702-8696-4e5a-8318-62f5e2616d52.jpg?1789470857" width="240" alt="Simulacrum Shaper" loading="lazy"></td><td><b>Simulacrum Shaper</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Insane, the most value you&#x27;re ever going to get from a three drop.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/b/2bb7a8eb-227f-410b-859f-750ef0aea2f0.jpg?1789644841" width="240" alt="Verdant Kraken" loading="lazy"></td><td><b>Verdant Kraken</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;this card&#x27;s nuts… You cast this, you win. Insane.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/a/dad6afc9-8505-4cdd-bf79-e9ba4670f2bb.jpg?1789127966" width="240" alt="Edgar, Moonlit Sovereign" loading="lazy"></td><td><b>Edgar, Moonlit Sovereign</b> · Uncommon<br><br>🎧 <b>LR B+/B− → B.</b> 5-mana 4/4 flash that grows if you cast no spell.<br><br>🎓 <b>LLU Alex C− / Mark D+.</b> Two turns invested in one Unsummon target.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s cool… that&#x27;s not bad.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/8/28fbb55a-5c9d-45ee-bf42-a84b1048f5d2.jpg?1789127976" width="240" alt="Fblthp, Knows the Way" loading="lazy"></td><td><b>Fblthp, Knows the Way</b> · Uncommon<br><br>🎧 <b>LR B+.</b> Fetches X basics; usually a 4-mana 2/2 or 3/2 plus 2 lands. It helps splashes. Marshall has played it: &quot;absurd.&quot;<br><br>🎓 <b>LLU Alex B / Mark A−.</b> At 5 mana it&#x27;s a 3/2 that draws three lands. Mark suggests adding an off-colour basic even when not splashing. Alex: &quot;maybe I&#x27;m too low on it&quot; as long as you&#x27;re heavy green.<br><br>🎙 <b>Numot:</b> &quot;this one&#x27;s gross… fibble is great.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/7/f71958e9-6d6d-4393-8b49-567103b50877.jpg?1789470852" width="240" alt="Flourishing Grapple" loading="lazy"></td><td><b>Flourishing Grapple</b> · Uncommon<br><br>🎧 <b>LR sideboard B.</b> 1-mana instant bite, red or white targets only.<br><br>🎓 <b>LLU sideboard (no letter).</b> Mark: not a disaster to maindeck in Bo1, since about 70% of opposing pairs have a target.<br><br>🎙 <b>Numot:</b> sideboard hoser.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/d/1d535b5f-c916-4f16-89a7-9477578826d2.jpg?1788878290" width="240" alt="Ghalta the Unstoppable" loading="lazy"></td><td><b>Ghalta the Unstoppable</b> · Uncommon<br><br>🎧 <b>LR B → B− (&quot;I got carried away, I like dinosaurs&quot;).</b> Costs 9 minus your greatest power and gives your team trample; realistically cast for 4–5.<br><br>🎓 <b>LLU Alex C− / Mark D+ (&quot;probably too low&quot;).</b> Castable for about 5 off a 4/4, but it can rot in hand.<br><br>🎙 <b>Numot:</b> &quot;Yeah, solid.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/2/a2cc5d0e-9643-4ee2-81de-fa2c3bd1ab09.jpg?1789556822" width="240" alt="Hunter&#x27;s Axe" loading="lazy"></td><td><b>Hunter&#x27;s Axe</b> · Uncommon<br><br>🎧 <b>LR C+/C− (LSV &quot;C… maybe C−&quot;).</b> Pushed equipment: +2/+0 and trample or deathtouch when attacking.<br><br>🎓 <b>LLU Alex D / Mark D+.</b> Does nothing on defense.<br><br>🎙 <b>Numot:</b> &quot;It&#x27;s probably okay… kind of spicy.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/5/f5a0bb3e-8119-4739-8684-e61d1d607dcb.jpg?1789014406" width="240" alt="Jiang Yanggu, Never Alone" loading="lazy"></td><td><b>Jiang Yanggu, Never Alone</b> · Uncommon<br><br>🎧 <b>LR B+.</b> A 2/2 plus a 3/3 Mowu for 4 (&quot;Grave Titan for four&quot;).<br><br>🎓 <b>LLU Alex B− / Mark B.</b> Five power and toughness across two bodies, and it untaps Heartwood tokens.<br><br>🎙 <b>Numot:</b> &quot;Very good. Four drop.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/c/3cfa4fc6-4d90-4576-a83f-6496c7f21104.jpg?1789614764" width="240" alt="Loot, the Nexus" loading="lazy"></td><td><b>Loot, the Nexus</b> · Uncommon<br><br>🎧 <b>LR B.</b> 3-mana 2/1 dork that adds mana per distinct power among your creatures. Fragile, but you&#x27;re way ahead if it lives.<br><br>🎓 <b>LLU Alex C+ / Mark C−.</b> &quot;Really darn solid,&quot; but hard to set up on purpose.<br><br>🎙 <b>Numot:</b> &quot;Good. Three mana ramper.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/0/90f33f99-7bc5-42e1-815e-bfb4c2b74107.jpg?1789644564" width="240" alt="Marwyn, the Preserver" loading="lazy"></td><td><b>Marwyn, the Preserver</b> · Uncommon<br><br>🎧 <b>LR B−.</b> 2-mana 3/2 that returns lands from graveyard to hand.<br><br>🎓 <b>LLU Alex C+ / Mark B−.</b> Good early stats and late card advantage with mill.<br><br>🎙 <b>Numot:</b> &quot;2 mana 3/2 baseline&#x27;s fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/f/ff0bc30f-9d20-458e-808f-bdc2825905a5.jpg?1789387120" width="240" alt="Pia, Aether Ascetic" loading="lazy"></td><td><b>Pia, Aether Ascetic</b> · Uncommon<br><br>🎧 <b>LR build-around C.</b> Discard to tutor an enchantment; only worth it with an A-level target.<br><br>🎓 <b>LLU Alex C+ / Mark C−.</b> Needs a top enchantment to tutor; don&#x27;t take it early.<br><br>🎙 <b>Numot:</b> ranges from unplayable to &quot;very very good&quot; depending on the Ways you have. &quot;Looks nice.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/5/3546b93b-a7d1-451d-a369-22cc8ddcd00d.jpg?1788865848" width="240" alt="Restore with Empathy" loading="lazy"></td><td><b>Restore with Empathy</b> · Uncommon<br><br>🎧 <b>LR build-around, split: Marshall B in GW lifegain, LSV D (a UG rebuy tool at best).</b> <br><br>🎓 <b>LLU Alex D+ / Mark D.</b> Needs a slow format and good bombs to rebuy.<br><br>🎙 <b>Numot:</b> &quot;Love it… this is good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/e/e/eed83302-dc2c-45f4-a4bd-af9da51edef5.jpg?1789358701" width="240" alt="Ruric Thar, Magecrusher" loading="lazy"></td><td><b>Ruric Thar, Magecrusher</b> · Uncommon<br><br>🎧 <b>LR C+.</b> 7-mana 7/7 that can&#x27;t be countered and has hexproof until it deals combat damage.<br><br>🎓 <b>LLU Alex C+ → B− / Mark B−.</b> A good ramp target; weak to deathtouch and edicts.<br><br>🎙 <b>Numot:</b> &quot;very annoying. Pretty good. It is seven mana.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/e/d/edea6f70-a5a7-475d-b7f2-97933d0f32cf.jpg?1788329375" width="240" alt="Titanbones, Towering Heart" loading="lazy"></td><td><b>Titanbones, Towering Heart</b> · Uncommon<br><br>🎧 <b>LR B.</b> 4/3 reach that gets two counters per lifegain; gain 3 if it&#x27;s discarded.<br><br>🎓 <b>LLU Alex C− → D+ / Mark D.</b> &quot;Big dummy&quot;; 3 toughness dies to everything.<br><br>🎙 <b>Numot:</b> &quot;going to get real fat real quickly.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/8/98dc5470-507a-4364-8480-42607255e56c.jpg?1789729606" width="240" alt="Way of the Paradox" loading="lazy"></td><td><b>Way of the Paradox</b> · Uncommon<br><br>🎧 <b>LR C/C+ (LSV C+; B in a dedicated Jace deck, D without support).</b> Adds lifegain and an extra land drop on loyalty activations.<br><br>🎓 <b>LLU C (synergy tag for UG walker decks).</b> &quot;Three mana Explore with more play.&quot;<br><br>🎙 <b>Numot:</b> &quot;three mana empower five already good by itself.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/2/a252cb01-537b-4afe-9abc-81a98c4a1439.jpg?1789729602" width="240" alt="Way of the Wildspeaker" loading="lazy"></td><td><b>Way of the Wildspeaker</b> · Uncommon<br><br>🎧 <b>LR B+.</b> Empower Jace 7, and walkers gain −4: a 4/4 trampler. It effectively leaves a 4/4 plus a 3-loyalty Jace. Any green deck wants it.<br><br>🎓 <b>LLU Alex B− / Mark C+ (Mark: &quot;I like your grade more than mine&quot;).</b> It turns every other empower card into a 4/4 threat. &quot;One of the better uncommons to pick up early,&quot; but Unsummon hurts it.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s pretty good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/8/b8dfd087-2434-42c6-ac4c-1decbcdde2db.jpg?1789470909" width="240" alt="Yoshimaru, Scrappy Stray" loading="lazy"></td><td><b>Yoshimaru, Scrappy Stray</b> · Uncommon<br><br>🎧 <b>LR B−/B (LSV B).</b> 2-mana fight on ETB that leaves a 1/1, plus a 6-mana sink.<br><br>🎓 <b>LLU Alex C+ / Mark C.</b> Fight is weak and needs the bigger creature already out.<br><br>🎙 <b>Numot:</b> &quot;Yep, solid. Solid dog.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/b/1bf923c4-f0b7-4271-978c-fd2e79fe1cc8.jpg?1788878190" width="240" alt="Arcane Amphisbaena" loading="lazy"></td><td><b>Arcane Amphisbaena</b> · Common<br><br>🎧 <b>LR C+.</b> 2-mana 1/1 deathtouch plus Empower Jace 2.<br><br>🎓 <b>LLU Alex C / Mark C+.</b> Mark: &quot;the two drop of choice in a lot of decks.&quot;<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s a common, play all of them. Great card.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/e/0/e0de5f66-f0df-4866-9f73-104ce50411b4.jpg?1789127248" width="240" alt="Bestial Incursion" loading="lazy"></td><td><b>Bestial Incursion</b> · Common<br><br>🎧 <b>LR B/B− (LSV B−).</b> A 4/4 trample token for 4, flashback 6. Trample beats Jace-token chump blocks.<br><br>🎓 <b>LLU C+.</b> Card advantage, and good when milled or discarded. Unsummon ruins it.<br><br>🎙 <b>Numot:</b> &quot;a better Shadow Beast Sighting. Good card.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/8/18c59d60-2640-4576-9375-3ba38aa3ecb7.jpg?1789127120" width="240" alt="Budding Insurgent" loading="lazy"></td><td><b>Budding Insurgent</b> · Common<br><br>🎧 <b>LR C−/D+.</b> A 3/3 vigilance that sacs to kill an artifact or enchantment. Off-plan.<br><br>🎓 <b>LLU Alex C− / Mark D+.</b> Alex&#x27;s C− is a hedge in case Ways turn out central.<br><br>🎙 <b>Numot:</b> &quot;Yeah, solid enough.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/d/bd32d736-7a58-46b9-90b4-2cac3c3e80a1.jpg?1788521235" width="240" alt="Compel Brutality" loading="lazy"></td><td><b>Compel Brutality</b> · Common<br><br>🎧 <b>LR C+.</b> Instant bite, or a walker deals damage equal to its loyalty. Good with deathtouch and UG Jace. Floated as green&#x27;s best common.<br><br>🎓 <b>LLU C+.</b> &quot;Top green common territory.&quot; With a high-loyalty walker it hits for 4–6.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/5/a56e0f91-b128-4693-a949-53cb403f4fbf.jpg?1789127136" width="240" alt="Greenhouse Propagator" loading="lazy"></td><td><b>Greenhouse Propagator</b> · Common<br><br>🎧 <b>LR C+.</b> 2/3 mana dork that gains life when creatures enter.<br><br>🎓 <b>LLU Alex C+ / Mark C.</b> Lifegain &quot;sells me on it&quot;; curves into Bloombrute.<br><br>🎙 <b>Numot:</b> &quot;card&#x27;s great, very good common.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/7/073f4998-a204-447b-93d5-746ae87fd6a1.jpg?1788878192" width="240" alt="Inspired Tethermage" loading="lazy"></td><td><b>Inspired Tethermage</b> · Common<br><br>🎧 <b>LR C/D+ → C−.</b> A 3/2 that grows off loyalty counters.<br><br>🎓 <b>LLU D+.</b> &quot;Too vanilla for too long.&quot;<br><br>🎙 <b>Numot:</b> &quot;wow, that&#x27;s just a good common.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/2/02ee7817-40af-4fcf-a2df-eb218b669281.jpg?1788878199" width="240" alt="Something Worth Saving" loading="lazy"></td><td><b>Something Worth Saving</b> · Common<br><br>🎧 <b>LR C.</b> Mill 4, keep a permanent, gain 1. It enables several archetypes.<br><br>🎓 <b>LLU C.</b> Digs for strong uncommons and rares. Play one, two at most.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s not bad. Sure.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/6/b635389c-e286-4edb-80d1-23dbe4a18857.jpg?1789614751" width="240" alt="Sureshot Sower" loading="lazy"></td><td><b>Sureshot Sower</b> · Common<br><br>🎧 <b>LR C.</b> 2-mana 3/1 reach; pay 4 and discard it to kill a flyer.<br><br>🎓 <b>LLU Alex C / Mark C−.</b> &quot;Mostly just filler.&quot;<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/8/38589a7c-9cfb-4bcc-845e-9dc205095853.jpg?1789129937" width="240" alt="Tethermage&#x27;s Advantage" loading="lazy"></td><td><b>Tethermage&#x27;s Advantage</b> · Common<br><br>🎧 <b>LR D.</b> Plain pump trick.<br><br>🎓 <b>LLU Alex C / Mark C−.</b> Mark dropped from a planned C+ once he counted how little empower some decks run.<br><br>🎙 <b>Numot:</b> &quot;Decent.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/e/5/e5ed142b-2b61-4ef5-8b23-2db2a0a0319d.jpg?1789556814" width="240" alt="Vinelasher Adept" loading="lazy"></td><td><b>Vinelasher Adept</b> · Common<br><br>🎧 <b>LR C+.</b> 6-mana 2/4 reach plus three counters, with basic landcycling 2.<br><br>🎓 <b>LLU Alex C / Mark C−.</b> &quot;One of the lesser land cyclers.&quot;<br><br>🎙 <b>Numot:</b> green landcycler. &quot;That&#x27;s not bad. That&#x27;s better than the blue and better than the red.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/d/3d693cb0-681e-480a-8f70-07e94c39225c.jpg?1789385843" width="240" alt="Wrecking Gecko" loading="lazy"></td><td><b>Wrecking Gecko</b> · Common<br><br>🎧 <b>LR D+/C−.</b> 5-mana 5/5 ward 2; the ward is what lifts it.<br><br>🎓 <b>LLU Alex C− / Mark D+.</b> &quot;Not an embarrassing card to play.&quot;<br><br>🎙 <b>Numot:</b> &quot;just a big dumb green creature that will eventually kill you.&quot;</td></tr>
</table>

**Jump to:** [White (38)](#white) · [Blue (38)](#blue) · [Black (37)](#black) · [Red (39)](#red) · [Green (36)](#green) · [Multicolor (60)](#multicolor) · [Colorless (11)](#colorless) · [Lands (5)](#lands)

### Multicolor

<table class="expertcards">
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/1/f17d2792-b075-4c47-ad38-e7a7eaee5f8c.jpg?1788878199" width="240" alt="Aerid Konstrari" loading="lazy"></td><td><b>Aerid Konstrari</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;I assume all of these sphinx are just going to be bombs or at the very least very good flyers that are under costed.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/9/5905995b-7a20-4602-a7cc-90aa5089a082.jpg?1788878208" width="240" alt="Avatar of Burgeoning Echoes" loading="lazy"></td><td><b>Avatar of Burgeoning Echoes</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;That card&#x27;s insane… empower Jace 2 [on landfall] is nuts.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/8/986f9e98-9d8d-428b-9187-860745cf3269.jpg?1788878215" width="240" alt="Denzilore Fatehold" loading="lazy"></td><td><b>Denzilore Fatehold</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;I hate it. It&#x27;s great.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/4/6471b135-33a8-4005-9a07-ebb74e0bf145.jpg?1788878212" width="240" alt="Ingris Stingerquill" loading="lazy"></td><td><b>Ingris Stingerquill</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;That seems very good… Yeah, that card&#x27;s great.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/d/2d6ff182-a853-4898-895b-072c89324ca7.jpg?1788878236" width="240" alt="Kwia Vigorbloom" loading="lazy"></td><td><b>Kwia Vigorbloom</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;Seems pretty good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/7/a7ad622a-42ff-48fa-ae95-12e0a5bd9387.jpg?1788878220" width="240" alt="Uldaros Theorix" loading="lazy"></td><td><b>Uldaros Theorix</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;Whoa… That card is sweet.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/3/c3192390-1518-49fc-8716-f2c7a0384f39.jpg?1789646811" width="240" alt="Codie, Ravenous Codex" loading="lazy"></td><td><b>Codie, Ravenous Codex</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;cool, but you have to build a prepared deck.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/a/ca894d25-b9fc-4cd6-8746-70d8c2868721.jpg?1789614779" width="240" alt="Entrust the Spark" loading="lazy"></td><td><b>Entrust the Spark</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Obviously not good in limited.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/a/7a44581f-8fc4-457d-888a-1e211090ee7e.jpg?1789470870" width="240" alt="Frostbite Pyromental" loading="lazy"></td><td><b>Frostbite Pyromental</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s cool&quot;. The opponent won&#x27;t want to take the hit early.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/a/3abcae65-5b21-4c98-adad-34b8bc76ea3a.jpg?1789014541" width="240" alt="Karn, Gilded Guardian" loading="lazy"></td><td><b>Karn, Gilded Guardian</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Also lame. Not a good payoff card.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/3/a/3afdc75a-1bf5-4f2f-84eb-d82f77a095cd.jpg?1789127648" width="240" alt="Null Summoner" loading="lazy"></td><td><b>Null Summoner</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s great… Card&#x27;s great.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/f/cf0eec8c-0475-4050-8144-481a9bb13a0f.jpg?1789127661" width="240" alt="Proctor of Potential" loading="lazy"></td><td><b>Proctor of Potential</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;seems good&quot; with the surveil cards.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/e/1ef12dcf-df50-4da6-8c4c-e2937ba9698e.jpg?1789127651" width="240" alt="Solarium Sentry" loading="lazy"></td><td><b>Solarium Sentry</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Just better watch, I guess. Sure.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/1/5142bbb6-194c-4b12-b11a-1a21c9fe81a6.jpg?1788260690" width="240" alt="Solitary Cell" loading="lazy"></td><td><b>Solitary Cell</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;It&#x27;s fine. Not amazing.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/7/a7d78297-7411-4ec5-8931-a25146869d5b.jpg?1789385971" width="240" alt="Stinging Vitriol" loading="lazy"></td><td><b>Stinging Vitriol</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;maybe not very solid, but it&#x27;s… good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/5/6529d399-677e-45a6-ac3e-12a0b10f6c37.jpg?1789644886" width="240" alt="Tam, the Possibility" loading="lazy"></td><td><b>Tam, the Possibility</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Oh garbage.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/7/1703306d-6a3d-4ab8-bf58-a9992236ef0f.jpg?1789385792" width="240" alt="Tenured Tethermage" loading="lazy"></td><td><b>Tenured Tethermage</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Whoa, this card&#x27;s nuts… it&#x27;s very good.&quot; He corrected his misread that it enters as a 3/3.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/8/a803dbe7-153a-4e92-ad4d-c2babebe003d.jpg?1789127665" width="240" alt="Vindictive Triumph" loading="lazy"></td><td><b>Vindictive Triumph</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;It&#x27;s good. It&#x27;s good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/3/f3869752-eade-4e7a-8dd1-68cafb9e10be.jpg?1789128008" width="240" alt="Vraska, Soul of Stone" loading="lazy"></td><td><b>Vraska, Soul of Stone</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s good… Hard to cast maybe.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/c/5c28b012-5efb-488f-a1c1-09e2dddfd6ee.jpg?1789127776" width="240" alt="Vraska, the Cutting Glare" loading="lazy"></td><td><b>Vraska, the Cutting Glare</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;that&#x27;s great&quot;.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/b/6b804503-9c70-4b1f-bb13-a65fb6dd3ef8.jpg?1789644843" width="240" alt="Bloombrute" loading="lazy"></td><td><b>Bloombrute</b> · Uncommon<br><br>🎧 <b>LR A− (LSV B+–A−).</b> 4-mana 4/4 that draws on lifegain once per turn. &quot;This card&#x27;s busted.&quot; Highest-graded C/U in the episode, tied with Twisted Fates and Hapatra.<br><br>🎓 <b>LLU Alex B− / Mark C.</b> Huge upside if it sticks; Mark says you don&#x27;t get the card every turn.<br><br>🎙 <b>Numot:</b> &quot;Great.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/6/b61bcef7-5832-45e6-a2bc-26d4f23707fc.jpg?1788878210" width="240" alt="Clash of Elements" loading="lazy"></td><td><b>Clash of Elements</b> · Uncommon<br><br>🎧 <b>LR B.</b> 3-mana instant that answers any nonland permanent (top of library + 2 damage, or bottom).<br><br>🎓 <b>LLU Alex B− / Mark B.</b> Cheaper top-or-bottom removal. Against a token, don&#x27;t choose top.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s neat. Three mana tuck.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/3/03f9839c-aa07-4ee7-847b-091e47ab80c4.jpg?1789470711" width="240" alt="Craftwork Crusher" loading="lazy"></td><td><b>Craftwork Crusher</b> · Uncommon<br><br>🎧 <b>LR B+/B (LSV &quot;maybe A− if you&#x27;re enabling it&quot;).</b> A 7/5 trample for 7 that picks two of: 4 damage, a 2/2, or draw. &quot;The perfect payoff,&quot; but RRGG.<br><br>🎓 <b>LLU A−.</b> Compared to Titan of Industry. The highest grade in the review.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s insane… an insane uncommon. What? Wow.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/f/cfaa3ebd-5c21-4e99-a0dd-8426d19b53a5.jpg?1789644852" width="240" alt="Desperate Futurescribe" loading="lazy"></td><td><b>Desperate Futurescribe</b> · Uncommon<br><br>🎧 <b>LR B.</b> 4-mana 3/4 flyer that pushes aggro.<br><br>🎓 <b>LLU Alex B− / Mark B.</b> A Jace token enables its counter immediately. Mark: &quot;just incredible.&quot;<br><br>🎙 <b>Numot:</b> &quot;also great&quot;.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/c/7c619fed-2394-4efc-8cdc-6df5f51c1f57.jpg?1789127743" width="240" alt="Edgar, Ancient Bloodlord" loading="lazy"></td><td><b>Edgar, Ancient Bloodlord</b> · Uncommon<br><br>🎧 <b>LR B−/B.</b> 2-mana 2/3 sac outlet that gains life.<br><br>🎓 <b>LLU C+.</b> &quot;Almost a pull to WB, but maybe not quite.&quot;<br><br>🎙 <b>Numot:</b> &quot;It&#x27;s decent.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/f/cfc54011-647e-4428-bcdb-59400e1da49d.jpg?1789127637" width="240" alt="Fatehold Charm" loading="lazy"></td><td><b>Fatehold Charm</b> · Uncommon<br><br>🎧 <b>LR B.</b> &quot;Good with lots of creatures out, good with no creatures out.&quot;<br><br>🎓 <b>LLU C+ (&quot;might even be too low… could creep into B−&quot;; Alex later said he&#x27;d go higher).</b> <br><br>🎙 <b>Numot:</b> &quot;seems like an insane charm. Damn.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/2/8295c48c-b4dd-4bc1-a206-04cf12b79bbd.jpg?1789470746" width="240" alt="Grim Repriser" loading="lazy"></td><td><b>Grim Repriser</b> · Uncommon<br><br>🎧 <b>LR B.</b> 2-mana 2/2 prowess that returns once with non-combat damage. &quot;Really annoying card to see early.&quot;<br><br>🎓 <b>LLU C+.</b> Good if you end up BR; not worth pivoting into pings for.<br><br>🎙 <b>Numot:</b> &quot;a fine two drop.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/f/cf7c1534-af41-4991-b3c3-f0a34ae330b5.jpg?1789385991" width="240" alt="Hapatra, the Desert Fang" loading="lazy"></td><td><b>Hapatra, the Desert Fang</b> · Uncommon<br><br>🎧 <b>LR B+/A− (LSV A−, &quot;it&#x27;s just always going to work&quot;).</b> 5-mana 3/3 that places −1/−1 counters equal to the greatest MV in your graveyard.<br><br>🎓 <b>LLU Alex B / Mark B+.</b> The MV-6 land cyclers make it kill almost anything.<br><br>🎙 <b>Numot:</b> &quot;Oh, that&#x27;s good… kill something a lot of times.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/1/910a1f41-17fd-4ab0-9597-7151e79dc760.jpg?1789127630" width="240" alt="Heartwood Crafter // Soul Tether" loading="lazy"></td><td><b>Heartwood Crafter // Soul Tether</b> · Uncommon<br><br>🎧 <b>LR B−.</b> Enters prepared with Soul Tether: Rampant Growth on a body.<br><br>🎓 <b>LLU Alex C+ / Mark B−.</b> Soul Tether on turn 2 is strong. Great in an opening hand, weak as a topdeck.<br><br>🎙 <b>Numot:</b> &quot;pretty solid&quot;. A turn-2 Heartwood token.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/1/8151f5f5-e9f6-4fbe-b543-f456ebf22aa5.jpg?1789127745" width="240" alt="Kiora of Salt and Sand" loading="lazy"></td><td><b>Kiora of Salt and Sand</b> · Uncommon<br><br>🎧 <b>LR build-around B/B− (A− floated first).</b> Gives your walkers −8: an 8/8 hexproof Leviathan.<br><br>🎓 <b>LLU Alex C / Mark C− (Alex talked down a tier).</b> &quot;Upside trap.&quot;<br><br>🎙 <b>Numot:</b> &quot;that&#x27;s fine&quot;. Getting to 8 loyalty is hard.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/d/7d29dfa1-9582-47bc-8f42-62b611bdcc4e.jpg?1789127645" width="240" alt="Konstrari Charm" loading="lazy"></td><td><b>Konstrari Charm</b> · Uncommon<br><br>🎧 <b>LR C.</b> &quot;This thing sucks&quot; next to Stingerquill Charm; the counters-plus-trample mode is the real one.<br><br>🎓 <b>LLU C+.</b> The counters + trample mode is &quot;a very good combat trick&quot; and the main use.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s okay… Easily the worst charm we&#x27;ve seen.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/7/47abea4b-9848-48aa-bc1b-f04f4799e920.jpg?1789385857" width="240" alt="Mabel, Valley Hero" loading="lazy"></td><td><b>Mabel, Valley Hero</b> · Uncommon<br><br>🎧 <b>LR B/B+.</b> Every creature that enters gets a +1/+1 counter; a must-kill on turn 3.<br><br>🎓 <b>LLU Alex B− / Mark C (Alex conceded mid-discussion but stated no new grade).</b> <br><br>🎙 <b>Numot:</b> &quot;That&#x27;s cool.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/4/94c290ce-252c-42b3-bcb0-c1ef621df566.jpg?1789470861" width="240" alt="Mind Meanderer" loading="lazy"></td><td><b>Mind Meanderer</b> · Uncommon<br><br>🎧 <b>LR B−/B (LSV B).</b> 6-mana 4/4 flyer that fights; a 2-for-1 vs small and medium creatures.<br><br>🎓 <b>LLU Alex B− / Mark C+.</b> A flying Indrik Stomper; weaker if the format is full of deathtouch.<br><br>🎙 <b>Numot:</b> &quot;still good&quot; (a flying Affectionate Indrik that is harder to cast).</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/e/6/e61b9d48-0ace-4453-afe0-a1024444bac0.jpg?1788329390" width="240" alt="Paradox Shaper // Omit Variables" loading="lazy"></td><td><b>Paradox Shaper // Omit Variables</b> · Uncommon<br><br>🎧 <b>LR C+ (B− if UB lacks threshold enablers).</b> A re-preparing loop build-around.<br><br>🎓 <b>LLU Alex C / Mark D+.</b> An engine for a deck-yourself-to-zero plan.<br><br>🎙 <b>Numot:</b> &quot;repeatable self mill… Neato.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/4/04e64af7-cca1-499e-8951-f386e84c8b5b.jpg?1789644850" width="240" alt="Primal Witchstalker" loading="lazy"></td><td><b>Primal Witchstalker</b> · Uncommon<br><br>🎧 <b>LR B (maybe B+).</b> 3-mana 2/1 menace that mills 4 and returns a land untapped.<br><br>🎓 <b>LLU Alex B− / Mark C+.</b> The BG graveyard-midrange signpost.<br><br>🎙 <b>Numot:</b> &quot;That seems good too.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/c/6c1c790b-9e0e-4964-9ea3-554843907f06.jpg?1788329412" width="240" alt="Prudent Fateseer // Peer Review" loading="lazy"></td><td><b>Prudent Fateseer // Peer Review</b> · Uncommon<br><br>🎧 <b>LR C+/B−.</b> LSV prefers Chronologist; the 1/4 body is dull.<br><br>🎓 <b>LLU C.</b> It would have been very strong with flying on either side.<br><br>🎙 <b>Numot:</b> &quot;solid&quot;.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/6/8/68fddb6a-86d4-4ebb-907d-fdcaadebc4b3.jpg?1789556898" width="240" alt="Recursive Recruitment" loading="lazy"></td><td><b>Recursive Recruitment</b> · Uncommon<br><br>🎧 <b>LR B.</b> Two 2/2s for 4, then flashback for big tokens. &quot;Deck defining.&quot;<br><br>🎓 <b>LLU Alex B− / Mark C+.</b> Board presence buys time for the flashback; Mark calls it splashable in BG.<br><br>🎙 <b>Numot:</b> &quot;Still a good card… Eight mana later on, two five fives. Great.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/8/28d84ef6-e190-46d4-882d-1cea5e111e2a.jpg?1789644883" width="240" alt="Saheeli, Jewel of Avishkar" loading="lazy"></td><td><b>Saheeli, Jewel of Avishkar</b> · Uncommon<br><br>🎧 <b>LR B+.</b> &quot;Basically a Murmuring Mystic&quot; with hasty Thopters off any noncreature spell. &quot;Don&#x27;t let them untap with Saheeli.&quot;<br><br>🎓 <b>LLU C (&quot;a responsible C&quot;).</b> Splashable into artifact-leaning decks.<br><br>🎙 <b>Numot:</b> &quot;Great.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/1/81733ff7-e611-43ee-bf38-6bb700676017.jpg?1789127652" width="240" alt="Stingerquill Charm" loading="lazy"></td><td><b>Stingerquill Charm</b> · Uncommon<br><br>🎧 <b>LR B+.</b> &quot;Basically a Lightning Bolt,&quot; or a hasty 2/2, or first strike + deathtouch.<br><br>🎓 <b>LLU Alex B− / Mark B.</b> &quot;Probably the best charm.&quot; Alex started at B and dropped it because the rest of BR is weak.<br><br>🎙 <b>Numot:</b> &quot;that one&#x27;s pretty good, too.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/4/84b1c268-3b8a-41b6-92e3-a2ce0cc3d738.jpg?1788329418" width="240" alt="Stingerquill Voxmancer // Vicious Verse" loading="lazy"></td><td><b>Stingerquill Voxmancer // Vicious Verse</b> · Uncommon<br><br>🎧 <b>LR B, if BR works.</b> 1-drop ping enabler, &quot;a lot worse&quot; if the deck doesn&#x27;t come together.<br><br>🎓 <b>LLU Alex D+ / Mark C−.</b> Fragile; only good with many payoffs.<br><br>🎙 <b>Numot:</b> &quot;this is a good one drop… consistent source of bing.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/8/2835c9aa-0904-44db-8da2-e8c4e04201aa.jpg?1789127659" width="240" alt="Theorix Charm" loading="lazy"></td><td><b>Theorix Charm</b> · Uncommon<br><br>🎧 <b>LR B.</b> &quot;Spell Pierce plus Disfigure plus mill three draw a card.&quot;<br><br>🎓 <b>LLU C+.</b> More like two mana&#x27;s worth; Mark is confident it doesn&#x27;t reach B.<br><br>🎙 <b>Numot:</b> &quot;still good, but that seems a lot worse than the blue white one.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/7/c7c0765d-38fd-4d7b-bfb4-49b10ff5939b.jpg?1789614785" width="240" alt="Twisted Fates" loading="lazy"></td><td><b>Twisted Fates</b> · Uncommon<br><br>🎧 <b>LR B+ → A−.</b> Destroys any nonland permanent and gives your team counters. &quot;The last card cast in a lot of games.&quot; WWB is intense.<br><br>🎓 <b>LLU B.</b> &quot;A banger,&quot; likely one of the best uncommons; triple pips keep it with the WB drafter.<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s sweet… good enough.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/b/2b198e10-b507-4314-a29c-a219f06e48b7.jpg?1789127656" width="240" alt="Vigorbloom Charm" loading="lazy"></td><td><b>Vigorbloom Charm</b> · Uncommon<br><br>🎧 <b>LR B+.</b> Protect, draw + gain 3, or +counter + fight.<br><br>🎓 <b>LLU B−.</b> &quot;Probably the second-best charm&quot;; the lifegain mode matters more in this set.<br><br>🎙 <b>Numot:</b> &quot;another good charm&quot;.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/c/acefc515-bf97-4dc0-b0f7-ae8ae5a61671.jpg?1788329423" width="240" alt="Vigorbloom Vanguard // Seed Suture" loading="lazy"></td><td><b>Vigorbloom Vanguard // Seed Suture</b> · Uncommon<br><br>🎧 <b>LR B+/B.</b> Effectively a 3/3 vigilance for 2+1 that gains life.<br><br>🎓 <b>LLU C+.</b> Only exciting in GW, or RW counters.<br><br>🎙 <b>Numot:</b> &quot;Good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/c/6/c63d5b0e-ee72-42ed-aa7e-484ba84507cd.jpg?1789007648" width="240" alt="Warrior&#x27;s Blades" loading="lazy"></td><td><b>Warrior&#x27;s Blades</b> · Uncommon<br><br>🎧 <b>LR B.</b> A Lightning Helix, then decent equipment. &quot;Would play multiple copies.&quot;<br><br>🎓 <b>LLU Alex C+ / Mark C.</b> Equip 3 is expensive. Alex compared it to the Hobbit&#x27;s Crude Bent Blade.<br><br>🎙 <b>Numot:</b> (?) &quot;Lightning Helix on a trusty machete is good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/d/7d17f7e3-7b63-4674-9024-4fd1827f40ec.jpg?1788329429" width="240" alt="Woodwork Prodigy // Soul Tether" loading="lazy"></td><td><b>Woodwork Prodigy // Soul Tether</b> · Uncommon<br><br>🎧 <b>LR C+.</b> 3/3 for 3 that re-prepares Soul Tether each upkeep.<br><br>🎓 <b>LLU Alex C+ / Mark C.</b> Endless Heartwoods with diminishing returns.<br><br>🎙 <b>Numot:</b> &quot;It&#x27;s fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/b/bb975803-9bf2-401e-9414-d272df314398.jpg?1789556847" width="240" alt="Blessed Ghoul" loading="lazy"></td><td><b>Blessed Ghoul</b> · Common<br><br>🎧 <b>LR C+/C.</b> Hybrid lifelink recursion. Marshall: &quot;the glue that holds the entire set together.&quot;<br><br>🎓 <b>LLU Alex D / Mark D+.</b> Undersupported synergy.<br><br>🎙 <b>Numot:</b> &quot;I hate this type of card.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/e/5e77fbf0-9d1f-4e7d-a02e-43065d11b0d9.jpg?1789692643" width="240" alt="Blossom-Blessed Angel // Seed Suture" loading="lazy"></td><td><b>Blossom-Blessed Angel // Seed Suture</b> · Common<br><br>🎧 <b>LR C.</b> 4-mana 2/4 flying vigilance that enters prepared with Seed Suture. &quot;Ludicrous at common, and yet a C.&quot;<br><br>🎓 <b>LLU C (&quot;may have graded a little too low&quot;).</b> A 3/5 flyer if the counter goes on itself.<br><br>🎙 <b>Numot:</b> &quot;Good.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/7/87b40df5-5c0a-41f5-a09c-a04f17066a91.jpg?1788521570" width="240" alt="Charge the Sanctum" loading="lazy"></td><td><b>Charge the Sanctum</b> · Common<br><br>🎧 <b>LR C/C−.</b> Hybrid team pump; risks a blowout at 3 mana.<br><br>🎙 <b>Numot:</b> &quot;I don&#x27;t like these type of cards but that&#x27;s probably fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/e/de94d388-919d-44ff-baef-8c90a417ac6d.jpg?1789637792" width="240" alt="Emergency Phytomedic // Seed Suture" loading="lazy"></td><td><b>Emergency Phytomedic // Seed Suture</b> · Common<br><br>🎧 <b>LR C/C+ (LSV C+).</b> 1-drop that grows to 2/2 and gains 1. &quot;Happy playing that card pretty much always.&quot;<br><br>🎓 <b>LLU C− (Alex: &quot;maybe even C+&quot;).</b> <br><br>🎙 <b>Numot:</b> &quot;Good enough.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/9/29e7ec16-0c16-48aa-8e09-ce6e0d5bd40b.jpg?1789060173" width="240" alt="Fatehold Chronologist // Peer Review" loading="lazy"></td><td><b>Fatehold Chronologist // Peer Review</b> · Common<br><br>🎧 <b>LR B−.</b> Hybrid; &quot;a curve in and of itself&quot;: a 1/2 flyer, then Peer Review.<br><br>🎓 <b>LLU C.</b> Helps WU tempo flyers on both halves.<br><br>🎙 <b>Numot:</b> &quot;Seems fine.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/a/9/a9793ce9-5a0b-41fe-b9ad-02f6f7da2481.jpg?1789644856" width="240" alt="Ferocity of the Hunt" loading="lazy"></td><td><b>Ferocity of the Hunt</b> · Common<br><br>🎧 <b>LR C−/C.</b> Flash deathtouch aura that returns the creature when it dies. &quot;Normally a very solid D, so that&#x27;s a compliment.&quot;<br><br>🎓 <b>LLU Alex D+ / Mark C−.</b> Mark argued it up; Alex was convinced but kept his grade.<br><br>🎙 <b>Numot:</b> &quot;a good take on this effect&quot;.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/e/7e324816-552f-455d-97c4-5ea6b26d2e6e.jpg?1789127576" width="240" alt="Hallway Heckler // Vicious Verse" loading="lazy"></td><td><b>Hallway Heckler // Vicious Verse</b> · Common<br><br>🎧 <b>LR C.</b> 2/3 looter with a prepare ping (Vicious Verse). &quot;Bread-and-butter.&quot;<br><br>🎓 <b>LLU Alex D+ / Mark C−.</b> Rummage is much weaker on a 3-drop.<br><br>🎙 <b>Numot:</b> a 3-mana 2/3 rummager that pings. No explicit grade.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/2/42e28bd2-486b-45d4-8840-6e33c19c2d57.jpg?1789556881" width="240" alt="Konstrari Improviser // Soul Tether" loading="lazy"></td><td><b>Konstrari Improviser // Soul Tether</b> · Common<br><br>🎧 <b>LR C−/C.</b> &quot;A lot of mana to put a lot of mediocre stuff on the battlefield.&quot;<br><br>🎓 <b>LLU C.</b> Fixes the missing R/G source.<br><br>🎙 <b>Numot:</b> 2-mana 2/2 that makes a Heartwood. No explicit grade.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/7/e/7e5a640b-fd88-4b5a-9dfc-1d8f5a5cef41.jpg?1789127516" width="240" alt="Semester Foreseer // Peer Review" loading="lazy"></td><td><b>Semester Foreseer // Peer Review</b> · Common<br><br>🎧 <b>LR C.</b> 4-mana 3/4 that surveils and enters prepared (Peer Review). The hosts note that SOS&#x27;s similar Campus Composer underperformed.<br><br>🎙 <b>Numot:</b> (?) &quot;decent common&quot; (4-mana 3/4, surveil, Peer Review).</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/3/b3d33df2-a77b-4c2e-ba7f-2cc9c1505f9b.jpg?1788878215" width="240" alt="Tam&#x27;s Resistance" loading="lazy"></td><td><b>Tam&#x27;s Resistance</b> · Common<br><br>🎧 <b>LR C.</b> Counter + vigilance, then Empower Jace 4. Needs a creature target.<br><br>🎓 <b>LLU C−.</b> Better once UG has several ways to spend loyalty.<br><br>🎙 <b>Numot:</b> &quot;It&#x27;s really good for two mana.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/f/b/fb6bad96-841d-4738-8e62-92f346f914fd.jpg?1789556930" width="240" alt="Theorix Metamage // Omit Variables" loading="lazy"></td><td><b>Theorix Metamage // Omit Variables</b> · Common<br><br>🎧 <b>LR C+.</b> Enabler plus semi-payoff; a 3/3 flyer at threshold.<br><br>🎓 <b>LLU Alex C− / Mark D+.</b> Too understated on curve.<br><br>🎙 <b>Numot:</b> &quot;Okay, cool.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/5/55f85984-0137-4899-8993-bbc8c4794d33.jpg?1789556940" width="240" alt="Twinned Vision" loading="lazy"></td><td><b>Twinned Vision</b> · Common<br><br>🎧 <b>LR C+/C−.</b> The discard-a-card flashback cost &quot;really dents it.&quot;<br><br>🎓 <b>LLU Alex C / Mark C+.</b> &quot;The most gluey of glue cards.&quot;<br><br>🎙 <b>Numot:</b> no verdict.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/e/0eae2efb-bf25-48ee-9c07-9098008110ad.jpg?1789556787" width="240" alt="Void Extrapolator // Omit Variables" loading="lazy"></td><td><b>Void Extrapolator // Omit Variables</b> · Common<br><br>🎧 <b>LR C.</b> UB self-mill bread-and-butter (prepared with Omit Variables).<br><br>🎓 <b>LLU Alex D+ / Mark C−.</b> Filler 2-drop.<br><br>🎙 <b>Numot:</b> no strong verdict. A self-mill enabler.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/0/8096bc9a-a610-448f-bef2-7230e17e9777.jpg?1789127692" width="240" alt="Whiplash Wordsmith // Vicious Verse" loading="lazy"></td><td><b>Whiplash Wordsmith // Vicious Verse</b> · Common<br><br>🎧 <b>LR C/C+.</b> 5 mana: a prepare-ping, then a 3/3 flying haste.<br><br>🎓 <b>LLU D+ (&quot;somewhat optimistic&quot;).</b> Awful on defense.<br><br>🎙 <b>Numot:</b> &quot;that&#x27;s like okay.&quot;</td></tr>
</table>

**Jump to:** [White (38)](#white) · [Blue (38)](#blue) · [Black (37)](#black) · [Red (39)](#red) · [Green (36)](#green) · [Multicolor (60)](#multicolor) · [Colorless (11)](#colorless) · [Lands (5)](#lands)

### Colorless

<table class="expertcards">
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/e/e/ee609b68-5c9c-43e0-aff4-eb1bbc8b2911.jpg?1789060230" width="240" alt="Emrakul, the Exigent Doom" loading="lazy"></td><td><b>Emrakul, the Exigent Doom</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;so so expensive… it&#x27;s going to rot in my hand. But it&#x27;s cool. That&#x27;s all it is.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/7/d71d250f-c0e0-44b2-877c-76f3bcab4f34.jpg?1789385887" width="240" alt="The Echoverse Fulcrum" loading="lazy"></td><td><b>The Echoverse Fulcrum</b> · Mythic<br><br>🎙 <b>Numot:</b> &quot;Oh, that&#x27;s cool. Another wrath effect.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/1/e/1ebbbddb-2dc3-4194-b72b-13bcebe2ab89.jpg?1788878301" width="240" alt="Karn, Argent Defender" loading="lazy"></td><td><b>Karn, Argent Defender</b> · Rare<br><br>🎙 <b>Numot:</b> read aloud only (&quot;blah blah blah&quot;), no verdict.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/2/024bce1e-a5f3-4292-bc17-d0355a5d65e1.jpg?1789614867" width="240" alt="Archive Arbiter" loading="lazy"></td><td><b>Archive Arbiter</b> · Uncommon<br><br>🎧 <b>LR C+.</b> 6-mana 4/4 flyer: destroy a noncreature, nonland permanent (walkers!) or gain 4. &quot;One goes a long way.&quot;<br><br>🎓 <b>LLU Alex C / Mark C−.</b> It can destroy a Jace, a removal enchantment or a Way.<br><br>🎙 <b>Numot:</b> &quot;This is probably better than it looks.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/e/0edba64a-39cf-4a8d-ba20-4f7da10b6c3d.jpg?1789614864" width="240" alt="Eye of Jace" loading="lazy"></td><td><b>Eye of Jace</b> · Uncommon<br><br>🎧 <b>LR build-around C (Marshall, &quot;prove it&quot;) / C+ (LSV).</b> Surveils each upkeep, then drains 2 at threshold. LSV says it has enough homes (UB, BG, prowess) to take on spec.<br><br>🎓 <b>LLU Alex C / Mark C−.</b> It&#x27;s great on turn 1 and a bad topdeck. Alex&#x27;s First Impressions call: it could be &quot;quite a bit better than it looks… or one of the worst cards in the set.&quot;<br><br>🎙 <b>Numot:</b> &quot;That&#x27;s not bad… That seems okay&quot; in WU.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/0/5/05102c46-96f8-44a0-a1e6-e388fa5e0841.jpg?1789557046" width="240" alt="Traxos, Scourge Eternal" loading="lazy"></td><td><b>Traxos, Scourge Eternal</b> · Uncommon<br><br>🎧 <b>LR B/C+.</b> 4-mana 5/4 trample that untaps when you cast an artifact or creature spell, which is trivially easy. Stomps Jaces.<br><br>🎓 <b>LLU Alex C− / Mark C+.</b> Mark rates it a 5/4 trampler that stays active if you keep casting creatures; Alex says it&#x27;s still a 4-drop with no ETB.<br><br>🎙 <b>Numot:</b> &quot;Four mana 5/4 trampler then. Not bad.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/d/4d4b3bf7-a149-4099-b97d-4e36a87dfa60.jpg?1789385875" width="240" alt="Afterthought Sentry" loading="lazy"></td><td><b>Afterthought Sentry</b> · Common<br><br>🎧 <b>LR D.</b> Maybe a sideboard card.<br><br>🎓 <b>LLU D+.</b> Filler; RB may need the 2-drop.<br><br>🎙 <b>Numot:</b> &quot;Filler with artifact synergy&quot;.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/b/6/b6331218-dbb8-44a9-8ba5-5fb1ab41c5c0.jpg?1788878239" width="240" alt="Keeper of the Quiet Hour" loading="lazy"></td><td><b>Keeper of the Quiet Hour</b> · Common<br><br>🎧 <b>LR C/C−.</b> 3-mana 3/2 plus Empower Jace 2. Good for a colourless common.<br><br>🎓 <b>LLU Alex C− / Mark C.</b> Fine filler.<br><br>🎙 <b>Numot:</b> &quot;Colorless common… that&#x27;s just good… We&#x27;ll play that.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/5/d/5d4a8e5f-0024-4da3-a2f5-edb48b12e733.jpg?1789556949" width="240" alt="Living Library" loading="lazy"></td><td><b>Living Library</b> · Common<br><br>🎧 <b>LR no letter grade; clearly negative (&quot;Nah.</b> Nope. I would not do this&quot;).<br><br>🎓 <b>LLU Alex D+ / Mark D.</b> &quot;Very slow.&quot;<br><br>🎙 <b>Numot:</b> &quot;not awful… playable&quot; but rarely run.</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/8/b/8b07409a-1dce-461d-95e4-1130521ff4c4.jpg?1789556945" width="240" alt="Medic&#x27;s Kitesail" loading="lazy"></td><td><b>Medic&#x27;s Kitesail</b> · Common<br><br>🎧 <b>LR D+/C−.</b> +1/+0, flying and lifegain; LSV thinks it&#x27;ll be main-decked more than it looks.<br><br>🎓 <b>LLU C−.</b> A flyer and lifegain engine for board stalls. Don&#x27;t play a second copy.<br><br>🎙 <b>Numot:</b> &quot;going to be a really annoying card.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/6/d68eab2e-89dd-4377-b7af-01512b1804a0.jpg?1789385977" width="240" alt="Murmuring Volume" loading="lazy"></td><td><b>Murmuring Volume</b> · Common<br><br>🎧 <b>LR D.</b> 3-mana rock with a loot; RG has better ramp. &quot;Prove it.&quot;<br><br>🎓 <b>LLU C−.</b> For multicolour or ramp decks, not a single splash.<br><br>🎙 <b>Numot:</b> &quot;I don&#x27;t hate it… I&#x27;m a mana rock enjoyer.&quot;</td></tr>
</table>

**Jump to:** [White (38)](#white) · [Blue (38)](#blue) · [Black (37)](#black) · [Red (39)](#red) · [Green (36)](#green) · [Multicolor (60)](#multicolor) · [Colorless (11)](#colorless) · [Lands (5)](#lands)

### Lands

<table class="expertcards">
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/4/a/4a771010-b397-4849-ac9b-08e4dd5d6a72.jpg?1789644859" width="240" alt="Hall of Echoes" loading="lazy"></td><td><b>Hall of Echoes</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;not bad… I&#x27;ll play that in my two color decks.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/d/b/db61361b-bd12-453e-abc2-bbe09b66e3d9.jpg?1789514074" width="240" alt="Roiling Canopy" loading="lazy"></td><td><b>Roiling Canopy</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;a mono green payoff land… It&#x27;s weird.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/2/2/22db5bba-46c9-4a26-821d-303ddb386ea4.jpg?1788878256" width="240" alt="Theorist&#x27;s Sanctum" loading="lazy"></td><td><b>Theorist&#x27;s Sanctum</b> · Rare<br><br>🎙 <b>Numot:</b> &quot;Oh, that&#x27;s sweet too. Empower Jace, too, on a land.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/1/9128ce00-6744-4d36-bfbe-ef75d78110b0.jpg?1789556985" width="240" alt="Hexhaven Dueling Arena" loading="lazy"></td><td><b>Hexhaven Dueling Arena</b> · Uncommon<br><br>🎧 <b>LR F.</b> Colourless land with prepare activations. &quot;I would bet the win rate is negative.&quot;<br><br>🎓 <b>LLU Alex F / Mark D− (&quot;the coward&#x27;s D−&quot;).</b> <br><br>🎙 <b>Numot:</b> &quot;This one I don&#x27;t think I like.&quot;</td></tr>
<tr><td width="250"><img src="https://cards.scryfall.io/normal/front/9/a/9a467560-6676-4fc2-9400-768a79650aa4.jpg?1789557010" width="240" alt="Room of Refuge" loading="lazy"></td><td><b>Room of Refuge</b> · Common<br><br>🎧 <b>LR C+.</b> Tapped any-colour land; late game, 5 and sac for two +1/+1 counters.<br><br>🎓 <b>LLU C+.</b> Taken at about the same rate as the duals.<br><br>🎙 <b>Numot:</b> &quot;not bad. Still even play this in your two-color decks.&quot;</td></tr>
</table>

**Jump to:** [White (38)](#white) · [Blue (38)](#blue) · [Black (37)](#black) · [Red (39)](#red) · [Green (36)](#green) · [Multicolor (60)](#multicolor) · [Colorless (11)](#colorless) · [Lands (5)](#lands)

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

## First gameplay: Numot's Early Access Sealed (2026-09-23)

The only real FRA games in this repo so far: **one pool, six Bo1 games, 3-3.** It's a sample of
one, so read it as *how cards played*, not *how good they are*. Full notes are in
[`numot/FRA.md`](../numot/FRA.md).

- **Deck:** U/B splashing Ajani's Anguish off 3 red sources (9 blue, 9 black). He dropped green
  because its best cards were double-green and couldn't be splashed. Hapatra went with it, since
  she needs the green landcyclers to fuel her.
- **What won games:** `Ruric Thar, Biomagus` (won two; targeting it just drew him cards),
  `Sphinx of False Conclusions` (recurs), `Theorist's Proxy` (a 0/3 wall that stabilised a
  losing board) and `Mabel, Bitter Recluse` (kills a Jace token).
- **What beat him:** a menace attacker off the top, and a Heartwood + Garruk + unblockable/surveil
  deck piloted by an Arena Championship player.

**Lessons for our trio, in order of how cheap they are to apply:**
1. **Make the Jace before you play a Jace-land.** He lost a turn playing it tapped: "I should have
   played Oculus and then played this."
2. **Cast your creature first, then decide what to do with Jace.** He named this as his own punt.
3. **Play every landcycler.** He forgot Awaken the Inferno and regretted it twice. The cyclers
   also shuffle your library, which gets back a card you surveiled to the bottom.
4. **A 3-source splash can strand the card.** Ajani's Anguish sat in hand in the game that
   mattered. For a trio seat, give a splash 4 sources, or play a landcycler that can fetch the
   splash colour.
5. **Hold cheap removal for the first real threat.** He lost one game for want of a Last Gasp,
   and lost another at the opponent's 1 life to their cheap removal.

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
- **Best colour: three sources, three answers.** Kenji (Numot) ranks **white first and blue last**
  from the card read ("every single card" in white is playable). LLU's Mark has white
  *second-worst* and black worst, and in their blue episode LLU calls blue maybe the best colour
  at common/uncommon. LR is highest on black and red. Kenji's own Sealed pool then
  pushed him **into** blue ("I have too many good blue cards"). Read this as a set with no bad
  colour: build from your pool, not from a ranking.
- **Coverage gap.** One Sealed run is the only play data, and neither podcast has graded rares
  yet.

---

## Sources

- **Wizards of the Coast** — [Reality Fracture Prerelease Guide](https://magic.wizards.com/en/news/feature/reality-fracture-prerelease-guide),
  Jubilee Finnegan, 2026-09-18. Authoritative on the ten archetypes and pack contents.
- **LimitedMTG** — [Reality Fracture draft & sealed guide](https://limitedmtg.com/reality-fracture/).
  Per-pair removal and curve counts, format speed, the B/R pick and the G/U trap call. The
  strongest source here; it counts rather than predicts.
- **NumotTheNummy** — *QUICK* Reality Fracture Set Review + 1 Early Access Sealed, Kenji
  Egashira, 2026-09-23 (`jorRsIuS7RY`). Distilled in [`numot/FRA.md`](../numot/FRA.md).
- **Limited Resources 872** — Reality Fracture Set Review: Commons and Uncommons, Marshall
  Sutcliffe + LSV, 2026-09-21. Distilled in [`limited-resources/FRA.md`](../limited-resources/FRA.md).
- **Limited Level-Ups** — Reality Fracture set review (6 parts; blue transcribed locally with whisper after YouTube refused its captions) plus
  First Impressions #261, Alex + Mark, 2026-09-18 → 09-22. Distilled in
  [`limited-level-ups/FRA.md`](../limited-level-ups/FRA.md).
- **Not used:** Draftsim's and MTG Arena Zone's reviews were dropped 2026-09-22. Their captures stay
  on disk (`grades/draftsim_FRA.json`, `draft-guides/draftsim/`, `draft-guides/mtgazone/`).
- **Scryfall** — `set:fra`, 285 unique cards, fetched 2026-09-21.
- **Prior art:** [`HOB.md`](./HOB.md) — the trio choreography, contested-card rule and split rule
  are carried over from there, where they were tested at a real event.
- **17Lands GIH WR supersedes everything here** once FRA hits Arena.
