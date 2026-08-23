# DFT — Limited Level-Ups draft notes

> Source: **Limited Level-Ups** (host **Alex / Chord_O_Calls**) — **1 DFT (Aetherdrift) video**, the
> *Aetherdrift Flashback Primer* (2026-07-15, `OKepWLhO_XQ`, ~4,900 words). Built 2026-08-23.
> Auto-captions of speech, so card and mechanic names are mangled — corrected against the DFT card
> list where confident, uncertain readings marked `(?)`. (The captions also render "Aetherdrift" as
> "Aether Revolt" throughout and "Marvel" as "Arvel"; those are transcription artifacts, not the host.)

## ⚠ COVERAGE WARNING — READ BEFORE ANYTHING ELSE

**This guide rests on a single episode, and it is not a set review.**

- **There is exactly one DFT video in this batch.** The channel's usual product for a set — a
  per-color card-by-card review (White / Blue / Black / Red / Green + Multicolor/Colorless +
  Rare/Mythic) with a **letter grade on every card** — **does not exist here**. None of those
  episodes were captured for DFT.
- **Therefore there are NO letter grades in this guide.** Not one. The primer names cards and says
  whether they are good; it never grades them. **No grade has been invented.** Every `## Card tips`
  bullet below is an unranked note, which is a real loss of resolution versus this channel's
  MSH guide — do not read the bullet order as a pick order.
- **Coverage is a highlight reel, not a card list.** Alex says so himself: *"This is not an
  extensive list of the good cards. This is just like the cream of the crop."* Roughly **50 cards**
  are named out of a ~280-card set. **Silence here means "not mentioned", never "bad".**
- **What this guide IS good for:** the format-level read. A flashback primer is a re-orientation to
  a format that already came and went, delivered with full hindsight — the archetype ranking, the
  color ranking, the speed read and the "what the format rewards" framing are settled, played-out
  conclusions, not predictions. That is the strongest content here and it leads the guide.
- **What this guide CANNOT do:** rank two cards against each other, tell you a pick order, or
  evaluate any card it does not name. For that, use the 17Lands numbers and
  `draft-guides/lords-of-limited/DFT-draft-guide.md`.

## ⚠ Recency rule (read first)

- **The usual recency ladder does not apply — there is only one rung.** This channel's normal
  weighting (prerelease predictions weakest → per-color reviews → early-access gameplay) needs
  multiple episodes across a format. This batch has one episode recorded **after the format was
  over**.
- **The evidence is THIN but it is NOT stale and NOT predictive.** A flashback primer is written
  with the whole format in the rear-view mirror: Alex is describing what actually happened over the
  full run ("as the format went on, it kind of evened out"), plus a fresh draft he had just
  streamed that same day. On the *settledness* axis this is the strongest kind of source in the
  repo. On the *breadth* axis it is the weakest. Weight it accordingly: **trust the format read,
  do not lean on the card coverage.**
- **Flashback-specific edge, stated by the host.** He explicitly expects the flashback pod to be
  softer than the original run — *"during flashbacks, there's going to be a lot of people who just
  aren't super attuned with the set, or kind of have forgotten what the good cards are."* Green
  being open beyond its true strength is the specific prediction.
- **This guide decodes 17Lands rather than ranking beneath it.** DFT has a full public data set
  (`data/cache/17lands_DFT_PremierDraft_1200d.json`). Where a note here conflicts with GIH WR,
  **the data wins** — this is a single spoken opinion, not a sample. See `AGENTS.md`.

### Source timeline

| Date | Episode | Phase | Weight |
|------|---------|-------|--------|
| 2026-07-15 | Aetherdrift Flashback Primer (`OKepWLhO_XQ`) | post-format flashback primer (full hindsight, plus one same-day draft) | **Only source** — settled on format, very thin on cards |

## Supersessions

**None available — this batch has no first-impressions episode to compare against.** Supersessions
require at least two episodes from different phases of a format; there is one episode here, recorded
after the format ended.

The closest available substitute is Alex's own **self-reported corrections** — takes he states
inside the primer that he got wrong the first time around. These are hindsight admissions, not
reversals this batch reveals, but they are the highest-signal lines in the episode:

