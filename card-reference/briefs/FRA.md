## Format brief — everything that isn't a single card

Reality Fracture is a ten-archetype format built on two shared engines and an unusually cheap
answer pool. Jace Beleren's Echoverse gives every colour a way to build the same planeswalker
token, every allied pair a recurring free spell at common, and every colour pair a dual land at
common. The result is a format where fixing is nearly free, splashing is cheap, and the games are
decided by whether you answered the right threat and whether anyone attacked the Jace.

### ⚠ This brief predates play data

Captured 2026-09-21, four days before the prerelease and eleven before release. Everything below
is either a **count** taken from full set data, or a **pre-game prediction** from a published
reviewer. The two are labelled where it matters.

**17Lands data now exists (2026-10-08, ~251k PremierDraft decks)** and
contradicts parts of this brief: W/U and U/B lead the archetype table, B/R tops the tied bottom four,
and W/B is near the bottom. The archetype table and every card's GIH WR on this page are the live numbers;
where they disagree with the predictions below, the numbers win. The sample has now settled
(no card with 1,000+ games moved more than 1.2pp from day six to day ten).

### Synergy by pair — what the play data says (2026-10-08)

This section is post-release and overrides the predictions below it. It rests on two things:
17Lands **per-pair card data** (each card's IWD *inside* each two-colour deck, compared with the
same card's set-wide IWD — `card-reference/fetch_pair_synergy.py FRA` reproduces it) and the
published post-release coverage (MTG Arena Zone's 10-03 data update, Draftsim, r/lrcast trophy
threads). IWD is measured within the same decks, so it controls for deck quality: a card that
gains IWD in one pair is genuinely better *in that shell*. Only results on 1,000+ games with a
z-score of 2.5 or more are quoted as findings; single rows can be noise, patterns are not.

**The format is slow, and that sets the price of synergy.** Games average 9.68 turns and the
on-the-play win rate is only 52.1%. The three top pairs (W/U, U/B, B/G) win by card selection and
grinding, not curve-outs, and grind commons such as `Twinned Vision` overperform their grades.
Synergy that pays off on turn 6–9 is worth more here than synergy that needs a perfect turn 3.

#### Three format-wide findings

1. **The common duals are only good in blue decks.** Each dual enters untapped with a
   planeswalker, and blue makes the most Jace tokens. In its home pair, every blue dual is zero or
   better and every non-blue dual is negative (table below). Outside blue, a dual is a tapland
   that costs you tempo: take it late and play it only for a real splash. In blue, take it like a
   good playable.
2. **Black is a U/B colour, not a B/R colour.** The same black commons swing hardest between those
   two pairs: `Break Under Pressure` +9.5 in U/B vs +0.5 in B/R, `Silence the Echo` +3.6 vs −4.9,
   `Rank Rat` +3.5 vs −2.3, `Last Gasp` +5.7 vs +0.8. Averaged over all black cards, black
   performs **2.5pp worse in B/R** than its set-wide level and **1.7pp better in U/B**, the largest
   colour effect in the set. Two mechanisms explain most of it: `Silence the Echo` sacrifices a
   spent Jace token for free in blue but costs a real creature or 3 extra mana elsewhere, and
   discard and edicts (`Rank Rat`, `Break Under Pressure`) are control cards that a face-damage
   deck can't cash in.
3. **Empower is a rider that pays most where the deck is built on it.** Lords of Limited's
   post-early-access read ("you don't need to force Empower Jace", "the Ways are busted") holds:
   the Ways play well in most decks. But the cheap empower cards spike in G/U — `Arcane
   Amphisbaena` +7.5 there vs +1.6 set-wide, `Tam's Resistance`, `Way of the Paradox`, `Way of the
   Wildspeaker` and `Loot, the Nexus` all over-perform. You get one loyalty activation a turn, so
   run **two, at most three Ways**.

**Common dual IWD in its home pair:**

| Blue pairs (dual IWD) | Non-blue pairs (dual IWD) |
|---|---|
| G/U `Transformative Commons` +3.0 · U/B `Theorix Annex` +1.6 · U/R `Innovative Commons` +0.8 · W/U `Fatehold Annex` +0.5 | B/R `Stingerquill Annex` −4.0 · R/G `Konstrari Annex` −3.7 · B/G `Formidable Commons` −3.5 · R/W `Dedicated Commons` −3.1 · G/W `Vigorbloom Annex` −2.6 · W/B `Meticulous Commons` −1.5 |

#### New at day ten (2026-10-08, ~251k decks)

- **The top tie broke.** W/U (56.9%) and U/B (56.6%) are now the top two on their own. B/G (55.9%)
  dropped about 1pp behind them and leads a second tier with R/G (55.6%) and U/R (55.4%).
- **The U/B black finding got stronger.** More black commons now clear the bar in U/B:
  `Silence the Echo` +3.6 (vs +0.9 set-wide), `Multiply by Zero` +7.8 (vs +5.2) and `Void
  Extrapolator` +2.8 (vs +1.0). Blue's cheap interaction joins them: `Unsummon` +5.2 (vs +3.4)
  and `Icy Reception` +5.5 (vs +3.8). Black in B/R is still −2.5, the worst colour half in the set.
- **G/U's green cards are the best-fitting half in the set (+2.6), and the pair is still 10th.**
  New over-performers there: `Way of the Wildspeaker` +6.5 (vs +2.5), `Keeper of the Quiet Hour`
  +6.1 (vs +1.4), `Compel Brutality` +4.3 (vs +1.1), `Inspired Tethermage` +2.0 (vs −1.3). The
  cards work together; the deck loses on removal count. Treat these as reasons to stay in G/U if
  you land there, not reasons to aim for it.
- **Off-pair duals play well in U/R.** `Fatehold Annex` +6.7 and `Stingerquill Annex` +4.4 inside
  U/R (vs +0.8 and −1.2 set-wide), on about 1,000 games each. It fits finding 1: a blue deck makes
  Jace tokens, so a dual enters untapped and a splash costs almost nothing. Small sample — watch it.
- **R/W's white is now the weakest half after B/R's black (−1.8).** `Fateshaper Aspirant` −5.3,
  `Saheeli, Consul of Oversight` −3.8 and `Memory Trap` −1.2 all fall well below their set-wide
  numbers in R/W.
- **R/G: two more cards to skip.** `Awaken the Inferno` −0.8 (vs +1.4, 10.5k games) and `Something
  Worth Saving` −1.4 (vs +1.2) under-perform there; `Eardrum Rattler` fell to −6.7.
- **Newly rated cards (under 700 games, so ±3pp):** `Austere Command` 62.7%, `Splinter Twin`
  62.3%, `Consider` 57.4%; `Flourishing Grapple` 45.6% and `Codie, Ravenous Codex` 46.8% are
  near the bottom of the set.

#### Per pair

**W/U Fatehold — surveil fliers (56.9%, joint best).** *White carries it*: W/U's white cards run
slightly above their set-wide level while its blue cards run 1.3pp below (`Icy Reception`,
`Mindseeker Oculus` are both weaker here than anywhere). Engine: `Fblthp, Impossibly Lost` +7.8
(evasion turns it into a draw-two every turn), `Way of the Healer` +6.2 (its −2 makes a Cadet *and*
surveils), `Desperate Futurescribe` +5.2, `Thalia, the Survivor` +5.4. Every empower card is a
surveil source, because the token's −1 is Surveil 1; that makes 35 enablers in the set, and `Eye
of Jace` surveils every upkeep. Futurescribe checks at beginning of combat, so surveil in your
first main phase. `Surveillance Phantasm` still blocks as a 2/3 flier without the trigger. Trap:
13 removal spells — take `Prophesied End` and `Your Fate Ends Here` early.

**U/B Theorix — removal and two-for-ones (56.6%, joint best).** The only pair where *both* halves
over-perform (U +1.2, B +1.8). What wins is not turbo-mill — threshold is printed on only six
cards, and `Theorix Metamage` is just +1.4 in U/B across 13,009 games — but the value shell:
`Break Under Pressure` +9.5, `Extended Absence` +8.4, `Tam's Resistance` +8.2 (splashed off the
hybrid), `Fblthp, Impossibly Lost` +8.1, `Countersculpt` +7.1, `Mindseeker Oculus` +7.1.
`Prudent Fateseer` is +4.4 here (down from +6.7 on day six). Self-mill is a side plan: `Fblthp, Impossibly Lost` wins the game
if you draw from an empty library, and `Paradox Shaper`'s bottom-of-library ability is your brake.
Reach seven cards in the graveyard only if you have about four mill-3 effects (`Omit Variables`
carriers, `Theorix Charm`).

