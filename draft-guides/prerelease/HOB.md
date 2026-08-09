# HOB — The Hobbit: aggregated draft & Sealed guide

> **The master file for HOB.** Merges every source captured so far: Limited Resources 865 (letter grades, commons + uncommons), Draftsim (numeric /10 + set review), Card Game Base (letter tiers + archetypes), MTG Arena Zone, Wizards' prerelease guide — plus the full card list verified against **Scryfall, 2026-08-05**. Every card name links to its Scryfall page; click to see the card.
>
> **⚠ Weakest evidence tier, by construction.** Nothing here is backed by a single played game. HOB hits Arena **2026-08-11**; from that date **17Lands GIH WR supersedes every grade in this file.** LR 866 (rares & mythics) airs the week of Aug 10 and will supersede the rare section.
>
> **Update 2026-08-08 — read `limited-level-ups/HOB.md` first for rares.** Limited Level-Ups published a five-part HOB primer (2026-07-30 → 08-06) that this file predates. It is a **stronger source than anything merged here**: two reviewers ranking blind and reconciling on air, with explicit coverage of rares and mythics. **This file is no longer the only rare coverage in the repo.** Where the two disagree, prefer LLU — it is newer, it is channel-pure, and its card names are Scryfall-verified.
>
> Companion files, in descending order of weight:
> - [`draft-guides/limited-level-ups/HOB.md`](../limited-level-ups/HOB.md) — LLU primer: archetypes, top commons/uncommons, **rares + mythics**, Sealed guide. No letter grades (LLU skipped grading for this set); rankings and list positions instead.
> - [`draft-guides/limited-resources/HOB.md`](../limited-resources/HOB.md) — the channel-pure LR 865 distill (commons + uncommons only), kept separate per the ETL contract.

**Dates:** Prerelease **Aug 7–13, 2026** · Arena/MTGO **Aug 11** · Paper **Aug 14** · Set codes **HOB** (Standard/Pioneer/Modern legal) + **HOC** (eternal-only companion)

---

## Format in one line