- **Thunderhead Gunner — "the number one card I got wrong."** His flat self-assessment: *"I didn't
  give this card the credit it deserved."* Settled verdict: **the best red common**, happy to play
  multiples.
- **Afterburner Expert (?) — underrated on release, "one of the best rares in the set."** *"I
  remember even when this set first came out, people underrated this card."*
- **Marshals' Pathcruiser — underrated for the entire format.** *"I remember at the end of the
  format it was still an underrated card."* Not a take he reversed late; a take **the community**
  never corrected.
- **Green's opening week was chaos that settled.** *"For the first week [green] was all over the
  place — people didn't know, we're drafting a bunch of green decks, and the people who weren't
  weren't. As the format went on, it kind of evened out a little bit, but green's still really
  good."*
- **"Better than it looks" is the recurring shape of the whole set.** He applies the phrase to
  Marshals' Pathcruiser, Wreckage Wickerfolk, Engine Rat, Momentum Breaker, Skystreak Engineer and
  Keen Buccaneer, and generalizes: *"that's kind of been the theme for a lot of cards."* **DFT
  systematically rewards re-reading the unassuming commons.**

## Format speed / meta read

*(Post-format read with full hindsight — the strongest section in this guide.)*

- **Combat-centric and you are racing a decent amount — but the clock is a snowball, not a burn.**
  Alex compares the feel to Marvel: *"it's definitely combat-centric, absolutely. You're racing a
  decent amount."* The key nuance is that **the two-drops don't kill you; falling behind does** —
  *"if you're not affecting the board on turn two, on turn three, on turn four, things can snowball
  out of control very, very quickly."* **Practical rule: play to the board every turn of the early
  game.** Passing turns to hold up interaction is how you lose.
- **Stats are the master lens.** *"One thing about the cards in this set, it's like a lens to view
  them through: stats are very good. Power and toughness is very good in this set because of
  vehicles."* Raw P/T does triple duty — it crews vehicles, it saddles mounts, and it wins the
  combat the format is built around. This is why a plain overstated body like **Terrian, World
  Tyrant** is a top uncommon.
- **It is a vehicle set that is not ABOUT vehicles.** *"There are vehicles, but it's not like
  there's a ton of vehicle-matters cards. And the nature of vehicles means that you can't play too
  many of them — you're aiming for like three or four."* **Do not force vehicles.** Save the three
  or four slots for the genuinely good ones (Thundering Broodwagon, Marshals' Pathcruiser,
  Broadcast Rambler); the mediocre ones stay in the sideboard.
- **Color power order: green > blue > black > red > white.** Direct quote: *"very roughly, I think
  the power level of the colors is like green, blue, black, red, white, maybe — black and red
  swapped, but black's a good [color]."* **Green is the best color; blue and green are the two
  strong ones; white is the worst and it is "pretty bad."**
- **Exhaust is the premium mechanic and it is nearly bust-proof.** *"Almost all the exhaust
  abilities are really good. It's very rare you see an exhaust card that's not good. So if it says
  exhaust, for the most part it's going to be a pretty good card."* Exhaust is the blue-green
  mechanic (activate once, ever) and functions like MSH's power-up. **Treat "exhaust" as a
  positive keyword on sight.**
- **Start your engines / speed is a late-game relevance engine for aggro, not a race mechanic.**
  *"It's a way for your aggressive deck to retain some relevance in the late game — you get in some
  early hits, maybe your opponent stabilizes, but you've got a cheap flyer that can just keep
  pecking in. You hit to four and all your cheap cards become a little bit better."* Design verdict:
  *"a little more trouble than it was worth"* (it needs an out-of-game tracker).
  - **Speed rules worth knowing:** you go to speed 1 the first time you play a start-your-engines
    card; you go up 1 each turn the first time you deal damage to your opponent; **you cannot gain
    more than one speed in a turn** except on the turn you first turn the mechanic on (cast it, then
    deal damage → speed 2 immediately). Cheap evasive bodies are what actually get you to max speed.
- **Saddle = crew, but on creatures, with a bonus effect.** Another reason raw power matters.
- **Themes are loose — you are not locked into your color pair's theme.** *"You're not very strictly
  tied into your theme in your color pairing this set, which is cool."* He drafted a UR deck that
  same day with **no** discard theme at all, running exhaust instead. **Take the better card.**
