# Murders at Karlov Manor (MKM) — Draft Guide

> Agent-primary reference, synthesized from 6 Lords of Limited episodes (per-episode notes + transcripts in `sources/`). Treat as expert/theory opinion — weight it like a CGB grade; **17Lands GIH WR stays primary**. Source episodes from 2024-01 → 2024-03 (MKM's original release); cards are identical in the 2026 Quick Draft re-run.

## ⚠ Recency rule (read first)

- Notes span **2024-01-22 → 2024-03-25**. On any conflict, the **newest video wins**.
- The **2024-01-22 preview** is BLIND PREDICTIONS (no games played) — weakest; treat its evaluations as hypotheses, not data.
- The **2024-03-25 retrospective "Gone Too Soon"** is the MOST AUTHORITATIVE source — it's the hosts' final, fully-informed verdict. When it disagrees with earlier notes, the retro wins.
- **17Lands GIH WR stays primary over all of this.** This guide is expert/theory color, not data. If live win-rate data contradicts a take here, trust the data.

## Data caveat for the 2026 Quick Draft re-run

**IMPORTANT (coaching agent, read this):** This is a Quick Draft re-run (June 8–16 2026). Early in the window — and possibly the whole window — 17Lands **QuickDraft** data for MKM may be empty (0 games) or extremely thin. When QD data is sparse/missing, **proxy with MKM's original PremierDraft window: query 17Lands with `start_date=2024-02-01`** until live QD win-rates populate. QD and Premier metagames differ slightly (QD is bot-drafted, generally a touch slower / more forgiving, signals are weaker), but card-level GIH WR transfers well enough to be the primary signal. (Source: project memory / standing directive.)

## Source timeline

| Date | Episode | Phase | Weight |
|------|---------|-------|--------|
| 2024-01-22 | Preview Season | BLIND preview — predictions only | Weakest (predictions, mark reality divergence) |
| 2024-01-29 | Solving the Case of MKM | Pre-release crash course (still pre-games) | Low (theory, stats-based) |
| 2024-02-07 | Draft Battle Day 1 | Early, just post-release | Medium (early reps) |
| 2024-03-05 | Arena Open D2 Draft 1 | Late, high-level competitive | High |
| 2024-03-06 | Arena Open D2 Draft 2 | Late, high-level competitive | High |
| 2024-03-25 | "Gone Too Soon" retrospective | Wrap-up / final verdict | **Decisive (most authoritative)** |

## TL;DR meta read

- **Synergy format with a deep, fair rare pool.** You almost always end in one of two camps: (1) you opened/maximized something powerful, or (2) you found and committed to an **open lane**. Prefer finding the open lane. Picks 1–4 have an outsized ripple effect.
- **Speed: midrange-tempo, not hyper-aggro.** Ward-2 disguise 2/2s make 3-mana bodies viable, so the floor on board stalls is higher than a typical aggro format. White wants to **end the game sooner**; green wants to **survive and go long** — pick your win-condition lane early. Boros tempo/aggro is the best deck, but grindy value decks (Simic, Golgari) are right behind.
- **Color power (retro, decisive): White > Green > Red = Blue > Black.** Start White or Green for the most pivot points. Black is real but **fussy/hard to assemble** (last).
- **Archetype power (retro, decisive): Boros (RW) #1, Simic (GU) #2, Azorius (WU) #3.** All 10 pairs playable; format is balanced.
- **Mechanic priorities:** Ward-2 Disguise/Cloak is the defining pillar — it warps removal evaluation (removal must trade *profitably* with a face-down 2/2 OR generate extra value). Investigate/Clues are excellent and everywhere (decks rarely run out of gas). Collect Evidence was a rare *good* late-game mechanic. Suspect is clean but a small slice. Cases are flavor wins, deliberately not busted (pick 4–6 synergy rewards).
- **Want ~3+ efficient removal spells minimum.** Removal is the scarcest resource late in packs; prioritize cheap/instant interaction. Good **two-drops were hard to find; four-drops were everywhere** — prioritize good twos.

## Archetype / guild-pair tiers

Ranked by the **2024-03-25 retrospective** final consensus. (Earlier episodes hyped WU Detectives and UR artifacts as the two best linear decks — see Supersessions; the retro demoted both relative to Boros/Simic.)

| Guild | Colors | Tier | Game plan | Key commons/uncommons | Notes |
|-------|--------|------|-----------|----------------------|-------|
| **Boros** | RW | **S** | Aggro/tempo, go-wide + burn; Battalion-style attacking. End games fast. | Shock, Makeshift Binding, **On the Job** (Overrun-style go-wide payoff, premium), Dog Walker, Perimeter Enforcer, Case of the Gateway Express, Lightning Helix, Meddling Youths | **Best archetype.** Carried by mono-color cards, NOT its signposts. Signposts (Helix, Meddling Youths) good but not the reason it's great. |
| **Simic** | GU | **A** | Grindy value / go-long, Collect Evidence, surveil/self-mill. "Back and so good." | **Projector Inspector** (best blue common), Out Cold (best home), Nervous Gardener, Topiary Panther, Lochthwain Eavesdropper, Esika's Agency Chief | #2 deck. Strong signpost uncommons correlate w/ being a strong pair. Out Cold's best home. |
| **Azorius** | WU | **A** | Detective tempo, low curve, cheap interaction + flyers, go-wide payoffs. | Perimeter Enforcer, Novice Inspector, Projector Inspector, Granite Witness, Seasoned Consultant, **Fuss // Bother** (go-wide payoff), Private Eye, On the Job, Out Cold | Detective tribal "go wide." Low curve enables 17 lands. Often **short on interaction** — don't be shy about bounce/Dramatic Accusation/tricks. |
| **Selesnya** | GW | **B+** | White-core go-wide Disguise, On the Job payoff. | On the Job, Dog Walker (never cut in GW even though worse outside RW), Nervous Gardener, Sworn Sentry-type flip payoffs | "A white deck at its core" — you compromise the green plan more than the white plan. Still very good. |
| **Izzet** | UR | **B** | Artifact/Clue/Thopter sacrifice, fastest + highest-ceiling starts. | Case of the Filched Falcon, Gleaming Geardrake, Gadget Technician, Cryptic Coat, Krenko, Thopter Fabrication | **High risk / high reward** — unbeatable when it curves out, fragile when it doesn't. Filched Falcon is UR-only. |
| **Golgari** | BG | **B** | Graveyard value, self-mill, "leave the graveyard" payoffs, Collect Evidence. | **Chalk Outline** (snap ~pick 7), Insidious Roots, District Onlooker, Leering Onlooker, Aftermath Maverick, Vitu-Ghazi Inspector, Murder | Build-around (Roots/Outline) is fussy — needs high creature count + multiples + "creatures leaving yard." Real deck. Black's removal density is underrated. |
| **Orzhov** | WB | **C+** | Pint-size / "power 2 or less" + go-wide aggro. | Wisp-Drinker Vampire, Inside Source, Neighborhood Guardian, Case of the Gateway Express, Slimy Dualist, Sanguine Savior | Below the gap. Black being weak/fussy holds it back. Tight cheap aggro that can get under rare-heavy decks. |
| **Gruul** | RG | **C+** | Big Disguise, ramp into flip-up haymakers. | Greenbelt Radical, Nervous Gardener, red/green disguise bodies | Below the gap. Disguise as a primary plan underwhelms vs faster/grindier decks. |
| **Rakdos** | RB | **C** | Suspect aggro, sacrifice, Detective's Satchel value. | Rune-Brand Juggler, Detective's Satchel, Cranko, Connecting the Dots (mostly RB gold), Case of the Crimson Pulse | Below the gap. Can be a powerful grindy splash deck (double Satchel + Cranko + Thopters) but the *pair* underdelivered. |
| **Dimir** | UB | **C** | Clues control / "mediums" grind, Deadly Cover-Up. | Fairy Snoop (Faerie Snoop), Long Goodbye, Leering Onlooker, Deadly Cover-Up (best home) | **Worst pair** per retro. Pure control is hard because everyone has Clue card-advantage. Snoop is flexible but diminishing returns. |

## MKM format principles

- **Ward-2 Disguise is the defining mechanic — re-evaluate ALL removal through it.** A face-down creature is a ward-2 2/2; cheap removal must either (a) trade *profitably* with it (Shock, Long Goodbye, Slice from the Shadows, Extract a Confession edict) or (b) give you something extra (Makeshift Binding gains 2 life, Bite Down on Crime collects evidence, Case of the Burning Masks draws). Naked "deal 3 to one creature" loses value because of the ward-2 tax.
- **Removal that bypasses ward is premium:** fights/bites (Bite Down on Crime), edicts (Extract a Confession), and -X/-X (Slice from the Shadows) sidestep ward 2 because they don't target the creature for damage/destruction at full ward cost the same way.
- **Removal is sorcery-heavy (13 of 22 are sorceries) → instant-speed removal is at a premium:** Shock, Lightning Helix, Long Goodbye, Galvanize, Make Your Move, Out Cold.
- **Shock is excellent: ~46% of creatures are toughness-2,** and there is NO removal that punishes 1-toughness specifically (raises X/1 threats like Dog Walker). But efficient removal is "disparate" — great vs small creatures, weak vs rares/bombs (Aurelia/Kaya). **Have a plan for big threats.**
- **Want ~3 efficient removal spells minimum** (more depending on plan). It's the scarcest late-pack resource.
- **Don't over-prioritize Disguise/Cloak as a plan.** Disguising on turn 3 trades evenly on mana but isn't strongly punished, so it's fine *curve filler* — but it's mostly filler beyond premium hybrids (Dog Walker). Deploy face-down on 2/3 only when you'd otherwise do nothing. Red disguise bodies (5/4, the 3/2-makes-a-Thopter) are reasonable LATE filler — don't reach.
- **Investigate/Clues are everywhere and excellent** — decks rarely run out of gas. Great mana sinks. This also makes **pure control harder** (aggro has card advantage too). Novice Inspector (Thraben Inspector reprint) is a star and splashable.
- **Collect Evidence (CE):** a rare *good* late-game mechanic — competitive and fun. You DON'T need to build the whole deck around it; even small inclusions (Bite Down on Crime, Vitu-Ghazi Inspector) leverage it. **Distinguish CE from self-mill** — much graveyard fuel comes from self-mill creatures, so the "need tons of creatures for CE" rule is often relaxed. Split cards juice CE (cast cheap half; the other half's MV counts as evidence).
- **Cases:** all uncommon, mostly archetype-specific synergy rewards at picks 4–6, deliberately not busted. Best non-rare: **Case of the Gateway Express** (white go-wide, won't wheel). Case of the Filched Falcon is UR-only. Case of the Locked Hot House has huge range (dead sometimes, game-winning others).
- **Suspect** (menace + can't block until it leaves/un-suspected): clean on offense (push attackers) and defense (shut off a blocker), but a small slice. Beware suspecting *wrong* (e.g. suspecting your own creature targeted by a counter).
- **Mana / fixing: green does the heavy lifting** (no red/blue treasures). **Escape Tunnel is arguably a top-10 common** — best fixing, great for splashes and double-color requirements (ahead of Granite Witness). Worst nonbasics: Public Thoroughfare (mediocre, best in Grixis-ish UR), Scene of the Crime + Branch of Vitu-Ghazi (unplayable).
- **Land count: 17 with a low curve (Azorius tempo); 18 with mana sinks or color-intensive top-end** (WWUU six-drops). Abundant mana sinks (Clues, flipping disguise) support low land counts.
- **P1P1 priorities:** instant-speed removal (Shock, Makeshift Binding, Torch the Witness, Long Goodbye) → flexible hybrid gold commons (Dog Walker) → P1P1 bombs/power (Aelia, Perimeter Enforcer, Esika). Early gold-card picks can feel wasted (one fewer card per pack), so prioritize **on-color flexibility** early; delay the two-color decision and stay deep in one color.
- **Play Booster structure:** more uncommons than commons, multiple rares possible per pack, no guaranteed common of every color (only 4 of 5 colors guaranteed in commons). **The wheel is largely DEAD** — cards you want must come in the first 2–3 picks of a pack; don't bank on wheeling premium cards (e.g. Case of the Gateway Express). Rares/uncommons matter more; drafts feel more varied. Signals from commons read differently (a color absent from commons may just be pack texture).
- **Card-eval framework — "every piece of the buffalo":** evaluate cards by how many synergy boxes they check (surveil/self-mill, creatures leaving yard, collect-evidence-on, investigate, etc.). More boxes = better card. (Topiary Panther / Rubblebelt Maverick are exemplars.)
- **Speed/curve note:** good two-drops were HARD to find, four-drops were everywhere. Prioritize quality twos (Perimeter Enforcer, Seasoned Consultant, Sanitation Automaton); cards like Out Cold/On the Job underperform if you lack enough early plays.

## Card notes (community consensus)

Dedupe across episodes; later/ retro takes win. ⚠ = prediction-vs-reality reversal or over/under-rated flag.

### White
- **Novice Inspector** — Best white common (retro). Thraben Inspector functional reprint; never cut, even splashable. (preview, retro)
- **Makeshift Binding** — Premium white removal (O-Ring + gain 2 life). The "extra value" makes it beat ward-2 evaluation. Ethan's #1 common overall. (02-07, 03-05, retro)
- **Perimeter Enforcer** — Strong white aggressive uncommon, P1-pickable. 1/1 flying lifelink that grows when Detectives ETB / flip up. A key good two-drop. (02-07, 03-05, retro)
- **On the Job** — ⚠ Underrated → premium. Overrun-style go-wide payoff that ties white go-wide decks together; even better drawing a Clue. Better in WU; Out Cold does a similar job — don't sweat which you get. (retro)
- **Inside Source** — Incredible in WB: 3-mana 1/1 that brings a 2/2 token and pumps Detectives. Go-wide engine. (02-07)
- **Neighborhood Guardian** — Solid WB/WU go-wide flyer-anthem piece. (02-07, 03-05)
- **No Witnesses** — WW wrath; a devastating, swingy combat/board blowout. Play around it in close aggro spots. Fair overall (Clues help recovery). (preview, 03-05, retro)
- **Not on My Watch** — ⚠ Preview liked it (exile attacker); retro says **unplayable for white** — wrong timing, opposite of white's proactive plan. (preview → retro)
- **Granite Witness** — Good WU body/fixing-ish hybrid; wheels often (signal the WU lane is open). Escape Tunnel beats it for fixing. (03-05, retro)
- **Call a Surprise Witness** — Value recursion of cheap creatures (WU). (03-05)
- **Aurelia's Vindicator** — Mythic bomb; maybe better than Esika. (retro)
- **Aelia, Ardent Inquisitor** — Clear powerful P1P1 (Boros legend). (03-06)

### Blue
- **Projector Inspector** — ⚠ Best blue common (retro) but repeatedly called **"wildly underrated"** in-format. Investigate-on-attack Detective; excellent w/ go-wide and extra Detectives. Doubling it is great with Analyst. (03-05, retro)
- **Fairy Snoop (Faerie Snoop)** — ⚠ Preview/early hype as a top common; reality = flexible & strong but **mana-hungry, diminishing returns, and NOT great in tempo Detectives.** "Too many Snoops" is real. (preview, 02-07)
- **Out Cold** — 3-mana tap-two + investigate. Strong, but needs enough early plays. **Best home is Simic (GU)**; Out Cold > Lost in the Maze. (preview, retro)
- **Private Eye** — Bounce + tempo; anthem/unblockable Detective payoff. (preview, 03-05)
- **Reasonable Doubt** — Good tempo/counter-style trick; useful vs card-advantage engines (Outrageous Robbery). (03-05, 03-06)
- **Deduce** — Think-twice variant, fine card-flow. (preview)
- **Seasoned Consultant** — Good blue/WU two-drop backbone. (03-05, retro)
- **Analyst** — Great with double Projector Inspector. (03-05)
- **Cryptic Coat** — Strong rare (UR/blue). (retro)
- **Doppelgang** — Great rare. (retro)

### Black
- **Extract a Confession** — Best black common (retro). Efficient edict — bypasses ward 2. (preview, retro)
- **Long Goodbye** — Strong UB instant removal (kills MV≤3), great vs cheap disguise flips. ⚠ Caveat: gets **awkward late** since a flipped MV-4+ creature blows you out. (preview, retro)
- **Murder** — ⚠ Contested. Ben: still great (best in UB control). Ethan: only C+ ("Boomer showing"). Retro verdict: **fine but unexciting on ladder; better in high-level pod play.** "A magic card" — premium straightforward removal when black opens. (preview, 03-06, retro)
- **Leering Onlooker** — "Lingering Souls on defense" — great surveil/mill target, self-recur for Roots/Outline. Banger black uncommon. (preview, retro)
- **Night Drinker Moroii** — ⚠ Big disagreement: Ben B / Ethan D. Retro: **Slimy Dualist > Night Drinker Moroii.** Leans toward Ethan's low read. (preview, retro)
- **Slimy Dualist** — Better than Night Drinker Moroii; real home in Orzhov (WB). (retro)
- **Cornered Crook** — > Undercity Eliminator (Crook can go face). Neither is a Flametongue Kavu — ward 2 blunts both. (retro)
- **Undercity Eliminator** — Just a 5-mana 3/3; below Cornered Crook. (preview, retro)
- **Fester-Leech / Fester Leech** — Strong CE/self-mill one-drop enabler — but enablers are just bodies without payoffs. (preview, 02-07)
- **Soul Enervation** — Cheap black interaction (WB). (02-07)
- **Deadly Cover-Up** — BB 5-mana wrath; hard to build around, **best in Dimir (UB).** (preview, retro)

### Red
- **Shock** — Best red common (retro). Premium vs ~46% T2 creatures; can ambush face-down 2/2s; instant-speed. Ben took Shock over Lightning Helix at P4 for **color flexibility** (keeps UR open vs Helix locking RW). (01-29, 02-07, retro)
- **Lightning Helix** — "Disgusting" Boros removal + reach. Premium but color-committing. (preview, 02-07, retro)
- **Galvanize** — ⚠ Preview/early: top-tier (deal 3, or 5 if drawn 2+; crack a Clue first). Retro: **only average** (4 mana to kill a disguised creature). Reality < hype. (preview, 01-29, retro)
- **Torch the Witness** — Premium common removal alongside Makeshift Binding. (03-05)
- **Felonious Rage** — Situational burn; passed early as too narrow / hidden power. (03-06)
- **Krenko / Thopter Fabrication / Decimator Dragon** — UR artifact-deck haymakers; fastest unbeatable starts. (retro)
- **Connecting the Dots** — ⚠ Narrowly powerful, mostly a Rakdos (RB) gold card; Case of the Crimson Pulse does it better. **Ignore its dumpster 17Lands stats** BUT "never play it" is more right than wrong. (retro) — note: rare case where retro says ignore the data.
- **World Soul's Rage** — Red splash finisher (BG splash R). (03-06)

### Green
- **Nervous Gardener** — Best green common *early* (fixing + disguise that fetches a basic); a top fixing enabler for splashes. Shifts to Lochthwain Eavesdropper once you're in the right synergy deck. (preview, retro)
- **Lochthwain Eavesdropper** — Great (4-mana 3/3 feels fine in a 3-mana-2/2 format); best green common once in synergy. (retro)
- **Topiary Panther** — Cycles + loads evidence; "every piece of the buffalo" exemplar; clunky overperformer conversation. (preview, retro)
- **Bite Down on Crime** — ⚠ Preview: weak (4-mana sorcery fight, needs setup). Re-evaluated UP: fight bypasses ward 2 AND collects evidence — even small CE inclusions are good. (preview → 01-29, retro)
- **Vengeful Creeper** — Green 5-mana 5/5 that flips to blow up artifact/enchantment; great, always had targets; clunky-overperformer. (retro)
- **Greenbelt Radical** — RG disguise payoff: 4/4 that on flip puts +1/+1 on each of your creatures + trample. (preview)
- **Insidious Roots** — Build-around BG payoff (creatures leaving yard make plant tokens). Headliner build-around. (01-29, retro)
- **Tunnel Tipster** — Ramps but does little else; cuttable if you don't need ramp. (03-06)
- **Slime Against Humanity** — Build-around; needs ooze/named copies in exile to scale — easy to misread. (preview)
- **Grave Titan Strider (Strider)** — Golden Egg co-winner: higher-ceiling green/late-game/splash payoff. (retro)
- **Undergrowth Recon** — "Stinker" rare (healthy bad rare). (retro)

### Multicolor / gold
- **Dog Walker (RW)** — ⚠ Best hybrid common (Ethan: slightly *over*-loved; "second-best common after Makeshift Binding"). X/1 dodges the no-1-toughness-removal gap. Notably **worse outside RW but never cut from GW.** Often plays better cast full-cost on a do-nothing turn. (preview, 01-29, 02-07, retro)
- **Gadget Technician (UR)** — Top hybrid gold common (preview/early hype). Strong in UR artifacts. (preview, 01-29)
- **Sanguine Savior (WB)** — Top-tier hybrid gold common (early); ⚠ passed early as situational/hidden-power in one late draft. (preview, 03-06)
- **Push // Pull** — Top early uncommon (hybrid flexibility); "Pull" ends games + massive value. Only drops if you can't cast both halves. (retro)
- **Fuss // Bother** — Go-wide payoff Azorius (WU) wants; great w/ flyers + token-makers. (03-05)
- **Wisp-Drinker Vampire (WB)** — 4-mana 2/4 flyer; drains + grants lifelink/deathtouch when a power-2-or-less creature ETBs. WB pint-size payoff. (02-07)
- **Meddling Youths (RW)** — Good Boros signpost (but not why Boros is great). (preview, retro)
- **Aurelia** — Boros bomb (rare/mythic), raw power finisher. (02-07)
- **Kaya** — Splashable WB planeswalker bomb. (02-07)

### Cases (enchantments)
- **Case of the Gateway Express** — Best non-rare Case; cheap white go-wide payoff, good in most white/aggro decks. **Won't wheel.** (preview, 01-29, 02-07, retro)
- **Case of the Filched Falcon** — UR-only; turn a Clue into a 4/4 flyer; oppressive into Gleaming Geardrake. (preview, 01-29, retro)
- **Case of the Shattered Pack** — Easy to solve via hybrid commons; fixes + grants flying/double strike/vigilance. (01-29)
- **Case File Auditor** — Digs for enchantments / fixes for Case spells. (01-29)
- **Case of the Locked Hot House** — Huge range: sometimes dead, sometimes wins games nothing else could. (retro)
- **Case of the Burning Masks** — Removal that can draw — the "extra value" beats ward-2 eval. (retro)
- **Case of the Crimson Pulse** — Does Connecting the Dots' job better (RB). (retro)
- Cases generally: ⚠ Preview called them "more meme than dream"; retro = flavor win, fine synergy rewards at picks 4–6, deliberately not busted.

### Colorless / artifacts
- **Smuggler's Copter** — The premium colorless pickup (P1P1-tier). ⚠ Caveat: in 03-06 it was the drafter's *one regret* — taken while uncertain on colors, then drifted into a build (graveyard Golgari) that couldn't crew/support it. **Take it, but be honest whether your final deck supports the body/crew.** (Note: "Satchel" appears as a caption alias — see caveats.) (02-07, 03-06)
- **Sanitation Automaton** — Golden Egg co-winner: universal "glue card," high floor, goes in any deck; can give Esika hexproof. A good two-drop in a format short on them. (retro)
- **Detective's Satchel** — ⚠ Contested gradation gap in preview; reality = powerful grindy value engine, esp. doubled in a Rakdos splash (with Cranko + Thopters). (preview, 03-05)
- **Cryptic Coat** — Strong colorless/blue rare. (retro)
- **Thinking Cap** — 1-mana Detective equip; fine but **over-committing to "augmentation" is a trap** — cut Thinking Cap for cheap interaction (Make Your Move) won a draft. (preview, 03-05)
- **Make Your Move** — Cheap flexible interaction; key main-deck add when short on answers. (03-05)
- **Clue/equipment "weapons"** — Flavor win, gameplay fail — none worth playing. (retro)
- **Pick the Players** — Maindeckable; board-friendly, doubles as removal/answers; SB-in vs artifacts/enchantments. (03-06)

### Lands / fixing
- **Escape Tunnel** — ⚠ UNDERRATED → arguably a **top-10 common.** Best fixing in the set; great for splashes + double-color requirements (ahead of Granite Witness). (retro)
- **Public Thoroughfare** — Mediocre; best in Grixis-ish UR only. (preview, retro)
- **Scene of the Crime** — ⚠ Preview: real playable (artifact Clue land). Retro: unplayable. (preview → retro)
- **Branch of Vitu-Ghazi** — Unplayable (colorless land + disguise 3 not worth it). (preview, retro)
- **Treacherous Terrain (~treacherous terrain)** — Fine as a red-splash finisher + fixing (cycles for basics, dumps ~8 cards/evidence) despite being on an online "restricted-from-decks" list / rare in paper. (03-06) — ⚠ name uncertain, see caveats.

### Rares / bombs
- **Esika, Center of the Web** — **Best rare** in a deep, balanced rare pool. (retro)
- **Aurelia's Vindicator** — Mythic, maybe better than Esika. (retro)
- **Esika's Agency Chief** — Can sac enemy artifacts (not just Clues); pair w/ Sanitation Automaton to give Esika hexproof. (retro)
- **Incinerator of the Guilty / Ill-Timed Explosion** — Fair wraths/bombs. (preview, retro)
- **Stinker rares (healthy):** A Fisher's Interrogation, Treacherous Greed, Relive the Past, Case of the Ransacked Lab, Undergrowth Recon. (retro)
- **Wraths overall** — Everywhere but fair; didn't feel oppressive (Clues aid recovery). (retro)

## Signals & seat reads

- **Delay the two-color decision; stay deep in one color** (start White or Green for most pivots), then commit to the open pair and reap over packs 2–3. Following the synergy "trail" from P1 felt good.
- **Wheeling a premium card = lane is open.** Repeatedly seeing Granite Witness wheel confirmed WU open (03-05). A stream of District Onlooker/Basilica Stalker wheeling = Golgari graveyard open (03-06). But **the wheel is mostly dead** — late premium cards are a *strong* signal precisely because good drafters don't pass them.
- **White drying up early = the seat isn't open in white** — be willing to pivot off your P1P1 color (03-06 pivoted off white/Boros into Golgari).
- **Common-color absence is noisy:** no guaranteed common of each color, so a color missing from commons may be pack texture, not a signal.
- **Late premium cards (Aurelia, Kaya, Axebane Ferox) pull you toward open colors** — watch for them (02-07).
- **Picks 1–4 dominate your destination.** Prioritize on-color flexibility; early gold picks can be "wasted" (one fewer card per pack).

## Supersessions (early-was-wrong, now corrected — NOT live disagreements)

- **"WU Detectives & UR artifacts are the two best decks"** (01-29 early read, "WU impossible to fail") → **Retro demoted both:** Boros (RW) #1, Simic (GU) #2, Azorius #3, Izzet #5. WU is still A-tier but not the format-definer; UR is high-ceiling/high-variance.
- **Galvanize = top-tier red common** (preview/01-29) → **only average** in retro (4 mana to kill a disguised creature).
- **Fairy Snoop = top common** (preview) → strong but mana-hungry, diminishing returns, **bad in tempo Detectives** (02-07).
- **Bite Down on Crime = weak/slow** (preview) → **good**: bypasses ward 2 + collects evidence (01-29/retro).
- **Not on My Watch = playable white removal** (preview) → **unplayable for white** (retro, wrong tempo).
- **Scene of the Crime = real playable** (preview) → **unplayable** (retro).
- **Collect Evidence = clunkiest, late-game-only** (preview) → **a rare GOOD late-game mechanic**; small inclusions work, don't need to build around it (retro).
- **Cases = "more meme than dream"** (preview) → fine, fair synergy rewards (retro).
- **Escape Tunnel = unmentioned/minor** → **top-10-common-tier fixing** (retro).
- **Disguise as a primary plan** (preview enthusiasm) → mostly *filler* beyond premium hybrids; don't reach (retro).

## Live disagreements (genuine, unresolved)

- **Murder's grade:** Ben (best in UB control, high) vs Ethan (C+, "Boomer showing"). Retro splits the difference — fine but unexciting on ladder, better in high-level pods. Lean: solid playable, not a high pick.
- **Night Drinker Moroii:** Ben B vs Ethan D. Retro leans Ethan (Slimy Dualist > Moroii) but never fully resolved as a flat grade.
- **Dog Walker's exact ceiling:** Consensus best hybrid common, but Ethan flags it as slightly *over*-rated by the community (2nd-best common, not 1st). Treat as a very high pick in RW, lower elsewhere.
- **Connecting the Dots:** retro says "ignore the dumpster 17Lands stats" yet also "if your takeaway is never play it, you're more right than wrong" — internally tense. Net: narrow RB-only card, low priority. (⚠ This is the one spot where a host says to *override* 17Lands; the standing rule still keeps 17Lands primary — flag, don't auto-follow.)

## Card-name caveats from caption garble

Auto-transcribed names — verify against the actual card list before trusting:
- **"Fairy Snoop" / "Faerie Snoop"** — same card; correct spelling is **Faerie Snoop**.
- **"Satchel" used for Smuggler's Copter** — in 03-05/03-06 the captions blur Smuggler's Copter and Detective's Satchel; both are real cards (Copter = the colorless flyer; Satchel = the Clue-engine equipment). Treat references in context: "Satchel/Copter" likely = Smuggler's Copter when described as the premium colorless body.
- **~"treacherous terrain"** — likely **Treacherous Greed** or a terrain/cycling land; name uncertain (lowercase in source, described as cycling-for-basics finisher + fixing). Verify.
- **~"Cranko"** — likely **Krenko** (red goblin) misheard, or a distinct MKM legend; verify.
- **~"orangutan / Reckless... / Soul-Guide-style reach creature"** (03-05) — unidentified green reach creature; name uncertain.
- **~"Ezerix" / "WWUU six-drop bomb"** (03-05) — uncertain rare name; verify.
- **~"Lochthwain Eavesdropper"** — green common, name as transcribed; verify exact spelling.
- **~"Aelia"** — Boros legend (likely **Aelia, Ardent Inquisitor**); verify.
- **~"Slick Sequence / slice from the shadows / Slice the Shadows"** — the -X/-X removal; correct name likely **Slice from the Shadows**; verify.
- **~"Crowd Control Warden"** (clunky-overperformer award) — name as transcribed; verify.
- **~"Snarling Gorehound / Snarling Gargoyle Hound"** — black aggro creature; name inconsistent across episodes; verify.
- **~"Tulir"** — opposing green-ramp legend (03-05); verify.

## Source episodes

- [2024-01-22 — Murders at Karlov Manor Preview Season!!!](sources/2024-01-22-preview-season.md) — BLIND preview, predictions only.
- [2024-01-29 — Solving the Case of MKM Draft!!!](sources/2024-01-29-solving-the-case-draft.md) — pre-release crash course / stats.
- [2024-02-07 — MKM Draft Battle Day 1!!!](sources/2024-02-07-draft-battle-day-1.md) — early reps (BR splash vs WB aggro).
- [2024-03-05 — MKM Arena Open Day 2 Draft 1](sources/2024-03-05-arena-open-d2-draft-1.md) — late competitive (WU Detective Tempo, 3-1).
- [2024-03-06 — MKM Arena Open Day 2 Draft 2](sources/2024-03-06-arena-open-d2-draft-2.md) — late competitive (BG graveyard splash R).
- [2024-03-25 — MKM Is Gone Too Soon!!! (retrospective)](sources/2024-03-25-gone-too-soon-retro.md) — final verdict, MOST AUTHORITATIVE.