**A small, deliberately simple set: 193 cards in the Limited pool, five archetypes instead of ten, one per army in the Battle of the Five Armies.** Designed for **Pick-Two Draft** (4-player pods), same structural mold as Spider-Man and TMNT. Both LR hosts described it as Core-Set-adjacent — it contains an actual vanilla creature ([Ordinary Bear](https://scryfall.com/card/hob/133/ordinary-bear)).

Two allied pairs (W/U, B/R) and three enemy pairs (B/G, R/W, G/U). The five **unsupported** pairs — W/B, W/G, U/B, U/R, R/G — have no signposts and no payoffs; playable off raw card quality only.

## The nine format principles

1. **The mana-exchange test decides most cards.** "How would I feel if my opponent killed this with a removal spell that costs *less* than it?" LR applied this to nearly every card and it predicts their grades better than anything else. Five-mana creatures that must untap before doing anything got punished: Wilderland Scrounger D+, Iron Hills Stalwart D, Misty Mountains Raider C+, Glóin the Mighty C+.
2. **Corollary: cheap creatures that replace themselves grade above rate.** Desolation Prowler (B+) and Bilbo Baggins, Burglar (B) are the clearest cases.
3. **Amass is worth less than a token of the same size.** LSV, explicitly: "discount amass goblins — it is worse than just getting a 2/2 or a 3/3." Sacrificing between triggers beats stacking counters, and one removal spell erases the whole investment.
4. **Storied switches on almost by accident.** The storied card counts toward its own three, so you need only two more artifacts/legends/sagas — and Treasure tokens count. Don't grade storied cards as build-arounds, and don't jam bad artifacts to enable them.
5. **Ferocious is entirely attack-triggered.** Every ferocious ability in the commons/uncommons is "whenever this attacks." The deck must be able to attack profitably, not just have a big creature.
6. **Blue is not assertive.** It ramps or draws extra cards. LR did not believe in a blue beatdown deck. The draw-two payoffs all need real enabler density to be more than C-range.
7. **White is the go-wide, low-curve color** — but the set deliberately does *not* go very wide (Goblin Armies are one body), so its payoffs may be under-supported.
8. **Splashing looks bad and the fixing is a trap.** No gold cards pull toward 3+ colors. LR graded [Old Thrush](https://scryfall.com/card/hob/2/old-thrush) a D specifically because bad fixing misleads players into losing games.
9. **Adventure heuristic:** compare the adventure half's cost to the creature's. If the adventure is *cheaper*, you get both halves nearly every time — a real grade bump ([Bilbo Baggins, Burglar](https://scryfall.com/card/hob/34/bilbo-baggins-burglar-take-a-glance), [Gollum, Silent Slinker](https://scryfall.com/card/hob/71/gollum-silent-slinker-meager-meal)). If it's *more expensive*, you usually give the spell half up ([Bilbo, Luckwearer](https://scryfall.com/card/hob/32/bilbo-luckwearer-burglars-plot)).

**Speed:** moderate. B/R and B/G lean aggressive, W/U and R/W grind, G/U is slowest and takes longest to set up. Prioritize 2–3 mana creatures; the format rewards a turn-two play.

## Mechanics

Counts link to a live Scryfall list — tap one to see every card with that mechanic as images.

| Mechanic | Rules | How to play it |
|---|---|---|
| **Recruit** ([10](https://scryfall.com/search?q=set%3Ahob+oracle%3Arecruit)) | Draw a card, then discard a card. If you discarded a nonland, create a 1/1 white Human Soldier. | Free value; smooths flood and screw. Never a reason to take a worse card. Cards you're happy to discard (flashback spells, [Silvan Reveler](https://scryfall.com/card/hob/163/silvan-reveler)) get better. |
| **Storied** ([9](https://scryfall.com/search?q=set%3Ahob+oracle%3Astoried) · [74 enablers](https://scryfall.com/search?q=set%3Ahob+%28type%3Alegendary+or+type%3Aartifact+or+type%3Asaga%29)) | While you control 3+ artifacts, legendary permanents and/or Sagas (combined), you have an **enduring story** for the rest of the game — it doesn't turn off if you lose the permanents. | Like City's Blessing. Easy to switch on; Treasure tokens and common legends count. |
| **Amass Goblins X** ([14](https://scryfall.com/search?q=set%3Ahob+oracle%3Aamass)) | Put X +1/+1 counters on an Army you control; create a 0/0 black Goblin Army first if you have none. | One body, not a wide board. Keep a second threat in hand. Against it, save unconditional removal. |
| **Ferocious** ([6](https://scryfall.com/search?q=set%3Ahob+oracle%3Aferocious) · [33 enablers](https://scryfall.com/search?q=set%3Ahob+pow%3E%3D4)) | Bonus while you control a creature with power 4+. | Count your 4-power creatures before committing. Below ~6 the payoffs are blanks. |
| **Landfall** ([10](https://scryfall.com/search?q=set%3Ahob+oracle%3Alandfall)) | Triggers when a land enters under your control. | Rewards the 18th land and land-return effects. |
| **Hone counters** ([12 equipment](https://scryfall.com/search?q=set%3Ahob+type%3Aequipment)) | Counters on Equipment that raise its bonus. | Boros glue. Bad in multiples — two equipment is plenty. |
| **Adventure** ([17](https://scryfall.com/search?q=set%3Ahob+is%3Aadventure)) | Cast the spell half, exile, cast the creature later. | Two cards in one. Raises your deck's floor more than any synergy. |
| **Treasure** | Sac for one mana of any color. | Your splash enabler, and a free storied enabler. |
| **Cameos** | Kicker, affinity (Elves), behold, prowess, threshold, gift, mountaincycling, **halflingcycling** ([Hobbit Hole](https://scryfall.com/card/hob/184/hobbit-hole), finds one of the set's 9 halflings). | Read once at deckbuilding. |

## The five armies

### W/U Humans — recruit
**Signposts:** [Bard the Bowman](https://scryfall.com/card/hob/145/bard-the-bowman) (B) · [Patient Instructor](https://scryfall.com/card/hob/162/patient-instructor) (C+) · [Eagle's Rescue](https://scryfall.com/card/hob/155/eagles-rescue) (B)
Ground-based aggro-tempo. Recruit converts card selection into bodies, feeding go-wide payoffs and a secondary "drew your second card this turn" shell. Most consistent commons in the set — the strongest **Sealed** default. LR were skeptical of the draw-two payoffs in isolation; they need 3+ enablers.

### R/W Dwarves — storied + equipment
**Signposts:** [Nori, Teller of Tales](https://scryfall.com/card/hob/161/nori-teller-of-tales) (C) · [Thorin Oakenshield](https://scryfall.com/card/hob/165/thorin-oakenshield) (C+) · [Bifur, Melodic Rider](https://scryfall.com/card/hob/147/bifur-melodic-rider) (B)
Efficient creatures, equipment and removal that accumulate storied enablers as a side effect. **The most forgiving pair** — storied happens on its own, so you just play good cards. [Dwarven Mattock](https://scryfall.com/card/hob/172/dwarven-mattock) is a build-around **B inside Dwarves, D outside** — the equipment payoffs live entirely here.

### B/R Goblins — amass + sacrifice
**Signposts:** [Goblin Plate Mail](https://scryfall.com/card/hob/157/goblin-plate-mail) (C/C+) · [Fearsome Goblin Pair](https://scryfall.com/card/hob/156/fearsome-goblin-pair) (B−) · [Bolg of the North](https://scryfall.com/card/hob/148/bolg-of-the-north) (C+)
Best removal in the format, worst resilience. Wants sacrifice outlets because amass pays you for *re-making* the Army. [Snowslope Hunter](https://scryfall.com/card/hob/112/snowslope-hunter) (B) is the engine — a free, no-mana sac outlet that turns Army tokens into cards. Bolg was LR's disappointment: much harder to line up than it reads.

### B/G Wolves & Wargs — ferocious
**Signposts:** [Duskwatch Hunter](https://scryfall.com/card/hob/153/duskwatch-hunter) (C/C+) · [The Chief Warg](https://scryfall.com/card/hob/150/the-chief-warg) (B) · [Large Bear](https://scryfall.com/card/hob/159/large-bear) (B−)
Aggressively-slanted midrange playing naturally large creatures. [Desolation Prowler](https://scryfall.com/card/hob/64/desolation-prowler) (B+) is the best card in the archetype and the **highest-graded card in LR's entire review** — a two-mana Putrid Leech that turns ferocious on by itself.

### G/U Elves — landfall + ramp
**Signposts:** [Mirkwood Nurturer](https://scryfall.com/card/hob/160/mirkwood-nurturer) (C/C−) · [Silvan Reveler](https://scryfall.com/card/hob/163/silvan-reveler) (B) · [Thranduil, Sindarin Liege](https://scryfall.com/card/hob/166/thranduil-sindarin-liege-silvan-rally) (B+)
Thranduil is the highest-graded signpost in the set. Marshall: "blue-green looks incredible." **LSV's counter is the one to weight:** "blue-green misses a lot of the time — one of the decks that misses the most often, up to and including the last Lord of the Rings." Slowest lane, thinnest on removal, run 18 lands.

---

## Rares & mythics

**LR has not graded these** — LR 866 covers rares and mythics the week of Aug 10. Grades below are Draftsim (/10) and Card Game Base (letter) only, both pre-gameplay. Cards with no grade were not covered by either written source; the cost and type are Scryfall-verified so you can evaluate them yourself at the table.

### Graded

| Card | R | Cost | DS | CGB | Note |
|---|---|---|---|---|---|
| <img src="https://cards.scryfall.io/normal/front/3/6/367d5f8b-77ee-47f7-bc71-972d62c280a9.jpg?1784632151" width="230" alt="Beorn the Fierce"><br>[Beorn the Fierce](https://scryfall.com/card/hob/119/beorn-the-fierce) | M | {3}{G}{G} | — | **A** | CGB's #1 card in the set |
| <img src="https://cards.scryfall.io/normal/front/a/5/a56a88ba-fcfa-4b56-bdae-a080b297b871.jpg?1783902783" width="230" alt="The Arkenstone // Seek the Heart"><br>[The Arkenstone // Seek the Heart](https://scryfall.com/card/hob/170/the-arkenstone-seek-the-heart) | M | {5} // {2}{W} | — | **A** | Colorless — goes in every deck |
| <img src="https://cards.scryfall.io/normal/front/3/a/3aa29fe8-1687-486f-b4df-c04977869ab1.jpg?1783902787" width="230" alt="An Unexpected Party // At the Door"><br>[An Unexpected Party // At the Door](https://scryfall.com/card/hob/29/an-unexpected-party-at-the-door) | R | {2}{W}{W} | **10** | **A−** | Both sources' top white card |
| <img src="https://cards.scryfall.io/normal/front/5/5/550cd0b6-ca61-4db7-9d20-0b68c48066f9.jpg?1785236704" width="230" alt="Dancing from Dark to Dawn"><br>[Dancing from Dark to Dawn](https://scryfall.com/card/hob/123/dancing-from-dark-to-dawn) | M | {3}{G}{G} | — | **A−** | Green's other top-tier bomb |
| <img src="https://cards.scryfall.io/normal/front/f/a/fa0554fc-9448-4ae2-8712-4f4f7af3c7b4.jpg?1784636060" width="230" alt="The Lord of the Eagles"><br>[The Lord of the Eagles](https://scryfall.com/card/hob/46/the-lord-of-the-eagles) | R | {7}{U}{U} | **9** | — | Cost reduction with fliers out |
| <img src="https://cards.scryfall.io/normal/front/3/1/31a7a5e2-4cb8-48fc-8351-18344b4a7560.jpg?1785496349" width="230" alt="Settle the Wreckage"><br>[Settle the Wreckage](https://scryfall.com/card/hob/26/settle-the-wreckage) | R | {2}{W}{W} | **9** | B+ | Best white answer |
| <img src="https://cards.scryfall.io/normal/front/b/0/b02142f3-5e55-40dc-a02c-9113fb7d763c.jpg?1785496367" width="230" alt="Fíli the Pathfinder"><br>[Fíli the Pathfinder](https://scryfall.com/card/hob/14/f%C3%ADli-the-pathfinder) | R | {3}{W} | **8** | B+ | ⚠ **Rare, not uncommon** — see conflicts |
| <img src="https://cards.scryfall.io/normal/front/1/8/1805532f-6d99-47d0-9529-5f5831a7fdc8.jpg?1785496242" width="230" alt="Kíli the Resourceful"><br>[Kíli the Resourceful](https://scryfall.com/card/hob/17/k%C3%ADli-the-resourceful) | R | {1}{W} | **8** | — | ⚠ **Rare, not uncommon** |
| <img src="https://cards.scryfall.io/normal/front/6/a/6a5d8fad-2ffd-4645-8c49-907999b6cecf.jpg?1783902784" width="230" alt="Smaug the Magnificent"><br>[Smaug the Magnificent](https://scryfall.com/card/hob/110/smaug-the-magnificent) | M | {2}{R}{R} | — | B+ | The headliner. 4-mana dragon; **indestructible**, so The Black Arrow can't kill it |
| <img src="https://cards.scryfall.io/normal/front/1/1/117347af-0dd7-4350-901d-8c8a81387e22.jpg?1783902784" width="230" alt="Thorin, Mountain-king"><br>[Thorin, Mountain-king](https://scryfall.com/card/hob/114/thorin-mountain-king) | M | {3}{R} | — | B+ | ⚠ Mythic, not a rare |
| <img src="https://cards.scryfall.io/normal/front/5/f/5f4f4683-ffd2-447a-932b-276f7fa17cca.jpg?1785496221" width="230" alt="Stone-Giant of High Pass"><br>[Stone-Giant of High Pass](https://scryfall.com/card/hob/113/stone-giant-of-high-pass) | R | {5}{R}{R} | — | B+ | |
| <img src="https://cards.scryfall.io/normal/front/0/b/0bda1b62-47fc-42c2-a841-ccad8ea0db48.jpg?1784376936" width="230" alt="The Eagles Are Coming!"><br>[The Eagles Are Coming!](https://scryfall.com/card/hob/12/the-eagles-are-coming!) | R | {1}{W} | — | B+ | |
| <img src="https://cards.scryfall.io/normal/front/3/f/3ffe34d4-72f4-4562-a948-8909b9321e59.jpg?1785152416" width="230" alt="Head of the Hunt"><br>[Head of the Hunt](https://scryfall.com/card/hob/75/head-of-the-hunt) | R | {2}{B}{B} | — | B+ | Black's best by CGB |
| <img src="https://cards.scryfall.io/normal/front/4/2/42fbd61d-e1a6-465d-b1a3-f5ee0869d3af.jpg?1785496910" width="230" alt="Celebrate the Mountain-king"><br>[Celebrate the Mountain-king](https://scryfall.com/card/hob/7/celebrate-the-mountain-king) | U | {3}{W} | **7** | — | *(uncommon; listed here because both sources rate it)* — LR **B+** |
| <img src="https://cards.scryfall.io/normal/front/7/d/7d6ece3d-8e7a-41ad-974f-3c9748de4825.jpg?1785323269" width="230" alt="Gigantic Big Bear"><br>[Gigantic Big Bear](https://scryfall.com/card/hob/126/gigantic-big-bear) | R | {5}{G}{G} | — | B+ | |
| <img src="https://cards.scryfall.io/normal/front/b/2/b2fb3995-5b43-4776-88b2-346d353edee0.jpg?1784862975" width="230" alt="Great Gilded Boat"><br>[Great Gilded Boat](https://scryfall.com/card/hob/42/great-gilded-boat) | R | {2}{U} | **7** | B | Vehicle |
| <img src="https://cards.scryfall.io/normal/front/e/9/e95eba5c-e0d6-46b4-a0be-8e373b2185ea.jpg?1785496330" width="230" alt="Bejeweled Warg"><br>[Bejeweled Warg](https://scryfall.com/card/hob/117/bejeweled-warg) | R | {1}{G} | — | B | |
| <img src="https://cards.scryfall.io/normal/front/b/b/bbdc7e37-c65a-497a-92b7-a30a6e369c71.jpg?1784376959" width="230" alt="Gollum, Riddle Master"><br>[Gollum, Riddle Master](https://scryfall.com/card/hob/70/gollum-riddle-master) | M | {1}{B} | **6** | B | ⚠ Both sources call it **underwhelming for a mythic** |
| <img src="https://cards.scryfall.io/normal/front/5/7/5741bbad-a6e4-45e0-b827-73f48c9975bf.jpg?1785496313" width="230" alt="Radagast of Rhosgobel"><br>[Radagast of Rhosgobel](https://scryfall.com/card/hob/136/radagast-of-rhosgobel) | R | {2}{G}{G} | high | — | |
| <img src="https://cards.scryfall.io/normal/front/c/a/ca0f7bf4-b8a2-4ec4-ad7e-b639de9fa76a.jpg?1785496323" width="230" alt="Troll Negotiations"><br>[Troll Negotiations](https://scryfall.com/card/hob/138/troll-negotiations) | U | {2}{G}{G} | — | — | LR **B** — part of the answer to G/U's removal shortage |

### Ungraded — evaluate at the table

**White:** [Belladonna Took](https://scryfall.com/card/hob/4/belladonna-took) {1}{W} · [Bilbo's Gambit](https://scryfall.com/card/hob/5/bilbos-gambit) {1}{W} · [Gleaming Splendor](https://scryfall.com/card/hob/15/gleaming-splendor) M {1}{W} · [The Queen of Dale](https://scryfall.com/card/hob/24/the-queen-of-dale) M {1}{W} · [Roads Go Ever, Ever On](https://scryfall.com/card/hob/25/roads-go-ever-ever-on) {1}{W} Saga

**Blue:** [Bilbo, Thief in the Night](https://scryfall.com/card/hob/33/bilbo-thief-in-the-night) M {1}{U} · [Elrond, Moon-Reader](https://scryfall.com/card/hob/36/elrond-moon-reader) M {2}{U} · [Fateful Discovery](https://scryfall.com/card/hob/40/fateful-discovery) M {3}{U}{U} · [Riddles in the Dark](https://scryfall.com/card/hob/53/riddles-in-the-dark) {2}{U} · [Roll-Roll-Roll-Roll](https://scryfall.com/card/hob/54/roll-roll-roll-roll) {2}{U} Saga · [Uncover the Moon-Letters](https://scryfall.com/card/hob/57/uncover-the-moon-letters) {3}{U} · [Most Decrepit Old Bird // Speak Secrets](https://scryfall.com/card/hob/49/most-decrepit-old-bird-speak-secrets) {U} · [Wizard's Staff](https://scryfall.com/card/hob/59/wizards-staff) {1}{U}

**Black:** [Along the Crooked Way](https://scryfall.com/card/hob/60/along-the-crooked-way) {2}{B} · [Azog, Moria's Ruin](https://scryfall.com/card/hob/61/azog-morias-ruin) {2}{B} · [Inside Information](https://scryfall.com/card/hob/76/inside-information) M {X}{B}{B} · [The Master of Lake-town](https://scryfall.com/card/hob/77/the-master-of-lake-town) {1}{B}{B} · [Rhovanion Rampager](https://scryfall.com/card/hob/82/rhovanion-rampager) {2}{B} · [The Sackville-Bagginses](https://scryfall.com/card/hob/83/the-sackville-bagginses) {1}{B} · [Supper for Spiders](https://scryfall.com/card/hob/86/supper-for-spiders) {1}{B}

**Red:** [Balin, Loremaster](https://scryfall.com/card/hob/87/balin-loremaster) {3}{R}{R} · [Dáin Ironfoot](https://scryfall.com/card/hob/91/d%C3%A1in-ironfoot) {2}{R} · [Desert Were-Worm](https://scryfall.com/card/hob/92/desert-were-worm) {4}{R}{R} · [Desolation of Smaug](https://scryfall.com/card/hob/93/desolation-of-smaug) {2}{R}{R} · [Gandalf, Goblins' Bane // Flameshape](https://scryfall.com/card/hob/96/gandalf-goblins-bane-flameshape) M {2}{R} · [Getaway Barrel](https://scryfall.com/card/hob/98/getaway-barrel) {3}{R} · [Last Light of Durin's Day](https://scryfall.com/card/hob/103/last-light-of-durins-day) {1}{R} · [The Misty Mountains Cold](https://scryfall.com/card/hob/104/the-misty-mountains-cold) {2}{R} Saga

**Green:** [Cantankerous Keepers](https://scryfall.com/card/hob/122/cantankerous-keepers) {5}{G} · [Down in the Valley](https://scryfall.com/card/hob/124/down-in-the-valley) {2}{G} Saga · [The Notary Hobbits](https://scryfall.com/card/hob/131/the-notary-hobbits) {3}{G}{G} · [Part in Friendship](https://scryfall.com/card/hob/134/part-in-friendship) {4}{G} · [Through the Forest Gate](https://scryfall.com/card/hob/137/through-the-forest-gate) {6}{G}{G}

**Multicolor:** [Bard, King of Dale](https://scryfall.com/card/hob/144/bard-king-of-dale) M {4}{W}{U} · [Bard's Company](https://scryfall.com/card/hob/146/bards-company) {2}{W}{U} · [Bolg's Company](https://scryfall.com/card/hob/149/bolgs-company) {B}{R} · [Chief Warg's Company](https://scryfall.com/card/hob/151/chief-wargs-company) {1}{B}{G} · [Dáin's Company](https://scryfall.com/card/hob/152/d%C3%A1ins-company) {R}{W} · [Dwalin, Weaponmaster](https://scryfall.com/card/hob/154/dwalin-weaponmaster) {1}{R/W} · [The Great Goblin](https://scryfall.com/card/hob/158/the-great-goblin) {1}{B/R}{B/R} · [Smaug, Wicked Worm](https://scryfall.com/card/hob/164/smaug-wicked-worm) {3}{B}{R} · [Thranduil, the Elvenking](https://scryfall.com/card/hob/167/thranduil-the-elvenking) {2}{B}{G}{U} · [Thranduil's Company](https://scryfall.com/card/hob/168/thranduils-company) {2}{G}{U} · [Tom, Bert, and William](https://scryfall.com/card/hob/169/tom-bert-and-william) {3}{B}{G}

**Artifacts & lands:** [Orcrist, Goblin-cleaver](https://scryfall.com/card/hob/177/orcrist-goblin-cleaver) M {3} · [Glamdring, Foe-hammer // Gleam of Death](https://scryfall.com/card/hob/174/glamdring-foe-hammer-gleam-of-death) {2} · [My Precious // Allure of Power](https://scryfall.com/card/hob/176/my-precious-allure-of-power) {3} · [Sting, Bilbo's Sword](https://scryfall.com/card/hob/178/sting-bilbos-sword) {2} · [The Lonely Mountain](https://scryfall.com/card/hob/187/the-lonely-mountain) · [Elven Passage](https://scryfall.com/card/hob/181/elven-passage)

---

## Commons & uncommons — LR 865 grades

LR's A–F scale with ± subgrades, plus **sideboard** and **build-around**. Splits between Marshall and LSV preserved. **`R` column: c = common, u = uncommon.**

### White

| Card | R | Grade | Note |
|---|---|---|---|
| <img src="https://cards.scryfall.io/normal/front/4/2/42fbd61d-e1a6-465d-b1a3-f5ee0869d3af.jpg?1785496910" width="230" alt="Celebrate the Mountain-king"><br>[Celebrate the Mountain-king](https://scryfall.com/card/hob/7/celebrate-the-mountain-king) | u | **B+** | Four-mana O-Ring that also recruits. Highest-graded white card. |
| <img src="https://cards.scryfall.io/normal/front/6/8/68f4893d-e9a5-4f89-ade3-9ab78a834ad5.jpg?1784631780" width="230" alt="The Mountain-king's Return"><br>[The Mountain-king's Return](https://scryfall.com/card/hob/22/the-mountain-kings-return) | u | **B** | Saga: recruit → raise dead (MV ≤3) → +1/+1 counter. Needs 1–3 drops. |
| <img src="https://cards.scryfall.io/normal/front/9/9/99d27749-d16c-45e9-accc-6a01351c17f9.jpg?1785496921" width="230" alt="Dáin, Lord of the Iron Hills"><br>[Dáin, Lord of the Iron Hills](https://scryfall.com/card/hob/8/d%C3%A1in-lord-of-the-iron-hills) | u | **B−** | 2-mana 2/2 vigilance with storied; Propaganda is a bonus, not the reason. |
| <img src="https://cards.scryfall.io/normal/front/3/7/370e09c2-36c5-4662-8350-1db798afad3e.jpg?1784631771" width="230" alt="Iron Hills Blacksmith"><br>[Iron Hills Blacksmith](https://scryfall.com/card/hob/16/iron-hills-blacksmith) | u | **B−** | 1/1 double strike that makes an Axe token — artifact for storied, hits for 4. |
| <img src="https://cards.scryfall.io/normal/front/c/5/c5752731-253c-4b41-bdd8-94c26d715206.jpg?1784631953" width="230" alt="Stone by Sunlight"><br>[Stone by Sunlight](https://scryfall.com/card/hob/27/stone-by-sunlight) | u | **B−** | Destroy a power-4+ creature, or grant indestructible. Always trades up. |
| <img src="https://cards.scryfall.io/normal/front/6/7/67304269-c595-4cf0-8dbf-fcb2e9e01fe2.jpg?1785496951" width="230" alt="Lake-town Toymaker"><br>[Lake-town Toymaker](https://scryfall.com/card/hob/19/lake-town-toymaker) | u | **B−** | 3/4; +3/+0 and first strike if you've drawn two. Needs free recruit effects. |
| <img src="https://cards.scryfall.io/normal/front/3/f/3feca644-5f65-4477-bbc8-d505cec6f3a5.jpg?1784797947" width="230" alt="Eagle of the Great Shelf"><br>[Eagle of the Great Shelf](https://scryfall.com/card/hob/11/eagle-of-the-great-shelf) | u | **C/C+** | 2/5 flier that pumps per other creature. Meets the bar despite 5-mana risk. |
| <img src="https://cards.scryfall.io/normal/front/6/b/6b8e6435-7de4-41d5-bc7d-8e24c11897d0.jpg?1785496981" width="230" alt="Bofur, Reliable Guardian"><br>[Bofur, Reliable Guardian](https://scryfall.com/card/hob/6/bofur-reliable-guardian-concerted-care) | u | **C** | 1-mana 1/1 lifelink legend + hexproof/indestructible adventure. C+ in storied decks. |
| <img src="https://cards.scryfall.io/normal/front/1/7/178c4cf6-6b11-40e4-9673-c560d6818a6b.jpg?1785496946" width="230" alt="Lake-town Lookout"><br>[Lake-town Lookout](https://scryfall.com/card/hob/18/lake-town-lookout) | c | **C** | 1/1 that recruits on death. Low impact, but one-drops that do anything are hard to underrate. |
| <img src="https://cards.scryfall.io/normal/front/1/f/1f9a61a1-454e-4d5b-a6dd-1a79fe9dedf3.jpg?1785496922" width="230" alt="Dwarven Provisioner"><br>[Dwarven Provisioner](https://scryfall.com/card/hob/9/dwarven-provisioner) | c | **C** | 2/2 with a 4-mana team pump. "You'll see it on the battlefield all the time." |
| <img src="https://cards.scryfall.io/normal/front/f/2/f2341cf3-4d2c-4a4f-9aea-8834104a8910.jpg?1785496931" width="230" alt="Dwarven Shortsword"><br>[Dwarven Shortsword](https://scryfall.com/card/hob/10/dwarven-shortsword) | c | **C** | Four mana for a 3/4 that leaves a +1/+2 sword. |
| <img src="https://cards.scryfall.io/normal/front/5/c/5cc0f994-5048-4898-926e-b56cbc97e0ca.jpg?1785497031" width="230" alt="Velvetwing Butterflies // Gaze in Wonder"><br>[Velvetwing Butterflies // Gaze in Wonder](https://scryfall.com/card/hob/30/velvetwing-butterflies-gaze-in-wonder) | c | **C** | 2/2 flier + instant adventure that taps one or two creatures. |
| <img src="https://cards.scryfall.io/normal/front/5/7/573f67b0-6ce8-4857-a703-4a5728640736.jpg?1785496934" width="230" alt="Esgaroth Garrison"><br>[Esgaroth Garrison](https://scryfall.com/card/hob/13/esgaroth-garrison) | c | **C** | */5 for five that recruits; power = creature count. |
| <img src="https://cards.scryfall.io/normal/front/4/3/430c8916-1167-400b-9cad-d301f59d5e5d.jpg?1785497008" width="230" alt="Magnificent End"><br>[Magnificent End](https://scryfall.com/card/hob/20/magnificent-end) | c | **C** | Five damage for 5, or 2 if the target is tapped. |
| <img src="https://cards.scryfall.io/normal/front/0/a/0a6a6ff0-b1cd-4b06-bd31-612690094e0e.jpg?1785497012" width="230" alt="Moment of Glory"><br>[Moment of Glory](https://scryfall.com/card/hob/21/moment-of-glory) | c | **C** (from C−) | Flashback team pump; the card you *want* to discard to recruit. |
| <img src="https://cards.scryfall.io/normal/front/1/2/127367b6-9cfe-4516-9bfd-5b951468a25c.jpg?1785497020" width="230" alt="Thorin's Last Stand"><br>[Thorin's Last Stand](https://scryfall.com/card/hob/28/thorins-last-stand) | c | **C** (from C−) | Modal team pump / disenchant + 2 life. Can just win a go-wide game. |
| <img src="https://cards.scryfall.io/normal/front/c/5/c5727af5-a487-4b16-8278-81c3c928c417.jpg?1785323179" width="230" alt="Ori, Keeper of Songs"><br>[Ori, Keeper of Songs](https://scryfall.com/card/hob/23/ori-keeper-of-songs) | c | **C−** | 3/3 legendary dwarf with storied; you play it to *be* an enabler. |
| <img src="https://cards.scryfall.io/normal/front/8/d/8d4f3eb5-fedf-45d6-8bd8-aacbe0ce33b2.jpg?1785497034" width="230" alt="Vow to Erebor"><br>[Vow to Erebor](https://scryfall.com/card/hob/31/vow-to-erebor) | c | **D** | Untap + 2/+2 for two isn't enough unless the equipment rider matters. |

### Blue

| Card | R | Grade | Note |
|---|---|---|---|
| <img src="https://cards.scryfall.io/normal/front/6/a/6a109b3e-9f5b-4625-abb7-6b992c10530b.jpg?1785323194" width="230" alt="Bilbo Baggins, Burglar // Take a Glance"><br>[Bilbo Baggins, Burglar // Take a Glance](https://scryfall.com/card/hob/34/bilbo-baggins-burglar-take-a-glance) | c | **B** | **Best common in the set.** 3-mana 2/1 that draws, plus a Scry 2 you always get. LR compared it to Hero in Training (an A−). |
| <img src="https://cards.scryfall.io/normal/front/8/b/8bff0aa6-16d9-4c83-b598-ef00a3b33d2c.jpg?1783902786" width="230" alt="Bilbo, Luckwearer // Burglar's Plot"><br>[Bilbo, Luckwearer // Burglar's Plot](https://scryfall.com/card/hob/32/bilbo-luckwearer-burglars-plot) | u | **B** | Two-mana unblockable looter; the adventure costs more than the creature, so you usually forgo it. |
| <img src="https://cards.scryfall.io/normal/front/4/a/4a865cea-f947-4736-8ace-ba478fceeb22.jpg?1785497065" width="230" alt="Old Fat Spider Can't See Me"><br>[Old Fat Spider Can't See Me](https://scryfall.com/card/hob/50/old-fat-spider-cant-see-me) | u | **B / B−** | Saga: hexproof → fog a creature indefinitely → draw → draw. |
| <img src="https://cards.scryfall.io/normal/front/a/d/addcefdd-e012-4adf-9052-e60376a8d2d3.jpg?1784798124" width="230" alt="Master's Councillors"><br>[Master's Councillors](https://scryfall.com/card/hob/47/masters-councillors) | u | **C+** (from D) | 1/3 vigilance, mills 3 on your second draw. Really a 2-mana 3/3 vigilance. **Excellent in Sealed.** |
| <img src="https://cards.scryfall.io/normal/front/a/f/afb73190-b9bd-4744-a011-a37cd9c0148d.jpg?1785496438" width="230" alt="Plunder the Trollshaws"><br>[Plunder the Trollshaws](https://scryfall.com/card/hob/51/plunder-the-trollshaws) | c | **C+** | Think Twice. Triggers draw-two payoffs on both halves; flashback works on their turn. |
| <img src="https://cards.scryfall.io/normal/front/a/d/ad40a4b9-9fab-49c1-8e9f-6e0776966833.jpg?1785497045" width="230" alt="Enchanted River's Grasp"><br>[Enchanted River's Grasp](https://scryfall.com/card/hob/39/enchanted-rivers-grasp) | c | **C+** | Blue's clean removal aura. Templated specifically to kill Armies (strips counters). |
| <img src="https://cards.scryfall.io/normal/front/e/4/e49866d4-966a-40f9-b08d-18e5af6d726b.jpg?1785497074" width="230" alt="Uneasy Partings"><br>[Uneasy Partings](https://scryfall.com/card/hob/58/uneasy-partings) | c | **C+** | Top-or-bottom a creature; 1 less against attacking nontokens. |
| <img src="https://cards.scryfall.io/normal/front/c/d/cd5af94d-6321-4834-8e5f-e5d0261b3ef3.jpg?1785497055" width="230" alt="Long Lake Nuisance"><br>[Long Lake Nuisance](https://scryfall.com/card/hob/45/long-lake-nuisance) | c | **C** | Four-mana 3/1 flier with recruit. Good stat line for a flier. |
| <img src="https://cards.scryfall.io/normal/front/4/2/4202a678-a5f4-47f9-9c18-e88ab9ad20a4.jpg?1785237929" width="230" alt="Lake-town Mariners // Gone Fishing"><br>[Lake-town Mariners // Gone Fishing](https://scryfall.com/card/hob/44/lake-town-mariners-gone-fishing) | u | **C** | 6/5 vigilance ward 2 + instant blink of two permanents. Two mediocre halves that add up. |
| <img src="https://cards.scryfall.io/normal/front/e/4/e4ded4c1-0e3e-47c5-8fdc-e7c187f68b12.jpg?1784760181" width="230" alt="Thranduil's Decree"><br>[Thranduil's Decree](https://scryfall.com/card/hob/56/thranduils-decree) | u | **C** | Six-mana counter that lets you cast a countered permanent free. "An F or an A, not in between." Worse in Bo1. |
| <img src="https://cards.scryfall.io/normal/front/9/d/9de48690-e5ae-495a-addf-305f1db7ec21.jpg?1785496428" width="230" alt="Confusticate and Bebother"><br>[Confusticate and Bebother](https://scryfall.com/card/hob/35/confusticate-and-bebother) | c | **C−** | Force Spike-for-4, or draw two discard one. |
| <img src="https://cards.scryfall.io/normal/front/c/1/c141695c-c108-41d5-85cb-1f7485d9d533.jpg?1784632054" width="230" alt="Elven Raft-Steerer"><br>[Elven Raft-Steerer](https://scryfall.com/card/hob/37/elven-raft-steerer) | u | **C−** | 3/2 landfall tap-or-untap. Blue isn't assertive enough to want the tempo. |
| <img src="https://cards.scryfall.io/normal/front/a/b/abfbb255-a39b-4df5-bfb6-5298584e89f0.jpg?1785497053" width="230" alt="Lakeshore Apothecary"><br>[Lakeshore Apothecary](https://scryfall.com/card/hob/43/lakeshore-apothecary) | c | **build-around C** | 1/2 vigilance that grows on your second draw. D outside a heavy recruit deck. |
| <img src="https://cards.scryfall.io/normal/front/d/d/dd32a1dd-3541-4572-a717-1deabc14b827.jpg?1784760160" width="230" alt="Sound the Trumpets"><br>[Sound the Trumpets](https://scryfall.com/card/hob/55/sound-the-trumpets) | u | **D+ draft / C+ SEALED** | Cancel that recruits off cheap spells. LR flagged it as notably better in Sealed. |
| <img src="https://cards.scryfall.io/normal/front/1/f/1f8403a2-849c-4a59-b0ed-c8803995028d.jpg?1785496472" width="230" alt="Gandalf, Wandering Wizard"><br>[Gandalf, Wandering Wizard](https://scryfall.com/card/hob/41/gandalf-wandering-wizard) | c | **D/D+** | 5-mana 4/5 ward 3 with a 6-mana "shuffle me in, draw 3." Rarely a responsible 11 mana. |
| <img src="https://cards.scryfall.io/normal/front/a/d/ad7ed4e6-3fe2-40f1-909b-a03b2a3c941a.jpg?1785497064" width="230" alt="Mirkwood Meditator"><br>[Mirkwood Meditator](https://scryfall.com/card/hob/48/mirkwood-meditator) | c | **D** | 2/4 landfall that can become 4/2. Lost between archetypes. |
| <img src="https://cards.scryfall.io/normal/front/a/c/acbb4d32-2771-469e-a6de-0df15155cc62.jpg?1784714603" width="230" alt="Ravenhill Flock"><br>[Ravenhill Flock](https://scryfall.com/card/hob/52/ravenhill-flock) | u | **D** | **Trap.** 1/2 flier that grows on every draw. "These basically never work." |
| <img src="https://cards.scryfall.io/normal/front/9/c/9c50656d-c74a-4e90-9ef7-afa237682516.jpg?1785497043" width="230" alt="Elvenking's Harper"><br>[Elvenking's Harper](https://scryfall.com/card/hob/38/elvenkings-harper) | c | **D** | 2/2 with a 5-mana unblockable activation. |

### Black

| Card | R | Grade | Note |
|---|---|---|---|
| <img src="https://cards.scryfall.io/normal/front/6/3/63c87009-ff1b-44b9-88b1-e26219094c67.jpg?1785237955" width="230" alt="Desolation Prowler"><br>[Desolation Prowler](https://scryfall.com/card/hob/64/desolation-prowler) | u | **B+** | **Highest-graded card in the review.** Putrid Leech that's easier to cast; auto-ferocious, right side of the mana exchange. |
| <img src="https://cards.scryfall.io/normal/front/d/3/d3cbe830-7e95-4019-89c4-cfb36bcf00f8.jpg?1784894860" width="230" alt="Nighthowl Pursuer"><br>[Nighthowl Pursuer](https://scryfall.com/card/hob/78/nighthowl-pursuer) | u | **B** | One-mana 1/1 menace that attacks as a 3/3 with ferocious on. |
| <img src="https://cards.scryfall.io/normal/front/2/c/2ce066be-e5ad-4b93-8245-1b5018990d03.jpg?1784733910" width="230" alt="Gathering of Darkness"><br>[Gathering of Darkness](https://scryfall.com/card/hob/68/gathering-of-darkness) | u | **B** | Four-mana Gravedigger that also amasses 3. "Reason to go into black." |
| <img src="https://cards.scryfall.io/normal/front/5/d/5d485d70-c7b9-40a4-9089-5e7f1c2b9213.jpg?1784734464" width="230" alt="Gnashing of Teeth"><br>[Gnashing of Teeth](https://scryfall.com/card/hob/69/gnashing-of-teeth) | u | **B** | Modal −5/−5 with exile, or a −1/−1 sweep. Sorcery speed is the only knock. |
| <img src="https://cards.scryfall.io/normal/front/b/7/b72e193c-e030-4936-9b79-c636eff750e1.jpg?1784733900" width="230" alt="Down, Down to Goblin-town"><br>[Down, Down to Goblin-town](https://scryfall.com/card/hob/65/down-down-to-goblin-town) | u | **B** | Saga: Duress → amass 1 → drain → drain. Strictly better than Rage into the Valley. |
| <img src="https://cards.scryfall.io/normal/front/c/8/c87f6004-e1cf-42b2-9647-322bc4939339.jpg?1785237962" width="230" alt="Great Ugly-Looking Goblin // Clap! Snap!"><br>[Great Ugly-Looking Goblin // Clap! Snap!](https://scryfall.com/card/hob/74/great-ugly-looking-goblin-clap!-snap!) | u | **B** | 4/4 for six + a 2-mana amass-2 adventure; grants menace to countered creatures. |
| <img src="https://cards.scryfall.io/normal/front/1/7/17892c93-b9b2-4720-933b-998ed0200492.jpg?1785497075" width="230" alt="Bilbo's Deadly Slice"><br>[Bilbo's Deadly Slice](https://scryfall.com/card/hob/62/bilbos-deadly-slice) | c | **C+/B−** | The set's Murder at {1}{B}{B}. Double black is the only friction. |
| <img src="https://cards.scryfall.io/normal/front/f/d/fd145e3a-c889-4390-accb-863dbcc845ce.jpg?1785497107" width="230" alt="Stir Up Trouble"><br>[Stir Up Trouble](https://scryfall.com/card/hob/84/stir-up-trouble) | c | **C+** | One-mana Destroy with an additional cost (sac an artifact/creature, or pay 4). Great with Armies. |
| <img src="https://cards.scryfall.io/normal/front/0/7/07bfc803-e11b-47ab-9f25-0ace7e174200.jpg?1785496282" width="230" alt="Front Porch Sentries"><br>[Front Porch Sentries](https://scryfall.com/card/hob/67/front-porch-sentries) | c | **C+** | Two-mana 2/2 that gives −1/−1 on death. Better than the usual 1-mana version. |
| <img src="https://cards.scryfall.io/normal/front/6/f/6fcc3699-b475-4612-884d-81bd4f21e9c1.jpg?1785497106" width="230" alt="Stony-Voiced Goblins"><br>[Stony-Voiced Goblins](https://scryfall.com/card/hob/85/stony-voiced-goblins) | c | **C+** | 1/1 that strips a card. Excellent sacrifice fodder. |
| <img src="https://cards.scryfall.io/normal/front/8/6/8651958c-3b94-47a9-a751-faf8f6236a42.jpg?1785496290" width="230" alt="Rage into the Valley"><br>[Rage into the Valley](https://scryfall.com/card/hob/79/rage-into-the-valley) | c | **C+** | Draw a card, lose a life, amass 2. |
| <img src="https://cards.scryfall.io/normal/front/e/a/ea7b5052-b343-466d-879e-2a211657ef0a.jpg?1785497096" width="230" alt="Ravening Warg"><br>[Ravening Warg](https://scryfall.com/card/hob/80/ravening-warg) | c | **C** | Two-mana 2/2 deathtouch, gains 2 life on a ferocious attack. |
| <img src="https://cards.scryfall.io/normal/front/6/c/6cfaa182-3fec-4907-8814-b4d29c33cec3.jpg?1785323234" width="230" alt="Gollum, Silent Slinker // Meager Meal"><br>[Gollum, Silent Slinker // Meager Meal](https://scryfall.com/card/hob/71/gollum-silent-slinker-meager-meal) | c | **C−/D** | 4/3 menace at common + a 1-mana adventure. You get both halves nearly always. |
| <img src="https://cards.scryfall.io/normal/front/f/a/fa8fd3c4-bd00-485d-80b1-2b67f5786fce.jpg?1785496297" width="230" alt="Crude Bent Blade"><br>[Crude Bent Blade](https://scryfall.com/card/hob/63/crude-bent-blade) | c | **C−/D** | Equipment stapled to an Edict. LSV: edicts will be bad in a format full of tokens and Armies. |
| <img src="https://cards.scryfall.io/normal/front/5/0/50d91ef3-6f5d-4255-8d47-be731b5dad30.jpg?1784733916" width="230" alt="Gollum the Abandoned"><br>[Gollum the Abandoned](https://scryfall.com/card/hob/72/gollum-the-abandoned) | u | **D+ / C+ in aggro** | Can't block — a much bigger liability than aggro drafters expect. Wants sacrifice fodder. |
| <img src="https://cards.scryfall.io/normal/front/6/7/67d52db5-597e-46d5-af39-c3a2de107d30.jpg?1785497085" width="230" alt="Dreaded Bat-Cloud"><br>[Dreaded Bat-Cloud](https://scryfall.com/card/hob/66/dreaded-bat-cloud) | u | **C+/D+** | 4/2 flying deathtouch, 3 less if a creature died this turn. Morbid is harder to enable than it looks. |
| <img src="https://cards.scryfall.io/normal/front/9/d/9d9ef88f-d208-4788-9553-cd672b3be1fe.jpg?1785497086" width="230" alt="Great Fierce Bee"><br>[Great Fierce Bee](https://scryfall.com/card/hob/73/great-fierce-bee) | c | **D/D+** | Three-mana 2/2 flier that scries on any creature death. |
| <img src="https://cards.scryfall.io/normal/front/1/6/16765eb2-d497-4cd6-b683-20eac2f10bbf.jpg?1785497096" width="230" alt="Reverent Howl"><br>[Reverent Howl](https://scryfall.com/card/hob/81/reverent-howl) | c | **D** | Draw 2 lose 2, or a bad +2/+2 lifelink trick. Weak on both halves. |

### Red

| Card | R | Grade | Note |
|---|---|---|---|
| <img src="https://cards.scryfall.io/normal/front/c/b/cb25b11a-6bf5-4a9a-b60f-d4dcac3816d6.jpg?1784894881" width="230" alt="Bothersome Noisemaker"><br>[Bothersome Noisemaker](https://scryfall.com/card/hob/89/bothersome-noisemaker) | u | **B** | Two-mana 2/2 that amasses on every noncreature spell. Kill on sight. |
| <img src="https://cards.scryfall.io/normal/front/4/7/47666099-ffb2-4d07-a801-70524dba0837.jpg?1785497147" width="230" alt="Snowslope Hunter"><br>[Snowslope Hunter](https://scryfall.com/card/hob/112/snowslope-hunter) | u | **B** | 2/3 with a **free, no-mana sac outlet** that exiles the top card to play. The B/R engine. |
| <img src="https://cards.scryfall.io/normal/front/7/c/7c5c6f1c-35cf-4172-b5a1-b73222b0723b.jpg?1784895032" width="230" alt="Gandalf, Spark Starter"><br>[Gandalf, Spark Starter](https://scryfall.com/card/hob/97/gandalf-spark-starter) | u | **B** | Six-mana 4/3 reach dealing 3 divided. Cleans up after a favorable attack. |
| <img src="https://cards.scryfall.io/normal/front/e/a/ea174cea-40e5-424e-9734-e39aae6c6b17.jpg?1785496194" width="230" alt="Pinecone Strike"><br>[Pinecone Strike](https://scryfall.com/card/hob/107/pinecone-strike) | c | **B−** | Two-mana instant, 3 damage with exile, + destroy an artifact token. Red's best common removal. |
| <img src="https://cards.scryfall.io/normal/front/6/3/63c317e7-432c-4817-8db4-3670a1d84be3.jpg?1785496185" width="230" alt="Bombur, Gentle Dreamer"><br>[Bombur, Gentle Dreamer](https://scryfall.com/card/hob/88/bombur-gentle-dreamer) | u | **B−** | Three-mana 5/3 that won't untap without an enduring story. Blocks fine, auto-ferocious, one-third of storied. |
| <img src="https://cards.scryfall.io/normal/front/3/8/38c16a0a-375e-48cb-9720-dbbc08c603ae.jpg?1785497148" width="230" alt="Tidings of War"><br>[Tidings of War](https://scryfall.com/card/hob/115/tidings-of-war) | c | **C+** | Amass 1, flashback for amass 3. Good to mill, discard, and sac. |
| <img src="https://cards.scryfall.io/normal/front/d/2/d2f60ad0-c887-4585-85f8-afcf72fb80d0.jpg?1785323237" width="230" alt="Dori, Bearer of Friends"><br>[Dori, Bearer of Friends](https://scryfall.com/card/hob/94/dori-bearer-of-friends) | c | **C+** | Three-mana 3/2 trample legend that makes a Treasure — two-thirds of storied on one card. |
| <img src="https://cards.scryfall.io/normal/front/5/7/5793b8eb-2fc5-454d-8fa2-20346fef167a.jpg?1785324545" width="230" alt="Glóin the Mighty // Easy Pickings"><br>[Glóin the Mighty // Easy Pickings](https://scryfall.com/card/hob/99/gl%C3%B3in-the-mighty-easy-pickings) | u | **C+** | 4/3 that adds {R} each main phase; adventure pings each opposing creature. Grade hinges on Easy Pickings. |
| <img src="https://cards.scryfall.io/normal/front/6/d/6dff14cd-b60b-48f4-9d9f-c9019b55df4c.jpg?1785152178" width="230" alt="Misty Mountains Raider"><br>[Misty Mountains Raider](https://scryfall.com/card/hob/105/misty-mountains-raider) | u | **C+** | Five-mana 4/4 that amasses 2 on attack. Has to survive. |
| <img src="https://cards.scryfall.io/normal/front/c/c/ccff7382-8609-494c-aeee-cd1436456dd0.jpg?1785497117" width="230" alt="Goblin-town Flunkies"><br>[Goblin-town Flunkies](https://scryfall.com/card/hob/100/goblin-town-flunkies) | c | **C+ / C−** | C+ when you can use the goblins, C/C− when you can't. |
| <img src="https://cards.scryfall.io/normal/front/7/b/7bf81a8b-52ad-49f5-a3d4-22613cad3a3d.jpg?1785497128" width="230" alt="Ragged Short Spear"><br>[Ragged Short Spear](https://scryfall.com/card/hob/108/ragged-short-spear) | c | **C** | Tormenting Voice stapled to an equipment. Storied enabler. |
| <img src="https://cards.scryfall.io/normal/front/9/9/9984b9ef-e81c-48f4-aa33-0504171a2d3c.jpg?1785496200" width="230" alt="Óin the Brave"><br>[Óin the Brave](https://scryfall.com/card/hob/106/%C3%B3in-the-brave) | c | **C** | 1/3 legend with storied + rummage. "Would have been a rare a decade ago." |
| <img src="https://cards.scryfall.io/normal/front/b/c/bc4a60b8-a5bb-4dbf-8d48-95caf757eac3.jpg?1785497118" width="230" alt="Gundabad Opportunist"><br>[Gundabad Opportunist](https://scryfall.com/card/hob/101/gundabad-opportunist) | c | **C** | Four-mana 4/2 that exiles-to-play the top card. A two-for-one served to cheap removal. |
| <img src="https://cards.scryfall.io/normal/front/f/c/fceb1a2d-121e-49ad-acf2-1bb5aebec116.jpg?1784376970" width="230" alt="Burn, Burn, Tree and Fern"><br>[Burn, Burn, Tree and Fern](https://scryfall.com/card/hob/90/burn-burn-tree-and-fern) | u | **C** | Saga: 6 damage → destroy artifact → {R} → {R}. Four-mana sorcery-speed kill, frontloaded. |
| <img src="https://cards.scryfall.io/normal/front/4/1/419ca9e5-8413-4378-a4ef-eda5a1024218.jpg?1785497136" width="230" alt="Smaug, the Great Calamity // Spew Flame"><br>[Smaug, the Great Calamity // Spew Flame](https://scryfall.com/card/hob/109/smaug-the-great-calamity-spew-flame) | c | **C** | Seven-mana 5/5 flying legendary dragon **at common**, with a 5-mana "deal 5." Dies to The Black Arrow; the mythic Smaug does not. |
| <img src="https://cards.scryfall.io/normal/front/b/d/bd0f0415-43af-4f5d-8999-853c5d42780d.jpg?1784895019" width="230" alt="Dwarven Mauler"><br>[Dwarven Mauler](https://scryfall.com/card/hob/95/dwarven-mauler) | u | **C−** | One-mana 2/1 that reduces equip costs by 2. Play it if you want a 1-mana 2/1 dwarf. |
| <img src="https://cards.scryfall.io/normal/front/a/1/a16f203a-785e-4c78-9410-fb9f8a0ffa01.jpg?1785497138" width="230" alt="Smaug's Fury"><br>[Smaug's Fury](https://scryfall.com/card/hob/111/smaugs-fury) | c | **D+** | +3/+0, reach and first strike. Generic pump with no payoffs behind it. |
| <img src="https://cards.scryfall.io/normal/front/4/6/46daa9ac-0ac7-4df9-b9d2-e03ab5b56c72.jpg?1785497126" width="230" alt="Iron Hills Stalwart"><br>[Iron Hills Stalwart](https://scryfall.com/card/hob/102/iron-hills-stalwart) | c | **D** | Five-mana 4/5 reach trample that reattaches an equipment. "Not interested." |

### Green

| Card | R | Grade | Note |
|---|---|---|---|
| <img src="https://cards.scryfall.io/normal/front/e/0/e0c0f842-40fe-4776-a988-a35216bcfd47.jpg?1785236709" width="230" alt="Old Fat Spider"><br>[Old Fat Spider](https://scryfall.com/card/hob/132/old-fat-spider) | u | **B** | Six-mana 6/7 reach, unblockable by power ≤2, draws when targeted. "What I want to spend six mana on." |
| <img src="https://cards.scryfall.io/normal/front/9/6/96bc7d25-2828-478a-8fe5-a1f4ede8c9c0.jpg?1785324620" width="230" alt="Nasty Little Rabbit"><br>[Nasty Little Rabbit](https://scryfall.com/card/hob/130/nasty-little-rabbit) | u | **B** | One-mana 1/2 that grows every combat with ferocious on. |
| <img src="https://cards.scryfall.io/normal/front/c/a/ca0f7bf4-b8a2-4ec4-ad7e-b639de9fa76a.jpg?1785496323" width="230" alt="Troll Negotiations"><br>[Troll Negotiations](https://scryfall.com/card/hob/138/troll-negotiations) | u | **B** | Two counters then fight. Swingy, but decides games when it resolves. |
| <img src="https://cards.scryfall.io/normal/front/2/4/2476e42b-b209-4207-8ed9-cb668f89b218.jpg?1783902784" width="230" alt="Wood Elves"><br>[Wood Elves](https://scryfall.com/card/hob/142/wood-elves) | c | **B / C+** | Unresolved split. 3-mana 1/1 that fetches an *untapped* Forest. Forest-only hurts; LSV suspects nostalgia. |
| <img src="https://cards.scryfall.io/normal/front/f/e/fe2b4bcf-56de-44d3-83af-aeb27f82c25e.jpg?1785237990" width="230" alt="Woodland Weavemaster"><br>[Woodland Weavemaster](https://scryfall.com/card/hob/143/woodland-weavemaster) | u | **build-around B** | Elf mana that only casts elf spells. Best card in a real Elves deck, unplayable outside it. |
| <img src="https://cards.scryfall.io/normal/front/5/9/5900a0b4-aa89-4019-94c9-7e9ea3b4792e.jpg?1785496166" width="230" alt="Quarrel"><br>[Quarrel](https://scryfall.com/card/hob/135/quarrel) | c | **C+** | Instant-speed bite. Reliable when green creatures are big. |
| <img src="https://cards.scryfall.io/normal/front/8/1/81263d5d-e402-4813-9458-161112da27ab.jpg?1785497157" width="230" alt="Attercop"><br>[Attercop](https://scryfall.com/card/hob/116/attercop) | c | **C/C+** | Two-mana 2/1 reach deathtouch with a small landfall pump. Kills any flier. |
| <img src="https://cards.scryfall.io/normal/front/1/c/1ccbf823-846f-4f09-9c67-1deebb5d1d92.jpg?1785497175" width="230" alt="Wargling"><br>[Wargling](https://scryfall.com/card/hob/140/wargling) | c | **C** | Two-mana 2/2 that gives your team trample on a ferocious attack. Rich-get-richer. |
| <img src="https://cards.scryfall.io/normal/front/b/0/b06d9cee-bb0f-4fe7-ab2a-b55d36461aec.jpg?1785497168" width="230" alt="Warg Tactics"><br>[Warg Tactics](https://scryfall.com/card/hob/139/warg-tactics) | c | **C** | Destroy a flier, **or** +1/+1 with trample and hexproof. Maindeckable despite the sideboard half. |
| <img src="https://cards.scryfall.io/normal/front/5/0/50fbedc0-bc66-4ffb-87f6-a2df69995091.jpg?1785152431" width="230" alt="Mirkwood Pathmaker"><br>[Mirkwood Pathmaker](https://scryfall.com/card/hob/129/mirkwood-pathmaker) | u | **C/C−** | */* equal to lands. Keeps up, never exciting. ⚠ CGB rates this **B** — see conflicts. |
| <img src="https://cards.scryfall.io/normal/front/9/8/985bd676-58c4-42c7-a570-1b413e9aa94c.jpg?1785152142" width="230" alt="Galion, Elvenking's Butler"><br>[Galion, Elvenking's Butler](https://scryfall.com/card/hob/125/galion-elvenkings-butler) | u | **C** | 4/4 that copies its stats onto another attacker. Narrower than it reads. |
| <img src="https://cards.scryfall.io/normal/front/0/f/0feb9817-56e1-465a-851c-b2fe202aa8ae.jpg?1785323277" width="230" alt="Ordinary Bear"><br>[Ordinary Bear](https://scryfall.com/card/hob/133/ordinary-bear) | c | **C/C−** | Four-mana 4/5 **vanilla** — the set's throwback. |
| <img src="https://cards.scryfall.io/normal/front/7/1/71bec005-2925-4944-be16-2cc5eb30f5d6.jpg?1785497158" width="230" alt="Boughside Wanderers"><br>[Boughside Wanderers](https://scryfall.com/card/hob/121/boughside-wanderers) | c | **C** | Six-mana 4/4 that digs 4 for a permanent, +2/+2 on landfall. The common ramp target. |
| <img src="https://cards.scryfall.io/normal/front/4/2/4265caec-8c28-44cd-8e6b-90b5af926d3c.jpg?1785497166" width="230" alt="Guardian of the Halls"><br>[Guardian of the Halls](https://scryfall.com/card/hob/127/guardian-of-the-halls) | c | **C/C−** | Two-mana 2/2 trample with a repeatable 7-mana pump. A ramp-deck two-drop. |
| <img src="https://cards.scryfall.io/normal/front/1/5/153ca57e-30f0-4ad7-ae9d-c55cbf0fd4c9.jpg?1785152153" width="230" alt="Beorn's Hospitality"><br>[Beorn's Hospitality](https://scryfall.com/card/hob/120/beorns-hospitality) | u | **C−** | Landfall counters; 7 mana to become a land-sized creature. LR skeptical. |
| <img src="https://cards.scryfall.io/normal/front/8/0/804589b7-3ef9-473d-97cc-c61a2d41f70d.jpg?1785323267" width="230" alt="Beorn, Reluctant Host // Till and Tend"><br>[Beorn, Reluctant Host // Till and Tend](https://scryfall.com/card/hob/118/beorn-reluctant-host-till-and-tend) | c | **C−/D+** | Five-mana 5/5 trample + an extra land drop that doesn't fetch. Weakest version of that effect. |
| <img src="https://cards.scryfall.io/normal/front/6/3/63078f42-f404-4c61-86be-45d934393b0a.jpg?1785236564" width="230" alt="Wilderland Scrounger"><br>[Wilderland Scrounger](https://scryfall.com/card/hob/141/wilderland-scrounger) | u | **C+ / D+** | Biggest disagreement of the episode. 3/6 that counters your whole team on a ferocious attack. LSV: "not where you want to put your mana." |
| <img src="https://cards.scryfall.io/normal/front/8/a/8a50858a-33b5-4c45-9c31-5956ae5a33a6.jpg?1785323276" width="230" alt="Little Bear"><br>[Little Bear](https://scryfall.com/card/hob/128/little-bear) | c | **D** | Three-mana 3/2 flash that untaps a creature; not enough bears in the set. |

### Artifacts, colorless and lands

| Card | R | Grade | Note |
|---|---|---|---|
| <img src="https://cards.scryfall.io/normal/front/a/d/ad0dba36-d056-4bc1-987a-391da26ad267.jpg?1785458557" width="230" alt="Thrór's Map"><br>[Thrór's Map](https://scryfall.com/card/hob/179/thr%C3%B3rs-map) | u | **B+ / B** | Fetch a basic to hand, then `{2},{T}: loot`. **Play it in ~80% of decks** — only very aggressive decks skip it. |
| <img src="https://cards.scryfall.io/normal/front/0/b/0b4b1c59-bcec-4779-9e27-0e6f9feb4e11.jpg?1785639568" width="230" alt="Troop of Ponies"><br>[Troop of Ponies](https://scryfall.com/card/hob/3/troop-of-ponies) | u | **B** | Two-mana colorless 2/1 that sacs for two basics (one onto the battlefield). Goes anywhere. |
| <img src="https://cards.scryfall.io/normal/front/a/b/ab181190-d53d-4972-8cd5-8e54b45f2276.jpg?1785496386" width="230" alt="The Black Arrow"><br>[The Black Arrow](https://scryfall.com/card/hob/171/the-black-arrow) | u | **B−** | Flash equipment: 1 damage to any target, **destroys a dragon outright**, then +1/+1 and reach for 1. "Mostly a C+, an A when they have a dragon." |
| <img src="https://cards.scryfall.io/normal/front/0/3/0365c439-30bf-4d32-a791-166751bdb996.jpg?1785323332" width="230" alt="Hobbit Hole"><br>[Hobbit Hole](https://scryfall.com/card/hob/184/hobbit-hole) | c | **C+** | Sac to fetch a basic; halflingcycling 4 finds one of nine halflings. Free inclusion. |
| Common dual cycle — [Lake-town](https://scryfall.com/card/hob/186/lake-town) (WU) · [Goblin-town](https://scryfall.com/card/hob/183/goblin-town) (BR) · [Mirkwood](https://scryfall.com/card/hob/188/mirkwood) (BG) · [Iron Hills](https://scryfall.com/card/hob/185/iron-hills) (RW) · [Elvenking's Halls](https://scryfall.com/card/hob/182/elvenkings-halls) (GU) | c | **C/C+** | Enter tapped; sac for two +1/+1 counters on the pair's tribe. |
| <img src="https://cards.scryfall.io/normal/front/d/1/d1a1e520-1fe2-4529-8afb-c187bb80da3c.jpg?1785639260" width="230" alt="Long-Bodied Grey Dog"><br>[Long-Bodied Grey Dog](https://scryfall.com/card/hob/1/long-bodied-grey-dog) | c | **C** | Three-mana 2/2 flash reach that makes a Treasure. |
| <img src="https://cards.scryfall.io/normal/front/9/2/92c6f09d-b525-4e8c-a87c-a74df9dc3b1e.jpg?1785412768" width="230" alt="Dwarven Mattock"><br>[Dwarven Mattock](https://scryfall.com/card/hob/172/dwarven-mattock) | u | **B in Dwarves / D outside** | Auto-attaches to a dwarf; +2/+2 and ward 1. Equip 3 for everyone else is too slow. |
| <img src="https://cards.scryfall.io/normal/front/c/e/ce254758-c928-4b43-a952-13fac1845668.jpg?1785497186" width="230" alt="Giant's Boulder"><br>[Giant's Boulder](https://scryfall.com/card/hob/173/giants-boulder) | c | **D** | Scry 2, mana filter, 7-mana sac-to-destroy. Fringe; counts for storied. |
| <img src="https://cards.scryfall.io/normal/front/6/5/659b687f-4068-496f-81b2-7b606bf07ec1.jpg?1785496409" width="230" alt="Well-Worn Spatula"><br>[Well-Worn Spatula](https://scryfall.com/card/hob/180/well-worn-spatula) | c | **D** | Gain 2, +1/+1, equip 1. Only if you need an artifact or a 4-power enabler. |
| <img src="https://cards.scryfall.io/normal/front/3/a/3ad02b56-13ec-46ef-92bd-ae078b8bb517.jpg?1785639558" width="230" alt="Old Thrush"><br>[Old Thrush](https://scryfall.com/card/hob/2/old-thrush) | c | **D** | Two-mana 1/2 flier, gain 2, tutor a basic **to the top**. Bad fixing as a trap. |
| <img src="https://cards.scryfall.io/normal/front/8/9/898c14a2-d897-4341-83ed-eee666df9648.jpg?1785412757" width="230" alt="Key to the Side-Door"><br>[Key to the Side-Door](https://scryfall.com/card/hob/175/key-to-the-side-door) | u | **F** | Unblockable activation, or discard a redundant legend to draw two. |

---

## The prerelease kit itself

From OzMTG's on-camera kit opening (2026-08-05). Practical, and none of it is in the written guides.

**What's in the box:** 6 play boosters · a spindown die · a **land pack** · a **date-stamped foil promo rare**.

- **The promo and the land-pack basics are both legal in your deck.** People ask every event; the answer is yes on both. Add the promo to the pile before you build, not after.
- **The kit does not tell you the archetypes.** OzMTG had to crack a separate play booster to find them printed. Know the five pairs before you sit down — nothing in the box will tell you.
- **The die is nothing special** — the five ordinary colours with the set symbol on it. No special face.
- **The land pack is the thing to keep.** Seasonal-art basics (spring, summer, autumn, winter), and OzMTG believes the four-season treatment is **Plains only**. In **non-foil these exist only in prerelease kits** — the bundle version is foil and the gift bundle is surge foil. If you want the non-foil seasonals for a Commander deck you need roughly 20–25, which is a lot of kits.
- **Kit supply was limited**, at least in Australia. Pre-order rather than walking in.

**Their format read, which is a genuinely different emphasis from the other sources:**

- **Commit to a tribe or lose.** *"If you don't build a tribe, you're going to be screwed, because anyone who builds tribes is going to get synergies."* Stronger than LR's or LLU's framing, and worth weighing since it's the only read here based on looking at a real 6-pack pool rather than a spoiler list.
- **But no more than two tribes.** B/G can support elves *and* wolves; a third dilutes both past the point where synergy pays.
- **The colours line up cleanly.** No three-colour cards appeared in the pool, and the archetype colours map exactly onto the tribes — the set isn't trying to pull you off your lane. *"Very easy colours to get into."*
- **The curve is low.** *"They are quite low mana costed... realistically you want to focus on two or three mana. That's going to be your bread and butter."* Matches the guide's advice to prioritise the 2–3 slot.
- Their build landed on **B/G wolves** off Radagast of Rhosgobel plus The Chief Warg, Large Bear, Head of the Hunt and black removal — three two-drops, two three-mana removal spells, a high top end.

## Sealed: building your 40

**Targets**

| Slot | Count | Adjust |
|---|---|---|
| Lands | **17** | 18 for G/U ramp or a curve topping at 6+; 16 only for genuine aggro capping at four |
| Creatures | **15–17** | Sub-50% decks are chronically creature-light |
| Removal / interaction | **6–8** | |
| Curve | ~5 twos · 5 threes · 4 fours · 3–4 at five-plus | Prioritize the 2–3 slot |

**Build order**

1. Sort by color, rares and gold face-up. Two minutes, read nothing yet.
2. Find your bombs *and* your removal. Both piles pick your colors. A bomb you can't cast doesn't count.
3. Pick the two **deepest** colors, not the two most exciting. Ten playables beats three playables and a mythic.
4. Lay out the curve before you cut.
5. Land on 17/16/7. Go to 18 lands only for ramp or a top-heavy curve.
6. **Cut every card that's only good if the theme is on.** Storied payoffs with two enablers, ferocious payoffs with three 4-power creatures, amass payoffs with one amass card. These lose games quietly.
7. Splash only for a bomb, only off a Treasure maker or fixer. A third color for a removal spell is not worth it.

**Sealed-specific card notes:** [Sound the Trumpets](https://scryfall.com/card/hob/55/sound-the-trumpets) goes from D+ to C+ · [Master's Councillors](https://scryfall.com/card/hob/47/masters-councillors) can be excellent · reactive cards generally gain value because games run longer.

## Trios / Team Sealed

"Trios" is **not** an official Wizards prerelease format — it's a store variant, and stores run it two ways. Variant B is three separate Sealed decks with no card sharing, in which case the ordinary Sealed advice above applies unchanged and you can skip this section.

**This section assumes variant A: shared pool, 18 boosters** — three prerelease kits into one pile, three 40-card decks built collectively. Cards move freely during building, then lock to their pilot. 1v1 against the opposing seat; first team to two match wins.

**18 packs is the good version of this format.** Official Team Sealed is 12 boosters; three kits gives you 18, so roughly six extra rares. Expect **4–8 genuine bombs** — enough that all three seats can have a real reason to win rather than one seat being knowingly sacrificed. Plan to give every deck a threat, not to stack one super-deck.

**You also get three foil promos and three land packs.** Both are legal to play (see [The prerelease kit itself](#the-prerelease-kit-itself)) — that's three extra rare-or-better cards in the shared pool that people routinely forget to add to the pile.

### The color-overlap math is forced, so choose which color you double

Three two-colour decks consume **six colour slots across five colours**, so at least one colour is played twice. HOB's five archetypes form a closed ring — W/U → U/G → G/B → B/R → R/W → W/U — and each colour appears in exactly two of them. Consequence: pick any three archetypes and you **cannot** avoid overlap. You only get to choose its shape.

| Shape | Example | Colours doubled |
|---|---|---|
| Two adjacent + one disjoint | B/R + B/G + W/U | **one** (black) |
| Three in a row | R/W + B/R + B/G | **two** (red and black), one colour unused (blue) |

**Recommended: B/R + B/G + W/U.** It is the only configuration that doubles the deepest colour, uses all five colours, and **never builds G/U** — the archetype both LLU reviewers rank last. Black is the right colour to double because black has five or six commons you're happy to play, so two seats can share it without either going hungry.

**Runner-up: R/W + B/R + B/G**, which dumps blue entirely and doubles both of the two deepest colours. Take this when your white rares are thin — see below — since it's the configuration that gets three aggressive decks out of one pool.

**Avoid any configuration containing G/U** unless the pool forces it (a G/U bomb rare, or genuinely nothing else). It is short on playable two-drops, its payoffs are unexciting, and its failure mode — drawing cards and making small bodies without ever turning the corner — is exactly the deck that loses long Sealed games.

### White is a dedicated seat, never a shared one

This is the HOB-specific trap. **White has the worst commons in the set and the best rares** — all three of both LLU reviewers' top rares are white, plus Kíli the Resourceful just below. White also has exactly **one** removal common ([Magnificent End](https://scryfall.com/card/hob/20/magnificent-end)), though its uncommon removal ([Celebrate the Mountain-king](https://scryfall.com/card/hob/7/celebrate-the-mountain-king), [Stone by Sunlight](https://scryfall.com/card/hob/27/stone-by-sunlight)) is excellent.

So: count your white rares first, before you assign anything.

- **Two or more white bombs** → build a white seat and give it *every* white card in the pool. Splitting white across two decks gives you two mediocre decks instead of one real one.
- **Zero or one** → skip white as a main colour and take the R/W + B/R + B/G configuration.

The white seat will be **removal-starved by construction**. Feed it black and red removal even at the cost of the other two decks — this is the concrete direction for the "split removal unevenly" rule.

### Build choreography (shared pool)

The whole design is that **only two phases are synchronous**; everything else runs three-wide. Teams that build as a committee — three people discussing one deck at a time — run out of clock.

**Budget for reading, and put it in the right place.** Eighteen play boosters is roughly **220 playable cards nobody at the table has seen before.** You cannot read all of them, and you shouldn't try. The structural fix is that **reading happens *after* pilot assignment, not during the sort** — once you know you're on B/G, you read black and green and skip the other three colours entirely. That cuts each player's reading load to about two fifths of the pool, in parallel, and every card they read is one they might actually play.

This is why the sort phase below is deliberately mechanical and silent. The person sorting white isn't necessarily the person playing it, so reading during the sort puts the knowledge in the wrong head.

Total ~75 minutes, including the open, the photo pass and the reading. Confirm your actual limit with the store — team builds usually get 45–60 rather than the 30 for individual Sealed. **If your clock is under 70, the reading does not get cut** (see the triage note after the timeline).

**Assign three roles before you open a single pack.** This is what separates a 45-minute build from a 90-minute one.

| Role | Who | Owns |
|---|---|---|
| **Decider** | Most Limited reps | Breaks every tie, immediately. Arguments end when they speak |
| **Clock** | Anyone | Calls each phase boundary out loud |
| **Scribe** | Anyone | The three-column sheet: config, pilots, then the contested list |

The Decider matters most. Three people with equal authority over one pool argue until the round starts. Name them out loud and agree the call is final even when you disagree — being overruled is cheaper than debating.

| Time | Phase | Mode |
|---|---|---|
| 0–4 | Open your own six packs | **Parallel** |
| 4–9 | **Photograph each pull, separately** | **Parallel** |
| 9–11 | Merge into one pool + stage the table | Together |
| 11–19 | Sort — mechanical, silent, **no reading** | **Parallel** |
| 19–24 | Bomb census + lock the config and pilots | Together |
| 24–38 | **Read your two colours** | **Parallel** |
| 38–58 | Build the three 40s | **Parallel** |
| 58–66 | Resolve contested cards | Together |
| 66–76 | Lands, sleeve, cross-check | **Parallel** |

**If your clock is shorter than 75 minutes**, cut in this order and never higher up the list: the neighbour cross-check to 1 minute · the contested pass to a single round with no debate · the build phase (you'll play more filler). **Do not cut the reading.** A deck built from cards nobody understood is worse than a deck built in a hurry from cards you did — and misreading a card at the table during round one costs a game outright.

**0–4 · Open your own six packs.** Each player opens their own kit into their own space. Don't merge yet. Land packs aside — basics are free and don't count.

**4–9 · Photograph each pull, separately.** This is the step with a hard ordering constraint: **photograph before you merge, and photograph each player's six packs as its own picture.** A photo of the combined pool cannot tell you who opened what, so it's worthless for splitting the cards back afterward. Merge first and the information is gone for good.

- Lay your six packs out in a grid, cards fanned so every name is readable. Two or three shots per player beats one crowded one.
- **Include your foil promo in your own photo** — it's date-stamped and non-fungible, and it should end the night back with you.
- Shoot in decent light and check the photo is legible *before* you sweep the cards together. A blurry photo you can't read is the same as no photo.
- Everyone keeps their own shots; send them to a group thread so there's one shared record.

**9–11 · Merge and stage.** Now combine. Clear the table into **three columns plus a wide strip across the top** — the strip is the shared pool, the columns are the decks. **Put the foil promos into the pool** — they're legal and they're rares, and your photo already records whose is whose.

**11–19 · Sort, in parallel — mechanical and silent.** Split the colours so nobody waits: player 1 takes white + blue, player 2 black + red, player 3 green + multicolour + colourless + lands. Within your colours sort **by mana value ascending**, rares and gold face-up. Sort by colour, **not** by tribe — OzMTG worked through exactly this decision on camera and landed on colour, because colour is what shows you where the depth is: *"then I can sort of see what I've got the most of."* Tribes are the second pass, once colour has narrowed it to two or three lanes. **Nobody evaluates cards yet** — talking about cards here is what turns seven minutes into twenty.

**19–24 · Census, then lock.** All three at the top strip. Five minutes, and it decides the whole build.

1. **Count the white rares.** That single number picks between the two configurations above.
2. **Lock the configuration.** Lay the chosen three archetypes out as the three columns.
3. **Assign pilots** — this must happen here, because the next phase is each pilot reading their own colours. Assign by hardest-to-misplay (see the table below), and give the third player the leftovers as the **grindy** deck: most removal, highest curve, least synergy dependence.
4. **Scribe writes all of it down** — config, pilots, columns.

Then stop. **Do not revisit the configuration after this point**, even if someone finds a great card in an unused colour. Reopening the config at minute 30 is how teams submit two decks and a pile.

**24–38 · Read your two colours.** Fourteen minutes, parallel, silent. Take your two colours off the top strip and physically read them — roughly 80–90 cards each, about ten seconds a card. **Do not read the other three colours at all.** Read colourless and your pair's gold/hybrid cards too; they're short.

- **Sort into three piles as you read: yes / maybe / no.** Don't rank within the piles yet — that's the build phase. You're only converting "unknown card" into "card I understand."
- **Adventures and modal cards take three times as long.** HOB has a lot of both. Read those first while you're fresh; they're also the ones most likely to be misplayed later.
- **Use your phone for anything ambiguous** rather than debating it. Open your pair's full card list on Scryfall and set the view to Images — it's every card castable in your two colours, colourless and hybrid included, and nothing else:

  | Pilot | Cards | | Pilot | Cards |
  |---|---|---|---|---|
  | **B/R** | [78](https://scryfall.com/search?q=set%3Ahob+ci%3C%3Dbr+-type%3Abasic) | | **W/U** | [77](https://scryfall.com/search?q=set%3Ahob+ci%3C%3Dwu+-type%3Abasic) |
  | **B/G** | [75](https://scryfall.com/search?q=set%3Ahob+ci%3C%3Dbg+-type%3Abasic) | | **R/W** | [78](https://scryfall.com/search?q=set%3Ahob+ci%3C%3Drw+-type%3Abasic) |
  | **G/U** | [75](https://scryfall.com/search?q=set%3Ahob+ci%3C%3Dgu+-type%3Abasic) | | | |
- **Say the weird ones out loud** to the table — one sentence, not a discussion. "Storied is permanent once you get it." "Amass stacks on one token." Thirty seconds of shared vocabulary saves arguments in the contested pass.
- **Read the rares last, not first.** You'll have already seen the ones that matter during the census, and the temptation to re-litigate the config while holding a shiny off-colour rare is exactly the failure mode below.

**38–58 · Build three decks at once.** Each player takes their column and builds their own 40 from their yes/maybe piles, pulling anything else from the top strip.

- **The constrained deck picks first.** Whoever is on the shallowest colours goes first, because they have the fewest options. The deck on the deepest colours has slack and absorbs what's left. Letting the strongest deck pick first starves the seat that was already going to be weakest.
- **When two decks want the same card, don't fight — put it in a contested zone** in the middle of the table and keep building. Build assuming you *don't* get it. You're establishing each deck's floor; contested cards are upside, resolved in one pass later.
- Everyone targets 17 lands · 15–17 creatures · 6–8 removal · ~5 twos, 5 threes, 4 fours, 3–4 at five-plus.

**58–66 · Resolve the contested zone.** One pass, all three, Decider breaks ties. One rule governs it:

> **A contested card goes to the deck with the worse alternative, not the deck that uses it better.**

Counterintuitive and load-bearing. If Bilbo's Deadly Slice is the B/R deck's 7th-best removal spell and the W/U deck's 2nd-best, it goes to W/U — even though B/R is the better removal deck. You are not maximising any single deck. **You need two match wins**, so you are raising the floor of the worst one. The same logic drives the removal split: push interaction toward the weakest seat, since the aggro deck survives on four and the leftovers deck doesn't.

**66–76 · Lands, sleeve, cross-check.** Parallel. Whoever finishes first starts sleeving for whoever's behind — nobody sits idle in the last ten minutes. Then the step almost every team skips: **hand your finished deck to a neighbour for a two-minute count.** Not a discussion, a count — lands, creatures, removal, eyeball the curve. You cannot see your own deck's holes after twenty minutes of staring; a fresh pair of eyes spots a 13-creature deck in fifteen seconds. Keep the leftover pool in its own container sorted by colour; it's your sideboard. Confirm with the store whether cards may move between decks between games — rules vary.

### Three ways this goes wrong

1. **The committee.** Three people building one deck at a time. The parallel phases above are the fix and they're non-negotiable.
2. **The reopen.** Someone finds a bomb in an unused colour at minute 28 and the config gets relitigated. The Decider says no; it's a sideboard card now.
3. **The last-10% spiral.** Once a deck has its bomb, 6+ removal, 15–17 creatures and 17 lands it is **done** — physically slide it out of the middle of the table and move to the next seat. In a trio every extra optimisation pass costs three times what it does in solo Sealed.

### What is and isn't contested in this pool

| Card class | Contested? | Handling |
|---|---|---|
| **Removal** | Heavily — it's concentrated in black and red | Allocate deliberately, weakest deck first |
| **Anthems** | Yes, between the two go-wide seats | HOB has almost no sweepers, so anthems are unusually good. [An Unexpected Party](https://scryfall.com/card/hob/29/an-unexpected-party-at-the-door), [The Arkenstone](https://scryfall.com/card/hob/170/the-arkenstone-seek-the-heart), Dwarven Provisioner, Thorin's Last Stand, Moment of Glory. Resolve early, don't leave it to the end |
| **Equipment** | Only if you built R/W | Nobody else needs artifacts; storied is an R/W-only concern |
| [Duskwatch Hunter](https://scryfall.com/card/hob/153/duskwatch-hunter) | No — only B/G wants it | Give the B/G seat all of them. It's the only cheap four-power common, so it's the single most important ferocious enabler you have |
| **Dual lands / fixing** | Barely | The cycle is pair-specific, so each land goes to exactly one seat. HOB has lots of fixing and very little worth splashing for |
| **Legends** | No | Despite the density, near-duplicates have different names — the three Bilbos, three Gollums, two Thranduils, two Bards, two Beorns and three Smaugs are all distinct cards. No legend-rule conflicts within a deck |

### Assign decks by "hardest to misplay," not "best deck to best player"

You need 2 of 3 wins, so what loses matches is one player getting a deck they can't pilot.

| Pilot profile | Give them | Why |
|---|---|---|
| Limited novice | **B/G Wolves**, then **R/W Dwarves** | Curve out, attack, point removal at blockers. B/G first: fewest in-combat decisions to get wrong |
| Experienced but rusty | **the grindy / leftovers deck** (often W/U recruit) | Recruit rewards knowing what to discard |
| Most current reps | **the bomb deck** | |

**Never give B/R Goblins to the novice**, even though it's the strongest pair. Amass is the most removal-vulnerable board state in the format — one removal spell erases every counter you've invested — and knowing when to sacrifice the Army for value instead of growing it is a learned skill. Give B/R to whoever has the most recent reps.

### This team, specifically

Two teammates with opposite failure modes. Neither is a weak player; both are strong at something the other isn't, and the assignments below are built around that rather than around a skill ranking.

#### Andy — Mythic in Constructed on one deck (mono-green landfall), new to Limited

**Read the Mythic carefully: it's Mythic with a single linear deck, not Mythic across a format.** Climbing with mono-green landfall is real — it takes reps and discipline — but it is close to the **least transferable** Constructed experience for Limited. On that deck he has never built a deck, never made a mana-base decision, never mulliganed on colours, and never held up interaction. Treat the experience as **narrow and deep**, not broad.

**What genuinely transfers:**

- A **proactive creature plan.** He's comfortable playing to the board, attacking, and winning through one large trampling threat. That is exactly what B/G and R/W want to do.
- **Landfall as a concept** — he'll read G/U faster than anyone at the table.
- **Sequencing land drops** and playing around his own curve.

**What doesn't transfer, and matters:**

- **Using removal.** Mono-green plays almost none. In Limited, knowing *when to hold* removal and what to point it at is a top-three skill and he has no reps at it. Expect him to fire it at the first creature he sees.
- **Blocking.** Landfall decks race; they rarely block well. Limited games are decided on the ground.
- **Instant-speed play.** He's used to sorcery-speed pump; holding up mana won't be instinctive.
- **Pricing unfamiliar cards.** A fixed 60-card list never asked him to evaluate a card he'd never seen.

So "he'll build badly but pilot fine" is **half right at best** — there's a build gap *and* an interaction gap. **Don't let him build alone, and say the removal-and-blocking part out loud before round one rather than assuming it.**

The specific reflexes to head off at deckbuild:

| Reflex | Why it's wrong here | The rule |
|---|---|---|
| Cutting creatures for spells | Constructed wins with few threats and lots of interaction. Limited is a creature-combat format | **15–17 creatures. Not negotiable** |
| "This 6-drop is the most powerful card" | Card quality loses to curve in Limited | ~5 twos, 5 threes, 4 fours, 3–4 at five-plus |
| Wanting 16 lands | Constructed runs 24/60 = 40%; Limited wants 42%+ | **17 lands** |
| Dismissing vanilla creatures | [Ordinary Bear](https://scryfall.com/card/hob/133/ordinary-bear) is a literal French-vanilla 4/5 and it's a real playable — five toughness blocks the format and four power turns on ferocious | Bodies are cards here |
| Mulliganing to find the good draw | Limited is lower-power; every card lost hurts more | Keep 2–5 lands. Rarely mulligan |
| Over-respecting the unknown | You play around tricks you know exist; in a brand-new set nobody knows | Ask "does a long game favour me?" first |

**Give him B/G Wolves specifically**, not "R/W or B/G." Ferocious is the closest thing in HOB to the deck he already knows: keep a big creature on board, attack, win through size. R/W is the more decision-dense lane — equip timing, when to move equipment between creatures — and that's the kind of decision density he has the least practice with. **Do not give him B/R Goblins**; amass sequencing is the single hardest thing in the format.

**Two things to tell him before round one, because his deck never taught them:**

1. *"Don't spend removal on the first creature you see."* In a format this creature-dense, the removal spell you held is usually better than the one you cast on turn three.
2. *"You're allowed to block."* Racing is his default. Sealed games go long and are decided on the ground.

**One sentence to say to him at the census:** *"Build it like a creature deck that happens to have removal, not a removal deck that happens to have creatures."*

#### Kyle — the analytical one

Opposite risk: not that he'll misvalue cards, but that he'll try to **solve the pool instead of building a deck**, and the clock is the resource that actually runs out. Three specific traps, all of which HOB makes worse:

- **The greedy manabase.** HOB has a lot of fixing — [8 nonbasic lands](https://scryfall.com/search?q=set%3Ahob+type%3Aland+-type%3Abasic) plus Treasure makers and Thrór's Map — and a good manabase argument can be constructed for almost any splash. But the archetypes are on rails and there's very little worth splashing *for*. The math being sound doesn't make the splash correct.
- **Synergy that needs three pieces.** He'll spot the amass-sacrifice loop or the equipment engine and want to assemble it. That's exactly the "cut every card that's only good if the theme is on" trap, and it's worse in a three-way split where each deck gets a thinner slice of its own theme.
- **Re-solving after new information.** Every card read in the reading phase is a reason to reconsider the config. It isn't.

**Put his strength where it actually pays: give him the contested pass.** Allocating contested cards across three decks by *marginal* value — which deck has the worse alternative, not which uses it better — is a genuine optimization problem and he'll do it better than anyone. It's also naturally time-boxed at eight minutes.

**Give him the grindy / leftovers deck**, usually W/U recruit. It's the hardest of the three to build well and the one that most rewards squeezing value out of marginal cards, and recruit is a genuinely skill-testing mechanic — every trigger is a real "what do I discard" decision.

**Give him a hard stop, out loud.** *"Twenty minutes, then your deck is done."* An open-ended optimizer with no deadline is the single biggest clock risk on this team.

#### Suggested roles

| Role | Who | Why |
|---|---|---|
| **Decider** | Albert | Most Limited reps and the person holding this guide |
| **Scribe + contested pass** | Kyle | Marginal-value allocation is the one place analysis genuinely wins |
| **Clock** | Andy | Deliberately: it carries **zero card-evaluation load**, so it's the one job his Limited inexperience can't affect — and it puts the stop-times in the hands of the person least likely to want to keep optimizing |

That last one is the point of the arrangement. The novice enforcing the clock on the optimizer is a better team than either instinct left unchecked.

| Seat | Deck | Rationale |
|---|---|---|
| Andy | **B/G Wolves** | Ferocious is the nearest shape to mono-green landfall: big creature, attack, win through size |
| Kyle | **W/U recruit** / the leftovers deck | Most build-reward, most in-game decisions |
| Albert | **B/R Goblins** | Most removal-vulnerable, needs the most reps |

If the white-rare count pushes you to `R/W + B/R + B/G` and there's no W/U seat, Kyle takes **R/W** — equipment is the most decision-dense of the remaining lanes — and Andy keeps **B/G** either way.

### Talking during the match is the biggest edge in the format

In Team Limited, teammates sit together and **may confer freely during games**. Confirm your store honours this, then actually use it — most trios teams don't.

- **Seat your best player in the middle.** They can watch and advise both neighbours between their own turns.
- **Call out [Settle the Wreckage](https://scryfall.com/card/hob/26/settle-the-wreckage) the moment anyone sees it.** It's the only real sweeper in the format, the opposing team likely has one copy across three decks, and the whole point of knowing is attacking with four creatures instead of seven. LLU predicts this card will be one of the biggest skill-deltas on 17Lands — in trios you get to share that read across three matches at once.
- Same for the mini-sweepers: [Desolation of Smaug](https://scryfall.com/card/hob/93/desolation-of-smaug) (3 to all), Easy Pickings (Glóin's adventure, 1 damage to each of their creatures), and the −1/−1 mode on [Gnashing of Teeth](https://scryfall.com/card/hob/69/gnashing-of-teeth).
- **Ask before you commit to a race.** A teammate who is watching has a cleaner view of your board than you do.

### Build for floor, not ceiling

You need two match wins, not one blowout. Three decks with high floors beat one great deck and two greedy ones. Concretely:

- **No three-colour decks.** Not one of the three. HOB's fixing is plentiful but there's little worth splashing for, and the archetypes are on rails.
- **Splash only for a bomb**, only off a Treasure maker or real fixer, and only in one seat.
- **Cut every card that's only good if the theme is on** — storied payoffs with two enablers, ferocious payoffs with three four-power creatures, amass payoffs with one amass card. In a three-way split these dead-theme cards multiply, because each seat gets a thinner slice of its own theme than a solo Sealed deck would.
- **Ferocious needs 8–10 enablers** in a single deck (counting equipment and counters, not just naturally-large creatures). If the B/G seat can't get there after the split, build it as plain mid-range instead of chasing the aggro shell.
- Once a deck's core 40 is good — right bombs, enough removal, real creature count — **lock it and move to the next seat.** Extra passes introduce mistakes.

### Bring for a three-deck build

- ~51 basic lands (17 × 3) plus spares. Stores supply them, but a personal stack of 20 of each saves ten minutes.
- Sleeves for three decks, ideally in **three different colours** — this is how you keep track of whose card is whose when the decks come apart afterwards.
- Three deck boxes plus one for the shared leftover pool.
- Paper with three columns, one per player, to see the colour split at a glance.

## Playing the games

- **Play first.** In Limited, choosing to play is almost never wrong. Draw only if both decks are slow and grindy and neither can race.
- **Mulligan less than in Constructed.** Keep 2–5 lands. Rarely keep one-landers. Six-landers only with a defining bomb.
- **Sealed games go long** — decks are less consistent and more bomb-dependent than draft decks. Value cards that still do something on turn eight.
- **When ahead:** simplify. Trade creatures and resources; fewer total pieces magnifies your lead. Close off their outs even at slight cost.
- **When behind:** keep the board complex, preserve decision points, play to your outs.
- **Safe vs. scared:** hedging against a trick they may not have costs real games. First ask whether a long game favors you. If not, push.
- **Against amass:** save one unconditional removal spell rather than trading it for a 2/2. Playing it, don't over-invest counters while they have four mana open.

---

## Where the sources disagree

These are the places to trust the primary data over a written guide.

1. **Fíli the Pathfinder and Kíli the Resourceful are RARES, not uncommons.** Draftsim listed both as "8/10 uncommons that make Boros Dwarves real." Scryfall says rare. The archetype is not built on cards you'll reliably see — treat R/W as a good-cards deck.
2. **Card count: 193, not 183 or 321.** Draftsim said 183, Card Game Base 193, Gatherer 321. Scryfall's HOB Limited pool is **193**; the 321 figure counts special treatments and bonus printings.
3. **Three different Smaugs.** [Smaug the Magnificent](https://scryfall.com/card/hob/110/smaug-the-magnificent) (mythic, {2}{R}{R}, indestructible), [Smaug, Wicked Worm](https://scryfall.com/card/hob/164/smaug-wicked-worm) (rare, {3}{B}{R}), [Smaug, the Great Calamity](https://scryfall.com/card/hob/109/smaug-the-great-calamity-spew-flame) (**common**, {5}{R}{R} + adventure). Written sources conflate them. The Black Arrow kills the common but not the mythic.
4. **Thorin, Mountain-king is a MYTHIC {3}{R}**, not a red rare as CGB implies.
5. **Mirkwood Pathmaker:** CGB **B**, LR **C/C−**. LR watched the whole set in context; weight them.
6. **Gollum, Riddle Master** is a mythic both written sources call underwhelming. Do not first-pick it on rarity.
8. **OzMTG dissents (weakest tier — a casual pool crack, not a graded review, so treat these as minority reports):**
   - [Radagast of Rhosgobel](https://scryfall.com/card/hob/136/radagast-of-rhosgobel) is their pool's defining card and neither LR nor LLU ranked it. *"If you can get Radagast, then all these are basically one or two mana."* The cost reduction applies on **both** turns. Genuinely under-covered elsewhere — evaluate it yourself.
   - [Gollum the Abandoned](https://scryfall.com/card/hob/72/gollum-the-abandoned) — *"he's actually really good, I would definitely run him."* Two-mana 2/2 with graveyard hate, a drain, and self-recursion. Note the mirror: **their** Gollum can exile **your** Gollum out of your graveyard, and the recursion is sorcery-speed only.
   - [Thorin's Last Stand](https://scryfall.com/card/hob/28/thorins-last-stand) — *"pretty average."* Against LR's C and LLU's Mark, who nearly put it in his top three white commons for the instant-speed disenchant mode. **Trust the reviewers here** — OzMTG were reading it cold.
   - [Mirkwood Nurturer](https://scryfall.com/card/hob/160/mirkwood-nurturer) — *"that's pretty crappy, let's just put it to the side."* Directly against LLU's Mark, who had it as a top-three "other" common. This is the widest three-way split in the file.
   - [Dwarven Mauler](https://scryfall.com/card/hob/95/dwarven-mauler) — *"not the best for this"* (they rate it a Commander card). LLU talked themselves **up** on it. Both agree it needs 4–5 equipment, so the disagreement is really about whether you'll have them.
   - [Thranduil's Decree](https://scryfall.com/card/hob/56/thranduils-decree) — *"it's expensive, you're never going to play it."* LLU's Alex called it good blue top-end. Six mana in a format LLU reads as fast; lean toward OzMTG unless your deck is genuinely the slow one.
   - [Sound the Trumpets](https://scryfall.com/card/hob/55/sound-the-trumpets) — split within OzMTG itself, one on the recruit rider, the other on *"inefficiency built into a card."* LR's D+ draft / C+ Sealed split is the reconciliation.
9. **Ignore the AI-generated "prerelease guides"** ranking in search right now. One claims Red is the strongest Sealed color with R/B and R/G as the best pairs — R/G isn't one of the five archetypes. If a guide doesn't name recruit, storied, amass, ferocious and landfall, it hasn't seen the set.

## Before you leave the house

### The night before — 20 minutes, then sleep

**Read the commons. Not the whole set.** → **[all 65 HOB commons](https://scryfall.com/search?q=set%3Ahob+rarity%3Acommon+-type%3Abasic)** *(set the view to "Images" and swipe)*. Commons are the bulk of what you'll physically open, and they're the cards you have to evaluate fastest at the table. Every common you already know is ten seconds you don't spend in the reading phase.

If you only have five minutes, read the two colours you most expect to play:

| | Commons | | Commons |
|---|---|---|---|
| **White** | [12](https://scryfall.com/search?q=set%3Ahob+rarity%3Acommon+color%3Aw) | **Red** | [12](https://scryfall.com/search?q=set%3Ahob+rarity%3Acommon+color%3Ar) |
| **Blue** | [12](https://scryfall.com/search?q=set%3Ahob+rarity%3Acommon+color%3Au) | **Green** | [12](https://scryfall.com/search?q=set%3Ahob+rarity%3Acommon+color%3Ag) |
| **Black** | [12](https://scryfall.com/search?q=set%3Ahob+rarity%3Acommon+color%3Ab) | | |

*(Counts overlap — hybrid cards appear under both their colours. 65 distinct.)*

**Do not try to read all 193 cards.** You won't retain it, and the [68 rares and mythics](https://scryfall.com/search?q=set%3Ahob+rarity%3E%3Drare) are the ones you'll have time to read carefully at the table anyway.

**Worth two minutes each — the mechanics as card lists:** [17 adventures](https://scryfall.com/search?q=set%3Ahob+is%3Aadventure) (the slowest cards to read at the table, so front-load them) · [14 amass cards](https://scryfall.com/search?q=set%3Ahob+oracle%3Aamass) · [10 recruit cards](https://scryfall.com/search?q=set%3Ahob+oracle%3Arecruit) · [12 equipment](https://scryfall.com/search?q=set%3Ahob+type%3Aequipment) · [8 sagas](https://scryfall.com/search?q=set%3Ahob+type%3Asaga) · [8 nonbasic lands](https://scryfall.com/search?q=set%3Ahob+type%3Aland+-type%3Abasic).

**Send one message to your teammates.** The split rule is the only thing that genuinely cannot be fixed at the table, and settling it at 11pm costs two minutes:

> Split rule for after — photo-split back, snake draft, or builder-keeps? Everyone brings their own sleeves. We each keep our own foil promo regardless.

**Send the roles too**, so nobody negotiates them at the table: who is Decider, who is Clock, who is Scribe (see [Build choreography](#build-choreography-shared-pool)).

### Audio, if you want it in the car

**Limited Resources 865, minutes 0:00–14:36 only** — the mechanics chapter. Skip the remaining three hours; that's card grades you'll have in front of you anyway. Everything else in [Go deeper](#go-deeper-before-the-event) is reference material for the table, not listening.

### What to pack

- **Sleeves in three different colours**, 50+ each. This is how you unpick whose card is whose after the event — worth more than any single deckbuilding tip here.
- A deck box per player, plus a fourth container for the leftover pool (submitted decks lock; keep the sideboard organized).
- Dice or counters — amass and hone counters both stack up fast, across three simultaneous games.
- Basic lands, 20 of each. Stores supply them, but a personal stack saves ten minutes across three decks.
- A sheet of paper with **three columns**, one per player, for the config, pilots and contested list.
- A phone with Scryfall open, for the reading phase.

## Go deeper before the event

Ranked by how much it changes your prerelease.

| Source | Length | What you get |
|---|---|---|
| **Limited Resources 865** (Marshall + LSV) | 3h 20m | The gold standard, and already distilled into this file. Listen to the mechanics chapter (0:00–14:36) plus your two likely colors. |
| **Limited Level-Ups HOB primer** (Alex + Mark) | ~2h 30m across 5 videos | Archetypes, top commons/uncommons, **rares + mythics**, and a Sealed-specific prerelease guide. **Now distilled** → [`limited-level-ups/HOB.md`](../limited-level-ups/HOB.md). Two reviewers ranking blind then reconciling on air — the disagreements are the most useful part. |
| **[OzMTG, *The Hobbit Prerelease Kit Building*](https://www.youtube.com/watch?v=tuFQbNpulRg)** | 15m | The only source that opens an actual kit. Kit contents, what's legal to play, the seasonal Plains, and a real 6-pack pool built on camera. **Distilled into this file.** Weakest evidence tier — reading cards cold, not a graded review. |
| **Draftsim set review + pick order** | reference | Numeric 1–10 grades, searchable on your phone at the table. |
| **Card Game Base tier list + draft guide** | reference | Letter grades from a second reviewer. Disagreements with Draftsim mark the genuinely uncertain cards. |
| **17Lands** | — | Nothing until Arena release Aug 11 — four days *after* prerelease. The single best source the week after. |

## Sources

**Distilled (video):**
- 2026-08-04 — Limited Resources 865, *The Hobbit Set Review: Commons and Uncommons* (`G9bqewk4i4Y`) → [`limited-resources/HOB.md`](../limited-resources/HOB.md). Chapters: mechanics 0:00 · gold 14:36 · red 45:52 · green 1:15:30 · white 1:42:00 · blue 2:04:22 · black 2:39:48 · artifacts+lands 3:03:50.

**Web prose:**
- Wizards, *The Hobbit Prerelease Guide* — `magic.wizards.com/en/news/feature/the-hobbit-prerelease-guide`
- Draftsim, *Cards, Mechanics, and Set Information* — `draftsim.com/mtg-the-hobbit/`
- Draftsim, *The Ultimate Limited Set Review* + pick order — `draftsim.com/mtg-hob-limited-set-review/`, `draftsim.com/HOB-pick-order/`
- Card Game Base, *Draft Guide* + *Draft Tier List* — `cardgamebase.com/the-hobbit-draft-guide/`, `cardgamebase.com/the-hobbit-draft-tier-list/`
- MTG Arena Zone, *HOB Limited Archetypes Guide* — `mtgazone.com/the-hobbit-hob-limited-archetypes-guide-and-example-decks/`

**Card data:** Scryfall `set:hob`, 193 cards, fetched 2026-08-05. All card names and mana costs in this file are Scryfall-verified.

**Also distilled (video):**
- 2026-07-30 → 2026-08-06 — Limited Level-Ups HOB primer, 5 videos (`m-qR8GeZ96A`, `jD3Tr03b2MQ`, `nt-OvtlAGBY`, `-DZnv_Ap-qo`, `gXrmVcPfg24`) → [`limited-level-ups/HOB.md`](../limited-level-ups/HOB.md). Ingested 2026-08-08.
- 2026-08-05 — OzMTG, *The Hobbit Prerelease Kit Building* (`tuFQbNpulRg`, 15m23s) — distilled directly into this file (kit contents + pool-build method + dissents). OzMTG is **not** a registered channel in `src/ingest/channels.json`; captions were fetched ad hoc, consistent with this folder being outside the `src/ingest/` ETL.

**Not yet ingested:** LR 866 (rares & mythics, airs week of Aug 10) · Lords of Limited (no HOB content as of 2026-08-08) · Numot (channel has neither a videos nor a streams tab — needs a manual look) · 17Lands (no HOB data until Arena release Aug 11).