- **Reanimation is a real minor theme.** Cycle a big body early (Migrating Ketradon, Thundering
  Broodwagon), then reanimate it with **Broodheart Engine**. Low-cost, high-payoff line in BG.
- **Colorless start-your-engines lands are traps.** Called out explicitly and repeatedly — see
  the Lands bullets in `## Card tips`.

## Archetypes

*(Not a ranked 10-pair list — the primer covers 7 pairs and does not rank them numerically. Order
below follows the strength language Alex actually uses. **WU, WR and RG are not discussed at all**;
their absence is a coverage gap, not a verdict.)*

### Tier 1 — the pairs he calls strong

**UG — Exhaust.** The home of the format's best mechanic, in the format's two best colors. *"The
best two colors are blue and green. Blue and green are really, really strong. The mechanic for
green-blue specifically is exhaust."* Key cards: Stampeding Scurryfoot, Hazard of the Dunes,
Greenbelt Guardian, Rangers' Refueler, Skystreak Engineer, Keen Buccaneer.

**BG — Graveyard / reanimator value.** *"Black-green also really good."* A light reanimator-graveyard
theme built on **Broodheart Engine** (upkeep surveil; sac to reanimate a vehicle or artifact) plus
cheap cycling on big bodies. *"A lot of good enters-the-battlefield effects in this set, a lot of
good value to be had. Good place to be."*

**UB — Artifacts / tempo drain. Alex's favorite deck in the format.** *"Blue-black is so, so much
fun."* The engine is **Haunt the Network** (5-mana sorcery: two flying Thopters, then drain per
artifact you control) alongside **Pactdoll Terror** (4-mana 3/4 that drains for 1 on every artifact
ETB, itself included). *"That in tandem — that's a whole lot of drain."* You want as many copies of
both as you can get. Play pattern: **tempo-y drain**.

### Tier 2 — good, with a caveat

**UR — Discard / exhaust.** *"Blue-red can be really good."* The discard payoffs live at uncommon —
**Marauding Mako** (R 1/1, counter per discard) and the blue 1/2 flyer that does the same
(**Scrounging Skyray** (?)) — and **Broadside Barrage** is a premium removal spell that loots. But
the theme is optional: Alex's same-day UR deck ran **exhaust** instead and was fine.

**BR — Start your engines.** The aggro shell that keeps late-game relevance via speed. Signpost is
**Gastal Thrillseeker** (2-mana 2/3, drain 1 on ETB, deathtouch + haste at max speed) — *"even in
the late game, you're pretty happy about that."*

### Tier 3 — white pairs, i.e. mostly-not-white pairs

**GW and WB.** White is the worst color and *"it's pretty bad"* — but the few good white cards are
excellent. **The construction rule is explicit:** *"If you are in green-white, ideally it's heavy
green and a little bit of white — that's kind of the deal for any white deck. You're hoping you're
heavy one color and kind of light on the white cards, only playing some select white cards."* The
white cards worth being there for: **Veteran Beastrider** (GW), **Embalmed Ascendant** (WB),
**Gloryheath Lynx**, **Ride's End**, **Perilous Snare**.

### Not covered

**WU, WR, RG** — the primer never discusses them. No read available from this source.

## Card tips

**⚠ NO LETTER GRADES.** This channel's per-color graded set review does not exist for DFT in this
batch, and the primer never grades a card. Every bullet below is an ungraded note from the
2026-07-15 flashback primer. Bullet order is not a pick order. ~50 cards named out of ~280 —
**absence from this list carries no information.**

