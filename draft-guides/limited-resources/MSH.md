# MSH — Limited Resources draft notes

> Source: **Limited Resources** podcast (Marshall Sutcliffe + Luis Scott-Vargas / "LSV") — **7 MSH (Marvel Super Heroes) episodes**, spanning the entire format lifecycle from release-week set review (2026-06-17) through the end-of-format **Sunset Show retrospective** (2026-07-31, #864). Built 2026-06-23; updated 2026-08-23 with the Rare/Mythic review (#859), a pre-release banter episode (#854), the Format Overview (#860), a Sealed strategy episode (#861), a live Draft Walkthrough (#862), and the Sunset Show (#864). LR is an audio podcast on YouTube, so card/mechanic names are heavily mangled in the auto-captions — corrected against the MSH card list (`data/cache/17lands_MSH_PremierDraft_1200d.json`) where confident, uncertain readings marked `(?)`.
>
> **This guide now covers the full arc of the format**, not just release-week predictions. The Sunset Show is an explicit "what did we get right/wrong" retrospective that revisits the set-review grades against real 17Lands data — its corrections are the single highest-value content in this file and are captured in `## Supersessions`.
>
> ⚠ **KEY CONTEXT FOR READING THIS GUIDE:**
> - **Release-week grades (#858 C/UC, #859 R/M) were PREDICTIONS made before any games** — the weakest evidence on the recency scale, though many held up.
> - **17Lands data exists from ~2026-06-26 onward** (MTGA launch) and is cited directly by the hosts starting with the Format Overview (#860, 2026-07-03) and used heavily in the Sunset Show.
> - **The Sunset Show (#864) is the most authoritative source in this file.** It gives a final format grade (**B**, both hosts), explicit archetype win-rate tiers, and a "what we got wrong" segment naming specific grade corrections.
> - **MSH turned out to be a genuine outlier "print set"**: 12+ cards beat the win rate of the best card in a typical recent set (Secrets of Strixhaven's best card was ~62% GIH WR; MSH has *The Super Hero Civil War* at ~70%+, plus Captain Marvel and the bonus-sheet Sword of Fire and Ice close behind).
> - **Never invent.** Where a caption couldn't be mapped, the bullet is dropped or hedged with `(?)`.

## ⚠ Recency rule (read first)

- **The newest episode wins on any conflict.** Order of authority, weakest → strongest: #858 C/UC review (6/17, release-week) → #859 R/M review (6/26, release-week, still pre-games) → #854 pre-release banter (5/24, cited only for context, not grades) → #860 Format Overview (7/3, first real 17Lands data + a week of games) → #861 Sealed strategy (7/8) → #862 Draft Walkthrough (7/16, played read woven through a live draft) → **#864 Sunset Show (7/31, end-of-format retrospective — the settled, most-authoritative verdict).**
- **Set-review grades (#858, #859) are PREDICTIONS** — recorded before the hosts had played a game. Treat the letter grades as hypotheses, not data; a claim resting only on them is suspect until confirmed by a later episode.
- **The Sunset Show is the endgame tiebreaker.** It explicitly revisits the set review ("what cards were we most wrong about"), gives hard win-rate numbers per archetype, and delivers the final format grade. Where it speaks to a card, its read wins outright.
- **This guide decodes the 17Lands data rather than ranking beneath it.** MSH is a 10-archetype synergy set on paper (heroes/villains tribal, teamwork, power-up, plan, artifacts, +1/+1 counters) — but the hosts' settled read (Format Overview, Sunset Show) is that the archetypes **did not feel distinct from each other** in practice (outside UR artifacts) and that color power level (white/blue >> black/red) dominated synergy almost entirely. Trust the WR where a card is generically castable (removal, efficient bodies, fixing); discount it where it's a build-around — nearly all the plan/build-around cards underperformed. See AGENTS.md.

### Source timeline

| Date | Episode | Phase | Weight |
|------|---------|-------|--------|
| 2026-05-24 | #854 — pre-release banter (Marvel mentioned in passing; confirms no "Omenpaths" naming split with paper) | pre-release (context only, no grades) | Weakest |
| 2026-06-17 | #858 — Set Review: Commons & Uncommons | EARLY (release-week — blind predictions/grades) | Weak |
| 2026-06-26 | #859 — Set Review: Rares & Mythics + bonus sheet | EARLY (release-week — blind predictions/grades) | Weak |
| 2026-07-03 | #860 — Format Overview | mid (first week of real 17Lands data) | Medium-Strong |
| 2026-07-08 | #861 — Sealed strategy deep dive | mid (games-played, sealed-specific) | Medium-Strong |
| 2026-07-16 | #862 — Draft Walkthrough (live draft) | mid-late (played read, pick-by-pick) | Medium |
| 2026-07-31 | #864 — Sunset Show (end-of-format retrospective) | LATE (settled verdict) | **Strongest** |

## Supersessions (newer take wins)

The Sunset Show (#864) runs an explicit "what did we get wrong in the set review" segment — this is the single highest-leverage content in this file. Ranked roughly by significance:

- **Murdoch's Crusade: C−/C (#858 release) → SUPERSEDED, one of the best white commons, arguably 2nd only to Hero in Training (#864).** "What an overperformer. Holy smokes — we underrated this one." A 1-mana sorcery, teamwork 4, exile a toughness-4-or-greater creature (or, with teamwork, a 4+-MV enchantment) is "the poster child" for LR's own removal-should-trade-up hypothesis — it's *structurally* almost impossible for it not to trade up on mana, and the hosts admit the "nerfed-looking" extra restrictions (toughness-4, MV-4-enchantment) should have been a *tell* that it was pushed, not a reason to discount it. **This is the single biggest miss of the entire release-week review** and the card LR would most want back if they could re-grade day one.
- **Hero in Training: C+/B− (#858 release) → CONFIRMED as a "mythic common," win rate on par with rares (#864).** Not really a miss on the grade (both hosts liked it going in) but a miss on *magnitude* — "we probably should have thought it was better than it was... I don't think either of us expected it would be up in the win rates of the rares." Format Overview (#860) independently clocked it at **62.3% GIH WR — higher than the mythic rare Thor, God of Thunder.** Not because Hero in Training is a better card than Thor, but because white is simply that much better than red; a "mythic common" is real.
- **Ant-Man, Colony Commander: build-around B (#858 release) → SUPERSEDED, ended up closer to C/D (#864).** "It ended up being a D partially, or at least a C partially — Blue-Green wasn't as good as we thought, and the +1/+1-counters-and-tokens plan just didn't come out particularly well." A miss driven by both weak archetype support and weak color pairing.
- **Secret Invasion: C+/D (#859 release, hosts split) → SUPERSEDED toward Marshall's side, "definitely should have been higher," one of the better blue cards (#864).** LSV's original D was too pessimistic; the ward-2 tempo swing held up better in practice than either host expected.
- **The Coming of Galactus: A− (#859 release) → SUPERSEDED UP, ~A-level in practice, "an A-ish card" per LSV (#864).** Marshall's original A− undersold it slightly.
- **Earth's Mightiest Heroes: build-around C+/B (#859 release) → SUPERSEDED UP, sitting at B− on 17Lands, LSV floats "close to an A-ish" (#864).** Both hosts undersold the teamwork mode; the reveal-8/put-any-number-into-play mode over-delivers once you have the creature density (15+) to support it.
- **The Sentry, Golden Guardian: B (#859 release, both hosts) → SUPERSEDED DOWN, a genuine liability in practice — ~52% GIH WR, "basically a negative card to put in your deck" (#864).** The card that best illustrates the format's most controversial-card discussion: on paper it's an unanswerable 5/5 flying vigilance indestructible, but MSH's removal suite is deep enough (Web Up, Cruel Alliance, Frozen in Ice, Murdoch's Crusade, Raft Security Officer as a tapper) that the drawback (opponent gets an indestructible 5/5 too) bites far more often than the upside pays off. **Verdict: don't play it — the theoretical ceiling never showed up in the win-rate data.**
- **Plans (all build-around enchantments) — confirmed a near-total miss except Political Triumph (#859/#860/#864, consistent across every episode).** Format Overview: Political Triumph is "above 60% win rate" — the standalone standout. Sunset Show: "basically all of them missed... the plans were kind of seeded build-arounds and stuff, but basically all of them missed." Doom Reigns Supreme (A− build-around, #859) is singled out by Marshall as the one he most wanted to work ("that was cool, it's a rare, pushed a little on power level, only 2 mana") but it "fell victim to villains not being very good" — a good design let down by its archetype's overall weakness, not a bad card in isolation.
- **Red's removal (Lightning Strike, HULK SMASH!) — confirmed both efficient in isolation, still not enough to save the color (#864).** "They were barely above average in win rate — it's the worst I've seen Lightning Strike be in a long time." The lesson: efficient removal alone can't compensate for a color whose creature base and card-quality floor are simply worse.
- **Land cyclers (the whole cycle) — CONFIRMED as a bright spot / correctly graded, not a miss, but flagged as a rare case where set-review optimism actually panned out (#860, #864).** "The Land Cyclers were a bright spot in this format — very very cool." LR is normally skeptical of land cyclers (they usually undersell in practice); this cycle is the exception, largely because they search for *any* land color (real fixing, not a same-color basic) and the games are slow enough that a 2-mana tempo hit for a land is rarely backbreaking. Confirmed independently in the Format Overview: both hosts started sideboarding their two-drop slot with land cyclers because the format's actual two-drops were weak enough to make the trade worth it.
- **The mana-sink utility lands (Avengers Tower, Villainous Hideout, Baxter Building) — CONFIRMED strong, another correctly-graded bright spot (#860).** Normally "a land that taps 3-4 times to draw a card is too slow to matter" — but MSH's slower, grindier pace means the hosts consistently found the mana and the time to use them. Avengers Tower specifically doubles as real color-fixing for a blue/white heroes deck.
- **Stature, Size Shifter: C (#859 blue release) → CONFIRMED underrated at release, "real sweet" (#864).** Both hosts flag it as a card whose one-mana-unblockable-into-late-game-finisher shape they didn't fully credit at review time.
- **Widow's Bite / narrow removal that "requires the target to be tapped" — CONFIRMED a design pattern the hosts actively avoid (#860 recurring theme).** Any card whose interaction requires the opponent's creature to already be tapped underperforms because "you got hit a lot of the time" to get into that position.

## Format speed / meta read

- **FINAL FORMAT GRADE (#864 Sunset Show): B from both hosts** (Marshall: B; LSV: "probably closer to a B− for my own enjoyment, but I'd give it a B"). "It checked the box... this swung for a double and hit the double." Compared explicitly to Final Fantasy (A+, swung for the fences and connected) — MSH aimed lower and safer, appropriately given the stakes of a first-ever Marvel Magic set, and hit its target.
- **Speed: medium-fast, creature-based, NOT crazy fast (#860).** "Comparable to or even slightly slower than a lot of recent formats." Curving out and bounce spells matter, but it isn't a race-to-the-death format. Notably, WotC deliberately made two-drops *weaker* and removal *less efficient* than the recent norm — a departure from the usual "every set gets its checklist of a 6-drop lifegainer, a tuck spell," etc. — and the hosts liked that willingness to deviate even though it produced real texture (land cyclers becoming a live 2-drop option; the mana-sink lands becoming reliably castable).
- **HARD WIN-RATE DATA (#860 Format Overview, week 1 of Arena; #864 Sunset Show, end of format — numbers moved a little but the tiers did NOT change):**
  - **Azorius (WU): a tier of its own** — 60% GIH WR at Format Overview, ~2% clear of the field by Sunset Show, and **played roughly DOUBLE the games of the next-most-played archetype** (58,000 vs. ~28,000) despite also having the highest win rate — "usually those two things work against each other; instead they compounded." This is *the* headline of the format.
  - **Selesnya (GW) and Simic (GU): the next tier down**, both borrowing white or blue's power. GW specifically is "the second-best deck in the format" and a safe fallback if you're not getting Azorius.
  - **Everything else bunches together in the middle**, roughly 53-55% GIH WR.
  - **Rakdos (BR) is the clear outlier at the bottom — 51.3% GIH WR, "way below" the field average of ~54.5-55%.** "Black-red villains" is explicitly named as the one archetype that never got off the ground.
  - **Illustrative color-power gap:** Hero in Training (a common) posted a *higher* GIH WR than Thor, God of Thunder (a mythic rare) — not because it's a better card, but because white is simply that much stronger than red. "These cards shouldn't be read on the same win rate, but they just are."
- **Archetypes did NOT feel distinct from each other in practice (#860) — the format's biggest design miss alongside color balance.** "The difference between the heroes deck and the villains deck feels a lot more like a win-rate difference than a how-it-feels-to-play difference — it's just checking a different creature type." The lone exception is **UR artifacts**, which felt genuinely siloed (you either have the density to make it work or you don't) — everything else played out as "creature deck vs. creature deck, whoever has the better body wins." Confirmed at the Sunset Show as the "missing 11th archetype / lack of longevity" complaint: no five-color-matters, no vivid-lands-style payoff, nothing that opened up a genuinely different deckbuilding lane the way recent sets have.
- **Removal is thinner and less efficient than recent formats, on purpose (#860).** The hosts frame this as a real design departure and it materially changes deckbuilding math: because so many MSH creatures leave value behind or are part of a bigger plan even in a losing trade, breaking exactly even on mana with a removal spell often isn't good enough — you need real efficiency, and cards like Repulsor Blast (5 damage, sorcery, 3 mana) fail that bar while Lightning Strike and Murdoch's Crusade clear it. **Exile removal is prized above all** — the set has enough indestructible/hard-to-kill threats (Captain Marvel, Sentry, the Doombots) that plain "destroy" or "-X/-X" isn't always enough.
- **Land cyclers and the utility-land cycle are the format's standout, correctly-hyped bright spot** (see Supersessions) — a rare case of set-review optimism paying off in full.
- **Sealed plays meaningfully differently than draft (#861), and — unusually — both hosts preferred sealed to draft in the Sunset Show retrospective ("the first format maybe ever where I like the sealed format more than the draft format," LSV).** Reasons: (1) bomb-and-rare density completely dominates sealed deckbuilding — "bombs and removal still rule the day, doubly true in this format"; look at your rares and your lands first, in that order; (2) sealed games run slower and more multicolor than draft — hand disruption and counterspells (We Say Thee Nay!) punish stretched mana bases better in sealed than draft; (3) a handful of cards graded lower for draft genuinely improve in sealed because the extra time lets you actually use them — Unliving Legionnaire, Iron Lad Diverging Destiny, Echo Perceptive Prodigy, Restorative Technique all move up a grade band; (4) two dominant sealed shapes: **white-based aggro** (check your white pool + gold pairings + curve + removal density) or **3-5 color "soup"** built around wherever your bombs cluster — LSV explicitly prefers a bad-mana bombs deck over a good-mana deck with no bombs, since even great fixing rarely closes the power gap between a 2-color deck of real cards and a 5-color deck of filler; (5) draft's homogeneity (so much of every draft pod fighting over the same blue/white cards) is exactly what sealed avoids, and that variety is why both hosts preferred it this format specifically.
- **Print set confirmed (#859, #864).** MSH has an unusually large cluster of format-defining rares/mythics — Sunset Show: "this set has the distinction of having a murderer's row of the best rares we've seen in any set. The Super Hero Civil War is at almost 70% GIH WR, Captain Marvel and Sword of Fire and Ice are about the same... a typical set's *best* card is around 62%; this one has 12 cards better than that." The good news: the removal suite (Web Up, Cruel Alliance, Frozen in Ice) is deep enough that most of these bombs are still answerable, which the hosts credit as the thing keeping the bomb density from ruining the format outright.

## Archetypes

*(Ranked by the settled 17Lands win-rate tiers from the Format Overview / Sunset Show — see `## Format speed` above for the hard numbers. This IS now a settled tier list; #858/#859 release-week reads are preserved per pair below and marked as such.)*

### Azorius (WU) — Teamwork — TIER 1, alone (settled: ~60% GIH WR, by far the best deck all format)
- **Plan (WotC):** Call on your team to supercharge instants/sorceries; find ways to untap creatures so they're free for offense + protection.
- **Signposts:** **Captain America, Living Legend** (B−; untaps the first creature tapped each turn — makes teamwork "free"), **Spider-Woman, Secret Agent** (B; flash 1/4, locks down a creature — "pretty solid first pick, most decks can play it").
- **Settled read (#860/#864):** This is *the* story of the format. Not because the archetype's "teamwork" plan is exceptional — the hosts note the pair doesn't even feel mechanically distinct from other white/blue decks — but because white and blue are simply the two best colors by a wide margin. Soft-force it; expect it to be contested at a competent table, wide open on Arena.

### Selesnya (GW) — Heroes matter — TIER 2 (second-best archetype, ~57.5% GIH WR)
- **Plan (WotC):** Assemble as many heroes as you can (tribal, mirror of Rakdos).
- **Signposts:** **Spider-Man, To the Rescue** (B−/C+; 3/2 flash that saves a creature with indestructible — better tempo than a bounce), **Black Panther, Vanguard** (B+; 4-mana 4/4 that goes wide / pumps when heroes enter — both enabler and payoff).
- **Settled read (#860):** "The second-best deck in the format" and a strong fallback when Azorius is cut. Borrows white's power directly; Ka-Zar of the Savage Land (green uncommon, A−, highest-graded common/uncommon in the set) and the green land cyclers make this pair splashable and consistent.

### Simic (GU) — +1/+1 counters — TIER 2 (borrows blue's power, one of the stronger pairs despite a skeptical release-week read)
- **Plan (WotC):** Adapt and evolve; pile counters via cards and power-up abilities.
- **Signposts:** **Ant-Man, Colony Commander** (B+ at release, "closer to A−" — pays 1 on attack to counter + spits out insects), **Beast, Erudite Aerialist** (B−; 3/3 that flies + draws when it connects, once you've put a counter on it). **SUPERSEDED (#864): Ant-Man ended up closer to C/D** — "GU wasn't as good as we thought, and the counters-and-tokens plan just didn't come out particularly well." Take the archetype's overall strength (it borrows blue) over the specific build-around payoff.

### Dimir (UB) — Draw your second card / Connive — TIER 3 (mid-pack, ~53-55% GIH WR)
- **Plan (WotC):** Be the calculating mastermind; draw two-or-more cards a turn, backed by connive.
- **Signposts:** **Kang, Temporal Tyrant** (B−; 4-mana 3/4 connives on attack + drains on your 2nd-card-draw), **Ghost, Spectral Saboteur** (C; 3-mana flash 2/2 unblockable — hosts think it secretly wants BR/connive, not UB). Also see **Leader, Super Genius** (rare, A — draw-a-card-then-connive engine, one of the format's true bombs) and **Taskmaster, Mercenary Mimic** (rare, B+) in `## Card tips`.

### Golgari (BG) — Creatures in graveyard (2+ creature cards) — TIER 3 (mid-pack; individually strong gold cards, weaker as a pairing)
- **Plan (WotC):** Reclaim fallen forces; key threshold is **two-or-more creature cards in graveyard**.
- **Signposts:** **Titania, Rugged Rumbler** (B+; a bare 3-mana 5/5 with ward, "make them figure it out — no clean way out"), **Killmonger, Scourge of Wakanda** (B−/B; sac a creature → destroy any nonland permanent, +2/+1 with 2 creatures in yard). Combo note: T3 Titania (discard a creature) → T4 Killmonger (sac your 2-drop) = two 5-power bodies + a kill on turn four. Also home to **The Coming of Galactus** (gold mythic saga, A−/A — one of the best rares in the set; the pairing's ceiling is high even if its floor is average).

### Boros (RW) — Non-creature spells (prowess) — TIER 3 (mid-pack; carried almost entirely by one bonkers gold rare)
- **Plan (WotC):** Arrive fast with creatures, back them with blasty instants/sorceries + crafty artifacts/enchantments.
- **Signposts:** **War Machine, Legacy of Iron** (C/C+; finicky pump-flyer, low consistency), **Thor Odinson** (B−/C+; 5-mana 4/4 flying vigilance with DOUBLE prowess — scary ceiling, "a little behind the curve when not triggering"). Also: Quake, Agent of S.H.I.E.L.D. (B) and Agent 13 (B) reward the spell count.
- **Settled read (#864):** Home to **The Super Hero Civil War**, the single best card in the set (A+, ~70% GIH WR, "the goat groan-test card" — the hosts' new benchmark for a scary bomb, dethroning Umezawa's Jitte). Remarkably, RW itself was **never a real archetype** — the card is so cheap to splash (5 mana, steal-up-to-two-creatures) that it's overwhelmingly played as a splash in *other* colors rather than as a reason to actually draft red-white.

### Izzet (UR) — Artifacts — TIER 3 (mid-pack; the one archetype that felt genuinely distinct)
- **Plan (WotC):** A steady stream of artifacts to invent your way out of trouble.
- **Signposts:** **Speedball, New Warrior** (C+ build-around; effectively hexproof to targeted spells — predicted-volatile), **Iron Man, Master of Machines** (B+ build-around; flying/vigilance that scales with + draws off artifacts — "all in on artifacts and seems really strong at it"). Also **Tony Stark / Invincible Iron Man** (rare, A — a bomb on both sides regardless of which half you cast) and **Vision Quest** (rare, build-around B/B− — search library-or-graveyard for an artifact creature; "one of the bright spots of the format," a successful build-around in a format almost devoid of them). Hosts note the *prowess/spells* feel leaks toward RW, while the artifact payoffs are the real UR engine.
- **Settled read (#860):** The only pair that consistently felt siloed off / mechanically distinct in practice — "either you have the density to do the thing, or you go 'eh' and ignore it." Every other pair just played as generic creature-combat.

### Orzhov (WB) — Attack alone (exalted-style) — TIER 3 (mid-pack; theme rarely mattered, payoffs still fine)
- **Plan (WotC):** Send your best operative on a stealthy solo attack; pile up bonuses on one attacker.
- **Signposts:** **Black Widow, Double Agent** (B−; 3/2 deathtouch giving the lone attacker first strike + menace — needs an aggressive shell), **U.S.Agent, John Walker** (B; 4-mana 4/4 that leaves a +1/+2 equipment — "plays out quite well"). NOTE: LSV singled out the **attack-alone deck as the archetype that caught his eye most** in white (multiple payoffs: Agent 13, Agents of S.H.I.E.L.D., Luke Cage, Crowd of True Believers) — but warned it's brutalized by instant-speed removal / bounce.
- **Settled read (#860):** "Attack-alone doesn't feel like an archetype at all — it comes up sometimes in the game, but many, many times you're just attacking with everything." Draft the payoffs as generically good cards (Agents of S.H.I.E.L.D. specifically is "mostly getting carried by the fact that its color combination is good"), don't expect the theme to define your games.

### Gruul (RG) — Power-up / Ramp — TIER 3 (mid-pack; carried by Wolverine + power-up as a mechanic, not the pairing itself)
- **Plan (WotC):** Hit hard; generate extra lands/mana to fuel power-up abilities.
- **Signposts:** **Abomination, Terrifying Titan** (B; 4-mana 4/4 trample that can be a punchy 7-mana fight-machine), **Hulk, Gamma Goliath** (B−/B+; 5-mana 6/5 reach trample that cheapens other power-ups). Also **Wolverine, Fierce Fighter** (rare, A — hasty 3/5 that fights on ETB and self-heals; one of the best gold rares) and **Alien Invasion** (rare, B+ — a slow but near-unbeatable inevitability enchantment if it resolves turn four).

### Rakdos (BR) — Villains matter — TIER 4, alone at the bottom (settled: ~51.3% GIH WR, "way below" the field average)
- **Plan (WotC):** More villains on the battlefield → more payoffs; overwhelm with pure evil.
- **Signposts:** **Bullseye, Death Dealer** (B+; sac-artifact/discard to deal 2, repeatable — "completely justifies itself," loves trinket artifacts), **Madame Hydra** (B; spawns a 2/1 menace token per villain cast — must-kill but fragile 2/3, predicted-volatile).
- **Settled read (#860/#864): the format's clear worst archetype, and the one true design miss.** "Heroes are good and villains are bad" is the hosts' one-sentence summary of the entire set. Red's removal (Lightning Strike, HULK SMASH!) is individually efficient but "barely above average in win rate — the worst I've seen Lightning Strike be in a long time," and black's villain payoffs (Crossbones, Baron Strucker) are legitimately well-designed cards trapped in an under-supported archetype. If you must be in these colors, treat it as a support pairing — splash their removal and rares into a stronger base color rather than committing to the villains-matter plan.

## Card tips

Grades below are on roughly an A+→F scale, plus the channel's two subgrades: **build-around** (low floor, high ceiling with the right shell) and **sideboard** (rarely main-decked). Split grades shown as Marshall/LSV; ranges shown like `C/C+`. Commons/uncommons are graded from **#858 (release-week)**; rares/mythics from **#859 (release-week)**; both are **predictions made before any games were played**. Where a later episode (#860 Format Overview, #864 Sunset Show) corrected a grade, that's flagged inline as `**SUPERSEDED**` — see also the consolidated list in `## Supersessions`.

### White (W)
- **Agent Maria Hill** — B− (#858 release). 1-mana 2/1; draws + grows whenever tapped for teamwork. "Endless search for relevant one-drops" — good with ~3 teamwork cards.
- **Crowd of True Believers** — C (#858 release). 1-mana 1/2; pumps + lifegains the lone attacker. "A lot of value for one mana" in attack-alone.
- **Helicarrier Strike** — C+ (#858 release). 1-mana, deal 2 (4 with teamwork) to an attacking/blocking creature; "half a notch below" unconditional removal but will see lots of play.
- **Panther Pounce** — D (#858 release). One mana doing many things (investigate + pump/fly/untap) none well; no clear home. *Predicted-volatile — "wouldn't be shocked if it's a solid C."*
- **Political Triumph** — B (#858 release). 1-mana plan: scry + plan counter per creature ETB → pops for a card + team-wide +1/+1. "Oh no" if cast turn one in a 16-17 creature deck; suffers if creature-light. **CONFIRMED as the ONE plan that actually works, all format (#860/#864).** Over 60% GIH WR at the Format Overview — the standalone standout of the entire build-around suite. "Basically all the other plans missed" (see Supersessions); this is the exception, precisely because it costs only 1 mana and is never a dead turn.
- **S.H.I.E.L.D. Spy Kit** — D (#858 release). 1-mana equip; +1/+1 + attack-alone scry/untap. "Low impact, doesn't pay you back for a whole card." **SUPERSEDED (#864): "underrated for sure at the beginning of the format — this card ended up doing some work, man."** Still ranked below Murdoch's Crusade as a pick, but a clear release-week miss on the low side.
- **Agent of Atlas** — C− (#858 release). 1W 2/2 prowess; for the RW non-creature-spells deck.
- **Brave Brawler** — C (#858 release). 1W 2/2 lifelink with a power-up (4-3 lifelinker for 5). "Just a fine card."
- **Colleen Wing, Street Samurai** — build-around C+ (#858 release). 1W 2/2; grows + scries when you target your own creature. Fine with ~3 self-targeting spells, unplayable with none.
- **Murdock's Crusade** — sideboard (#858 release). 1W sorcery, teamwork: exile a toughness-4+ creature and/or a 4+-MV enchantment. Too narrow + sorcery speed; plan to sideboard it. **SUPERSEDED (#864): one of the best white commons in the set, arguably #2 behind Hero in Training.** "What an overperformer, holy smokes — we underrated this one." Structurally near-guaranteed to trade up on mana; take it as a maindeck removal spell, not a sideboard card. The single biggest miss of the release-week review.
- **Night Nurse, Healer of Heroes** — C+ (#858 release). 1W 2/1 flash lifelink; return a permanent put in your yard this turn. Patient two-for-one; "doesn't matter what you get back."
- **Patriot, Shield Wielder** — C+ (#858 release). 1W 2/2; pay 2 + tap to give another creature +2/+0 + hexproof (no sorcery clause). Annoying like Giver of Runes but "annoying ≠ good"; they kill it first.
- **Raft Security Officer** — C+ (#858 release). 1W 1/3; taps a creature (cheaper vs. power ≤3). Sneaky pseudo-removal that scales with the game; hosts optimistic. **Confirmed (#860): "played out really well — usually costs one to do the thing, sometimes two, still fine."** Note it's a soldier, not a hero — does NOT trigger hero-matters payoffs (Agent Phil Coulson, Avengers Assemble); Marshall lost a sealed match specifically because his opponent's tapper-plus-token-maker curve produced no hero triggers for his own Coulson.
- **Super Villain Lockup** — B (#858 release). 1W flash enchantment; exile a tapped creature (Seal-of-Authority effect). "Fantastic."
- **Take Up the Shield** — C+ (#858 release). 1W instant reprint; +1/+1 counter + lifelink + indestructible. "Top-tier combat trick — leaves behind the counter."
- **Agent 13, Sharon Carter** — B (#858 release). 2W 3/2; investigate whenever a creature attacks alone (counts herself). "A payoff I don't mind — must-kill, makes a clue at first blush."
- **Agents of S.H.I.E.L.D.** — C (#858 release). 2W 2/4; lone attacker gets +1/+1. LSV's beloved exalted-style design; the attack-alone payoff that caught his eye.
- **Hero in Training** — C+ (#858 release). 2W 2/2; draws a card unconditionally (+2 life with another hero). "One of the better commons — usually you pay four mana for that." **CONFIRMED and strengthened (#860/#864): a "mythic common."** 62.3% GIH WR at the Format Overview — higher than the mythic rare Thor. "We probably should have thought it was better than it was; we didn't expect it to be up in the win rates of the rares." Not a grading miss so much as a magnitude miss.
- **Kree Commandos** — C− (#858 release). 2W 2/1 flying vigilance prowess; "a lot of stats" but 1 toughness blocks/survives poorly.
- **Quake, Agent of S.H.I.E.L.D.** — B (#858 release). 2W 3/3; tap a creature OR land on each non-creature cast. "Rude" upkeep tapper; "dominates the battlefield" in RW.
- **Red Guardian, Super-Soldier** — B (#858 release). 2W 2/2 flash; destroy a creature that dealt damage this turn. Play-aroundable, but "on Arena nobody plays around it"; removal + a body.
- **Web Up** — B (#858 release). 2W enchantment; O-Ring any nonland permanent. "Fantastic"; dodges its own three-mana-removal class by being 3 MV.
- **Luke Cage, Power Man** — B− (#858 release). 3W 2/5; attacks alone as a 4/5 indestructible. Polarizing — wrecks decks without instant removal/bounce; just a 2/5 otherwise.
- **Mockingbird, Ace Agent** — C− (#858 release). 3W 2/2 double strike that grows when you target it. "A trap until proven otherwise" — 4-mana 2/2 dies too easily before the counter lands. *Predicted-volatile.*
- **Okoye, Dora Milaje Leader** — B+ (#858 release). 3W 3/2 + two 1/1 soldiers; tokens get first strike attacking. "Potential mythic uncommon — pure stats is incredible."
- **Wakandan Drone Flock** — C (#858 release). 3W 3/3 flying artifact, scry 2 ETB. "Looks like it has enough and might just not be." *Predicted-volatile.* *(Not specifically revisited in the Sunset Show "what we got wrong" segment — treat the release-week grade as roughly holding.)*
- **White Widow, Free Agent** — B+ (#858 release). 3W 2/3; +1/+1 on up to two creatures OR regrow an artifact/enchantment. "Mythic-uncommon candidate — win with tempo or card advantage."
- **Borough Backup** — C (#858 release). 4W sorcery; two 3/2 vigilance tokens, also a basic landcycler. "No real drawback — should be higher than C, experience says it isn't."
- **Captain Mar-Vell, Space-Born** — C (#858 release). 4W 4/4 flying vigilance + flash-while-opponent-cast. "Not quite up to snuff" at 5 mana but playable.
- **Invisible Woman, Sue Storm** — build-around B (#858 release). 4W 2/5 lifelink; makes 0/4 walls when you counter another hero. Very defensive; ceiling depends on counter flow.

White rares & mythics (#859 release-week):
- **Nick Fury, Agent of S.H.I.E.L.D.** — C (#859 release). 1W 2/1 hero; power-up (WUBRG) to dig top 7 for a hero/equipment/vehicle. Mostly just a playable 1-mana 2/1; the five-color ability is a bonus, not a reason to draft it — pairs nicely with Baxter Building if you happen to have one.
- **Agent Phil Coulson** — A− (#859 release). 1W 2/2 vigilance hero; tap to put +1/+1 on each other hero. "Fantastic — a two-mana must-kill, not even really a build-around since white decks incidentally run a ton of heroes."
- **Jennifer Walters** — A (#859 release). 1W 2/3 hero (opponents can't cast on your turn) / transforms to Sensational She-Hulk, 3GW 6/6 reach trample that punches back whenever your creatures deal damage. "Obscene." Playable and good on either side; cast whichever is more mana-efficient in the moment.
- **Origin of the Avengers** — B+ (#859 release). 1W saga; scry 2 → put a ≤3-MV hero into play (no draw that turn) → team +1/+1. "A good addition to pretty much any deck" with enough creatures; effectively a one-turn-delayed cantrip with a free hero and a team pump attached.
- **Super Soldier Serum** — B (#859 release). 1W aura; +2/+2, first strike, vigilance, and re-attaches any equipment on attack/block. Feast-or-famine (huge if unanswered, a nonevent if the creature dies), but cheap enough that the downside is contained.
- **The Mind Stone** — B (#859 release). 1W legendary indestructible mana rock, tap-for-white; pay 5W to "harness" it into a repeatable blink engine. Playable in any white deck as a plain 2-mana rock; the blink upside needs ~2 good ETB targets to matter.
- **Captain America, Super-Soldier** — A− (#859 release). 1WW 3/2 first strike hero; enters with a shield counter (prevents the next instance of damage/destruction) that also grants you and your other heroes hexproof while it's up. Extremely hard to remove in combat.
- **Captain America, Wings of Freedom** — A− (#859 release). 2W 3/1 flying first strike ward-1 hero; on attack, pumps each other hero by its own toughness. A near-twin of the above; both are "fantastic," pick whichever fits your curve.
- **Monica Rambeau** — A+ (#859 release). 2W 3/3 flying prowess hero / transforms (or hard-casts) for 2RW into Photon, Living Light, a 4/4 flying hexproof prowess that puts a counter on every other creature you control on noncreature casts. "Bordering on busted — basically just cast the Photon side and never expose Monica; hexproof is absurd." Near-unanswerable in a sweeperless format.
- **The Sentry, Golden Guardian** — B (#859 release, both hosts) → **SUPERSEDED DOWN, ~52% GIH WR in practice (#864).** 3W 5/5 flying vigilance indestructible hero; ETB gives the opponent a 5/5 flying indestructible Void that must attack each combat. On paper a controversial "how do you beat this" bomb; in practice MSH's removal suite (exile effects especially) is deep enough that the downside (handing over a matching 5/5) bites more often than it should. **Verdict: skip it — a rare case where the theoretical ceiling never showed up in the win-rate data.**
- **Avengers Assemble!** — build-around A (#859 release). 4W flash enchantment; heroes get +2/+2, and at each end step you attacked-or-played-a-hero-this-turn, draw a card. "Ridiculous — flash it in mid-combat and it's a disaster for the opponent; the free draw engine on top is absurd." Only a build-around insofar as it wants a hero-dense deck, which most white decks already are.
- **Captain Marvel, Earth's Protector** — A+ (#859 release). 3WW 5/4 flash flying lifelink hero; power-up (5W) for a +1/+1 counter and indestructible. "One of the best cards I've seen in a while for Limited." Flash lets it double as an ambush blocker; once indestructible, essentially unkillable and unraceable.

### Blue (U)
- **Aerial Doombot** — C+ (#858 release). 1-mana 1/1 flying artifact villain; power-up to a 4/4. "One of the good commons — annoying, flexible, an artifact AND a villain."
- **Kid Loki** — B− build-around (#858 release). 1-mana 1/1; hexproof for creatures you counter'd this turn, grows on your 2nd-card-draw. Strong with rummagers; needs enabling.
- **Pym Particles** — B (#858 release). 1-mana sorcery; target creature gains vigilance + unblockable, draw a card. "Gitaxian Probe of Limited — free attack + cantrip, plays super smooth." *(Caption "Prying/Pin Particles.")*
- **Stature, Size Shifter** — B (#858 release). 1-mana 1/1 unblockable while power ≤1; power-up (UUX) as a finisher. "A better Doombot — great mana sink, end the game with it."
- **Super Intelligence** — F / sideboard (#858 release). 1-mana aura; enchanted creature's controller draws each upkeep. "Rewards their removal too much"; only a sideboard card vs. removal-light decks.
- **Bold Biochemist** — C− (#858 release). 2-mana 1/3; playable but unexciting now that 1/3 blockers/slow two-drops are devalued.
- **We Say Thee Nay!** — C+ (#858 release). 2-mana counter that scales via teamwork. Solid clincher.
- **Atlantean Cavalry** — D (#858 release). Fine but very replaceable payoff body.
- **Depower** — C+ (#858 release). One mana to stop an attacker + a card. "Strong common."
- **Echo, Perceptive Prodigy** — D (#858 release). Too narrow, hard to use.
- **Frozen in Ice** — C+ (#858 release). 3-mana near-removal; strips abilities + taps down. "Could reach B−."
- **Iron Lad, Diverging Destiny** — build-around B (#858 release). 2/2 flying vigilance artifact that filters into card draw.
- **Justice, Vance Astrovik** — B+ (#858 release). 3-mana "grown-up Man-o'-War" that bounces + grows. *(Caption-garbled name; map confirmed.)* **Confirmed and independently rated the format's Man-o'-War standard-setter (#864): "it feels like every two or three sets we get a Man-o'-War that pushes the limits — this is another one, and it's above the competition."**
- **Rewrite History** — build-around B (#858 release). "F on average" but powerful built around draw-your-second-card. High variance.
- **S.H.I.E.L.D. Deployment Drone** — B− (#858 release). 3-mana 2/2 flyer + a 1/1 token, all-artifact. "Likely the best common."
- **Thirst for Knowledge** — build-around C/C+ (#858 release). Only good in the artifacts deck where you keep the card advantage.
- **A.I.M. Scientists** — C (#858 release). 4-mana 3/3 with ETB connive; flexible basic-landcycler.
- **Attuma, Atlantean Warlord** — C+ (#858 release). 3/4 that draws on merfolk attack; good even with few merfolk.
- **Giant-Sized Flying Ant** — D (#858 release). Fine stats, no theme fit, falls off.
- **Mister Fantastic, Reed Richards** — build-around B (#858 release). Great with repeatable token-making, otherwise benched.
- **Trickster's Stratagem** — C+ (#858 release). Good tuck + connive, even at sorcery speed.
- **Falcon, Winged Wonder** — B/B+ (#858 release). Two flyers, surveil on the token. "Great distributed stats."
- **Wiccan, Rising Magician** — C (#858 release). 5-mana 4/4 flyer with inconsistent flicker upside.
- **Atlantis Attacks** — C+ (#858 release). 7-mana, but teamwork yields a 6/5 hexproof + bounce two. "Great stabilizer."

Blue rares & mythics (#859 release-week):
- **Bruce Banner / Incredible Hulk** — C+/B− (Bruce, #859 release) and B (Hulk, transform side). U 1/1 hero, X-tap-draw-X activated ability / transforms via 2RRGG (or hard-cast for 2GGRR) into an 8/8 reach trample enrage Hulk. Treat as two near-separate cards depending on which colors you're actually in — Bruce is a scary 1-drop threat-of-activation in UB, the Hulk is a huge RG bomb; getting to run both wants an RG base splashing a couple blue sources.
- **Loki, God of Mischief** — build-around B (#859 release). 1U 2/1 legendary villain; draw a card the first time each turn one of your abilities targets something. "A card that when your opponent has it in play, you're not feeling great" — doesn't need much support (a single tapper or tuck effect turns it on) but is a genuine must-answer threat if left alone.
- **The Wondrous Wasp** — B+ (#859 release). 1U 2/1 flash flying hero; ETB tap a creature and strip its abilities for as long as the Wasp stays. "You're always going to get your mana's worth" — cheap, flexible, and shuts off ability-dependent threats (including opposing Doombots/tokens) cold.
- **Tony Stark / Invincible Iron Man** — A (#859 release). 1U 1/3 hero, tap-dig-4-for-an-artifact / transforms (or hard-casts for 4UR) into a 5/4 flying haste artifact hero that free-drops an artifact from hand each combat. Both halves are independently strong for a UR deck — "not like Bruce Banner where you're choosing between two different cards, this one is just good on both counts."
- **Miss Marvel, Kamala Khan** — build-around B (#859 release). 2U 1/4 hero, no max hand size; whenever you target one of your own creatures with a spell, draw a card and her power = your hand size until end of turn. Only needs ~3 self-targeting spells (Pym Particles, tricks) to turn on; can ambush blocks at instant speed since the pump happens mid-combat.
- **Namor the Sub-Mariner** — A− (#859 release). 1UU legendary merfolk hero with flying, power = merfolk you control; whenever you cast a noncreature spell with a blue pip, make that many 1/1 merfolk tokens (and grow accordingly). "Starting at 1/4 flying is already good, and then one spell turns it into a 2/4 or 3/4 with extra bodies."
- **Secret Invasion** — C+/D (#859 release, hosts split — Marshall higher, LSV lower). 1UU aura; exile a creature (yours or theirs), enchanted creature becomes a copy of it with ward 2. **SUPERSEDED toward Marshall's read: "definitely should have been higher... one of the better blue cards" (#864).** High-risk, high-reward — good with a mediocre creature underneath (you're up half a card even if it eventually dies) and devastating against a late-game bomb.
- **Shield Flying Car** *(bonus artifact vehicle, listed here for color)* — B (#859 release). 2U 3/3 flash flying vehicle, crew 1; ETB blink one of your own creatures. A real board piece on its own that doubles as instant-speed removal-dodge/ETB-replay.
- **Kang the Conqueror** — B+ (#859 release). 2UU 4/5 flying legendary villain; power-up (5UU) for an extra turn (power-ups can't be activated during it). "Already a B+/B on the body alone; the extra-turn upside is a dream scenario, not the reason to play it."
- **Leader, Super Genius** — A (#859 release). 2UU 1/3 legendary villain; your creatures draw a card instead of conniving, then draw-then-connive a creature at the beginning of each combat. "Unbelievable — draws a card straight away and STILL connives; way better than a same-cost 4/5 flyer sitting right next to it. The biggest lightning rod in the set — kill it or lose."
- **Ironheart, Clever Champion** — build-around B (#859 release). 4U 3/4 flying hero with improvise; your noncreature spells also gain improvise. Mostly just a solid flyer that's better in an artifact-dense shell.
- **Multiversal Incursion** — D (#859 release). 5UU sorcery; make a nonlegendary token copy of each nontoken creature you control. Pure "win more" — needs 3+ real creatures in play already to be worth the mana, and We Say Thee Nay! (2-mana counter) stomps it hard.

### Black (B)
- **Project Deathlok Soldier** — D, up to C/C+ with support (#858 release). 1-mana 1/2 artifact; recur from yard for 3. Needs sac/discard payoffs; "not a villain, randomly an artifact."
- **Whiplash, Vengeful Engineer** — C/C+ (#858 release). 1-mana 2/2 villain ETB tapped; drains by equipment count. "Play it if you care about villains."
- **Agents of HYDRA** — C+, B− in decks that need it (#858 release). 2-mana 1/1 that dies into a 2/1 menace. "Double villain — these always do well, don't sleep on them."
- **Dark Deed** — B+ (#858 release). 1B instant; target creature −4/−4. "Extremely efficient — kills Thor; the bane of clunky 4-5 drops." The removal benchmark.
- **Decoy Ploy** — C (#858 release). 1B instant; regrow a villain and/or a hero from yard.
- **Red Room Recruit** — C+ (#858 release). Villain + connive pivot; helps hit land drops.
- **Stolen Stark Tech** — C− (#858 release). Flash trick leaving a small equipment; better with sacrifice.
- **Swordsman, Sharp Scoundrel** — build-around B (#858 release). Cheap villain + equipment payoff; must draft equipment.
- **Widow's Bite** — C+ (#858 release). −2/−2 instant staple; teamwork upgrades to deathtouch.
- **Yellowjacket, Heartless Marauder** — C+ (#858 release). Aggressive villain flyer with growing lifelink; weak on defense.
- **Arnim Zola, Bio-Fanatic** — C+ (#858 release). Makes 2/1 menace tokens but gated on graveyard + high cost.
- **Baron Strucker, HYDRA Overlord** — build-around B (#858 release). Villain cost-reducer + connive; strong enabler.
- **Cruel Alliance** — C+ (#858 release). Exile removal; "likely the best black common." **Confirmed the best black common by a real margin (#864): "ended up significantly better than Hour of Defeat — you'd think Hour of Defeat is the default pick day one, but the exile, the occasional life gain, and the unlock-to-kill-anything mode put Cruel Alliance clearly above it."**
- **HYDRA Troopers** — C (#858 release). Enabler-and-payoff villain; wants a high villain count.
- **Kingpin's Enforcers** — C (#858 release). Villain with lifelink + flexible sac-to-draw; cost is high.
- **Klaw, Sonic Subjugator** — C+ (#858 release). 3-mana 2/2 with a built-in two-for-one discard; scales late.
- **Ninja of the Hand** — D (#858 release). Unexciting 3-mana 2/2 deathtouch; pump too expensive.
- **Ronin, Shadow Stalker** — D (#858 release). Powerful but narrow equipment build-around; prove-it card.
- **Too Evil to Stay Dead** — D/C (#858 release). Reanimation with too-high setup; competes with graveyard payoffs.
- **Visions of Villainy** — D+/C− (#858 release). Instant-speed Night's Whisper; pure draw rarely wanted.
- **Crossbones, Malicious Mercenary** — C/C+ (#858 release). Growing 3/3 deathtouch that pings; needs villain mass.
- **Grim Reaper, Lethal Legionnaire** — C− (#858 release). "Reads better than it plays" — high setup, must attack.
- **Hour of Defeat** — C+ (#858 release). 3-mana destroy + surveil. "Great catch-all removal."
- **HYDRA Infiltration** — C− (#858 release). Build-around drain enchantment; expensive single-attacker grind.
- **Moonstone, Harsh Mistress** — build-around D (#858 release). 2/4 flyer needing repeatable self-discard to pay off.
- **Robot Domination** — B / build-around B (#858 release). 4 mana for three cards + three 2/2s when creatures die.
- **Unliving Legionnaire** — D (#858 release). Bad at both modes; a 4-mana 3/2 liability.
- **Madame Masque** — B+ (#858 release). Connives on ETB + spits out 2/1 menace tokens. Card selection + bodies.
- **Roxxon Brutes** — C (#858 release). 5-mana 4/4 menace with basic landcycling; grows sometimes.
- **The Masters of Evil** — B (#858 release). Villain lord (+2/+1) that can cash in for a plan card. "Deck-ender."

Black rares & mythics (#859 release-week):
- **Black Widow, Super Spy** — A− (#859 release). 1B 2/1 legendary menace hero; combat damage forces the opponent to exile cards until a nonland, then you either counter-up Black Widow or free-cast the exiled card. "Incredible — 80% of the time it's a free counter, 20% of the time you get to cast a removal spell or creature off their deck for free."
- **Doom Reigns Supreme** — build-around A− (#859 release). 1B plan; each villain ETB drains 1 and adds a plan counter; at 5 counters, sacrifice to exile the opponent's top 5 and free-cast up to two of them. "A great build-around — both halves of the card are good on their own, and you're not even sad when it cashes in." Wants 12-14+ villains; strongest in BR or UB. **See Supersessions — one of the plans the hosts most wanted to work, but "fell victim to villains not being very good."**
- **Baron Helmut Zemo** — build-around D (main mode) / build-around B (in a near-mono-black shell) (#859 release). BBB 3/3 legendary villain; connives on each black spell cast, plus an expensive graveyard-boast mode. "The juice isn't worth the squeeze unless you're genuinely near-mono-black (11+ black sources) — LSV tried building around this twice and got crushed both times." Playable late in a heavy-black deck, never a good early pick.
- **Construct a Cosmic Cube** — build-around B+ (#859 release). 2B plan; draw-your-2nd-card makes a 2/1 menace villain token + a plan counter; at 7 counters, sacrifice to mind-control the opponent for their next turn. Slower payoff than Doom Reigns Supreme (7 counters vs. 5) but the tokens alone carry the card even if you never reach the top end.
- **Elektra, Daughter of the Hand** — A (#859 release). 2BB 3/3 legendary villain with Sneak (BB, return an unblocked attacker to hand to cast cheap); ETB destroys a power-3-or-less creature. "The sneak ability barely matters — she's just an incredible two-for-one on cast alone."
- **Super Scroll** — build-around B+ (#859 release). 1BBB 4/5 flying legendary villain with four activated abilities (one per other color: make a 0/4 wall, +4/+4, 4 damage to a creature, draw 4). "You don't need all the abilities on — just one, ideally the red (removal) or blue (draw-4) mode." Effectively a 5-6 mana threat once you account for getting a secondary color online, but a game-taker once it resolves.
- **Thunderbolts Conspiracy** — build-around C−/C (#859 release). 3B flash enchantment; return a dying villain to the battlefield as a hero too, with a finality counter. "Really hard to spend four mana and have it do nothing, and that's way too possible here — a vanilla D-level 3-drop black creature would probably win you more games on average."
- **M.O.D.O.K.** — A+ (#859 release). 3BB 2/2 legendary artifact villain, flying + lifelink; pay 3 life to connive (your turn only, can repeat); static: opponents' creatures get −1/−1. "Obscene — the static alone kills every X/1 they have, and it's a fine 2/2 flying lifelink on top of that. Hard to play against in any scenario where it survives."
- **Dr. Doom** — A+ (#859 release). 4B 3/3 legendary villain; ETB makes two 2/3 colorless Doombot artifact tokens; indestructible while you control an artifact/creature/plan; draw-a-card-lose-a-life every end step. "Six mana for three 3/3s that's also indestructible — you don't even need artifacts or plans in the rest of your deck, it comes with its own."
- *(Bonus sheet, black, notable — see the dedicated bonus-sheet section below for the full list: Deadly Dispute, Extinction Event, Final Act, Massacre Girl [as "Elektra, Deadly Assassin"], Dauthi Voidwalker [as "Widowmaking Infiltrator"].)*

### Red (R)
- **Hawkeye's Bow** — D/C (#858 release). Low-impact; only for the equipment deck.
- **Stark Industries Executive** — C (#858 release). Honest 1-drop making Treasures; ramps/splashes.
- **Super Speed** — D (#858 release). OK flash-haste aura trick with no clear home.
- **Blazing Crescendo** — C/D (#858 release). Combat trick that replaces itself; otherwise replaceable.
- **HULK SMASH!** — C (#858 release). Mostly a bite/removal spell when short on removal.
- **HYDRA Assault Robot** — build-around C (#858 release). Wants heavy villains/artifacts; better in the artifact deck.
- **K'un-Lun Warrior** — D (#858 release). Filler 2/2 looter/sac; awkward curve, not a villain.
- **Lightning Strike** — B (#858 release). 3 damage any target. "Efficient and flexible." Premium common removal. **Grade holds, but the color didn't (#864): "barely above average in win rate — the worst I've seen Lightning Strike be in a long time."** A clean illustration that individually-efficient removal can't rescue a color whose creature base is broadly worse.
- **Loki Laufeyson** — B/B− (#858 release). 2-mana spell-copier; strong but fragile/setup risk.
- **Misty Knight, Hero for Hire** — C+ (#858 release). 3-power 2-drop; good early + a late rummager.
- **Photon Blast Barrage** — sideboard C+ (#858 release). Inefficient unless killing multiple low-toughness creatures.
- **Speed, Young Avenger** — D (#858 release). Unimpressive 2/2 haste; the pay-1 weakens it, not a villain.
- **Team Tactics** — B− (#858 release). 1R instant, teamwork; double strike (+trample). "A finisher that comes out of nowhere — you'll lose games to it."
- **Vision of Love** — C (#858 release). Sac-artifact/discard to draw two. "Better than Tormenting Voice."
- **Death to Our Enemies** — build-around B (#858 release). 2R plan; tapped Treasure + plan counter per non-creature cast → 7 damage divided. "Not hard to pull off; stays alive and kills them."
- **Evil's Thrall** — C+ (#858 release). Supercharged Threaten; better with a bigger-MV villain + sacrifice.
- **Hex Magic** — D (#858 release). Discard-redraw still costs 3 mana; narrow, scales badly.
- **Hire a Crew** — C/C− (#858 release). 2/1 menace token + anthem; tries to do two jobs.
- **Human Torch, Johnny Storm** — C+ (#858 release). Flying pinger + solid power-up card for RG aggro.
- **Iron Fist, Living Weapon** — D (#858 release). Dangerous repeatable pinger but high build-around cost, fragile.
- **Jessica Jones, Private Eye** — B− (#858 release). Slow Mulldrifter; taps to dig, draws more if killed.
- **Machinesmith Automaton** — build-around C+ (#858 release). Grows per artifact; stack it in artifact decks.
- **Volcanic Villain** — D (#858 release). Vanilla 3/2 haste power-up baseline; unexciting.
- **Crimson Operative** — C (#858 release). Overcosted 3/2 but a free card, artifact + villain; triggers synergies.
- **Repulsor Blast** — C+ (#858 release). 5 damage removal; teamwork adds 2 to face. Fine for aggro.
- **Truck Toss** — B (#858 release). 4 damage any target; cheaper with vehicles. "I like B."
- **Kree Sentinel** — C (#858 release). 5/5 reach villain artifact with landcycling. Pushed solid common.
- **Wonder Man, Hollywood Hero** — C (#858 release). 4/4 flyer doubling power-ups, but rarely activated twice.
- **Red Hulk** — C/C+ (#858 release). Polarizing 6/7 enrage threat; "crushes RG, dies to bounce/removal." *Predicted-volatile (A-or-D).*

Red rares & mythics (#859 release-week):
- **Quicksilver, Brash Blur** — C (#859 release). R 1/1 legendary hero, haste; may start in play if in your opening hand; power-up (4R) for a +1/+1 counter and double strike. "Pretty bad — the free-drop gimmick barely matters when you could just tap a mountain for it anyway." Fine filler at best.
- **Hawkeye, Master Marksman** — B+ (#859 release). 1R 2/2 legendary hero, first strike + reach; whenever tapped, pay 1 up to 3 times for can't-block / 2 damage to a player / rummage (any combination). "Fantastic — a straight-up B as just a 2-mana 2/2 first strike reach, and then the trick-arrows menu is a lot to put on top of that."
- **Avengers Disassembled** — B (#859 release). 1RR sorcery; choose one or both — deal 3 to each creature, and/or destroy a land (search a basic, tapped). Matchup-dependent (best in RG/RB where you run fewer 3-toughness creatures than your opponent) but strong enough to maindeck in the right shell, not purely sideboard.
- **The Scarlet Witch** — D (#859 release). 2R 2/3 legendary hero; your ≥4-MV instants/sorceries cost 2 less (scales with her power). "Looks like a trap — a 3-mana 2/3 isn't up to snuff on its own, and you'll only rarely have 2+ eligible spells in hand to discount."
- **Fin Fang Foom** — B/B+ (#859 release). 2RR 3/5 legendary flying villain; copy instants/sorceries that target an artifact or land you control (works around by targeting an opposing artifact creature with removal). "You're mostly just happy to have a 3/5 flyer for four — the copy text is a bonus, not the reason to play it."
- **Mjölnir, Hammer of Thor** — B/B− (#859 release). 3R legendary equipment; ETB deal 4 to a creature; double damage dealt by the equipped creature; equip-worthy is any legendary nonvillain red/white creature; can also discard it (2R) as a mini-Pyroclasm (2 to each creature). "Not uber-mythic-must-take, but a genuinely flexible removal-plus-threat — B+ if your deck equips it well, B− if it doesn't."
- **Thor, God of Thunder** — A+ (#859 release). 3RR 5/5 legendary flying hero; ETB return an equipment/instant/sorcery from your graveyard (playable until end of next turn); whenever you cast a noncreature spell, deal damage equal to its mana value to any target. "Ridiculous — five mana 5/5 flyer that's up a card even if it dies, and starts throwing lightning bolts the moment you cast spells."
- *(Bonus sheet, red, notable: Monstrous Rage graded B/B+ — "one of the best combat tricks we've ever seen, goes in almost any red deck." Fiery Emancipation and Chaos Warp both graded F. Seize the Day / Fury of the Horde / Bedlam-style extra-combat cards uniformly avoided — "you shouldn't play the extra-attack cards.")*

### Green (G)
- **Giant Growth** — C (#858 release). Classic combat trick; good, but how many do you want.
- **Go Nuts!** — C/C+ (#858 release). 1-mana fight + optional +1/+1; good in creature-heavy decks.
- **Rapid Rescue** — D (#858 release). Cantrip mill-2 for a permanent + 2 life; filler, pick late.
- **Reptil, Dinomorpher** — D/F (#858 release). Temporary stat boosts cost too much mana; "a way to lose games."
- **Rick Jones, Destined Sidekick** — D (#858 release). 3 mana to dig + mill four, capped uses; unappealing.
- **Serpent Specialist** — C (#858 release). 1/1 deathtouch powering up to 3/3; playable, not exciting.
- **Call Damage Control** — D/D+ (#858 release). Regrow up to two permanents; late refuel, low priority.
- **Claim the Kingdom** — C (#858 release). Landfall spreads counters then indestructible; stifles your curve.
- **Guerrilla Gorilla** — C (#858 release). 2/2 reach hero; free sac to destroy an artifact/enchantment.
- **Hellcat, Undying Vigilante** — B− (#858 release). 2/2 haste that returns bigger on death; GG cost hurts early.
- **Knight of Wundagore** — D (#858 release). One extra counter per turn; super replaceable.
- **Tigra, Feline Fury** — D, build-around C−/C with support (#858 release). Flash trample 2/1 needing lifegain counters.
- **Undercover Skrull** — B−/B (#858 release). 2-mana mana-dork that becomes a 3/3 all-types with a graveyard. Versatile. **CONFIRMED as the best green common and Marshall's personal favorite card of the whole format (#864).** "The card I'll miss drafting most — pick one, don't know where you're going with it yet, could end up 3-4 colors or just green-white. Every other archetype in this set felt on-rails by comparison." The one true "keeps you guessing" pick-one in an otherwise low-synergy format.
- **White Tiger, Ava Ayala** — B (#858 release). Power-up makes a 4/4 token + a 3/3. "Lots of value."
- **Ant-Man's Army** — C+ (#858 release). 3/2 with a Food or Treasure token; flexible value.
- **Hercules, Prince of Power** — C+ (#858 release). Raw stats; late 4/4 indestructible vigilance haste.
- **Hulkling, Burgeoning Bruiser** — B−/C+ (#858 release). Easily a 3/4+ vigilance in green, but "just stats."
- **Mister Hyde, Monster Within** — B− (#858 release). Draws or grows each upkeep; a must-kill 3/2 magnet.
- **Powerful Broker** — D (#858 release). Adds one counter of each kind; mediocre without counter support.
- **Punishing Punch** — B+ (#858 release). Often a one-mana instant dealing double power. "Premium green removal."
- **Restorative Technique** — D (#858 release). Ramp/fix + life + counter; needs real splash demand.
- **Pet Avengers** — C (#858 release). 4/4 reach common with strong power-up value; hard to miss.
- **She-Hulk, Jade Defender** — C+ (#858 release). 4-mana 4/4 reach trample; power-up destroys an artifact/enchantment.
- **Training Regimen** — D (#858 release). Counter + trample each turn, but no body — does too little.
- **Doc Samson, Super Psychiatrist** — D+ (#858 release). Doubling-Season mana-dork on a below-rate 5-mana 3/6.
- **Ka-Zar of the Savage Land** — A− (#858 release). 3/2 + landfall 2/2s; plays lands off the top. "Strong card advantage." Highest common/uncommon grade in the review. **Confirmed: "currently the best green card in win rate" (#860)** — still trailing plenty of white/blue commons in raw number, but the clear engine that makes GW/GU/BG all playable.
- **Super Strength** — D (#858 release). +4/+4 trample ward aura, no flash; high-variance — "you'll just kill people sometimes."
- **Wakandan Royal Guard** — D (#858 release). 5-mana 4/4 vigilance distributing counters; "a 24th-25th card" without a counters payoff.
- **Savage Land Dinosaur** — C (#858 release). 4GG 7/6 trample, basic landcycler. "Totally fine playable, hits land drops, feeds the GB graveyard count."
- **The Thing, Ben Grimm** — C/C− (#858 release). 6-mana 7/7 trample that grows off hero combat damage. "Absurdly large, not absurdly good — locked at six mana, doesn't protect itself." Worse than Savage Land Dinosaur next to it.

Green rares & mythics (#859 release-week):
- **Shang-Chi, Master of Kung Fu** — build-around B (#859 release). 1G 2/2 legendary hero; your creatures' abilities can be activated as though they had haste; tap for 2 mana of any one color, spend only on creature abilities. Needs power-up cards to be worth it, but "there's a ton of power-up around" so the support exists — treat as a good pickup once you know you're heavy on power-up creatures.
- **Epic Fight** — B (#859 release). 2G sorcery; choose one or both — double a target creature's power/toughness, and/or fight. "Basically means it kills anything and you still get in for a ton — the only real risk is casting it into open removal/bounce, so pick your window."
- **Heroic Feast** — build-around C (#859 release). 2G enchantment; ETB a Food; whenever you gain life, put that many +1/+1 counters split among up to that many creatures. "Not good enough on its own — you want 3-4 other lifegain sources before this is worth a deck slot."
- **Mole Man, Moloid Master** — D+ (#859 release). 2G 1/1 legendary villain; play lands from graveyard; landfall makes a 1/1 that mills on attack. "Everything here is just too small — you need a land in the yard to start the engine, and there's no reliable way to put one there early."
- **The Unbeatable Squirrel Girl** — A− (#859 release). 1GGG 4/4 legendary hero; ETB/attack makes a 1/1 squirrel; 1GG: make X 1/1 squirrels (X = squirrels you control). "Just always good if you can cast it — even without attacking, activate once for 2 squirrels, again for 4, and they have to answer it or die very quickly." The heavy green cost (GGG) is the only real drawback.
- **World War Hulk** — C− (#859 release). 3GG saga; free-cast your next red/green creature this turn → +3 counters on a creature → double power/toughness + trample. "Too all-in — no card is drawn, and if they have one removal spell for whatever you pump, you're just down a five-mana do-nothing."
- **Earth's Mightiest Heroes** — build-around C+/B (#859 release) → **SUPERSEDED UP (#864): 17Lands has it around B−, LSV floats it as high as A-ish.** 4GG sorcery, teamwork 5; reveal top 8, put a creature into play (ALL of them, into the graveyard otherwise, if teamworked). Needs real creature density (15-17) on both sides of the card to be worth it, but is a genuine blowout when it lands 3-4 bodies.

### Multicolor / gold (signpost uncommons + gold rares)
*(Each pair has one true-gold + one hybrid uncommon, plus — new in this update — the pair's gold rares/mythics. See `## Archetypes` for the per-pair plan and tier; grades repeated here for the card list.)*
- **Captain America, Living Legend** (WU) — B− (#858 release). Untaps the first creature tapped each turn — teamwork enabler.
- **Spider-Woman, Secret Agent** (WU, hybrid) — B (#858 release). Flash 1/4, flicker-lock a creature. "Solid first pick, most decks can cast it."
- **Kang, Temporal Tyrant** (UB) — B− (#858 release). 3/4 connives on attack + drains on 2nd-card-draw.
- **Ghost, Spectral Saboteur** (UB, hybrid) — C (#858 release). 3-mana flash 2/2 unblockable; secretly a BR/connive card.
- **Bullseye, Death Dealer** (BR, hybrid) — B+ (#858 release). Sac-artifact/discard → 2 damage, repeatable. "Justifies itself; loves trinket artifacts." *(Caption "Claw of Sauron's.")*
- **Madame Hydra** (BR) — B (#858 release). 2/1 menace token per villain cast; must-kill but fragile. *Predicted-volatile.*
- **Abomination, Terrifying Titan** (RG, hybrid) — B (#858 release). 4-mana 4/4 trample; a punchy 7-mana fight-machine.
- **Hulk, Gamma Goliath** (RG) — B−/B+ (#858 release). 5-mana 6/5 reach trample that cheapens other power-ups.
- **Spider-Man, To the Rescue** (GW, hybrid) — B−/C+ (#858 release). 3/2 flash that saves a creature with indestructible.
- **Black Panther, Vanguard** (GW) — B+ (#858 release). 4/4 that goes wide / pumps when heroes enter. Enabler + payoff.
- **Black Widow, Double Agent** (WB) — B− (#858 release). 3/2 deathtouch; lone attacker gets first strike + menace. Wants an aggressive shell.
- **U.S.Agent, John Walker** (WB, hybrid) — B (#858 release). 4-mana 4/4 leaving a +1/+2 equipment.
- **Speedball, New Warrior** (UR) — C+ build-around (#858 release). Effectively hexproof to targeted spells. *Predicted-volatile (could be B+).*
- **Iron Man, Master of Machines** (UR) — B+ build-around (#858 release). Flying/vigilance scaling + draws off artifacts. "All in on artifacts and strong at it."
- **Titania, Rugged Rumbler** (BG, hybrid) — B+ (#858 release). Bare 3-mana 5/5 with ward. "Make them figure it out."
- **Killmonger, Scourge of Wakanda** (BG) — B−/B (#858 release). Sac a creature → destroy any nonland permanent; +2/+1 with 2 creatures in yard.
- **War Machine, Legacy of Iron** (RW, hybrid) — C/C+ (#858 release). Finicky pump-flyer, low consistency.
- **Thor Odinson** (RW) — B−/C+ (#858 release). 5-mana 4/4 flying vigilance with DOUBLE prowess. Scary ceiling, "behind the curve untriggered."
- **Ant-Man, Colony Commander** (GU) — B+, "closer to A−" (#858 release). Counter on attack → makes insects. "Pushing the limits all by itself." **SUPERSEDED DOWN (#864): "ended up being a D partially, or at least a C partially — GU wasn't as good as we thought, and the counters/tokens plan just didn't come out particularly well."**
- **Beast, Erudite Aerialist** (GU, hybrid) — B− (#858 release). 3/3 that flies + draws when it connects (once you've counter'd it).

Gold rares & mythics (#859 release-week, grouped by pair):
- **King T'Challa** (WU) — A (#859 release). 1UW 3/2 flash legendary hero; whenever a player draws their 2nd card each turn, you draw. Transforms (or hard-casts, 4UW) into Black Panther, Hope Enduring — a 3/3 double strike that prevents ALL damage to itself and draws a card on combat damage to a player. "Just doesn't die to anything but destroy/exile; flash it in combat to eat an attacker and draw two cards off the hit."
- **The Mighty Thor, Jane Foster** (WU) — A (#859 release). 1UW 3/3 flying legendary hero; on attack, blink a nonland/nontoken artifact or creature (yours or theirs — tapped on return); whenever an equipment enters, draw a card. "Three mana 3/3 flying that removes blockers is already an A; the equipment upside is real but secondary."
- **Kang, Temporal Tyrant** (UB) — B−/B (multicolor review). 3/4 connives on attack + drains on your 2nd draw. Strong if it untaps and attacks; much better on the play.
- **Scientist Supreme of A.I.M.** (UB) — D (#859 release). 2-mana legendary villain; pay 2 life to copy an artifact ability you control. "Pretty mid — too many layers of 'how many artifacts, are you actually building around this' for a UB deck (the artifact-payoff colors are really UR, not UB)."
- **Taskmaster, Mercenary Mimic** (UB) — B+ (#859 release). 2UB 3/5 legendary villain; at the start of your main phase, becomes a copy of any creature on the battlefield or in a graveyard (name stays Taskmaster) until your next turn. "Cool stuff — copy something with power-up, power it up, then re-copy the new best thing next turn. A fine 3/5 body even doing nothing."
- **Bullseye, Death Dealer** (BR, hybrid) — B+ (#858 release). Sac-artifact/discard → 2 damage, repeatable. "Justifies itself; loves trinket artifacts."
- **Madame Hydra** (BR) — B (#858 release). 2/1 menace token per villain cast; must-kill but fragile. *Predicted-volatile.*
- **The Ruinous Wrecking Crew** (BR) — A− (#859 release). XBR legendary villain, enters as a 2/2 + X counters; ETB choose up to X (once each): rummage, opponent loses 2, destroy a token, or each player sacrifices a creature. "Hard for it to be bad — three mana 3/3, four mana 4/4, five mana 5/5, each with real upside stapled on."
- **Ares, God of War** (BR) — B (#859 release). 1BR 4/3 legendary villain, must attack; attacking creatures that die return to hand instead. "Not as risky as it looks — worst case you recast a 3-mana 4/3 that can still block the turn it comes down, and it protects your whole attacking team, not just itself."
- **Avengers: Under Siege** (BR) — B+ (#859 release). 2BR saga; two 2/1 menace villain tokens → 2 damage to each nonvillain creature and opponent → a Treasure per villain. "Good stuff up front (2 mana for two 2/1 menaces already), the middle chapter is a free bonus if it kills even one thing, and the treasures set up an explosive turn."
- **Abomination, Terrifying Titan** (RG, hybrid) — B (#858 release). 4-mana 4/4 trample; power-up to 7 to fight (like a 7-mana ETB). Instant-speed power-up creates good combat tension.
- **Hulk, Gamma Goliath** (RG) — C (#859 release). 3-mana 6/5 reach trample with power-up; cheapens other power-ups + pumps itself huge late. Solid big body, but a notch below the pair's real stars.
- **Alien Invasion** (RG) — B+ (#859 release). 1RG enchantment; each combat, make a hasted alien token that must attack, gets bigger (and existing tokens get counters) each subsequent trigger. "Slow the first two turns, then a huge problem — if the game goes long, you're going to lose to this."
- **Wolverine, Fierce Fighter** (RG) — A (#859 release). 2RG 3/5 legendary haste hero; ETB fights a creature; damage marked on Wolverine heals at end of turn (any single hit still kills him if lethal). "A four-mana 3/5 hasted fight that basically regenerates — kill a thing, smash for three, feels like an A every time."
- **Black Panther, Vanguard** (GW) — B+ (#858 release). 4/4 that goes wide / pumps when heroes enter. Enabler + payoff.
- **Spider-Man, To the Rescue** (GW, hybrid) — B−/C+ (#858 release). 3/2 flash that saves a creature with indestructible.
- **Storm, Windrider** (GW) — B (#859 release). 1GWW 4/4 legendary flying hero; your flying creatures can't be attacked/blocked by flyers; your targeted spells grant flying until end of turn. "Locks down all their natural flyers on a 4/4 body alone, and the second ability turns any pump/removal spell into a temporary flying-blocker or unblockable-attacker trick."
- **The Coming of Galactus** (BG) — A−/A (#859 release, Marshall lower / LSV higher, **SUPERSEDED UP toward LSV's read at #864**). 2BG saga; destroy a nonland permanent → opponent loses 2 (x2 chapters) → make Galactus, a 16/16 flying trample that destroys a land on attack. "Effectively a five-mana kill-anything sorcery with a bonus 16/16 three turns later — devastating even if the game ends before chapter four."
- **Killmonger, Scourge of Wakanda** (BG) — B−/B (#858 release). Sac a creature → destroy any nonland permanent; +2/+1 with 2 creatures in yard.
- **Titania, Rugged Rumbler** (BG, hybrid) — B+ (#858 release). Bare 3-mana 5/5 with ward. "Make them figure it out."
- **The Serpent Society** (BG) — B− (#859 release). 1BG 3/4 legendary deathtouch villain, ward — 5 poison counters (lose at 10); when another of your deathtouchers dies, each opponent sacrifices a nontoken creature. "You can't go too wrong with a 3-mana 3/4 death touch alone — the ward and poison text are gravy that rarely comes up, except the first ward hit is free, so make them pay it twice."
- **War Machine, Legacy of Iron** (RW, hybrid) — C/C+ (#858 release). Finicky pump-flyer, low consistency.
- **Thor Odinson** (RW) — B−/C+ (#858 release). 5-mana 4/4 flying vigilance with DOUBLE prowess. Scary ceiling, "behind the curve untriggered."
- **Daredevil, Man Without Fear** (RW) — A (#859 release). 2RW 3/4 legendary vigilance haste hero; you may look at your top card anytime; on attack, may exile your top card — if a hero, Daredevil gets +2/+1 — and you may play it that turn regardless. "Splash it into an all-villain deck and it's still a 3/4 vigilance haste that plays cards off the top; the hero-only pump is a bonus, not a requirement."
- **The Super Hero Civil War** (RW) — A+ (#859 release). 3RW saga; gain control of up to two creatures totaling ≤6 MV → your creatures get +1/+1 and vigilance → one of your creatures fights another. **"This might be the best card in the set — currently 71.3% GIH WR. You cast it and you basically win: steal their board, get a free pumped attack, then have their own creature kill their other creature."** Splash it in either color from pack three off any amount of fixing — "if you're neither color, just count your land cyclers."
- **Iron Man, Master of Machines** (UR) — B− (#858 release). Flying/vigilance that scales with + draws off artifacts. "All in on artifacts and strong at it."
- **Speedball, New Warrior** (UR, hybrid) — C+ (#858 release). Effectively spell-hexproof to targeted spells. *Predicted-volatile.*
- **Vision Quest** (UR) — build-around B/B− (#859 release). XUR sorcery; search library-or-graveyard for an artifact creature ≤X, put into play with X +1/+1 counters (haste if X≥4). "One of the bright spots of the format — best on War Machine (pumps equal to its power) but good enough as a general artifact tutor to pull you into the archetype on its own."
- **Ant-Man, Colony Commander** (GU) — see **SUPERSEDED** note above.
- **Beast, Erudite Aerialist** (GU, hybrid) — B− (#858 release). 3/3 that flies + draws when it connects (once you've counter'd it).
- **The Astonishing Ant-Man** (GU) — B (#859 release). 1UG 1/1 legendary hero; +1/+1 counter each time you draw a card (any draw, not just 2nd); 2G, tap, remove any number of counters to make that many 1/1 insects. "Doesn't ask much — just play it on two, it either gets killed or keeps growing, and you can cash counters for tokens whenever you want."
- **Absorbing Man** (GU) — B+ (#859 release). 1UG 4/4 legendary vigilance villain; at your main phase, copies a target artifact/nonaura-enchantment/land (keeps its own name/type/vigilance). "Plays better than it reads — copying a land, including the opponent's, turns it into a 3-mana 4/4 vigilance mana-fixer."
- **Moon Girl and Devil Dinosaur** (GU) — build-around B (#859 release). 1UG 2/2 legendary hero; whenever you draw your 2nd card, becomes a 6/6 trample until end of turn; whenever an artifact you control enters, draw a card (once/turn). "Two build-arounds in one card — either the artifact half (which also fixes the transform trigger) or a straightforward draw-two shell both make it playable."
- **Worlds Within Worlds** (GU) — unplayable (#859 release). 5UG sorcery; exile all creatures, each player may replay any number from hand, then return exiled cards to hand. "We don't need to go into it — not a card you want to pay seven mana for."
- **Thanos, the Mad Titan** (WBR / 5c) — C+ (#859 release). WBR 4/4 legendary deathtouch lifelink villain; power-up (colorless-heavy) to choose odd/even and destroy every other creature of that MV parity ("the Snap"). "A three-mana 4/4 death touch lifelink splash is legitimately fine on its own in a BR-plus-splash shell; mostly ignore the power-up unless your manabase is built to actually enable the colorless cost, which is the hard part."

### Colorless / artifacts
- **Vibranium Energy Daggers** — D (#858 release). Indestructible but uninteresting; equip 3 too hefty.
- **A.I.M. Synthoids** — D (#858 release). Needs artifact payoffs and still mediocre; plays for artifact count.
- **Dependable Quinjet** — D, near F (#858 release). Crew 4 is brutal; just a mana rock with no demand.
- **Ultron Drone** — C− (#858 release). Good filler; power-up to 4/5 + a 2/2 (Grave-Titan-ish).
- **Viv Vision, Teen Synthezoid** — C/C− (#858 release). Scales with the game; pump-able flyer, but power-up costs high.
- **H.E.R.B.I.E. Scout Unit** — C+ (#858 release). Cantrip + occasional ramp; flying is nice.
- **S.H.I.E.L.D. Helicarrier** — D− (#858 release). Crew 6 too much; tokens aren't artifacts. "Wouldn't play it."
- **Falcon's Wing Harness** — B− (#858 release). Free first equip; +1/+1 + flying + ward. "Very annoying in any aggressive deck." *(Listed blue in the data; an equipment.)*
- **Futurist Forge** — build-around C (#858 release). Needs artifact payoffs or you fall behind on mana. *(Listed blue.)*
- **Hydraulic Helper** — build-around C (#858 release). Cheap artifact mana-dork; part of most good artifact decks. *(Listed blue.)*
- **Shuri, Wakandan Inventor** — build-around B (#858 release). Cheapens artifacts + copies your best one. Enabler + payoff. *(Listed blue.)*
- **Super Suit** — D+, C in artifacts (#858 release). Free-equip combat trick; needs artifact synergies. *(Listed blue.)*
- **I Am Iron Man** — D+ (#858 release). Fringe; cantrip is fine but wants an aggressive/equipment deck. *(Blue instant.)*

Colorless rares & mythics (#859 release-week):
- **Captain America's Shield** — B+/B− (#859 release, hosts split — Marshall higher after LSV's in-play testimony). 2-mana legendary indestructible equipment; equipped creature gets +0/+8 and vigilance; tap a blocker on attack; equip 2. "Absurdly good — it's a 2/10 vigilance that taps their best blocker every attack, and if they don't have removal, they're just not attacking on the ground at all."
- **Super-Adaptoid** — D/C (#859 release, hosts split). 2-mana legendary artifact villain; power = your legendary creatures; ETB/attack, steal a keyword (haste, flying, first strike, etc.) from a target creature (yours or theirs) permanently. "Needs to be at least a 2/2, ideally 3/3, before the keyword-stealing starts to matter — the villain/artifact type is real upside, but the base card is unexciting."
- **Iron Man Armor** — A− (#859 release). 3-mana mythic equipment; ETB auto-attaches to target creature you control; +2/+1 flying, equip 2; 2: if not already a creature, becomes a 0/0 construct hero artifact with flying, +1/+1 per artifact you control. "Even without the animate mode this is amazing — a free first equip for +2/+1 flying is a beating on its own."
- **Ultron, Artificial Malevolence** — build-around B+ (#859 release). 3-mana mythic legendary artifact villain, 2/4; whenever another nontoken artifact you control enters, pay 2 to make a copy (nonartifact copies become 2/2 robot villains). "The stats alone (2/4 for three) are fine, and the copy mode is worth pursuing precisely because Ultron itself is an artifact — you're not diluting your build-around density to run the payoff."
- **The Vision** — A (#859 release). 4-mana rare legendary artifact hero, 2/5 flying vigilance; whenever you cast a noncreature spell, choose an unused mode this turn — double strike, indestructible, or draw a card. "Colorless, so it goes in literally any deck — every noncreature spell you'd cast anyway just got upside stapled on."
- **Arc Reactor** — F (#859 release). 5-mana rare artifact with improvise; enters tapped, taps for 3 colorless. "Not what you want to be doing in Limited — skip it outside a maximalist artifacts deck, and even then it's marginal."
- **Cosmic Cube** — B+ start, "could settle anywhere from B+ to B−" (#859 release). 5-mana mythic artifact, ward 2; on attack, look at top 6, free-cast anything with MV ≤ your biggest attacker's power. "High variance — sometimes it rots in hand, sometimes you curve a 4-drop into an attack, flip a spell, and the game's basically over. I'll take this card every time I open it."
- **The Ten Rings** — F (#859 release). 8-mana rare artifact; draw up to 10 at each end step. "You're never casting this, and if you do, you deck yourself."

### Lands
- **Avengers Hangar** — C/C+ (#858 release). Gain-land that fixes + adds wiggle room; "play as many as needed." **Confirmed and then some (#860): the gain-land is sitting at ~58.7% GIH WR** — "almost 50%... slightly edging out Iron Man Armor, the mythic" — a stark illustration of the color-rising-tide effect (blue/white's power inflates even their most modest fixing lands), not a statement that the card itself is a bomb.
- **Avengers Tower** — build-around B (#858 release). Good in a heavy-hero deck for the dig + fixing. **CONFIRMED strong, and specifically flagged as a bright spot alongside the land cyclers (#860): "the lands that draw cards — Avengers Tower, Baxter Building, Villainous Hideout — are all really good; normally these are too slow, but this format's pace let us actually use them."**
- **Baxter Building** — F (#858 release). Too slow; "won't spend five mana to draw a card." **SUPERSEDED (#860): "better than I thought — four-tap draw-a-card when you control a 4-toughness creature, plus a genuine four-color filter mode, is a free card in a lot of decks."** Revise up from F toward playable-fixing-land territory; still not a first-pick land, but not a trap either.
- **Surveillance Room** — D (#858 release). Only for three-color decks; low priority.
- **Villainous Hideout** — build-around C (#858 release). Run it in a heavy-villains deck, but not a focal point.
- **The land cyclers (Borough Backup, A.I.M. Scientists, Savage Land Dinosaur, Roxxon Brutes) — CONFIRMED a genuine bright spot of the whole format, not just "fine" (#860/#864).** "The Land Cyclers were a bright spot in this format — very very cool." Two-drop weakness elsewhere in the format means both hosts started actively using them ON TURN TWO as a real play, not just a last-resort fixer — a first for this card type in recent LR memory. They fix for *any* color (real fixing, not a same-color basic fetch), which is the specific design choice the hosts credit for the reversal from the usual "land cyclers underperform" pattern.
- *(The other named "building" duals — Asgardian Citadel, Birnin Zana Plaza, Castle Doom, Dark Fortress, Fisk Tower, Gathering Place, Gleaming Bastion, Hell's Kitchen, Hidden Lair, Los Diablos Missile Base, Pym Technologies, Stark Industries, Subterranean Cavern, Training Compound, A.I.M. Labs — all play the same way: fix colors at a below-rate cost + an expensive value mode. Take the one in your pair; treat as hero/villain build-around fixing.)*

Rare lands (#859 release-week):
- **The friendly-color rare dual cycle** (Gleaming Bastion and its five cycle-mates) — C, "good lands, better than the commons" (#859 release). Tap for colorless always; tap for one of two friendly colors if a land entered this turn or you control a basic. "Effectively straight-up dual lands in practice — it's hard to have three lands in play in Limited and not control a basic." Take over the common gain-lands when your colors line up.
- **Castle Doom** (colorless, artifact-matters) — build-around B− (#859 release). Taps for colorless; 1 of any color (artifact spells only); 3, tap, sac an artifact: make a 3/3 Doombot token (sorcery speed only). "Come around after playing the format more — the activated ability is a lot more live than it looks, since you'll often just have an artifact sitting around that's fine to upgrade into a 3/3."

### Bonus sheet (#859 release-week — appears ~once per 24 packs; mostly reprints)

*"Very rare that you'll see these — not like Secrets of Strixhaven where there was one in every pack. But there are a number of A-level cards on the sheet, so pay attention when they pop up, and some straight Fs too."* Notable hits, by color (grade shown where the hosts gave one; skip anything not listed — it was waved off as unplayable filler):
- **White:** Heavensent Marvel *(Archangel of Thune)* — auto-include if seen, "amazing by itself." Path to Exile — A−, "don't cast in the first ~5 turns if avoidable, but still great at one mana." Final Showdown — B (flexible trick / board wipe / Dub Blast hybrid). Steel Shaper's Gift — build-around C (needs an A-level equipment, e.g. Iron Man Armor or Captain America's Shield, to be worth it). Ephemerate — good with strong ETBs, situational. Concerted Effort, Don't Move, Light of Promise, Return to the Ranks, Righteous Fury, T'Challa's Protection *(Teferi's Protection)* — all F/avoid.
- **Blue:** Cyberdrive Awakener — strong auto-include in the artifacts deck (turns every noncreature artifact into a temporary 4/4). Dig Through Time — B−, a strong lategame two-of-the-top-7 spell, pairs well with connive. Counterspell — C+, playable. Simulacrum Synthesizer — build-around B, rewards a 2nd artifact after it resolves. Three Steps Ahead — B, flexible modal counter/clone/loot. Mechanized Production — "should probably never play this, but kind of fun and not literally an F." Show and Tell, Black Panther's Redirection *(Narset's Reversal)*, Reconnaissance Mission, Harbinger of the Seas, Lord of Atlantis (unless you have other merfolk) — avoid.
- **Black:** Widowmaking Infiltrator *(Dauthi Voidwalker)* — B+/A−, "super dangerous," unblockable 3/2 that can steal and free-cast the opponent's best exiled card. Deadly Dispute — C+, proven card, plays well with sac/artifact synergies. Extinction Event — B+/A−, a wrath you can usually set up to one-side. Final Act — C, a plain 6-mana wrath. Elektra, Deadly Assassin *(Massacre Girl)* — A, "played awesome, can wipe the whole board." No Mercy — F outside a dedicated lifegain shell.
- **Red:** Monstrous Rage — B/B+, "one of the best combat tricks we've seen, goes in almost any red deck." Fiery Emancipation, Chaos Warp — F. Fury of the Horde, Seize the Day, Bedlam — avoid ("don't play the extra-attack cards").
- **Green:** Ranker *(Rancor)* — B/B+ in an aggressive deck, "excellent, returns to hand instead of dying with the creature." Force of Vigor — sideboard only. Steely Resolve, Unnatural Growth — narrow/unplayable outside mono-green. Heroic Intervention (x3 copies seen in one pack!) — too purely defensive for the hosts' taste, no stat boost attached.
- **Multicolor/gold:** Anthem of Champions (GW) — B+/A depending on creature count. Aurelia, the Warleader *(Monica the Marvel)* (RW) — A if castable, "a beating — attacks for 6 by itself." Black Panther, Wakandan King (GW) — A−, absurd land-counter engine. Captain America, First Avenger (WUR) — B/B+, an equipment-throwing engine once running. Escape to the Wilds (RG) — B, a strong "draw 5" effect best cast on 6-7 mana. Fight to the Death (RW) — avoid, hard to profit from without a token theme. Iron Man, Titan of Innovation (UR) — A, a hasty flying 4/4 that "birthing pods" into bigger artifacts. Privileged Position (GW) — not applicable to Limited (combo piece). Ravenous Tyrannosaurus (RG) — B/B+, a devour-3 finisher, usually correct not to devour. Storm, Force of Nature (GUR) — B, castable but the storm-copy payoff is clunky. Sundering Growth (GW) — sideboard. Warleader's Call (RW) — A, "play this, play creatures, you win." Wolverine, Best There Is (RG) — B+/A−, double-damage regenerating threat-of-activation.
- **Colorless:** Patriotic Shield *(Sword of Fire and Ice)* — A, "complete beating," near-unbeatable if the opponent is red or blue and still excellent otherwise. Horn of Greed — F but funny (you pay for your own card draw too).

## Source episodes

- **#854** — pre-release banter (2026-05-24) — `KhuYIdOsl5s` — cited only for its confirmation that MSH does NOT use the Spider-Man set's dual-naming ("Omenpaths") system; no card grades.
- **#858** — Set Review: Commons & Uncommons (2026-06-17; release-week predictions) — `JM3Lz3tu7jY`
- **#859** — Set Review: Rares & Mythics + bonus sheet (2026-06-26; release-week predictions) — `y11-rxC1rQk`
- **#860** — Format Overview (2026-07-03; first week of real 17Lands data — establishes the WU-alone-on-top / BR-alone-on-bottom win-rate tiers) — `r5Ev8usyWwI`
- **#861** — Sealed strategy deep dive (2026-07-08) — `piD5IyFDfe0`
- **#862** — Draft Walkthrough, live pick-by-pick draft (2026-07-16; played read woven through commentary, no distinct summary segment) — `QdEu9FW1Jy4`
- **#864** — Sunset Show, end-of-format retrospective (2026-07-31; **the single most authoritative episode** — explicit "what we got wrong" grade corrections, hard archetype win-rate tiers, and the final format grade of **B** from both hosts) — `O9IUuoEAd6Q`
- *Settled.* This channel's MSH coverage now spans the full format lifecycle; no further LR MSH episodes are expected (the hosts have moved on to The Hobbit). Re-run the distill only if new content surfaces.
