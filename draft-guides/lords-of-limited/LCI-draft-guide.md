# The Lost Caverns of Ixalan (LCI) — Draft Guide

> Synthesized from 6 Lords of Limited episodes (transcripts in `data/subs/lords-of-limited/LCI/`). This guide is the lead lens that **decodes** the 17Lands data — every GIH WR is archetype-conditional (trust where it transfers, discount where it inflates; see AGENTS.md). This guide is secondary color for decision-making.

## ⚠ Recency rule (read first)

- Notes span **2023-11-10 → 2024-01-24**. On any conflict, the **newest episode wins**.
- The **2023-11-10 early-access draft battle** is the weakest source — it's the hosts' very first draft of the format, zero reps beforehand. Evaluations from that episode are first-impressions only; treat as hypotheses.
- The **2024-01-08 "Redesigning Cards for LCI"** episode is the most analytical and critical — a format post-mortem where the hosts identify what worked and what didn't. It is the most authoritative source for format-level reads.
- The **2023-12-04 "Is Black the Worst Color?"** pod episode is the midpoint analysis and the most useful archetype-building reference — both hosts had played heavily and had settled reads on archetypes.
- **This guide decodes the 17Lands data rather than ranking beneath it.** Every GIH WR is archetype-conditional — use the guide to tell which archetype's deck a number came from: trust the WR where it transfers (cleanly-castable cards), discount it where it inflates (payoffs/multicolor). See AGENTS.md.

## Source timeline

| Date | Episode title | Phase | Weight |
|------|--------------|-------|--------|
| 2023-11-10 | Draft Battle — LCI Early Access Event | Early access / preview (blind first reps) | Weakest — first-ever draft impressions |
| 2023-11-16 | HELP I NEED MORE REMOVAL!!! - LCI Draft | Early (first days of Arena release) | Low-medium — early reps, opinions forming |
| 2023-11-29 | Arena Open Day 2 Draft 2 — Lost Caverns of Ixalan | Early-mid (competitive play) | Medium |
| 2023-12-04 | Is Black the Worst Color in LCI??? | Mid-format analysis pod | High — settled reads on archetypes and format shape |
| 2024-01-08 | Redesigning Cards for LCI Limited!!! | Late / retrospective — format post-mortem | **Decisive — most authoritative overall read** |
| 2024-01-24 | Arena Open Day 2 Draft 1 — LCI | Late competitive | High — late-format, high-stakes drafting |

## TL;DR meta read

- **Format speed: faster than it looks, but not blisteringly so.** The "format starts on turn one" framing from early weeks is true but was over-applied. Slow control decks (blue-black descend, caves) are real and competitive once you understand the format's shape. Still: never be the deck without early plays.
- **Best colors: Blue #1, Red #2, White and Black tied for #3, Green last.** Blue is highly flexible and pairs well with most colors. Green is strictly bad with Blue (blue-green was the worst archetype by data) and requires a clear plan (dinos or descend).
- **Three pillars: (1) artifact/tempo decks (blue-white, blue-red), (2) dinosaur beatdown (red-green), (3) black-based descend control (black-blue best, black-green second).** Caves is a real cross-archetype tool for control/descend decks, not a standalone archetype.
- **Craft is the most influential mechanic**, far ahead of explore, discover, and descend in terms of raw format impact. Descend requires the most work and the longest games.
- **Key mechanic trap: explore on non-evasive creatures.** River Herald Scout is a good Magic card that is actively bad in this format because you want the +1/+1 counter, not the land — and on a non-flyer, missing the counter is devastating. Shipwreck Sentry (always a 3/3) outperforms River Herald Scout here.
- **Removal depth: white has the best cheap interaction** (spring-loaded saw blades, cosmic blast, dead weight in black). Dead weight and tithing blade together cover the early + mid game. Black struggles to answer big threats with dead weight alone — plan for it.
- **Descend does NOT count tokens.** This is a major intuition fail; design around it, not around token generation.

## Archetype / color-pair tiers

Ranked by the 2023-12-04 and 2024-01-08 episodes (most authoritative). Data reference: per the hosts, all four of White's color pairs clustered near the top of trophy rates; blue-green sat alone at the bottom.