**B/G Garruk's Bestiary — graveyard grind (55.9%, 3rd — slipped out of the top tie).** Deathtouch is incidental; the
engine is recursion and big bodies. Engine: `Hapatra, the Desert Fang` +5.0, `Break Under Pressure` +5.3,
`Extended Absence` +5.0, `Ghalta the Unstoppable` +4.4, `Wrecking Gecko` +4.2,
`Winter, Tormented Loner` +3.4. (Ghalta, Gecko and Winter all cooled 1–1.3pp since day six.) Key pair: `Hapatra` reads the greatest mana value in your
graveyard, so a landcycled `Apex Witchstalker` makes it six −1/−1 counters. Black loses some edge
here (−1.4): `Multiply by Zero` drops to +1.1 from +5.2. Skip `Formidable Commons` (−3.5).

**R/G Konstrari — ramp into two uncommons (55.6%, 4th).** Below rare there are only three
Heartwood makers and one artifact payoff, so this is not an artifact deck. It is "make mana, cast
`Kiora of Fire and Ashes` (+9.5) or `Craftwork Crusher` (+8.6)". Both work on their own. Both
halves under-perform slightly, the dual is among the worst lands in the set here (−3.7), and
`Eardrum Rattler` (−6.7) and `Inspired Tethermage` (−3.4) are aggro and Jace cards in a deck that
has neither plan. Green can splash red's double pips through Heartwood for Crusher; red can't do
the reverse.

