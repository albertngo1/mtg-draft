# DSK — Limited Resources draft notes

> ## ⚠⚠ COVERAGE WARNING — READ BEFORE USING THIS FILE ⚠⚠
>
> **This guide rests on ONE episode, and that episode is not a set review.**
>
> Limited Resources' normal per-set arc — Set Review: Commons & Uncommons, Set Review: Rares & Mythics, Format Overview, and the end-of-format Sunset Show — **does not exist in this repo for Duskmourn.** DSK aired September 2024, before this repo's LR ingest window. The only DSK transcript available is **#824 "Duskmourn and Modern Horizons 3 Refresher" (2025-10-10)**, recorded a full year after the set, when Arena re-ran DSK as a flashback draft format.
>
> A **refresher** is a different genre from a set review. It is a ~25-minute retrospective onboarding for players returning to a format: archetype tier list, one crack-a-pack, a best-commons-by-color rundown, and a handful of build-arounds. It is **not** a card-by-card grading pass.
>
> Consequences, stated plainly:
>
> - **There are almost no letter grades in this file, because the episode gives almost none.** One grading utterance appears in the entire Duskmourn half ("these cards were all Ds," covering three cards in the cracked pack). Every other card bullet below is ungraded prose. **No grade has been invented to fill the channel's usual format.**
> - **Card coverage is 37 cards out of 281 draftable.** Anything not named in the episode is simply absent. This file cannot be used as a pick-order list.
> - **`## Supersessions` is genuinely empty.** There is no release-week LR episode in this batch to flip. See that section.
> - **Rares and mythics are effectively uncovered** — exactly one rare (Marina Vendrell's Grimoire) is discussed, and only because it fell out of the cracked pack.
>
> The one thing this episode is *unusually strong* on: the **format-level read**. See `## Format speed / meta read` and `## Archetypes` — those are settled, hindsight-informed verdicts from a year of played reps, not predictions. Lead with them.
>
> Built 2026-08-23 from the YouTube auto-caption transcript. LR is an audio podcast on YouTube, so card and mechanic names are heavily mangled — corrected against the DSK card list where confident, uncertain readings marked `(?)`.
>
> **The episode covers two sets.** Only the Duskmourn half (~the first 45% of the transcript) is distilled here. Nothing from the Modern Horizons 3 half appears in this file.

## ⚠ Recency rule (read first)

- **The usual LR recency warning is INVERTED for this set.** LR's normal weakest source is the release-week set review (blind predictions). **This file contains no predictions at all.** The single source is a retrospective recorded ~12 months after release, with the format fully solved and Arena win-rate data long since settled. Everything below is a **late take**.
- **So: what is here is high-confidence; what is missing is most of the set.** Trust the archetype tiers and the best-commons list. Do not read a card's absence as a low grade — read it as "the episode never mentioned it."
- **The two hosts explicitly frame the tiers as post-hoc knowledge**: "because this is post-set, we know what the best ones are. We don't have to guess." That is the strongest evidentiary phase LR ever speaks from.
- **This guide decodes the 17Lands data rather than ranking beneath it.** DSK is a multi-axis synergy set (enchantments/Glimmers, Delirium, Manifest Dread, sacrifice, rooms, survival). A payoff's GIH WR comes from *its* deck. Trust the number where a card is generically castable (removal, efficient bodies, fixing); discount it where it is a build-around. See `AGENTS.md`.

### Source timeline

| Date | Episode | Phase | Weight |
|------|---------|-------|--------|
| *never ingested* | Set Review: Commons & Uncommons | release-week (predictions) | Weakest — **NOT AVAILABLE** |
| *never ingested* | Set Review: Rares & Mythics | release-week (predictions) | Weakest — **NOT AVAILABLE** |
| *never ingested* | Format Overview | early | Medium — **NOT AVAILABLE** |
| *never ingested* | Sunset Show | late retrospective | Strongest — **NOT AVAILABLE** |
| 2025-10-10 | **#824 Duskmourn and Modern Horizons 3 Refresher** (Duskmourn half only) | **LATE — retrospective refresher, ~1 year post-release, format fully solved** | **Strongest available — and the only source** |

## Supersessions (newer take wins)

**None available — this batch has no release-week episode to compare against.**

This section is normally the highest-value product of the Limited Resources channel: which release-week letter grades the format later reversed, and by how much. Producing it requires at least two episodes from different phases of a format. This batch has one, and it is already the late phase.

Do not read the empty section as "LR's early DSK takes all held up." It means the early takes were never ingested. If an LR DSK set-review episode is added to `data/subs/limited-resources/DSK/` later, this section becomes fillable — every bullet in `## Card tips` below is a settled late verdict and can serve as the right-hand side of a supersession.

## Format speed / meta read

- **Not a fast format, but the two best decks were assertive.** LSV's framing: "Duskmourn was not the fastest set, but the two best archetypes were fairly assertive. Had a lot of play on the board and a lot of synergy." Midrange baseline; the top of the format is board-centric tempo and aggro, not control.
- **THE thesis of the episode: take the payoff, not the enabler.** Marshall: "each of these archetypes has that dynamic of, should I prioritize the enabler or should I prioritize the payoff? And it's almost always correct to prioritize the payoff, as they made it relatively easy for the enablers in the good archetypes." Wizards seeded so many incidental enchantments and artifacts into the commons that Delirium and enchantment-matters turn on nearly for free. The scarce resource is the card that *rewards* you.
- **The set's design succeeded because the enablers are invisible.** "Look at the red and green creatures at common and uncommon. Tons of them just happen to be artifacts" — so a creature trading in combat quietly advances Delirium. LSV: "too much of that doesn't really go wrong, but not enough definitely does."
- **Four-drops are a trap, and three toughness is a fault line.** LSV: "four-drop 3/4s and 4/4s have really fallen off, and I'm not exactly sure why — maybe they just interact too poorly with cheaper cards." And separately: "three toughness was a critical part of the set. If you're spending four mana and they're spending two, it's not going to go well for you." Both hosts flagged three consecutive bad four-drops in a single cracked pack. **Keep your curve low; be suspicious of any four-mana ground creature.**
- **Survival cards played worse than they read.** Marshall on House Cartographer: "this card always played way worse than it looked. The survival cards really really did." The whole mechanic underdelivered, which is why GW is a bottom archetype.
- **Glimmers are a real payoff, not flavor.** "Glimmers are very, very powerful. Cards that make Glimmers are great." A 1/1 Glimmer token is an enchantment creature, so it feeds enchantment-matters *and* is a body — this is why Tunnel Surveyor and Glimmerburst outperform their text.
- **Ramp is good because there is so much mana sink.** "There's a lot to do with your mana in Duskmourn, so ramping was pretty good" — unlocking rooms, Manifest Dread activations, flipping face-down creatures. Threats Around Every Corner and Spineseeker Centipede are strong for this reason as much as for fixing.
- **Fixing is good enough that three colors is normal in the green decks.** Common dual lands (the Abandoned Campground cycle) plus Spineseeker Centipede mean the Delirium/graveyard shells routinely splash. Temur is a real deck: "mostly blue-green splashing red for some Scorching Dragonfires, or red-green splashing a good blue card or two like some Oblivious Bookworms."
- **Do not open on a black card.** LSV's clearest pick-order heuristic: "I didn't like starting with black cards, because blue-black and black-white were both fairly poor archetypes, and red-black was also pretty linear. There weren't that many ways to go if you started with a black card." A first-pick Final Vengeance basically commits you to BR.
- **Do open on green.** "You take Spineseeker, you could go blue-green, you could go green-black, you could go red-green" — and all three are top-tier. Green is the maximum-flexibility start.
- **Black-red is the one archetype that does NOT splash.** "It just really wanted to do the black-red stuff. It didn't really want cards of other colors anyway." Marshall: "if you are red-black, it's very focused — you're on rails." That rigidity is also its strength: nobody else at the table wants your payoffs.
- **Overall verdict:** both hosts rate DSK "close to an all-timer, if not an all-timer" draft format — LSV picked it over drafting the current set. LSV won a four-figure prize in the Duskmourn Arena Open with RG Delirium.

## Archetypes

All ten pairs are covered. The episode presents them as **three tiers**, not a strict 1–10 ordering; within-tier ranks are not stated and are not invented here.

### TIER 1 — the two best decks

#### Azorius (WU) — Enchantment tempo — BEST (tied)
- **Plan:** Flood the board cheaply while every enchantment and every room unlock triggers a payoff. Tempo, not control.
- **Key cards:** Gremlin Tamer (WU 2/2 — makes a 1/1 on every enchantment/room unlock), Inquisitive Glimmer (WU 2/3 — your enchantment spells cost 1 less), Tunnel Surveyor (2U 2/2 that brings a 1/1 Glimmer with it — "a two-drop that cared about enchantments, plays this, gets a 2/2 and a 1/1 and triggers your enchantment thing"), Glimmerburst, Trapped in the Screen, Meat Locker // Drowned Diner.
- **Why it works:** the Glimmer tokens are enchantment creatures, so board development and payoff-triggering are the same action. "That's what signpost uncommons are supposed to do."

#### Boros (RW) — Aggro — BEST (tied)
- **Plan:** Just aggro. LSV: "Red-white was just aggro. That was just the deck. It didn't really have any special theming going on."
- **Key cards:** Clockwork Percussionist (a turn-1 and turn-2 clock that also replaces itself), Scorching Dragonfire, Trapped in the Screen, Piggy Bank, and the red room that pumps attackers (Painter's Studio // Defaced Gallery (?) — the episode describes only "the room that gave all your attacking creatures +1/+0").
- **Note:** the only top-tier deck with no synergy tax. If the cheap red and white creatures are flowing, this is the lowest-variance lane in the format.

### TIER 2 — "all quite good," not far behind

The hosts are explicit that the gap is small: "it's not like these two decks were 10 shoulders above — this is roughly in tiers."

#### Gruul (RG) — Delirium, aggressive — LSV's personal favorite
- **Plan:** Delirium with a beatdown bent. Cheap artifact creatures that trade profitably *and* fill card types in the yard.
- **Key cards:** Wildfire Wickerfolk (RG 3/2 haste trample, +1/+1 with Delirium — and it is an **artifact** creature, "so you'd play it, it would die, and now suddenly you have two types in your graveyard for other Delirium cards while benefiting from setting up Delirium"), Spineseeker Centipede, Clockwork Percussionist, Piggy Bank, Fear of Burning Alive.
- **Track record:** LSV won the Duskmourn Arena Open with this deck.

#### Golgari (BG) — Delirium, controlling
- **Plan:** Same Delirium engine as Gruul, oriented toward attrition rather than pressure. Good self-mill support.
- **Key cards:** Spineseeker Centipede, Final Vengeance (playable here, "but you didn't really want to all that much"), Threats Around Every Corner.
- LSV groups RG and BG together: "I really like drafting red-green and black-green."

#### Simic (GU) — Manifest Dread control
- **Plan:** Manifest Dread as engine — look at the top two, one becomes a face-down 2/2, the other fuels the graveyard. Grind with graveyard payoffs. Splashes very easily.
- **Key cards:** Oblivious Bookworm ("one of the best uncommons in the set" — GU 2/3 that loots each turn and skips the discard if you manifested or flipped a face-down; "turn 2 Bookworm, turn 3 manifest, you just drew a card in a turn — incredible card"), Tunnel Surveyor, Glimmerburst, Threats Around Every Corner, Spineseeker Centipede.
- **On flipping:** paying a manifested creature's cost to turn it face up "wasn't actually a huge part of the card. It did happen sometimes, but mostly it did not." Treat Manifest Dread as a 2/2 plus a self-mill trigger, not as a value engine.

#### Rakdos (BR) — Sacrifice
- **Plan:** The one linear deck in the format, and it actually works. "Kind of like you've seen in a lot of other sets, but it actually worked. They had the support for it, they had the good tools."
- **Key cards:** Disturbing Mirth (the payoff — see Card tips), Final Vengeance, Clockwork Percussionist, Piggy Bank, Innocuous Rat, plus "threatens and a lot of fodder."
- **Draft posture:** does not splash, and does not want other colors' cards. The upside is that you are the only drafter at the table who wants the payoffs — Marshall: "hopefully you're the one player at the table who actually wanted it." The downside is that first-picking a black card locks you here.

### TIER 3 — the bottom four: draft only with a compelling reason

LSV's framing: "these are the bottom four archetypes, which doesn't mean they're undraftable. It just means you usually don't want to be here unless you have a compelling reason."

#### Selesnya (GW) — Survival — WORST
- **Why it failed:** Survival ("if this creature is tapped at the beginning of your second main phase, do a thing") "kind of didn't work. Just wasn't very good." Marshall: "it's just too hard to get that consistently going." Baseball Bat, the marquee uncommon, "had a very low win rate."

#### Orzhov (WB) — Reanimator
- **Why it failed:** the pieces were all present — big creatures, Rite of the Moth (4 mana, flashback 6), discard outlets — "but it just was a little bit too fragile. Didn't come together quite often enough."
- LSV is visibly disappointed rather than dismissive: "could still be good if you got the right deck, but again, didn't really want to start there."

#### Izzet (UR) — Rooms
- **Why it failed:** LSV notes he "initially had a really good success rate with blue-red rooms," then: "it turned out the rooms deck was just a little bit too slow. Most of the rooms didn't get you on board enough." **This is the closest thing to a self-correction in the episode** — an early positive read that the format overturned.
- **Key card:** Smoky Lounge // Misty Salon (UR uncommon — "a Sol Ring just for rooms": adds {R}{R} at the start of your main phase, spendable only on casting/unlocking rooms; the back half makes an X/X flier where X is rooms unlocked). "Powerful," and you could have some good Smoky Lounge decks, "but mostly that wasn't super successful."

#### Dimir (UB) — Enchantment control
- **Why it failed:** "kind of like the mirror of blue-white, but instead of being aggressive you wanted to be control. It just didn't pan out quite enough."
- **Key card:** Skullsnap Nuisance (UB 1/4 flier, surveil 1 on each enchantment) — "it was just okay."

### Three-color / Temur
- **Temur is a real deck, in two builds:** UG splashing red for Scorching Dragonfire, or RG splashing blue for a card or two like Oblivious Bookworm. Marshall drafted "a lot of Temur in that set."
- **The general shape:** the green-based Delirium/graveyard midrange decks are fluid and blend into each other. Marshall's summary of the whole format: be WU or RW aggro, **or** be some green-based Delirium/graveyard midrange pile.
- **The one three-color combination to avoid:** "don't really want to go red-green-white" — but you can reach every other combination off a green start "without too much trouble."

## Card tips

**⚠ Only 37 cards are named in the Duskmourn half of this episode, and exactly THREE carry a stated letter grade** (Cackling Slasher, Anthropede, Ripchain Razorkin — all "D," from a single utterance: "these cards were all Ds"). Bullets without a grade are ungraded in the source — no grade has been fabricated. The absence of a card here means the episode never mentioned it, not that it is bad.

### White (W)
- **Trapped in the Screen** — **the best white common.** Oblivion Ring with ward 2. "It was a removal spell that triggered all your enchantments and it was fairly hard to get off the table." LSV: "maybe the best Oblivion Ring we've seen in a long time, at common especially."
- **Unsettling Twins** — filler. 3W 2/2 that manifests dread on ETB. "Not quite good enough. You could play it if you needed to — it's four mana for two 2/2s, but yeah, definitely filler."

### Blue (U)
- **Glimmerburst** — **the best blue common.** 3U instant: draw two and make a 1/1 Glimmer. "Kind of a two-and-a-half-for-one at instant speed, did all your enchantment stuff. It just played really well."
- **Vanish from Sight** — the second-best blue common, same cost. Instant-speed tuck a creature to top or bottom of library plus surveil 1. Blue's removal spell.
- **Tunnel Surveyor** — actively wanted, especially in WU. 2U 2/2 that brings a 1/1 Glimmer. "Really good for blue-white just because you could play a two-drop that cared about enchantments... but it was fine in blue-green as well." The benchmark card in the cracked pack — LR ranked Ghostly Keybearer and House Cartographer explicitly *below* it.
- **Meat Locker // Drowned Diner** — LSV's favorite room, a blue common. Front half: three mana, stun a creature for two turns and tap it. Back half: five mana, draw three and discard one. "You can see how that card played pretty nicely."
- **Scrabbling Skullcrab** — a fun uncommon build-around. Cheap 0/3 that mills 2 whenever you cast an enchantment or unlock a room. Hard to get multiples, "but if you ever could, your opponent really would have to start considering using their removal on it." You can mill 16–18 in an enchantment/Glimmer deck. **Sneaky upside:** it is *better* against Delirium decks, because they self-mill for you — "they just use this to put me over the edge."
- **Ghostly Keybearer** — playable, mid-pack. 3U 3/3 flier; on combat damage to a player, unlock a locked door of a room you control for free. "This card was okay, but it kind of needed a lot of stuff to go right. I wouldn't take it over Tunnel Surveyor." Fine in WU or UG; hurt by the rooms deck not coming together.
- **Get Out** — an uncommon, but **do not take it early**: "it's just a double-blue card that's a little bit situational." (UU instant, modal: counter a creature or enchantment spell, or bounce one or two of your own creatures/enchantments.) Historical footnote: it was busted in the Duskmourn Omniscience draft, which does not transfer to normal Premier draft.
- **Marina Vendrell's Grimoire** — the rare from the cracked pack, and not a good one. {5}{U} legendary artifact (a blue card): on ETB (if cast) draw five, no maximum hand size, and you don't lose the game for having 0 or less life — but whenever you gain life you draw that many, whenever you lose life you discard that many, and if you have no cards in hand you lose. "Your life total just becomes your cards in hand, and when they hit you start discarding. So that's definitely not a good card." LR passed it for Piggy Bank.
- **Twist Reality** — the double blue killed it. 1UU: counter target spell, or manifest dread. "This card could have been a little bit better if you could cast it more frequently, but it just wasn't good enough to risk not being able to cast it when you wanted to."

### Black (B)
- **Final Vengeance** — **the best black common**, and LR treats that fact as diagnostic. Sorcery: sacrifice a creature or enchantment as an additional cost, exile a creature. "Seeing this as the best common really just keys you into how good sacrifice was." Playable in BG "but you didn't really want to all that much." **Pick-order caveat: first-picking it effectively commits you to black-red.**
- **Innocuous Rat** — two-mana 1/1 that manifests dread when it dies. The canonical Disturbing Mirth food.
- **Cackling Slasher** — **D.** A four-mana 3/3 deathtouch that enters with a +1/+1 counter if a creature died this turn. "This is a classic example of a card that you read it and you go, what's wrong with this? And it just didn't really play well."
- **Fear of the Dark** — not good. 4B 5/5 that only gains menace and deathtouch when attacking if the defender controls no Glimmer. "This one is like a bridge too far. Just ended up just not being that good."
- **Appendage Amalgam** — filler. 2B 3/2 enchantment creature with flash; surveil 1 on attack. Grouped with the rest of the cracked-pack chaff: "these cards are all just straight up filler."

### Red (R)
- **Clockwork Percussionist** — **the best red common**, ahead of Scorching Dragonfire. "Kind of goated." R 1/1 haste artifact creature; on death, exile your top card and you may play it until the end of your next turn. Works in *three* top archetypes at once: Delirium (it is an artifact, so it fills a card type by dying), sacrifice (free fodder that replaces itself), and RW aggro (a real turn-1/turn-2 clock — "when your opponent went turn 1 Percussionist, turn 2 Percussionist, you're just like, okay, well, I can't just take a million damage"). Marshall: "a card you wanted in your yard, but also mostly replaced itself."
- **Scorching Dragonfire** — the second-best red common and "really good in that set." The premium red splash card — the reason UG decks go Temur.
- **Piggy Bank** — LR's pick out of the cracked pack, ahead of Tunnel Surveyor. 1R 3/2 artifact creature at uncommon; makes a Treasure when it dies. "Great for the Delirium deck, great for the sacrifice deck, good for the aggro deck. You really couldn't go wrong with Piggy Bank." Good stats with upside, and it points you toward RG while leaving BR and RW open.
- **Fear of Burning Alive** — an uncommon LSV "really liked taking early and building around." 4RR 4/4; ETB deals 4 to the opponent, and with Delirium every source you control that deals non-combat damage also deals that much to one of their creatures. "It was always a six-mana 4/4 that nogged them for four, but if you had Delirium, that then nogged one of their creatures for four. And if you could turn it into that, you were really cruising." Even better with recursion or multiples.
- **Ripchain Razorkin** — **D.** 3R 5/3 reach with a sac-a-land-and-pay-three draw ability. "Definitely not picking Razorkin — also at three toughness, [and] three toughness was a critical part of the set."
- **Painter's Studio // Defaced Gallery (?)** — the episode names only "the room that gave all your attacking creatures +1/+0," cited as a good RW/BR aggro card alongside Clockwork Percussionist. Name uncertain.

### Green (G)
- **Spineseeker Centipede** — **the best green common, and arguably the best common in the set.** "It's just the best. That's the best green common, one of the best commons if not the best common overall... it wasn't close. I would happily take Spineseeker Centipede first pick." 1G 2/1: search your library for a basic land and put it in your hand; with Delirium it gets +1/+2 and vigilance. "You'd already play it, but then sometimes they turn into 3/3 vigilances in the middle of the game." It is simultaneously a fine two-drop, a splash enabler, and a Delirium payoff — **and it is the most flexible first pick in the format**, keeping GU, GB and GR all open.
- **Threats Around Every Corner** — 3G uncommon enchantment. ETB manifest dread; then whenever a face-down permanent enters under your control, search for a basic and put it onto the battlefield tapped. "Basically a Solemn Simulacrum — you paid four mana, got a 2/2, got a tapped land, but also when you manifested other times, you would get more." Snowballs into "overwhelming them in the mid-to-late game."
- **House Cartographer** — do not take it. 1G 2/2 with survival: land-fetch to hand at second main if tapped. "This card always played way worse than it looked. The survival cards really really did."
- **Cautious Survivor (?)** — named only by description ("a four-mana 4/4 survivor that if it's tapped you gain two life"). Cited as an example of the format's bad four-drops.
- **Anthropede** — **D.** Four mana 3/4 reach with a discard-a-card or pay-2-destroy-a-room mode. "So sometimes it did something." One of the three consecutive unwanted four-drops in the cracked pack.

### Multicolor / gold
- **Gremlin Tamer** (WU) — the Azorius signpost uncommon and a core WU card. 2/2 for WU; makes a 1/1 whenever you play an enchantment or unlock a room. "They just do all the things you want in this deck."
- **Inquisitive Glimmer** (WU) — the other core WU uncommon, same cost. 2/3 that makes your enchantment spells cost 1 less.
- **Oblivious Bookworm** (GU) — **"one of the best uncommons in the set"** and "one of the better first picks." 2/3 that loots on your turn, but you skip the discard if you played or flipped a face-down creature. "Turn 2 Bookworm, turn 3 manifest, you just drew a card in a turn. Incredible card." Also the marquee blue splash for a RG Delirium deck.
- **Disturbing Mirth** (BR) — the Rakdos payoff and "a really sick one." An enchantment; ETB, you may sacrifice an enchantment or creature to draw two, and when *it* is sacrificed you manifest dread. LSV's line: sac an Innocuous Rat or Clockwork Percussionist to it, then later sac Mirth itself to another outlet — **"for two mana you got two cards, a death trigger and a 2/2 manifest. It was an incredible deal."** Marshall: "that was one of the great payoffs, because nobody else wanted that card."
- **Wildfire Wickerfolk** (RG) — 3/2 with haste, trample, and +1/+1 with Delirium, **and it is an artifact creature**. That last line is the point: it enables the Delirium it also rewards. "What's so sick about that card, it was also an artifact — so you'd play it and it would die and now suddenly you have two types in your graveyard for other Delirium cards."
- **Baseball Bat** (WG) — the Selesnya Survival marquee uncommon. "Had a very low win rate." The clearest single data point on why Selesnya is the bottom archetype.
- **Skullsnap Nuisance** (UB) — the Dimir signpost. 1/4 flier; surveil 1 whenever you play an enchantment. "It was just okay."
- **Smoky Lounge // Misty Salon** (UR) — the Izzet rooms driver. 2R front half: adds {R}{R} at the start of your main phase, spendable only on casting or unlocking rooms — "a Sol Ring just for rooms. Powerful." The back half makes an X/X flier where X is the number of rooms you have unlocked. Real power, wrong archetype: the rooms deck was too slow.
- **Rite of the Moth** (WB) — the WB Reanimator payoff: four mana to reanimate, with flashback for six. The card is fine; the archetype around it was too fragile to start in.

### Colorless / artifacts

- *Nothing in this category is discussed in the episode.* The two artifacts LR names (Piggy Bank, Clockwork Percussionist) are red cards and appear under Red; Marina Vendrell's Grimoire is a blue card and appears under Blue.

### Lands
- **Abandoned Campground** (and its full cycle of common duals) — "totally fine. Obviously you don't really want to first-pick one, but they were good." Enters tapped unless a player has 13 or less life, "which some in the middle of the game started to not be tapped, which was great." Part of why the green midrange decks splash freely.

## Crack-a-pack — the one worked pick in the episode

The full pack, with LR's stated ordering — the only explicit pick-order signal in the source:

**Take: Piggy Bank** (> Tunnel Surveyor > Ghostly Keybearer > everything else). LSV: "I would take Piggy Bank leaning towards red-green, but if red-black or red-white presented themselves, I'd be okay."

Rest of the pack: Get Out (foil), Abandoned Campground, Twist Reality, Cackling Slasher (D), Anthropede (D), Ripchain Razorkin (D), Tunnel Surveyor, Unsettling Twins, Fear of the Dark, Appendage Amalgam, Ghostly Keybearer, House Cartographer, Marina Vendrell's Grimoire (rare).

The pack is itself the evidence for the four-drop warning: Cackling Slasher, Anthropede and Ripchain Razorkin are three consecutive four-mana creatures, none of which either host wanted.

## Caption garble

Auto-caption corrections applied, for auditability:

| Transcript | Corrected |
|---|---|
| "Duskborn" / "Duskmoren" | Duskmourn |
| "Spinecleaper Centipede" / "Spine seeker centipede" | Spineseeker Centipede |
| "meat locker set ground diner" | Meat Locker // Drowned Diner |
| "Grotesque Tamers" | Gremlin Tamer |
| "Ripchain Razor Cane" | Ripchain Razorkin |
| "Marina Vantress' Grimoire" | Marina Vendrell's Grimoire |
| "Rite of the Serpent" (in the WB reanimator context) | Rite of the Moth |
| "the wicker folk" | Wildfire Wickerfolk |
| "Smokey Lounge" | Smoky Lounge // Misty Salon |
| "Skull Sap Nuisance" | Skullsnap Nuisance |
| "cursed rat" | Innocuous Rat |
| "Final Fantasy" (in "if you first pick a final fantasy") | Final Vengeance |
| "John slash Sultai" / "Jund slash Simic" | the green-based Delirium/graveyard midrange decks (BG/GU/RG/Temur) |
| "nogged them for four" | knocked / hit them for four |
| "the room that gave all your attacking creatures +1/+0" | Painter's Studio // Defaced Gallery **(?)** — unresolved |

## Source episodes

- 2025-10-10 — Limited Resources 824 – Duskmourn and Modern Horizons 3 Refresher (`iNzFEJvQidg`) — **Duskmourn half only; the Modern Horizons 3 half is out of scope for this file.**

**Not available for this set:** Set Review: Commons & Uncommons, Set Review: Rares & Mythics, Format Overview, Sunset Show. See the coverage warning at the top.