### Green (G) — best color
- **Stampeding Scurryfoot** — *"This card is amazing… you want as many copies as you can get."* 1-mana 1/1; exhaust 4 mana: put a counter on it and make a 3/3 token. Reads fine, plays far better than it reads — a turn-one drop that later warps a combat. Alex flags that his description undersells it: *"me just saying it here probably doesn't paint the full picture, but trust me."*
- **Hazard of the Dunes** — 4-mana 4/4 trample reach (?) with exhaust: put three counters on it. *"A nice big body."*
- **Migrating Ketradon** — *"one of the best kind of this kind of cards we've ever had."* 6-mana 6/6 reach, gain 4 life on ETB, **cycling 2**. The cycling is load-bearing: cycle it early, reanimate it with Broodheart Engine.
- **Run Over** — *"a pretty good efficient green removal spell."*
- **Greenbelt Guardian** — 2-mana 2/2 that grants trample; exhaust to become a 5/5. *"Just great rate, really good."*
- **Autarch Mammoth** — *"another phenomenal uncommon."* 6-mana 5/5; makes a 3/3 on ETB or attack if saddled. Saddle 5 looks steep but is worth it for the token.
- **Terrian, World Tyrant** — *"it's kind of funny to just look at this and be like, yeah, this is one of the best uncommons. It is massive."* Part of the overstated-vanilla cycle. Very little removal kills it; two connections is close to lethal. *"This should be a card that sticks out to you from the pack."*
- **Fang-Druid Summoner** — 2-mana 2/4 reach; ETB search library **or graveyard** for a vanilla creature. Curves directly into Terrian.
- **Afterburner Expert (?)** — *"one of the best rares in the set"*, and the card Alex says people underrated on release. 3-mana 4/2; exhaust to make it a 6/4; returns from the graveyard for free whenever you exhaust something else. *"Such a pain to deal with."*

### Blue (U) — second-best color; the uncommons are where the action is
- **Spectral Interference (?)** — 1U instant: counter an artifact or creature spell unless they pay 4. "Negate-adjacent."
- **Flood the Engine** — *"good removal spell."*
- **Bounce Off** — *"great bounce spell… actual Unsummon, and even better because it can hit vehicles."*
- **Skystreak Engineer** — 2-mana 1/3 flyer; exhaust 5 mana: put two counters on it. One of two exhaust creatures *"better than they look."*
- **Keen Buccaneer** — *"Love this card. This is such a gluey card."* 2-mana 2/3 vigilance; exhaust: counter + loot. Not a first-pick common, but *"so good in basically all the decks"* — good if you care about exhausting, good if you care about discarding, and a fine on-curve attacker that threatens to become a 3/4.
- **Spikeshell Harrier** — *"reads like a great card."* 5-mana 4/4, bounce something on ETB, and drop the opponent's speed by 1 (the speed clause is minor but occasionally relevant).
- **Stock Up** — the known quantity. *"It was very good [in Strixhaven]. It's very good here, too."*
- **Rangers' Refueler** — 2-mana 3/3 crew 2 vehicle. You rarely crew it; you pay to animate it and put a counter on it, and **draw a card on every exhaust activation, including its own**. *"Kind of like a six-mana 4/4 draw-a-card that also stands to draw you more cards later."* Much better with a real exhaust count.
- **Transit Mage** — 3-mana 2/2, tutors an artifact of mana value 4 or 5 **to hand**. *"No shortage of good things to go get"* — e.g. Spikeshell Harrier.
- **Aether Syphon** — 3-mana artifact, start your engines, tap for a card; at max speed each opponent mills 2. *"Pretty legit in any slower blue deck"* (e.g. UB artifacts) **only if you have cheap evasive bodies to reach max speed** — otherwise it is *"just a very clunky draw spell."*
- **Riverchurn Monument** — *"a busted one at rare. This card's really, really strong. You should take it if you see it."* 2-mana artifact; tap: any number of target players mill 2; exhaust 4: those players each mill cards equal to the number of cards in their graveyard. Wins from a topdeck in the late game, and turn-two deploy → repeat activations gets there on its own.
- **Scrounging Skyray (?)** — blue 1/2 flyer that grows when you discard; the blue half of the UR discard pair with Marauding Mako.
- **(unidentified blue uncommon) (?)** — a 3/4 flyer with **affinity for artifacts**. Alex flags it against MSH's *Ironheart* (a rare 3/4 flyer with **improvise**) and warns not to conflate them: improvise taps your attackers/blockers, affinity doesn't. *"Pretty often a one-mana 3/4 flyer in the mid part of the game if you're drafting the artifact-heavy decks."* Caption did not yield a confident name.