**U/R Chandra's Prowess — red removal plus blue cards (55.4%, 5th).** *Red is the better half
here* (+1.1; blue −1.2). Red's removal plays best in this pair: `No Admittance` +5.3, `Wrath of the
Bloodmane` +3.3, `Violent Echoes` +7.4, `Way of the Warlord` +4.2 (a noncreature spell that adds a
removal ability to Jace). `Kiora of Fire and Ashes` peaks here at +10.2. The pair has 27
noncreature spells at common and uncommon, counting Ways and `Eye of Jace`. Pick one lane — red
spells-aggro or blue control — and don't mix the payoffs. `Twinned Vision` is glue.

**G/W Vigorbloom — lifegain into counters (54.3%, 6th).** Eighteen lifegain sources at common
and uncommon, only four payoffs (`Unflinching Hortimancer`, `Titanbones`, `Bloombrute`, `Way of
the Mentor`). What matters is *repeatable* gain — `Greenhouse Propagator`, `Medic's Kitesail`,
`Koth of the Homestead` landfall — because `Bloombrute` triggers once per turn. Engine: `Generous
Revival` +4.3, `Way of the Paradox` +4.2, `Koth` +4.0, `Bloombrute` +4.2. Skip the dual (−2.6)
and don't take `Greenhouse Propagator` early.

**R/W Ajani's Army, B/R Stingerquill, G/U Jace's Mastery, W/B Liliana's Attrition — the tied
bottom four (53.3–53.7%).**
- **R/W:** both halves under-perform (W −1.8, R −1.2). It needs `Mabel, Valley Hero` and
  `Warrior's Blades`; without them it is a burn deck with white bodies, and it is an aggro deck in
  a slow format. Best cards here are generic: `Jiang Yanggu, Alone` +3.3, `Prophesied End` +3.8.