| Pair | Colors | Tier | Game plan | Key commons/uncommons | Notes |
|------|--------|------|-----------|----------------------|-------|
| **Azorius** | WU | **S** | Tempo/craft — low curve evasive threats, craft them into late-game wins. Blue provides flexibility; white provides cheap interaction + pump. | Waterwind Scout, Spring-loaded Saw Blades, Cogwork Wrestler, Spy Glass Siren, Ruin Lurker Bat, Clay-Fired Bricks (uncommon), Master's Guide Mural (rare) | Best archetype per data. Clay-Fired Bricks lets you win early AND late — strongest single craft card. Master's Guide Mural is a late-game bomb only; don't splash in blue-black. |
| **Izzet** | UR | **A** | Artifact-aggro: pirates + artifacts, Captain Storm Cosmium Raider as signpost, flip craft cards into threats. | Captain Storm Cosmium Raider, Goblin Tomb Raider, Plundering Pirate, Dowsing Device, Zoetic Glyph | Very powerful when on plan, fragile if not. Goblin Tomb Raider + artifact density is key. |
| **Boros** | RW | **A** | White aggro with red dinos or burn support. Low curve, wide board. | Spring-loaded Saw Blades, Miner's Guide-Wing, Ironpaw Aspirant, Burning Sun's Cavalry, Staggering Size, Ancestor's Aid | Strong but must commit to aggro — the "half-committed white deck" is where players lose most. |
| **Jund** | BRG | **A** | Black descend + red/green dinos. Best three-color combination. Defossilize/recursion recurs Palani's Hatcher. | Defossilize, Dead Weight, Palani's Hatcher (rare), Chupacabra Echo, Ancestor's Aid | Three-color is fine if built around. Jund is the hosts' most common three-color combination. Black provides recursion; green/red provides the threats. |
| **Dimir** | UB | **A** | Turbo self-mill descend control — best descend shell. Blue fills graveyard, black recurs bombs. | Deep Cavern Bat, Death-Cap Marionette, Another Chance, Chupacabra Echo, Skull-Cap Snail, Sage of Days, Hoverstone Pilgrim | Most played descend deck at high levels. Bat is the #3 or better uncommon in the entire set. |
| **Golgari** | BG | **B+** | Descend midrange — mill two creatures, recur them, outlast. | Death-Cap Marionette, Another Chance, Defossilize, Chupacabra Echo, Corpses of the Lost, Calamitous Cave-In | Second-best descend shell. Slower to assemble. |
| **Gruul** | RG | **B+** | Dinosaur beatdown — low curve aggressors into big dinos, staggering size closes. | Burning Sun's Cavalry, Armored Kincaller, Staggering Size, Ancestor's Aid, Pathfinding Axejaw, Hulking Raptor, Earthshaker Dreadmaw (rare) | Best version is low-to-ground + staggering size, not ramp-heavy. Burning Sun's Cavalry is the key card (not on radar week one). |
| **Rakdos** | BR | **B** | Attrition/descend, NOT aggro. Sahil's Lattice discard engine, Volatile Wander-Glyph. Sacrifice-based value. | Sahil's Lattice, Fanatical Offering, Zoyowa Lava-Tongue, Plundering Pirate, Acolyte of Aclazotz, Dead Weight | "Black cannot be aggressive" — must be framed as attrition, not beatdown. Zoyowa is an attrition card, not an aggro card. |
| **Orzhov** | WB | **C+** | Sacrifice/descend hybrid — risky, easy to end up "half and half" with mediocre white aggro + mediocre black descend. | Ruin Lurker Bat, Sanguine Evangelist, Deep Cavern Bat, Dead Weight, Tithing Blade | Very punishing if 4-5 cards are misaligned. Hosts ran this and called it their biggest trap archetype. Black can't do white's aggressive job. |
| **Simic** | GU | **D** | Explore value — River Herald Guide + explore synergies. | River Herald Scout, River Herald Guide, Murol (rare), Cave Diver | **Worst pair in format by data — avoid.** Green and blue's synergies don't overlap. Blue-green explorer was a failed archetype. |

## Format principles

1. **Commit early and draft a cohesive plan.** This format has very little overlap between archetypes — the three pillars (artifact/tempo, dinos, black descend) do not bleed into each other well. Blue is the only color where you can stay flexible late. Once you have Palani's Hatcher or Resplendent Angel, commit to that plan; don't hedge.

2. **Craft first, flip when convenient.** The best craft cards (spring-loaded saw blades, clay-fired bricks) don't need to flip to be good — they stand on their own. Tithing Blade is great because of the edict, not because you're flipping it. Once you stop expecting to flip it and just play it as a removal spell, it becomes much better.