### Black (B) — third color, deep and synergistic
- **Wreckage Wickerfolk** — *"this card does everything… a pretty quality black common. I'd take it pretty highly."* 2-mana 1/3 flying **artifact** creature, surveil 2 on ETB. Artifact for the UB affinity/drain deck, flying to peck in for max speed, surveil to smooth draws (*"you can keep a two-land hand with this card and feel very comfortable"*) and to fill the graveyard.
- **Pactdoll Terror** — 4-mana 3/4: whenever it or another artifact enters, drain 1. *"If you're drafting black, these two cards [with Haunt the Network] are kind of your bread and butter. You really want as many copies as you can of both."* Stacks with itself.
- **Engine Rat** — *"a little bit unassuming."* 1-mana 1/1 deathtouch with an expensive drain-2 activation. *"A lot of games do come down to this activation. The threat of this being on the battlefield makes your opponent play pretty differently."*
- **Grim Bauble (?)** — a fine removal spell (-2/-2); can also be sacrificed to surveil 2.
- **Spin Out** — *"your classic Murder variant."*
- **Momentum Breaker** — *"better than it looks."* 2-mana enchantment, start your engines; opponent sacrifices a creature or vehicle, or discards if they can't; sac it to gain life equal to your speed. *"Not going to always kill their best thing, but it's pretty good value — you're getting enough for the mana."*

### Red (R) — fourth; thinner, but real standouts
- **Thunderhead Gunner** — **the best red common**, and Alex's self-declared biggest miss on release. Huge body with reach that blocks nearly everything, plus a repeatable discard-a-card-draw-a-card every turn. *"Exactly what you want after you've played out your hand… ensures that you basically never flood"*, and it triggers your discard payoffs every single turn. *"I'm happy to play multiple."*
- **Lightning Strike** — the known efficient burn.
- **Crash and Burn** — 4-mana instant: 6 damage to a creature or destroy a vehicle. *"A little bit expensive… not too sad about that."*
- **Marauding Mako** — 1-mana red 1/1 that grows on each discard. The UR discard payoff; **Mako + Thunderhead Gunner** is the named pairing.
- **Greasewrench Goblin** — *"a really good rate."* 1-mana 2/1; exhaust 3 mana: counter plus loot/rummage up to twice.
- **Outpace Oblivion** — 3-mana, deal 5, plus ding the opponent if they aren't at max speed. *"Another pretty good removal spell."*

### White (W) — worst color, but its good cards are genuinely excellent
- **Ride's End** — *"a good removal spell."* 5-mana exile anything, or 2 mana if the target is tapped.
- **Broadcast Rambler** — *"a fine card."* Big vehicle that arrives with a 1/1 flyer that can crew it.
- **Gloryheath Lynx** — *"excellent… that's a phenomenal rate."* 2-mana 2/3 lifelink, saddle 2, searches up a Plains when it attacks.
- **Gallant Strike** — *"fine removal spell with cycling."*
- **Perilous Snare** — *"a very good splashable rare"* and the main reason to be in white. 3-mana artifact: exile something until it leaves; at max speed, tap to put a counter on a creature or vehicle you control. *"Kind of like a Web Up from Marvel, but puts stats on the board eventually — it turns into something that takes over the game."*

### Multicolor
- **Haunt the Network** (UB) — *"excellent card."* 5-mana sorcery: make two flying Thopters, then drain the target opponent for each artifact you control. The centerpiece of Alex's favorite deck; wants Pactdoll Terror alongside it.
- **Thundering Broodwagon** (BG) — *"one of the better ones"* among the format's vehicles. 6-mana 6/5 menace reach, crew 3, **cycling**, and destroys an opponent's nonland permanent of mana value 4 or less on ETB. *"Reads like a pretty good card."* Cycle-then-reanimate target.
- **Broodheart Engine** (BG) — *"pretty good engine card."* 2-mana artifact: surveil 1 each upkeep; sacrifice for 4 mana to reanimate a vehicle or an artifact. The hub of the BG cycle-and-reanimate line.
- **Broadside Barrage** (UR) — *"just great removal spell."* 3-mana instant: 5 damage, then loot.
- **Veteran Beastrider** (GW) — *"very, very strong… this is a must-kill card."* 3-mana 3/4 that untaps all your creatures at end step — free vehicle crews and effective vigilance across the board — plus a 4-mana team pump. *"Makes combat almost impossible for the opponent. The threat of activation is really, really tough."*
- **Embalmed Ascendant** (WB) — *"this card is really good… just a very, very strong effect."* 3-mana 1/2 that makes a 2/2 on ETB; start your engines; at max speed it drains the opponent whenever a creature dies. Note the speed timing: cast it → speed 1, deal damage that turn → speed 2 immediately.
- **Gastal Thrillseeker** (BR) — *"a phenomenal rate."* 2-mana 2/3, drain 1 on ETB (which also gets you to speed 2 the turn you cast it), start your engines; deathtouch and haste at max speed. *"Even in the late game, you're pretty happy about that."*