- **B/R:** see finding 2 — black's control cards don't fit a face-damage deck. The payoffs check
  for noncombat damage *this turn*, and `Stingerquill Voxmancer` is the only repeatable source
  below rare. If you are B/R, draft red removal and the gold cards (`Violent Echoes` +5.1,
  `Kiora of Fire and Ashes` +4.8, `Fulminous Forte` +3.3) and treat pings as reach.
- **G/U:** the least-drafted pair. Its cards synergise (finding 3) but it has the fewest removal
  spells. If you land here, max out cheap empower and play `Kiora of Salt and Sand`, whose −8
  needs real loyalty density; `Mind Meanderer` +6.9 is its removal. Don't aim for it.
- **W/B:** draft it as black removal plus white bodies; the sacrifice theme is thin.
  `Tinybones, Pocket Nuisance` +6.4 and `Extended Absence` +5.3 lead. `Void Extrapolator` is −5.1
  here (no self-mill to turn on threshold).

#### Expert takes since day six (2026-10-05 → 10-08)

New since the last update: Lords of Limited ep 499 (10-05), Rough Drafts ep 82 (10-08), Numot's
Arena Direct sealed compilation (10-07) and 32 Reddit threads (10-05 → 10-08). Full notes in
`draft-guides/{lords-of-limited,rough-drafts,numot,reddit}/`. Where these disagree with the
17Lands numbers above, the numbers win.

- **Colour order (Rough Drafts): blue first, then black and green, red and white well behind;
  avoid R/W.** Blue-first and R/W-last match the data. *White behind* does not: W/U is the top
  pair at 56.9%, and in W/U the white cards play slightly above their set-wide level (+0.6) while the blue ones play below it.
- **`Mindseeker Oculus` is "clearly the best common"** (Rough Drafts; 60.2% GIH, +7.1 IWD in
  U/B). The claim that it still goes late on Arena doesn't hold: 17Lands has its average last-seen
  pick at 3.7, so it is already taken early.
- **`Theoretical Necromancer`: two in every black deck** (Rough Drafts, Reddit). Its 55.9% GIH
  understates it because you want to mill it, not draw it. The Omit Variables creatures move up
  from D to a solid C.
- **Discount `Fblthp`'s 60.9%.** It shuffles back in and gets redrawn in winning games, which
  inflates the number (Rough Drafts, Reddit).
- **Self-mill decks play exactly 40 cards** unless they lack Fblthp, a second Paradox Shaper and
  real finishers (Rough Drafts).
- **Draft for ceiling, and attack the opponent's Jace by default** (Lords of Limited). Their
  ramp combo is `Way of the Pyromancer` + `Way of the Paradox` + `Inspired Tethermage`; note that
  Pyromancer is 52.1% and Tethermage under-performs everywhere except G/U, so treat it as a
  ceiling play, not a default. Numot disagrees on Jace: he ignores a 1-loyalty Jace when his own
  deck has plenty of empower.
- **`Kindred Judgment` (61.5%) and `Countersculpt` (60.7%, +7.1 in U/B)** are named on Reddit as
  under-picked; the U/B guide calls Countersculpt "arguably the best uncommon". 17Lands pick data
  disagrees on the under-picked part (average last seen at pick 3.2 and 4.2), so expect to take
  them early, not wheel them.
- **U/B wins without bombs.** A rareless U/B deck of discard, removal and three or four `Theorix
  Metamage` went 7-1 (Lords of Limited), and Reddit favours U/B splashing green for control. Both
  agree with U/B at 56.6%.

#### What Reddit adds (and where it's wrong)

From 67 post-release threads on r/lrcast, r/MagicArena and r/magicTCG (2026-09-29 → 10-04; full
notes in `draft-guides/reddit/FRA.md`). Trophy posts are survivorship-biased, so where Reddit and
the numbers disagree, the numbers win.