3. **Get on the board early.** Take two-drops aggressively. A "two-drop" is also a "four-drop" (craft it later), so cheap plays double-dip on curve and late-game. Compass Gnome was one of the most-played cards across all these videos and consistently overperformed.

4. **Descend ≠ tokens.** Tokens do not count toward descend. You need CARDS in the graveyard (permanents). Design your descend deck around self-mill (Death-Cap Marionette, Another Chance, Sage of Days), not tokens.

5. **Black = control, not aggro.** Never draft black as an aggro color. Dead weight + tithing blade + Chupacabra Echo is the core of the black plan. If you find yourself putting Miner's Guide-Wing in a black deck, stop and reconsider.

6. **Blue-green is a trap.** The data confirms it — worst color pair. Blue explores want +1/+1 counters, green explores want +1/+1 counters, and neither color's cards cooperate. Shipwreck Sentry is better than River Herald Guide here because Sentry is always a 3/3. If you find yourself in green-blue, look for a pivot.

7. **Caves as a backdoor, not a plan A.** Don't pack-one-pick-one Calamitous Cave-In. Draft your normal signals; note caves going late; if you see Calamitous Cave-In around pick 6-9, build the package. You don't need many caves (5-7) if you have Compass Gnomes and Scampering Surveyors to find them. Cave-In is a sweeper — the best control payoff — but requires the game to go long, which means you need other control elements first.

8. **Hidden lands (cave ETB lands) help you splash anything**, especially in the caves/control shell. The Sunken Citadel tap-for-any-color-with-caves makes splashing almost free. Use this to take powerful off-color bombs.