### Colorless / artifacts
- **Starting Column** — *"one of the better ones we've had"* of the Manalith family (though *"not quite as good as Potioner's Trove"* from another set). 3-mana, start your engines on ETB, taps for any color; sac at max speed to draw 2 and discard 1. His general rule: *"If your additional mana source converts into some other resource later, that's usually a sign of a good Manalith."*
- **Marshals' Pathcruiser** — *"card is very underrated… a lot better than it looks. Relatively high pick, I would say."* 3-mana 6/5 crew 5 vehicle — clunky on its face — but it searches up a basic land to hand on ETB, making it a **card-advantage vehicle that goes in basically any deck**. (It has a 5-mana WUBRG exhaust cost to animate; you rarely use it.) Alex does not count it as a multicolor card.
- **Scrap Compactor** — *"a fine removal spell if you don't pick up anything better."*

### Lands — flagged as traps
- **Avishkar Raceway (?)** (common) — the only one Alex will occasionally play, *"when my mana is really good, I don't have any double pips, and maybe I'm a little bit low on mana sinks."* Rummage at max speed. *"Playable-ish, but it's still not great."*
- **Amonkhet Raceway (?)** (uncommon) — tap to give something haste at max speed. *"Not really worth the squeeze."*
- **Muraganda Raceway (?)** (rare) — *"Sol Ring, or I guess like Ancient Tomb, at max speed. Also not really worth the squeeze."*
- **General rule:** *"As always, colorless lands come with a major cost. They have to be good. You don't want to put a colorless land in your deck with the potential of it not doing anything more than tapping for colorless mana."* He had already seen these cards misplayed multiple times on flashback day one. **Stay away.**

## Caption garble

Names corrected from the auto-captions, listed so a future reader can audit them:

| Caption | Correction |
|---|---|
| "Aether Revolt" | **Aetherdrift** (the set itself, mangled throughout) |
| "Arvel" | **Marvel** (MSH, the set the audience was tired of) |
| "Thundering Bridgewagon" | **Thundering Broodwagon** |
| "Brute Heart Engine" | **Broodheart Engine** |
| "Hot Network" / "Haunted Network" | **Haunt the Network** |
| "Pact of the Titan" / "Pact of the Serpent" | **Pactdoll Terror** |
| "Gestalt Thrillseeker" | **Gastal Thrillseeker** |
| "Veteran Beast Rider" | **Veteran Beastrider** |
| "Embodiment Ascendant" | **Embalmed Ascendant** |
| "Stampeding Scion" | **Stampeding Scurryfoot** |
| "Migratory Carnosaur" | **Migrating Ketradon** |
| "Terrian World Tyrant" | **Terrian, World Tyrant** |
| "Fang Druid Summoner" | **Fang-Druid Summoner** |
| "Riverturn Mimic" | **Riverchurn Monument** |
| "Ether Syphon" | **Aether Syphon** |
| "Ranger's Refueler" | **Rangers' Refueler** |
| "Wreckage Riggerfolk" | **Wreckage Wickerfolk** |
| "Crush and Burn" | **Crash and Burn** |
| "Greasefang Goblin" | **Greasewrench Goblin** |
| "Ride Down" | **Ride's End** |
| "Glory Seeker Lynx" | **Gloryheath Lynx** |
| "Perilous Snooper" | **Perilous Snare** |
| "Mardu's Path Cruiser" | **Marshals' Pathcruiser** |
| "the Mako" | **Marauding Mako** |
| "Grim Initiate" | **Grim Bauble** (?) |
| "the Brood Weaver" | unresolved (?) — a third cycling body used with Broodheart Engine; not confidently mapped, so no bullet was written for it |

## Source episodes

- 2026-07-15 — Aetherdrift Flashback Primer (`OKepWLhO_XQ`)