- **Kill your own Jace to activate twice in a turn.** Use the token's −3 to draw, taking it to 0;
  it dies, and the next empower card makes a fresh token that can activate again that turn. (It
  doesn't work with `Sanctum Lurker` out, which keeps 0-loyalty planeswalkers alive.)
- **`Ajani Unrelenting` (74.0%, the best card in the set) feeds on Jace.** It makes a Cadet on
  *any* loyalty activation, the Jace token's included, so keep a Jace on 1 loyalty to fire every
  turn. Its −3 spares your tokens and kills everything with toughness 4 or less.
- **Bounce is removal here.** `Unsummon` (57.8%) beats its grade because the board is full of
  tokens and big bodies that cost a turn to recast; `Twinned Vision` (58.5%, 4th-best common) is
  the grind card everyone under-picked.
- **Leave colour hosers in the sideboard in Bo1:** `Refute Destiny` 51.3%, `Terminal Criticism` 51.1%.
- **Reddit gets these wrong:**
  - "B/R is great": the trophy feed is full of B/R 7-0s, but the pair is tied bottom.
  - "The set wants three colours": true three-colour decks win 53.6% vs 55.4% for two, and every
    three-colour deck with white is 52.5% or worse. Splash a card; don't play a third colour.
  - "White is bad": white is the half carrying W/U. It is bad only outside W/U.
  - "`Surgical Precision` is bad": it is the 12th-best common (57.3%); a third of creatures have 4+ toughness.
  - "The re-preparing uncommons are engines": `Stingerquill Voxmancer` 54.0%, `Paradox Shaper` 55.7%,
    `Woodwork Prodigy` 52.8% are all at or below the set median, and `Command the Stage` is 49.6%.

#### Take on power vs take only in the lane

| Good in any deck it's castable in | Good only in its lane |
|---|---|
| `Kiora of Fire and Ashes` (+4 to +11 in all four red pairs), `Craftwork Crusher`, `Extended Absence` (+4.6 to +8.5 everywhere), `Fblthp, Impossibly Lost` (any evasive deck; +1.0 in G/U), the Ways (two or three), `Twinned Vision`, `Recursive Recruitment`, landcyclers | `Silence the Echo` and `Rank Rat` (U/B), `Prudent Fateseer` (W/U, U/B; −4.8 in R/W), `Theorix Metamage` and `Void Extrapolator` (threshold), `Arcane Amphisbaena` and `Tam's Resistance` (empower decks), the common duals (blue decks), `Surveillance Phantasm`, `Whiplash Wordsmith`, `Konstrari Improviser`, `Mabel, Valley Hero`, `Kiora of Salt and Sand` |

### The ten archetypes

There are ten two-colour archetypes, not five. The allied pairs are the colleges of Hexhaven; the
enemy pairs are built around the Echoverse versions of major characters. All ten have a signpost
and all ten have a common dual land.

| Pair | Name | Plan | Signpost | Removal | 2-drops | Avg MV |
|---|---|---|---|---|---|---|
| B/R | Stingerquill | Face burn, noncombat damage | `Grim Repriser` | **26** | 12 | 3.10 |
| W/B | Liliana's Attrition | Small creatures dying for value | `Twisted Fates` | 23 | 11 | 3.10 |
| B/G | Garruk's Bestiary | Deathtouch trades, creature value | `Primal Witchstalker` | 21 | 11 | 3.28 |
| U/B | Theorix | Graveyard math, threshold at seven | `Recursive Recruitment` | 20 | **14** | **3.01** |
| R/W | Ajani's Army | Go-wide, +1/+1 counters, Cadets | `Warrior's Blades` | 20 | 13 | 3.23 |
| R/G | Konstrari | Heartwood ramp into big creatures | `Craftwork Crusher` | 18 | 15 | **3.39** |
| U/R | Chandra's Prowess | Noncreature spells matter | `Clash of Elements` | 17 | 15 | 3.11 |
| G/W | Vigorbloom | Lifegain into counters and cards | `Bloombrute` | 13 | 15 | 3.35 |
| W/U | Fatehold | Surveil aggro, cheap fliers | `Desperate Futurescribe` | 13 | **16** | 3.07 |
| G/U | Jace's Mastery | Empower Jace, planeswalker value | `Mind Meanderer` | **11** | 16 | 3.27 |

**The pick is B/R.** It has the most removal of any pair and no colour has more at common than
black or red. Its weakness is the curve — it is light on two-drops for a deck that wants to
attack, and black has the fewest two-drops at common of any colour. If the two-drops aren't
there, black's removal is just as good in U/B, which has the most.

**The trap is G/U.** It has the least removal of any pair, its signpost is a six-mana flier that
fights on entry, and the loyalty it needs comes from cards every other drafter wants as well.
Take the Jace pieces for whatever deck you end up in and leave the pair alone.

Three more that read differently than the table suggests:

- **W/B is a removal deck with a sacrifice angle, not a sacrifice deck with removal.** Draft it as
  black removal plus white bodies. Don't plan to race — few pairs are lighter at two mana.
- **U/B is the cheapest pair and deepest at two mana**, and it is the one pair whose enablers and
  payoffs genuinely feed each other. The cost is the wait: before the seventh card hits the
  graveyard, none of the threshold bonuses are switched on.
- **R/G carries the highest curve in the format** and only gets away with it because Heartwood
  tokens ramp and its expensive commons carry basic landcycling.

### Where the removal is

Sixty removal spells: black 14, red 11, white 7, blue 5, green 5, and 18 gold or colourless. At
common the gap narrows — red 4, black 3, green 3, white 2, blue 2 — so the black-and-red
advantage is real but concentrated at uncommon.

**Blue does not kill things.** Its answers bounce a creature, tap it, or strip its abilities. A
blue deck needs a second colour that can actually kill, and that is the single most reliable
deckbuilding constraint in the format.

**Green's answers are fight effects.** They need a body already on board and they are card
disadvantage into an opposing removal spell. Count them at a discount.

Five spells are colour-hosed, and the rates are premium precisely because the conditions are
punishing: `Refute Destiny` (green or blue), `Terminal Criticism` (blue or red), `Essence Burn`
(black or green), `Flourishing Grapple` (red or white), `Precise Redaction` (white or black).
These are sideboard cards that steal games — board them in hard once you know the matchup.

Twenty-eight removal spells cost one or two mana and twenty-two are instants, so both players
have interaction. Three damage kills 68% of creatures and the step to four damage buys nineteen
points more. Thirty-two percent of creatures have toughness four or greater, which is why
conditional removal keyed to big bodies is live more often than it reads.

### Engine one: the Jace token

Thirty-five cards empower Jace, eleven of them at common, spread across all five colours. This is
not a blue mechanic — it is a colourless one that happens to make a blue token.

The rule that makes it matter: **you only ever have one Jace token, and every empower card feeds
the same one.** Five separate cards reading "Empower Jace 2" build a single ten-loyalty
planeswalker. No payoff card is required, only volume. The token surveils for one loyalty and
draws a card for three.

Three interactions are worth more than the token's own abilities:

- **It turns on the mana.** All ten common duals enter untapped if you control a planeswalker. An
  early Jace fixes the rest of the game.
- **`Compel Brutality` turns it into removal.** Its second mode has a planeswalker you control
  deal damage equal to its loyalty.
- **`Silence the Echo` eats a spent token.** It wants a creature or planeswalker sacrificed, and a
  drained Jace is ideal fodder.

Cheapest loyalty at common: `Arcane Amphisbaena` and `Academic Ascent` for two, `Campus Crier`
from the graveyard for one, `Protege's Awakening` for six loyalty at four mana.

**Attack the Jace.** A token left alone plausibly decides more games than a two-drop does, and
most opponents will leave yours standing because it doesn't threaten the board.

### Engine two: Prepared

Twenty-four cards, ten at common. A prepared creature carries a spell on its other face; while
prepared you may cast a free copy, which unprepares it. Each allied pair owns one spell, and that
spell is the pair's plan in miniature — `Peer Review` (W/U, a 2/2 Cadet and surveil),
`Omit Variables` (U/B, mill three), `Vicious Verse` (B/R, 1 damage to an opponent), `Soul Tether`
(R/G, a Heartwood token), `Seed Suture` (G/W, a +1/+1 counter and 1 life).

The commons enter prepared and fire once. **Three uncommons re-prepare at your upkeep whenever
they aren't, so they fire every turn for the rest of the game:** `Stingerquill Voxmancer`,
`Paradox Shaper`, `Woodwork Prodigy`. In a long game those are the strongest engines available,
and they cost one to three mana.

### The mana

Ten common dual lands, one per pair, each entering untapped if you control a planeswalker. Add
basic landcycling for two mana on big commons in four colours, plus `Room of Refuge` and
`Murmuring Volume` as colourless fixers. **A third colour for one removal spell is affordable**,
and you should be readier to splash than instinct suggests. Sequencing matters: playing a cheap
empower spell before the dual is often worth a full turn.

### The draft plan

1. **Removal first.** `Last Gasp` and `No Admittance` ask nothing of you. `Silence the Echo` wants
   a sacrifice or three more mana. `Compel Brutality` wants a body. `Surgical Precision` wants a
   target with toughness four or greater.
2. **Then the cheap fliers and the deathtouch bodies**, then cards that are two bodies in one.
3. **Then read which pair's prepared creatures are wheeling.** They signal what's open more
   reliably than the gold cards do, because every deck in those colours wants them.
4. **Walk in wanting B/R** and move off it only when the two-drops don't show.

### Sealed and deckbuilding doctrine

Find the bombs first, then the removal, then let those two choose your colours. A reasonable
curve is one or two one-drops, seven or eight twos, five or six threes, three or four fours, two
or three fives, at most one six, and seventeen lands. Slower decks push that up, aggressive decks
pull it down.

Specific to this format:

- **Never run blue as your only interactive colour.**
- **Count green's fight effects at a discount** when you're deciding whether you have enough
  answers.
- **Take the self-preparing uncommons highly in Sealed specifically.** Sealed games go long and a
  free spell every turn compounds; in a fast draft deck they're merely fine.
- **Splash freely** given the fixing, but only for removal or a bomb.
- **Play around instant-speed removal in every colour.** White's `Prophesied End` kills anything
  for two at instant speed, and it draws its controller a card only if the creature wasn't
  attacking — so attacking into it is the cheaper line.

### Limited Level-Ups after play (State of the Format, 2026-10-05)

Alex's first post-play address. It's opinion informed by early access and the first Arena days, not
data, but it answers two of the open questions below.

- **Speed: grindy.** Turns 2–5 are setup, and by turns 5–6 boards are stable at 15–20 life each.
  The player who runs out of ways to spend mana loses. Build in mana sinks, 3–4 card-draw spells,
  and **6–7 removal spells** (counterspells count). Prefer removal that hits planeswalkers.
- **Aggro is niche.** The real aggressive decks are U/W flyers and go-wide, plus near-mono-red when
  red is wide open. B/R adds little to the red plan.
- **Favoured shells:** U/W surveil and go-wide (the easiest deck to win with), B/G (often Sultai)
  graveyard recursion with Rewrite Regrets, and R/G ramp as the base for 3–5-colour decks.
  W/B is the lowest-winning pair on 17Lands, but it works as white go-wide plus black removal.
- **Splash freely, even double pips.** Fixing is the best in years: duals, Murmuring Volume,
  landcyclers and Heartwood tokens. Hold 7–8 sources for any double-pip splash. Splash off-colour
  removal to reach the removal count.
- **Ways: top three are Healer, Mind Sculptor, Paradox.** Run three at most, since Jace activates
  only once per turn. Way of the Mind Sculptor is the big flip from the review (D+/C− → "one of the best
  non-rare ways to go over the top"). Pyromancer, Warlord, Deathbringer, Mentor and Necromancer are
  weak or niche.
- **Cards he says are underrated:** Twinned Vision, Protege's Awakening, Countersculpt, Recursive
  Recruitment (around A− on 17Lands), Something Worth Saving, Rewrite Regrets.
- **Reading 17Lands here:** high win rates are reliable. C−/D+ win rates often belong to build-arounds played in
  decks without enough support (Danitha, Sword of Hope wants 9–10 targeting effects). At
  recording, Ajani Unrelenting had about a 73% GIH WR.

### Where the sources disagree

- **Removal density versus raw power.** The per-pair counts point at B/R. The reviewer grades
  cluster their top scores in **red and green** — five of the nine perfect scores are one or the
  other. If a pool hands you two red or green mythics, believe the bombs over the archetype table.
- **G/U.** One source calls it the format's trap on removal count; the official archetype guide
  presents it as a normal deck. The count is the more reliable signal.
- **Prepared's ceiling.** One source treats the self-preparing uncommons as major engines, another
  grades them as solid-but-unexceptional. Both readings survive: strong in a long game, mediocre
  in a short one, and nobody yet knows which kind of game this format produces.
- **G/W, per Limited Resources.** The removal count ranks G/W near the bottom (13). The Limited
  Resources commons-and-uncommons review ranks it near the top, on the strength of its gold cards:
  `Bloombrute` (A−, "this card's busted"), `Vigorbloom Charm` and `Vigorbloom Vanguard` (both B+),
  plus deep lifegain filler. The same review agrees with the count on B/R (good) and G/U (fragile:
  "the fancier the deck, the likelier it does nothing").
- **Two engines that review is openly skeptical of.** R/G Heartwood ramp: "how often are we
  really happy to pay three mana for a mana rock?" U/R prowess creatures: "these type of cards
  have not held up lately." Both are predictions to check against the first week of data.
- **Limited Resources versus Limited Level-Ups.** Both podcasts give Craftwork Crusher their top
  C/U grade (A− from LLU, B+/B from LR) and both rate the Jace duals C+. They split on how good the
  gold cards are. LR grades `Bloombrute` A−, `Saheeli, Jewel of Avishkar` B+ and `Mabel, Valley
  Hero` B/B+. LLU has them at B−/C, C and B−/C. LLU also sees no bad colour: Mark ranks black
  worst and white second-worst, while Alex first called red the weakest and then took it back. BR
  pings is the archetype both podcasts doubt most.
- **Colour ranking: three sources, three answers.** Numot (Kenji Egashira, first read-through)
  ranks white first and blue last. LLU's Mark has black worst and white second-worst, and LLU's blue episode calls blue maybe the best at common/uncommon. LR is highest
  on black and red. Kenji's own first Early Access Sealed pool (3-3) ended up U/B because blue
  was its deepest colour. Treat the set as having no bad colour until 17Lands says otherwise.
- **Card grades where the two reviewers split by two grade steps or more.** Limited Resources
  rates these much higher than Draftsim does: `Vigorbloom Vanguard` (B+/B vs 3/10), `Thalia, the
  Survivor` (B vs 3/10), `Koth of the Homestead` and `Mabel, Valley Hero` (B vs 4/10), `Generous
  Revival` (C+ vs 2/10). Draftsim rates `Loot, the Anomaly` higher (5/10 vs D). Neither side has
  played a game; the first week of 17Lands data decides these.

### Open questions the data can't settle

- **Format speed.** *(LLU 10-05 calls it grindy after play; see above. 17Lands still decides.)* The averages say normal — mana value 3.2, 68% of spells at three or less — but
  averages have been wrong about speed before, and speed decides whether the grindy graveyard pair
  is real.
- **Whether Jace is a build-around or a rider.** *(LLU 10-05: the Ways want 5–7 other empower cards to shine; three Ways at most.)* Every colour can empower. Nobody knows yet
  whether decks that lean in beat decks that take the free loyalty and move on.
- **How much the colour-hosed removal actually costs you.** In a diverse field it's a liability;
  in a field that settles on black and red it's close to unconditional.
- **Whether the echoed-pair legends matter mechanically** or are just flavour. Several cards check
  for a legendary creature, and with 32 characters printed twice the density is high enough that
  those checks may be effectively free.