9. **Removal ratios in black control:** roughly 3 dead weights, 2 tithing blades, 1-2 join the deads is the right skeleton. Dead weight handles the one/two-drops; tithing blade handles the three/four-drops (doesn't need to flip); join the dead handles bombs and larger threats. Don't zero out on join the dead.

10. **Explore on flyers is high-variance.** Spy Glass Siren and Waterwind Scout making map tokens on a one/two-drop flyer is feast-or-famine: hit the +1/+1 counter and your flyer is dominant; miss and you drew a land with a mediocre body. Opponents in the same color are likely to hit too. Account for this variance in evaluating "good draws" vs "bad draws" in the blue-white matchup.

11. **White's late-game weakness.** White can't win the late game — it must commit to ending the game fast. If you have a white deck that isn't hyper-aggressive, you are likely to lose to medium dinosaur decks that just have 4 and 5 power creatures when your stuff has 1 and 2 power. Petrify and combat tricks can look bad against big dinos — sideboard them out.

12. **17 or 18 lands.** Caves decks often want 18 because they have mana sinks and need to hit multiple caves. Aggressive white/red decks can run 17. With triple River Herald Guide or similar explore engines, 16 is sometimes correct in green.

## Card notes (community consensus)

Later episode takes override earlier ones. (?) = garbled card name in captions; best-guess translation provided.

### White
- **Spring-loaded Saw Blades** — Premium common in almost every white deck. 1-mana Flash instant deals 5 to a tapped creature, then crafts into a 5/5 Chariot vehicle. One of the best craft cards in the format; splashable. (All episodes)
- **Cosmic Blast** — 1W instant, deal 4 to attacking/blocking creature. Excellent cheap instant-speed removal. Key piece for white control. (xKoK8XV06z8)
- **Miner's Guide-Wing** — 1W one-one flying lifelink, put +1/+1 counter on ETB. Overrated early; correct to take in dedicated white aggro, bad in defensive white. Don't put in control shells. (xKoK8XV06z8)
- **Ironpaw Aspirant** — 1W 1/2, ETB put +1/+1 counter on a creature. Good in white aggro. (TC_1yV79T0g)
- **Petrify** — Decent removal but poor against big dinosaurs. Sideboard out in game 2 against dino decks. (TC_1yV79T0g, xltOJRS53JU)
- **Ruin Lurker Bat** — Single white, 1/1 flying lifelink, scry 1 if you descended. Good in aggro; problematic in that players use it as an aggro card rather than an attrition card. Design failure — the descend part doesn't matter, the 1/1 flying lifelink does. Should be nerfed per the hosts. (tArZTyQfiYw)
- **Old-Growth Cloud Guard (?)** — ~3W 3/2 flyer + makes a 1/1. Hosts call it too good and want it nerfed to 3/1 flyer. Still one of white's best commons. (tArZTyQfiYw)
- **Clay-Fired Bricks** — 1W artifact, searches a plains, gains 2 life, crafts into Cosmium Kiln which makes two 1/1 gnomes + pumps tokens. Hosts called it "egregious" — lets white decks win early AND late. If your opponent resolves this on turn two, it's very hard to come back. (xKoK8XV06z8, tArZTyQfiYw)
- **Quicksand Whirlpool** — 5W instant, Exile target creature (3 cheaper if tapped). Premium white removal for control decks. (xKoK8XV06z8)
- **Resplendent Angel** — 1WW 3/3 flyer, make a 4/4 Angel token at end step if you gained 5+ life. One of white's best rares; commit to white after picking this. (xKoK8XV06z8)
- **Helping Hand** — Return another target permanent to owner's hand. Flash/ETB synergy, especially good with explore (bounce your cash). (TC_1yV79T0g)
- **Vanguard of the Rose (?)** — 1W 3/1, sac artifact/creature to give target creature indestructible. Sacrifice outlet for descend and artifact synergies. (xltOJRS53JU)
- **Sanguine Evangelist** — 2W 2/1 battlecry, ETB/dies makes 1/1 black bat token with flying. "Incredible" — especially in any white deck running bats or needing air presence. (TC_1yV79T0g)

### Blue
- **Waterwind Scout** — 1U 2/2 flyer, ETB make a map token. One of the best blue commons; extremely high-variance (hit the +1/+1 counter and dominant, miss and mediocre). Hosts want to nerf to 0/1 or 1/1. (All episodes)
- **Spy Glass Siren** — U 1/1 flyer, ETB make a map token. Same package as Waterwind Scout on a one-drop; busted when it connects. Hosts want to nerf to 0/1. (kv6e2NAGCz4, tArZTyQfiYw)
- **Cogwork Wrestler** — U 1/1 flash, ETB target creature gets -2/-0 until end of turn. Flash + body + pseudo-interaction; synergizes with artifacts. Acceptable nerf target but not outright broken alone. (tArZTyQfiYw)
- **Master's Guide Mural** — 3WU artifact, ETB make a 4/4 Golem token, crafts into a factory that makes 4/4s. Busted late-game win condition for blue-white. Do NOT splash in blue-black — you won't have enough artifacts or white mana to craft it. (TC_1yV79T0g, xKoK8XV06z8, tArZTyQfiYw)
- **Zoetic Glyph** — 2U enchantment, enchanted artifact is a 5/4, when Glyph leaves discover 3. Mythic uncommon — triggers on ANY way Glyph leaves, not just when the creature dies. "Pretty bad" design per hosts. Still very strong. (kv6e2NAGCz4, tArZTyQfiYw)
- **Sage of Days (?)** — 2U 3/2, mills three, keep one. Key blue piece in blue-black descend for proactively filling the graveyard. (xKoK8XV06z8)
- **Hoverstone Pilgrim (?)** — Artifact 2/5 flyer, Ward 2, pay 2 to bottom a graveyard card. Ward protects it; pairs with Black's recursion to bottoming opponent's grave. Very strong in blue-black self-mill. (xKoK8XV06z8)
- **Staunch Crewmate (?)** — 1U 2/1, ETB look at top 4, reveal artifact or pirate to hand. The "best card in the pack" in a vacuum at P1P1 if you're in blue artifacts; take it over off-color cards. (xKoK8XV06z8)
- **Captain Storm Cosmium Raider** — 2RW 2/2, whenever an artifact ETBs put +1/+1 counter on target pirate. Blue-red signpost; gets out of hand fast. Hosts want to nerf to once-per-turn trigger. (kv6e2NAGCz4, tArZTyQfiYw)
- **River Herald Scout / River Herald Guide** — U 1/2, ETB explore. Good Magic card that is bad in this format. You want the +1/+1 counter (not the land) and even then a 1/3 doesn't tussle well. Hosts describe as the most instructive card for why the format doesn't work the way expected. Only worth it in the explore package. (xKoK8XV06z8, tArZTyQfiYw)

### Black
- **Deep Cavern Bat** — B 1/1 flying lifelink, ETB target opponent discards a card. Hosts call it #3 uncommon overall (or better). "Backbreaking" — disruption, pressure, and defense for 2 mana; the core of the black control plan. Synergizes with Another Chance (cast it again). (xKoK8XV06z8, kv6e2NAGCz4)
- **Dead Weight** — B enchantment, -2/-2. Black's best common. Excellent cheap interaction that also adds a permanent to the graveyard for descend. Pair with tithing blade to cover all mana values efficiently. (xKoK8XV06z8, all episodes)
- **Tithing Blade** — 1B artifact, ETB each opponent sacrifices a creature. Don't plan to flip it; you won't have time. The edict effect is what matters, plus the artifact rectangle in the graveyard for descend/craft. (xKoK8XV06z8, tArZTyQfiYw)
- **Death-Cap Marionette** — 1B 1/1 deathtoucher, ETB mill 2. "Most important card in the descend archetype" — single-handedly mills permanents, trades with big dinos (deathtouch), enables Another Chance loops. (xKoK8XV06z8)
- **Another Chance** — 2B instant, mill 2 then return two creature cards from graveyard to hand. The key late-game recursion engine. In ideal descend decks: mill with marionette → Another Chance gets marionette back → repeat. (xKoK8XV06z8)
- **Chupacabra Echo** — "Ravenous Chupacabra as a 3/2." 4B creature. Destroys target creature. Hosts call it "broken" and "completely illegal." If you're in black control, take every one. (xKoK8XV06z8)
- **Skull-Cap Snail (?)** — B 1/1, ETB opponent exiles top card. Budget Deep Cavern Bat — not nearly as good, but part of the hand disruption package. Goes up in value when you have Another Chance (recast it). (xKoK8XV06z8)
- **Join the Dead** — 3B instant, destroy target creature. Handles threats that dead weight misses (3+ toughness, big dinos). Hosts want 1-2 copies, less than dead weight. (xKoK8XV06z8)
- **Defossilize** — 4B sorcery, return creature from graveyard to battlefield, it explores twice. Pairs perfectly with Palani's Hatcher for Jund builds; one of the best recursion spells. (xKoK8XV06z8)
- **Grasping Shadows** — Black instant, destroy target creature. Good removal; hosts noted it alongside bitter triumph as a P2P1 choice. (xltOJRS53JU)
- **Fanatical Offering** — B sorcery, sacrifice a permanent, draw two. "Two-mana draw two" effectively when you sacrifice a treasure, map token, or artifact. Excellent in the red-black shell. (TC_1yV79T0g, xltOJRS53JU)
- **Acolyte of Aclazotz** — 1B 1/4, sacrifice creature or artifact to drain 1 and gain 1. Sacrifice outlet that generates descend AND provides life. (TC_1yV79T0g, xltOJRS53JU)

### Red
- **Plundering Pirate** — 2R 3/2, ETB make a treasure. "Sailor of Means 2.0." Excellent two-for-one in artifact shells and black-red attrition. Enables Fanatical Offering (sacrifice treasure = draw two). (TC_1yV79T0g, kv6e2NAGCz4)
- **Goblin Tomb Raider** — R 1/2, as long as you control an artifact +1/+0 and haste. Key one-drop in artifact-aggro/red-white; less relevant outside that shell. Hosts said it's fine but becomes oppressive alongside Captain Storm. (tArZTyQfiYw)
- **Burning Sun's Cavalry** — 1R 2/2, while you control a dinosaur it gets +1/+1 when attacking or blocking. Key "discovered" card in the dino deck — was not on anyone's radar week one. Synergy with staggering size. (xKoK8XV06z8)
- **Ancestor's Aid** — RG instant, +2/+0 first strike, make a treasure. Win combat, ramp into next dino. Key combat trick for dino aggro. (xKoK8XV06z8)
- **Geological Appraiser** — 2RR 3/2, ETB discover 3 (on-reveal). "Ravenous Chupacabra tier" — one of the best rares. Hosts wanted to take it P1P4 over on-plan uncommons. (xKoK8XV06z8)
- **Sunfire Torch** — Artifact, deal 2 to a creature or player, sac to deal more. Cheap damage, enables descend. Good in artifact shells and as removal for small creatures. (TC_1yV79T0g, xltOJRS53JU)
- **Calamitous Cave-In** — 3R enchantment (cave land), ETB deal X to each creature where X is # of caves you control. THE caves payoff — acts as a Pyroclasm/sweeper, scales with caves. Don't pick high in pack 1; find it at pick 6-9 and build around. With 5-7 caves, consistently clears boards. (xKoK8XV06z8, kv6e2NAGCz4)

### Green
- **Staggering Size** — 1G instant, target creature gets +3/+3 and trample until end of turn. "Best combat trick in the set." Closes games in the dino deck; Ben says he was systematically undervaluing it. (xKoK8XV06z8)
- **Jade-Seed Stones (?)** — 4G sorcery, distribute 3 +1/+1 counters among 1-3 target creatures. Good late-game pump; hosts liked it for green-white aggro. (TC_1yV79T0g, nvr6azpOksI)
- **Hulking Raptor (?)** — Green rare. Big green dino bomb; strong signal to go green when you see it. (nvr6azpOksI)
- **Corpses of the Lost** — Green creature, gets out of hand; strong in green-black. (nvr6azpOksI)
- **Malamet Battle Glyph** — G sorcery, fight + if your creature ETB'd this turn it gets +1/+1. Decent removal spell for green. (nvr6azpOksI, kv6e2NAGCz4)
- **Basking Capybara** — 1G 1/3, gets +3/+0 if descend 4. Hosts said this card is bad in both early AND late game; want to make it a 2/2 or give it reach. Still a serviceable chump blocker in the right shell. (tArZTyQfiYw)
- **Palani's Hatcher** — 3RG 5/3 haste, makes dinosaur eggs that become 3/3s. One of the best non-blue bombs; hosts draft Jund to recur it. P1P1 bomb — commit to it. (xKoK8XV06z8)
- **Pathfinding Axejaw** — Rare dino, likely the signpost green-red rare. Key payoff for dino decks. (xKoK8XV06z8)
- **Earthshaker Dreadmaw** — 4GG 6/6 trample, draw a card for each dino you control ETB. "Incredible magic card" — bomb for green dino decks. (xKoK8XV06z8)
- **Poison Dart Frog** — 1G 1/1, provides mana for dino spells (or ramps). Hosts debated whether it belongs in dino aggro; lean toward it going in the midrange versions that want to hit turn-3 4-drops. (xKoK8XV06z8)
- **Malamet Brawler** — 1G 2/2, when it attacks give another creature trample. Hosts want it to be a dinosaur type or a 3/1 that creates a map token when dealing combat damage. As printed, needs the dinosaur tribal support it lacks. (tArZTyQfiYw)

### Multicolor
- **Zoyowa Lava-Tongue** — BR 2/2 deathtoucher, descend trigger: each opponent may discard or sacrifice, deals damage to those who didn't. NOT an aggro card — frame it as an attrition/grindy control card. (xKoK8XV06z8, tArZTyQfiYw)
- **Cil-Malamet Exemplar (?)** — GW 3/3, when your creatures with greater power than base deal damage you draw. Synergizes with staggering size and +1/+1 counters in green-white. (TC_1yV79T0g)
- **Karakit Sunborn (?)** — RW 4/4, when it attacks tap two other artifact/creatures to discover 3. "Snowbally" bomb that is near-impossible to answer if it untaps. Hosts wanted it to deal 3 damage instead of discover 3. (tArZTyQfiYw)

### Colorless / Artifacts
- **Compass Gnome** — 2 colorless 1/1, ETB find a cave or basic land. Played in almost every game video; consistently overperforms. Enables splashing, fills cave count, blocks early attackers, two-drop craft fodder. "Format all-star." (TC_1yV79T0g, kv6e2NAGCz4)
- **Idol of the Deep King** — 2R 1/1(?), sacrifice to exile a creature with power 2 or less and create a treasure. Removal for small stuff + artifact for craft fodder + descend trigger. (TC_1yV79T0g)
- **Dowsing Device** — Blue-red artifact build-around, pumps artifacts then transforms into a land that taps to pump artifacts. Core of the blue-red artifact engine. (TC_1yV79T0g)
- **Sahil's Lattice** — 2R artifact, rummage (discard/draw) ability; enables red-black discard synergies and Volatile Wander-Glyph combos. (xKoK8XV06z8, kv6e2NAGCz4)
- **Mytic Draft (?)** — 1B artifact, draw a card / lose a life on ETB and on going to graveyard. Hosts want to buff it with a sac ability and mill trigger to help descend. As-is, still playable in black shells. (tArZTyQfiYw)
- **Curator of the Sun's Creation (?)** — Double-discovers using cave lands as part of its triggered ability. Ethan called this "kind of insane" in the caves deck with Calamitous Cave-In. (kv6e2NAGCz4)

### Lands / Caves
- **Calamitous Cave-In** — (see Red section above)
- **Sunken Citadel** — Cave, pay life to tap for any color if you control a cave. "Incredible" as a fixer in the caves deck; enables splashing literally anything. Compass Gnome can find it. (kv6e2NAGCz4)
- **Hidden Lands (e.g., Hidden Volcano, Hidden Necropolis, Hidden Courtyard)** — ETB tapped; can crack later to produce a spell. Provide card advantage in the late game. Not good in very aggressive decks but excellent in control/caves. (TC_1yV79T0g, xltOJRS53JU)
- **Promising Vein** — Cave that can sac to search a basic land. Hosts disliked it (the "pay 1" activation cost is too slow); wanted it to be an evolving wilds cave without the colorless tap. Still worth running 1 copy for fixing in two-color control decks. (tArZTyQfiYw)

### Rares & Bombs
- **Geological Appraiser** — (see Red section) 2RR discover-3 bomb. P1 slam. (xKoK8XV06z8)
- **Resplendent Angel** — (see White section) (xKoK8XV06z8)
- **Master's Guide Mural** — (see Blue section) (TC_1yV79T0g, xKoK8XV06z8)
- **Palani's Hatcher** — (see Green section) (xKoK8XV06z8)
- **Deep Fathom Echo (?)** — Blue rare, 2/2 flyer, explore + become a copy of another creature. Lower priority than the bombs above; best in blue explore shells. (TC_1yV79T0g)
- **Bone Horde Dracosaur (?)** — Red-green rare bomb. "Stone cold oops I win bomb." (nvr6azpOksI)
- **In Brass's Tunnel Grinder** — 3B artifact, discard any number / draw that many +1; each descend turn it gains a bore counter; at 3 counters flip into a discover-X engine per spell cast. Ethan built an entire caves deck around this; extremely powerful if you can protect it to flip. (kv6e2NAGCz4)
- **Throne of the Grim Captain** — "Your rare that was a common for you last format" per Ben. Multi-tribal sac payoff. (xKoK8XV06z8)

## Signals & seat reads

- **Blue open:** if you see Waterwind Scout or Spy Glass Siren going late (pick 5-7), blue is wide open. Both are priority picks in their respective shells.
- **Black open:** Skull-Cap Snail and Dead Weight going late signal black is underdrafted. Deep Cavern Bat should never wheel in a healthy pod; if it does, someone is asleep at the wheel.
- **White contested:** a white common missing at pick 4+ in pack 1 is a sharp signal. Ethan got crushed in game one by white being contested from BOTH neighbors. Respect the signal; don't fight two seats.
- **Red open:** multiple red commons missing from a single pack signals red is overdrafted at the table, or the pack was just weak. Seeing burning sun's cavalry going late means dino-red is open.
- **Green:** green-blue explorer is usually open because nobody wants it — do not take the bait. If green is flowing, look to pair with red (dinos) or black (descend), not blue.
- **Pivot advice:** blue is the only color that lets you stay flexible through mid-pack 1. Other colors commit you to a pillar early. If you take a black bomb, commit to the black descend plan. If you take a dino rare, commit to green-red. The archetypes don't overlap well enough to hedge mid-draft.
- **Caves:** Cave-In and Calamitous Cave-In can wheel in most pods because the caves plan is underrated. Note cave count in your passed packs. If you see 2+ Calamitous Cave-Ins and your deck is even slightly controlly, pivot into the caves package in packs 2-3.

## Supersessions (early-was-wrong, now corrected — NOT live disagreements)

| Early take | Date | Late correction | Date | Verdict |
|-----------|------|----------------|------|---------|
| "Format starts on turn 1; white is aggressive and good; blue-white is the best deck." Overcorrected toward Jesskai-aggro, treating every good format as hyper-speed. | 2023-11-10 | "Format slowed down. Black control is real. Overcorrected on aggro narrative. Blue-white IS best but you need a mid/late game plan too." | 2023-12-04 | **Late take wins.** Early access hyped speed too much. Control decks are competitive. |
| "Burning Sun's Cavalry is unplayable filler; hoping to not play it." | ~2023-11-10 | "Burning Sun's Cavalry is the key card for the dino deck — underrated entirely, now a cornerstone of the archetype." | 2023-12-04 | **Late take wins.** The dino two-drop you curved early aggro on was actually the key piece. |
| "River Herald Guide is great — one of Ben's best blue two-drops." | 2023-11-10 | "River Herald Guide is fine but the problem is you're hoping to hit a +1/+1 counter on a non-evasive 1/2, which is backwards. Shipwreck Sentry is better as a 3/3 every time." | 2023-12-04 | **Late take wins.** Guide went from being positive to being called out as the exemplar of what's wrong with explore in this set. |
| "Green is an interesting color; could be fine with explore." | 2023-11-10 | "Green is worst color. Blue-green is the worst archetype by data — it's almost alone at the bottom of trophy rates." | 2023-12-04 | **Late take wins.** Green got steadily worse in evaluation as the format settled. |
| "White is tied for #1 with Blue." | 2023-12-04 | "White is #3 — it has really low-statted creatures, weak uncommons, and loses the late game vs every other color. Amaz's tweet put it in perspective: avoid white or fully commit to aggro." | 2024-01-08 | **Late take wins.** White was downgraded from "tied with blue" to "third color." |
| "Sanguine Evangelist / the white 3W 3/3 angel-maker — that's garbage." (Ben's early instinct was negative) | 2023-11-10 | "Sanguine Evangelist is incredible — I feel bad saying it was garbage." (Ben corrects himself during gameplay) | 2023-11-10 (same video, post-game) | **Immediate self-correction within the early-access video.** |

## Live disagreements (genuine, unresolved)

- **Pit of Offerings:** Ben thinks it's playable/strong in control shells; Ethan called it "quite playable" in their crash course but then hedged during actual draft picks. No settled verdict across the sampled episodes.
- **Descend threshold design:** Ben thinks the thresholds (4 and 8) are close to right; Ethan thinks reducing them to 3 and 6 would have made descend competitive without being broken. Minor philosophical disagreement.
- **How good Caves really is as an archetype:** Ethan advocated for it more aggressively (built an entire Arena Open deck around it); the 2024-01-24 video shows Ethan going 0-3 with the caves deck. Ben was more skeptical. Both agree Calamitous Cave-In is the linchpin; disagreement is on floor vs ceiling.

## Card-name caveats from caption garble

The following card names were garbled in auto-captions and are reconstructed from context:

- "Gargantuan leech" — likely **Gargantuan Leech** (GW 6/6 cave payoff)
- "Chupacabra Echo" — correctly identified; also called "Ravenous Chupacabra" by hosts when they forget the name
- "Kali's Dawn Runner / Cali's Lattis / Sahil Lattice" — likely **Sahil's Lattice** (red artifact rummager)
- "Cavernous Ma" — likely **Cavernous Maw** (?)
- "Brood rage mid" / "Mytic Draft" — **Brood Rage Mid** likely "Brood Rage Myceloid" (?), Mytic Draft likely **Mytic Draft** (an artifact)
- "Zoa / Zoa lava tongue" — **Zoyowa, Lava's Tongue** or similar
- "Enenbach" / "UK Benach" — likely **Oaken Siren** or similar blue common
- "Forgotten Des send" — likely **Forgotten Depths** (?)
- "Dino tomaton / Dino tomato" — likely **Dinotomaton** (?)
- "Sunbird standard" — garbled, unclear
- "Geological appraiser" — correctly identified, confirmed as a real card
- "Bone horde dracosaur" — likely **Bonehoard Dracosaur** (rare)
- "Selekti stalker" — likely a green creature, unclear exact name
- "Oltec cloudguard" — likely **Oltec Cloud Guard**
- "Kaat scavenger" — likely a black 3/2 with descend recursion
- "Didactic echo" — unclear
- "Brine fang" — likely **Brine Fang** (?)
- "Screaming Phantom" — likely **Screaming Phantom** (?)

## Source episodes

- 2023-11-10 — ☠ DRAFT BATTLE ☠ - LCI Early Access Event #sponsored (TC_1yV79T0g)
- 2023-11-16 — HELP I NEED MORE REMOVAL!!! - LCI Draft (xltOJRS53JU)
- 2023-11-29 — Arena Open Day 2 Draft 2 - Lost Caverns of Ixalan! (nvr6azpOksI)
- 2023-12-04 — Is Black the Worst Color in LCI??? (xKoK8XV06z8)
- 2024-01-08 — Redesigning Cards for LCI Limited!!! (tArZTyQfiYw)
- 2024-01-24 — Arena Open Day 2 Draft 1 - LCI (kv6e2NAGCz4)
