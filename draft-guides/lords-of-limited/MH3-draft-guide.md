# Modern Horizons 3 (MH3) — Draft Guide

> Synthesized from 5 Lords of Limited episodes (crash course + early access + gameplay + RCQ). Coverage is moderate — one theoretical crash course, two early-access drafts, one arena gameplay video, one paper sealed/draft RCQ. No explicit late-season retro episode was captured. This guide is the lead lens that **decodes** the 17Lands data — every GIH WR is archetype-conditional (trust where it transfers, discount where it inflates; see AGENTS.md).

## ⚠ Recency rule (read first)

- Notes span **2024-06-03 → 2024-06-20**. On any conflict, the **newest episode wins**.
- The **2024-06-03 crash course** is BLIND PREDICTIONS (before any real games played, except ~3 practice-bot drafts by Ben) — weakest evidence; treat evaluations as hypotheses.
- The **2024-06-08 Early Access episodes** (Arena and MTGO) are first real reps — medium weight.
- The **2024-06-12 arena gameplay** and **2024-06-20 RCQ sealed/draft** are mid-to-late evidence, not a full retro, but more reliable than the crash course. The RCQ episode is the most authoritative source sampled.
- **This guide decodes the 17Lands data rather than ranking beneath it.** Every GIH WR is archetype-conditional — use the guide to tell which archetype's deck a number came from: trust the WR where it transfers (cleanly-castable cards), discount it where it inflates (payoffs/multicolor). See AGENTS.md.

## Source timeline

| Date | Episode title | Phase | Weight |
|------|--------------|-------|--------|
| 2024-06-03 | Modern Horizons 3 Coming to Arena!!! | Preview / crash course (pre-games) | **Weakest** — predictions only |
| 2024-06-05 | First Draft of a New Format - Modern Horizons 3 | Early Access Arena (Ethan solo) | Low-medium — first real games |
| 2024-06-08 | Modern Horizons 3 Early Access #MTGOCreator Draft Battle | Early Access MTGO (Ben vs Ethan) | Medium — early competitive reps |
| 2024-06-12 | INSANE Energy Deck in MH3 Draft | Arena day-1 gameplay (Ethan solo) | Medium — day-1 reps, energy focus |
| 2024-06-20 | Can we get the invite??? MH3 RCQ | Paper sealed + RCQ draft (Ethan) | **Most authoritative** — competitive event, more settled reads |

## TL;DR meta read

- **Three-wedge, high-synergy format.** The three mechanical wedges are (1) **Jeskai (RWU) — Energy aggro/tempo**, (2) **Abzan (WBG) — Modified/counters midrange**, (3) **Temur (RGU) — Eldrazi ramp/spawn**. Plus standalone **Blue-Black draw-three control** and **Red-Black artifacts**. Commit to one of these spaces early.
- **Energy is the most-open, highest-overlap theme.** Energy cards in Jeskai mostly stand on their own; they're good without the full engine and great with leftover energy. There are very few *repeatable* energy makers — conserving energy is key.
- **Eldrazi / big-Mana Temur is powerful and exploitable.** The RCQ episode confirms that ramping into 7+ CMC Eldrazi is a real game plan; the format is NOT "don't be mid-range" — it's "be aggressive or go over the top."
- **Galvanic Discharge is likely the best common in the set.** Flexible scalable removal that also generates energy.
- **Fetchlands (landscape lands) are premium** — they are triple-duty in this format: fixing, enabling brainstorm (with Brain Surge), generating energy (with Royal Cartographer), creating Eldrazi Spawn (with Skittering Precursor), and enabling Reckless Pyro-Surfer (?).
- **Modified is real but lighter-represented than expected.** Only 10 cards in the whole Abzan wedge explicitly care about "modified" — Cursed Wombat (BG signpost) is the payoff that makes the archetype worth pursuing. Evolution Witness is a key glue piece.
- **Red-Black artifacts is high-risk / high-reward** — needs Cranial Ram and enough artifact density; likely only supports one drafter per table. Cranial Ram is a bomb but avoid the archetype if you don't commit early.
- **Removal note:** Red doesn't have a clean "deal 2" or "deal 5+"; Galvanic Discharge fills the scalable role. Every color has good interaction. Wither and Bloom (Black instant, -3/-3 + graveyard mode) is one of the best commons.

## Archetype / color-pair tiers

Ranked by settled reads (RCQ + early access episodes). Where evidence is thin, noted as such.

| Pair | Colors | Tier | Game plan | Key commons/uncommons | Notes |
|------|--------|------|-----------|----------------------|-------|
| **Red-White** (Jeskai energy aggro) | RW | **S** | Aggressive energy — go-wide, use energy for pump/First Strike triggers. Very fast. | Galvanic Discharge, Thriving Skyclaw, Smelted Charge Bug, Amped Raptor, Ether Spike, Conduit Goblin | RCQ confirms: "best deck from earlier was a red-white aggro deck that went 7-1." Scurry of Gremlins as payoff. |
| **Blue-Red** (Jeskai energy tempo) | UR | **A** | Energy mid-range / tempo with Bespoke Battle Wagon engine. Dream Tide Whale build-around option. | Tune the Narrative, Galvanic Discharge, Bespoke Battle Wagon, Royal Cartographer, Ether Spike, Amped Raptor, Reiterating Bolt | Hosts drafted this multiple times. Battle Wagon is the core "engine." Consistent and powerful. |
| **Blue-White** (Jeskai energy flyers) | WU | **A** | Evasive energy threats, Riddle Gate Gargoyle + flyer package. | Riddle Gate Gargoyle, Tune the Narrative, Ether Spike, Mandibular Kite, Inspired Inventor, Static Prison | Riddle Gate Gargoyle (2-mana 2/2 flyer + 3 energy) is the premium signpost. Ethan took it to the top 8 draft. |
| **Black-Green** (Abzan modified/adapt) | BG | **A** | Adapt + counters synergy, grind with Cursed Wombat + Evolution Witness. | Wither and Bloom, Cursed Wombat, Evolution Witness, Lethal Throwdown, Refurbished Familiar (splash), Malevolent Rumble | Cursed Wombat is "nuts" — the signpost that makes BG worth pursuing. Wombat triggers counter doubling. |
| **Red-Green** (Temur Eldrazi spawn aggro) | RG | **A** | Eldrazi spawn go-wide into Titans Vanguard / Spawn Gang Commander. | Writhing Chrysalis, Eldrazi Repurposer, Spawn Gang Commander, Molten Gatekeeper, Reckless Pyro-Surfer, Malevolent Rumble | Reckless Pyro-Surfer with fetch lands + spawn tokens is a house. Molten Gatekeeper + spawns is surprisingly good. |
| **Blue-Green** (Temur ramp) | UG | **B+** | Ramp into big Eldrazi, Cosmotronic Sealing (?) + Monstrous Vortex build-arounds. | Malevolent Rumble, Eldrazi Repurposer, Annihilating Glare (?), Cox-on-Sealing (?), Path of Annihilation | Build-around enchantments (Cox-on-Sealing = "whenever you cast MV 4-6 get 2 spawns; MV 7+ draw 3") are the payoff. Malevolent Rumble is the glue piece here. |
| **Black-White** (Abzan modified artifacts) | WB | **B** | Death triggers on modified, Afterlife tokens, sacrifice synergy. | Dross Claw, Dread Mobile, Marionette Apprentice, Lethal Throwdown, Muster the Departed, Inspired Inventor | Less clearly supported than BG or WG. Muster the Departed ("Lingering Souls in disguise" per Ethan) is the payoff. Thin coverage. |
| **White-Green** (Abzan bestow/auras) | WG | **B** | Bestow creatures + Aura package. Tailspin Mentor (Golden-Tail Trainer?) is the signpost. | Indebted Spirit, Glyph Elemental, Dog Umbra, Mandibular Kite, Faithful Watchdog, Aria Auxiliary | "Golden-tail trainer is a house in green-white" per Ben at MTGO event. Faithful Watchdog is excellent here. Coverage thin — may be stronger than B. |
| **Red-Black** (artifacts) | RB | **B** | Artifact synergy, affinity payoffs, Cranial Ram + Dread Mobile. | Cranial Ram, Dread Mobile, Dross Claw, Refurbished Familiar, Marionette Apprentice, Pyretic Rebirth (BG uncommon) | High-risk high-reward. "Only supports one drafter per table." Feels like shooting the moon. Strong if you get Cranial Ram(s) early. |
| **Blue-Black** (draw-three control) | UB | **C+** | Draw three cards in a turn → payoffs (Mindless Conscription). Pure control. | Refurbished Familiar, Deem Inferior, Worm Coil Larvae, Arcbound Condor | Hard to assemble, no strong "draw-three" payoffs at common. Mentioned but not demonstrated positively in the sampled episodes. |

## Format principles

**Wedge structure — commit to a mechanic, not just colors:**
- Jeskai = Energy. Abzan = Modified/counters. Temur = Eldrazi/spawn. Two standalone: Blue-Black draw-three; Red-Black artifacts.
- Draft the *mechanic* you want first, then lock in the color pairs. Inspired Inventor (tuna white, 2/2, ETB: choose energy OR +1/+1 counter OR Servo token) is the archetypal "pivot card" — plays in all three wedges, great early pick.
- Cards that stand on their own in a wedge (energy cards that bring 3 energy and spend 2, leaving one behind) are more valuable than they look because extra energy is premium.

**Energy specifics:**
- Only two cards generate *repeated* energy: Bespoke Battle Wagon (tap for 2 energy) and Royal Cartographer (landfall: 1 energy). Everything else is one-shot.
- Evaluate energy cards as "what you see is what you get." A card that brings 3 and spends 2, netting 1, is a legitimate energy feeder.
- Tune the Narrative (1U, instant, draw a card + 2 energy) is the critical cantrip — it carries over both card and energy. High pick.
- Galvanic Discharge (R, instant, choose a permanent, get 3 energy, then pay any amount of energy to deal that damage) doubles as a removal spell AND an energy source. Best common in red.

**Fetchlands (landscape lands) are extremely high picks:**
- Tap for colorless OR fetch a basic of the wedge (ETB tapped) OR late-game cycle for a basic. Utility in multiple ways.
- Work with Royal Cartographer (energy), Reckless Pyro-Surfer (landfall), Skittering Precursor (create spawn when you sacrifice a non-token), Brain Surge (brainstorm-style with fetch shuffle).
- Brain Surge (2U, sorcery, draw 4 put back 2) + fetch = broken if you execute it correctly.

**Modified / adapt specifics:**
- Modified = creature has a counter, aura, or equipment. Low raw count of cards that *care* about modified (only 10 in Abzan), but evolve, adapt, and bestow interactions create a dense texture.
- Cursed Wombat (BG, 2/3 adapt 2 — when one or more +1/+1 counters are placed on *any permanent you control*, place an additional counter, once per turn) is the signpost that makes BG. It triggers the doubling on other adapt creatures too.
- Nesting Grounds (colorless land, move counters between permanents) is a high-upside utility land for BG and counter-based strategies.
- Evolution Witness (2G, 2/1 common, adapt 2 + whenever +1/+1 counters are placed on it return a permanent from graveyard) is a grindy value engine; higher on it post-crash-course.

**Eldrazi / Temur specifics:**
- You need the build-around enchantments (Path of Annihilation, Cox-on-Sealing) as the pull; then prioritize ramp pieces (Eldrazi Repurposer, Writhing Chrysalis, Malevolent Rumble, Nightshade Dryad) over the high-cost payoffs, because nobody else can take the big Eldrazi and you'll get them anyway.
- It That Heralds the End (common, 1 colorless — makes all colorless spells cost 1 less and pumps Eldrazi spawn to 1/1 or 1/2) is the most important common for the Eldrazi deck. Marionette Apprentice + spawn tokens creates a near-"Splinter Twin" lethal situation per Ethan.
- Big Eldrazi without ramp = clunky. Prioritize the two-drops that help you ramp.
- Colorless lands are important — the landscape lands double as wastes sources for Waste-Escape Battle Mage and Depth Defiler kicker.

**Red-Black artifacts:**
- Only 31 total artifacts in the set, only 18 in red or black. The deck needs Cranial Ram (common, 1/1 with equip for 1 energy) to function — if you don't see Rams, don't commit.
- Dross Claw (1B, living weapon equipment, equipped creature +1/+1 and drains on attacks, equip 2) enables Refurbished Familiar affinity and Lethal Throwdown sacrifice. Synergy C+ in the deck.
- Pyretic Rebirth (BR instant, return artifact/creature from graveyard + deal damage equal to its MV) is a two-for-one removal spell / recursion for the deck.

**Removal / interaction priorities:**
1. Galvanic Discharge (R, instant) — best removal in the set
2. Wither and Bloom (1B, instant, -3/-3 + graveyard reuse for +1/+1 counter) — best black common
3. Breathe Your Last (BB, instant, destroy any creature/planeswalker) — clean but double black
4. Fanged Flames (1R, sorcery, devoid, deal 4 + exile if dies) — good devoid synergy
5. Lethal Throwdown (B, sorcery, sac a creature OR modified creature to destroy target, draw if modified) — efficient with spawns and living weapon
6. Foul Strike / removal modes on MDFC cards

**Curve and land count:**
- Format has many incidental mana sinks (adapt costs, equip costs, energy activations) but fewer persistent activated abilities than typical.
- Run 18 lands if you have big top-end or splash. 17 works with a tight low-curve energy deck (Ethan ran 16+2 MDFCs in his blue-red energy deck).
- MDFCs (hybrid modal double-faced cards at uncommon — one side spell, other side ETB-tapped dual) are C+ baseline across the board — always play them in your colors as fixing, never prioritize them highly.

**Sweepers:**
- Very few. Wrath of the Skies (XX + WW, get X energy then destroy artifacts/creatures/enchantments with MV ≤ energy paid) at rare. Ral and the Implicit Maze (3R saga, chapter 1 deals 2 to all opponent creatures/PWs, chapter 2 discard + impulse, chapter 3 make a Weird creature) is the best accessible partial-sweeper at uncommon — Ben grades it B-minus.
- Colossal Dread Mask (4G common equipment, living weapon, +6/+6 trample, equip 3GG) is a recurring threat that forces opponents to run sweeper-type interaction; main-deck enchantment removal becomes important.

**Draft signals:**
- Green being underdrafted is a tell that the Eldrazi space is open. Green was overdrafted in Ben's early practice drafts suggesting it'll be contested at first.
- Energy cards in Jeskai colors drying up quickly signals those lanes are contested. Watch for late Tune the Narratives as a signal blue energy is open.
- If Cranial Ram or Dread Mobile tables early, artifacts may be open.

## Card notes (community consensus)

Later takes override earlier takes. "(CC)" = crash course prediction; "(EA)" = early access; "(RCQ)" = RCQ/late episode.

### White

- **Inspired Inventor** (2W, 2/2, ETB: choose energy OR +1/+1 counter OR Servo token) — B+; the best pivot card in the format, playable in all three wedges. Went late in CC practice drafts.
- **Aria Auxiliary** (3W, 3/3 flyer, ETB support 2 — put +1/+1 on up to two other creatures) — B; best white four-drop, turns all your cheap creatures into interchangeable threats. No other good fours in white.
- **Expel the Unworthy** (1W sorcery, exile MV 3 or less; kick 2W = exile any, opponent gains life) — C+; cleanest white removal despite the life-gain rider.
- **Indebted Spirit** (W, 1/1 bestow for 2W, afterlife 1) — C+; good in aggressive WG and WB. Gets spirit after blocking/dying; solid in modified/sacrifice synergy.
- **Dog Umbra** (1W, flash aura, pacify opponent's creature OR protection for your own, umbra armor) — C; flexible but neither mode is great. Better in GW bestow decks.
- **Muster the Departed** (2W enchantment, ETB 1/1 flying spirit; morbid at EOT populate) — B (Ethan); worse if your deck isn't aggressive. Token doubler ceiling compares to Lingering Souls but requires creatures dying on your turn.
- **Metastatic Evangel** (1W, 3/1, whenever another creature ETBs proliferate) — B; best white uncommon per Ben; proliferates energy counters AND +1/+1 counters. Great pivot card.
- **Proud Pack Rhino** (2W, 3/3, ETB shield counter on target OR proliferate) — B; plays in multiple archetypes. Either creates a modified creature or charges up energy.
- **Johnny Fels, the Godsire** (3WW saga, ch1 exile power 3+ creature, ch2 get cat warrior + vigilance counter, ch3 double strike until EOT) — B (Ben's #2 white uncommon); premium removal saga.
- **Glyph Elemental** (1W, 2/2 bestow 1W, landfall: +1/+1 counter on self; enchanted creature gets +P/+P per counter) — B (Ben's #1 white uncommon); two-mana growing threat, great with fetches.
- **Mandibular Kite** (W, living weapon equipment, +1/+1 + flying, equip 3W) — B (Ben's #3 white uncommon); a recurring evasion threat that can be re-equipped after the token dies.
- **Jolted Awake** (W sorcery, get 2 energy, pay energy = card's MV to return artifact or creature from graveyard to battlefield; cycle 2) — C+; high ceiling with leftover energy; can return a four-drop for 1 mana effectively.
- **Thraen Charm** (1W instant, deal damage = 2x creatures you control OR destroy enchantment OR exile target graveyard) — C+ (Ethan) vs C- (Ben); Ethan likes it in go-wide decks with spawn tokens.

### Blue

- **Tune the Narrative** (U, instant, draw a card + 2 energy) — B+; Ethan's #1 blue common; the key energy cantrip. Always in the top picks.
- **Deem Inferior** (3U sorcery, costs 1 less per card drawn this turn; put nonland permanent 2nd from top or bottom) — B+; effectively costs 1-2 in blue draw-three decks. Exceptional tuck effect.
- **Ether Spike** (1U instant, choose a spell, get 2 energy, then counter it unless its controller pays 1 for each energy paid) — B; flexible counterspell that also fuels the energy deck. Ben's #3 blue common.
- **Demon Fuor** (?) / **Demi-fuor** (?) — Ethan's #1 blue common over Tune; context suggests a high-impact rare blue creature (possibly Ethan's pick; name garbled in transcripts).
- **Bespoke Battle Wagon** (3U, 5/6 vehicle uncommon; tap for 2 energy; pay 2 energy to tap creature; pay 3 energy to draw a card; pay 4 energy to animate it; crew 4) — B; the format's primary repeatable energy generator; great in blue-red or any energy deck.
- **Royal Cartographer** (1U, 1/3, landfall: get 1 energy; pay 6 energy: draw 3) — B+; synergizes with fetches to generate energy; Ethan took two copies and said they were instrumental across multiple games.
- **Brain Surge** (2U, sorcery, draw 4 put back 2) — B/B-; Ethan's take — with fetchlands this is essentially brainstorm-on-steroids. High pick.
- **Cox-on-Sealing** (?) (2U enchantment, devoid; whenever you cast MV 4/5/6 creature: get 2 Eldrazi spawn; whenever MV 7+ creature: draw 3) — B (Ben's #1 blue uncommon); major payoff for the Eldrazi ramp deck.
- **Emers' Messenger** (?) (1U, 2/1 flyer, when you draw your 2nd card each turn: get an Eldrazi spawn) — B; good in draw-heavy blue; two-mana 2/1 flyer already fine.
- **Hope-Ender Quaddle** (?) (2U, 2/2 flash flying; ETB counter target spell opponent controls unless they pay 1) — B; the "Mystic Snake" analogue that Ben laments; soft counterspell on a flash flyer is powerful tempo.
- **Twisted Riddle Keeper** (8U, 5/5 flying; cast tap up to 2 permanents putting stun counters on them; has emerge for 5U sacking a creature) — B; Ben's later #1 blue uncommon. Turn-4 emerge play is back-breaking: 5/5 flyer that stuns two things.
- **Electro Zoa** (2U, 3/1 flash flying; ETB 2 energy; upkeep tap unless you pay 1 energy) — D+(Ben)/C (Ethan); best mode is flash-blocking as a removal spell + leaving 2 energy. Body itself is bad.
- **Utter Insignificance** (1U, aura flash; enchanted creature loses abilities and is 1/1; pay 2 colorless to exile it) — C (Ethan) vs C- (Ben); Ethan: "removal that gets the job done and can exile in a format with big Eldrazi."
- **Subtlety** (reprint, 4U) — A bomb; pick it.
- **Nadu, Winged Wisdom** (1GU, 3/4 flyer; whenever creatures you or opponents target: reveal top of library, land → battlefield, nonland → hand; triggers twice per turn) — A; game-changing when it resolves; Ethan P1P1'd it in the RCQ draft.
- **Drowner of Truth** (blue mdfc cycling Eldrazi) — C+ as a tapped Island that can grow late; play in most blue decks.

### Black

- **Wither and Bloom** (1B instant, target creature -3/-3 until EOT; exile from graveyard to put +1/+1 counter on a creature you control at sorcery speed) — B+; Ben and Ethan's #1 black common; premium removal that keeps giving.
- **Breathe Your Last** (BB instant, destroy any creature or planeswalker, gain 1 life per color it has) — B; clean unconditional removal, double black cost is the only downside.
- **Refurbished Familiar** (3B, 2/1 flying; affinity for artifacts; ETB: each opponent discards a card, and for each who can't, you draw a card) — B; format-defining black common. In artifact decks costs 1-2 and is a 2/1 flyer that strips hands.
- **Dross Claw** (1B, living weapon equipment; +1/+1 + drain 1 life on attacks; equip 2) — C+ (Ethan, specifically for black-red artifacts); the Nazumi Link Breaker analogue for the artifact deck. Enables affinity for Refurbished Familiar.
- **Dread Mobile** (2B, 3/3 Menace artifact vehicle; pay 1 + sac artifact/creature to put +1/+1 counter; crew 1) — B; both Ben and Ethan's top-two black uncommon. Good well beyond red-black; premium early pick.
- **Worm Coil Larvae** (3BB, 3/3 deathtouch lifelink; on death: 1/2 deathtouch token + 2/1 lifelink token) — B; Ben's #1 black uncommon; high stats and persistent threat.
- **Arcbound Condor** (2BB, 0/0 flying artifact with modular 3; ETB with 3 counters; on death move counters to target artifact; whenever another artifact ETBs target opponent's creature -1/-1 until EOT) — B; Ben's #3 black uncommon. The -1/-1 trigger is a pseudo-Aetherborn Marauder effect.
- **Marionette Apprentice** (1B, 1/2; fabricate 1; whenever another artifact you control goes to graveyard from battlefield, each opponent loses 1 life) — B; Ben's alternate #3; "Splinter Twin situation" with Eldrazi spawn tokens per Ethan. Wins from nowhere.
- **Lethal Throwdown** (B sorcery, sac a creature or modified creature to destroy target creature/planeswalker; if modified was sacrificed: draw a card) — B- (Ethan)/C (Ben); better Bone Splinters in a format full of spawn tokens and living weapon creatures.
- **Grim Servant** (3B, 3/2 Menace zombie; ETB search your library for a card with MV ≤ your Devotion to Black, reveal, put in hand, lose 3 life) — C+ (Ben)/C (Ethan); very wide range depending on board state; feels uncastable when behind.
- **Arcbound Ravager** (if drafted) — auto-bomb in artifacts.

### Red

- **Galvanic Discharge** (R instant, choose creature/planeswalker, get 3 energy, then pay any amount of energy to deal that much damage) — **A**; likely best common in the set. Scales to remove any threat, generates energy.
- **Thriving Skyclaw** (RR, 3/2 flyer; ETB 3 energy; attack: pay 3 energy for +1/+1 counter) — B (Ethan); four-mana 3/2 flyer that brings 3 energy with upside.
- **Fanged Flames** (1R sorcery, devoid, deal 4 to creature/planeswalker; if it would die exile it instead) — B; Ethan's #2 red common. Clean 4-damage removal with exile upside.
- **Smelted Charge Bug** (1R, 1/3 Menace artifact; ETB 2 energy; when attacks pay 1 energy to give another attacker +1/+1 and Menace) — B (Ben's #3 red common); plays in multiple archetypes, energy feeder, relevant body.
- **Amped Raptor** (1R, 2/1 first strike; ETB 2 energy; if cast from hand exile until you hit a nonland, may cast it by paying energy equal to MV) — B+; Ben's #1 red uncommon; high-power "cascade"-style effect that converts energy.
- **Reiterating Bolt** (1R sorcery, deal 3 to creature/planeswalker; replicate: pay 3 energy for another copy) — B; Ben's #3 / Ethan's #3 red uncommon; flexible 3-damage + energy sink.
- **Spawn Gang Commander** (3RR, 2/2; cast: create 3 Eldrazi spawn; pay 1 colorless + sac spawn: deal 2 to any target) — B; Ethan's #2 red uncommon; combo with Titans Vanguard; great go-wide threat.
- **Ghostfire Slice** (2R instant, devoid, costs 2 less if opponent controls a multicolored permanent; deal 4 to any target) — B (Ben's #2 red uncommon); essentially free in most matchups.
- **Ral and the Implicit Maze** (3R uncommon saga; ch1: 2 damage each opponent creature/PW; ch2: discard + impulse 2; ch3: make 2/2 Weird that grows from noncreature spells) — B- (Ethan) / C+ (Ben); sweeper effect on ch1 is inconsistent but the whole package does a lot for 5 mana.
- **Scoia Ember Mage** (4RR, 4/4 legendary; ETB deal 4 to any target; grandeur: discard another Scoia, sac 2 mountains to deal 4 more) — C+; six-mana 4/4 with ETB burn is floor; can be game-ending with multiples in hand.
- **Reckless Pyro-Surfer** (?) (2R, 2/2; landfall: create an Eldrazi spawn?) — B; Ethan was "not on until early access" but it's phenomenal with fetch lands and a go-wide Eldrazi deck.

### Green

- **Eldrazi Repurposer** (2G, 3/3 devoid; ETB create Eldrazi spawn; on death create Eldrazi spawn) — B (Ethan's #1 green common); the engine piece of the Eldrazi deck. Green's best common glue.
- **Writhing Chrysalis** (2RG, 2/3 devoid; reach; ETB create 2 Eldrazi spawn; whenever you sacrifice an Eldrazi put +1/+1 counter on it) — B; Ethan and Ben: "just a house as far as stats go." Four mana for a 2/3 + two spawn tokens + scales up.
- **Nightshade Dryad** (1G, 1/1 with deathtouch; tap for colorless, tap for any color) — B (Ethan's #2 green common); the Mana Dork of any color; makes splashing Eldrazi costs easy.
- **Malevolent Rumble** (1G sorcery, reveal top 4, keep a permanent, rest to graveyard, create Eldrazi spawn) — C+ (Ben, Ethan agrees for Temur); excellent digging tool to find enchantments and ramp payoffs in the Eldrazi deck. Graveyard synergy bonus.
- **Colossal Dread Mask** (4G, living weapon equipment; +6/+6 trample; equip 3GG) — C+/B; both hosts agree it's a scramble-inducing card in the format. Forces opponent to run main-deck removal for artifacts/enchantments. "If you're casting those large Eldrazi…"
- **Horrific Assault** (G sorcery, target creature you control deals damage equal to power to target creature you don't control; if you control an Eldrazi gain 3 life) — B (Ben's #1 green common, surprising himself); 1-mana fight with conditional lifegain.
- **Signature Slam** (2G instant, put +1/+1 counter on target creature; each modified creature you control deals damage equal to its power to target creature you don't control) — B (Ben's #3 green common); "Clearshot with upside"; modified fight that hits each creature.
- **Annoy-o-Altisaur** (5G, 6/5 reach trample Cascade) — B+; Ben and Ethan's #1 green uncommon; hard to race, cascades into relevant spells.
- **Path of Annihilation** (3G enchantment; ETB create 2 spawn; Eldrazi you control tap for any color; whenever you cast MV 7+ creature, gain 4 life) — B; Ben and Ethan's #2 green uncommon. Turns spawn into any color Mana AND gains life with big spells.
- **Propagator Drone** (1G, 2/2 devoid; devoid tokens you control have evolve; pay 3G to create Eldrazi spawn) — C+ (Ethan)/C (Ben); even without the activated ability, spawn tokens naturally evolving into 1/2s or 2/3s is strong in the go-wide deck.
- **Monstrous Vortex** (3G enchantment, whenever you cast a creature with power 5+, discover X = that spell's MV) — B (Ben initially); note: it's power 5+ not MV 5+. Chains are possible: discover into another power 5+ triggers again.

### Multicolor

- **Riddle Gate Gargoyle** (WU, 2/2 flying; ETB 3 energy; when attacks pay 2 energy to give a creature lifelink until EOT) — B (Ben) / B- (Ethan); the premier energy two-drop. "Two-mana 2/2 flyer + 3 energy" passes the vanilla test and then some.
- **Cursed Wombat** (BG, 2/3 uncommon; adapt 2 for 2BG; whenever one or more +1/+1 counters are placed on *any* permanent you control, place an additional counter once per turn) — A; "clearly the most powerful gold uncommon" per crash course. Doubles counters on every adapt creature you control. Possibly the single strongest uncommon in the set.
- **Inspired Inventor** (2W, 2/2; ETB: energy OR +1/+1 counter OR Servo token) — B+; note: despite being white it is THE pivot card across all three wedges.
- **Pyretic Rebirth** (BR instant, return artifact/creature from graveyard, Pyretic Rebirth deals damage equal to that card's MV to a creature/PW) — C+/B-; "two-for-one removal + recursion at instant speed" specifically for red-black artifacts. Artificially high MV from affinity means you can hit big.

### Colorless / Artifacts

- **Bespoke Battle Wagon** (see Blue) — key repeatable energy generator.
- **Solar Transformer** (2 colorless artifact; ETB tapped, ETB get 3 energy; tap for colorless; tap + 1 energy for any color) — B (Ben)/C+ (Ethan); flex card that plays in energy decks AND Eldrazi decks. Ben thinks it's premium; Ethan doubts the colorless Mana matters enough.
- **Cranial Ram** (common, artifact equipment; equip for 1 energy — equipped creature gets +1/+1 and has "when you gain life" effects?) — B+; the backbone of red-black artifacts. Went late in MTGO early access ("should not be going this late," notes Ethan).
- **Vexing Bobble** (1 colorless artifact; when a player casts a spell without paying its Mana cost, counter it; pay 1, tap, sac to draw a card) — D+(Ben)/C (Ethan, specifically in black-red as a 1-mana accelerator for affinity that cashes in for a card later).
- **Worn Power Stone** (2 colorless artifact; ETB tapped; tap for 2 colorless) — C+; pairs with big Eldrazi that need colorless Mana. Path of Annihilation makes spawn do any color, but this accelerates.

### Lands

- **Landscape lands** (one per Temur/Abzan/Jeskai wedge; tap for colorless; search for a basic of either wedge color ETB tapped; late-game cycle for a basic) — **A**; among the best fixing ever printed for Limited. Always high picks in the relevant colors. Enable splashes, produce colorless for Eldrazi kicker, cycle to avoid flooding.
- **Nesting Grounds** (tap for colorless; pay 1, tap, move a counter from one permanent to another at sorcery speed) — B- (Ben)/C (Ethan); game-changing in black-green counter decks; lets you re-trigger adapt bonuses; utility land worth the colorless slot in BG.
- **Fetch lands** (Wooded Foothills, Polluted Delta, etc.; reprints at rare/uncommon) — **A**; premium in almost every deck. Shuffle effects with Brain Surge, energy with Royal Cartographer, spawn with Skittering Precursor, landfall with Reckless Pyro-Surfer. Take very highly.

### Rares & bombs

- **Nadu, Winged Wisdom** — A; auto-first-pick. Abuses any targeting abilities and fetch land cracks to flood the board with lands and cards.
- **Subtlety** — A; reprinted bomb counterspell creature.
- **Titan's Vanguard** (?) (5 colorless, 5/5 trample; when attacks, put a +1/+1 counter on each colorless creature you control) — A; everything in Eldrazi tribal is colorless; this is an Overrun for the Eldrazi deck.
- **It That Heralds the End** (1 colorless; all your colorless spells cost 1 less; ETB pumps spawn tokens to 1/1 or 1/2) — A-; the glue of the Eldrazi deck at common cost. Multiple copies are fine.
- **Echoes of Eternity** (colorless enchantment rare; triggered abilities of colorless spells trigger an additional time; whenever you cast a colorless spell copy it) — A bomb; "got got" by it in early access per Ethan. Pure combo ceiling with Eldrazi.
- **Wrath of the Skies** (XX + WW sorcery; get X energy, may pay energy to destroy each artifact/creature/enchantment with MV ≤ energy paid) — A; flexible sweeper; very good in a format where creatures are often small.
- **Toxic Deluge** (reprint, 2B sorcery; pay X life, all creatures -X/-X) — A; powerful flexible wrath.
- **Diesa, the Restless** (?) (5 colorless, 5/6; when creatures deal combat damage make Lurker/Tag tokens; lurker can become a copy of a card in graveyard) — A; hard to evaluate from captions but Ethan snapped it up.
- **Path of Annihilation** (see Green uncommons) — Strong synergy rare; Ethan called it "another Writhing Chrysalis" for the Eldrazi ramp deck.
- **Ocelot Pride** (W uncommon saga/enchantment?; if you gained life this turn make a 1/1 cat; city's blessing: copy tokens) — A; "how does one gain life?" Ethan noted, but strong if triggered.

## Signals & seat reads

**What goes late / signals openness:**
- **Inspired Inventor** going late means ZERO of the three wedges is being contested at your table — very rare. Usually signals inexperienced table. Snap it up.
- **Galvanic Discharge** going late is alarming and suggests the red energy lane has already been spoken for multiple seats.
- **Refurbished Familiar** going late (happened in multiple early-access events) signals the artifacts lane is wide open — commit if you see it.
- **Cursed Wombat** going late (it wheeled once in Ethan's draft) is a massive signal that BG counter/adapt is wide open.
- **Cranial Ram** going late (it wheeled in MTGO early access) is the clearest signal to jam red-black artifacts.
- **Landscape lands** going very late signals a color pair in that wedge is empty; everyone needs these for their respective wedge.
- **Royal Cartographer** (late pick) = nobody at table is in blue energy; blue is wide open.

**Pivoting:**
- The "practice drafts had terrible packs" warning from Ben in the CC is validated in early access — some packs are truly weak. Don't force a commitment; take good cards early even if they're in the wrong color if they're clearly the best.
- Green was overdrafted in early practice drafts (Ben notes "OTJ bleed, love of green"). Expect it to be contested early in the format.
- Red-black artifacts: commit by pack 2 or don't. The deck needs multiple Cranial Rams and cannot survive with only 1-2 relevant artifacts. If you're 4 picks in and haven't seen Ram or Dread Mobile, bail into another archetype.
- The three-wedge structure means pivoting across full wedges (e.g., Jeskai to Temur) is painful. Pivot within a wedge first (RW → RU → UW all stay in Jeskai).

## Supersessions (early-was-wrong, now corrected — NOT live disagreements)

1. **Bespoke Battle Wagon (CC → EA):** Ben initially graded it C- in the crash course ("I'm not convinced this pulls me into blue"). After the MTGO early access, he said "I think this card is going to be like that [5/5 that just sits on the board] plus the energy. I agree I like this card, I'm coming around to B-minus." The vehicle's 4-energy "become a creature" ability acts as a perpetual blocker threat. **Early: C-. Later: B-. Verdict: Ben was too low.**

2. **Malevolent Rumble (CC → later):** Ethan originally graded it C- in the CC ("just doesn't do enough to me"). By the MTGO early access he was impressed: "Malevolent Rumble was great" after seeing it in action finding build-around enchantments and payoffs. **Early: C-. Later: C+/B-. Verdict: Ethan was too low.**

3. **Reckless Pyro-Surfer (CC → EA):** Ethan was "not on [Pyro-Surfer] until early access. I had a red-white deck with a couple of them and just like any go-wide stuff with Pyro-Surfer is fantastic." Suggests the crash course underrated it. **Early: not graded as premium. Later: B (clear standout in go-wide). Verdict: underrated pre-games.**

4. **Writhing Chrysalis (CC → EA):** Ben was lower on it initially ("a c that's a nice take"), moved up after the Ethan early access EA where it was described as "a house — two mana value, four mana for a 2/3 + two spawns + scales up." **Early: uncertain/C. Later: B. Verdict: underrated.**

## Live disagreements (genuine, unresolved)

- **Solar Transformer:** Ben grades it B ("premium flex piece, repeatable color fixing AND energy generation"); Ethan grades it C+ ("I don't love the two-mana manaDork in this form even though it can't die"). Unresolved — both could be right depending on how important colorless mana turns out to be.
- **Galvanic Discharge vs. other blue commons for #1 spot:** Ben says Galvanic Discharge is "probably best common in the set"; Ethan's #1 blue common is Tune the Narrative. Not a real dispute — they mean best in different colors — but underscores that both are top-tier and format-defining.
- **Ether Spike vs. Amped Raptor for #1 blue uncommon:** Ethan (Ether Spike #1) vs. Ben (Amped Raptor #1). Ether Spike is better in pure energy decks; Amped Raptor has more raw card-advantage ceiling. Ethan updated his MTGO deck by going "4x Ether Spike" so he's all-in.
- **How much to commit to Eldrazi at the start:** Ben warned "high risk if you pick the build-around enchantments first and don't get the big Eldrazi"; Ethan felt "take the ramp pieces and assume you'll get the payoffs." The RCQ suggests Ethan's approach is correct — prioritize ramp, the big stuff comes late.

## Card-name caveats from caption garble

The following names were uncertain or clearly mangled in auto-captions. Context was used to correct; marked with (?) where uncertainty remains:

- **"Writhing Crysalis" / "Rything Crysis"** → Writhing Chrysalis (RG common, 2/3 devoid, ETB two spawn)
- **"Cox on ceiling"** → likely **Cox-on-Sealing** or something similar (blue Eldrazi enchantment uncommon)
- **"Hender quaddle" / "Hope Ender quaddle"** → **Hope-Ender Quaddle** (?) (2U, 2/2 flash flying + soft counterspell ETB)
- **"Curs wombat" / "Cursed Wombat"** → Cursed Wombat (BG uncommon signpost) — this one is clear
- **"Titans Vanguard"** → **Titan's Vanguard** (?) (colorless uncommon, 5/5 trample, pumps all colorless when attacks)
- **"bountiful landscape" / "for boating landscape"** → Foreboading Landscape (?) / Bountiful Landscape (?) — various landscape fixing lands; names garbled throughout
- **"Cox unsealing"** → same as Cox-on-Sealing (?)
- **"Reckless pyrro Surfer"** → **Reckless Pyro-Surfer** (?) (red common with landfall ability)
- **"Condor"** = Arcbound Condor (BG artifact uncommon) — confirmed
- **"Galvanic discharge"** = Galvanic Discharge — confirmed
- **"deminfuor" / "demon fuor"** = **Demon-Fuor** (?) — high-impact blue card per Ethan; possibly a rare; name heavily garbled
- **"Diesa the Restless" / "daa"** = **Diesa, the Restless** (?) (tricolor rare)
- **"mustar The Departed"** = **Muster the Departed** (white uncommon enchantment) — confirmed by context
- **"Warren Soul Trader"** = **Warren Soul Trader** (pay 1 life, sac creature, make treasure)
- **"utter insignificance"** = **Utter Insignificance** (1U, aura, creature loses abilities and becomes 1/1)

## Source episodes

- 2024-06-03 — Modern Horizons 3 Coming to Arena!!! (68oXLXdSuD0)
- 2024-06-05 — First Draft of a New Format - Modern Horizons 3 (bieSwnm7ROM)
- 2024-06-08 — Modern Horizons 3 Early Access #MTGOCreator Draft Battle (Ha5oVgjxnSk)
- 2024-06-12 — INSANE Energy Deck in MH3 Draft (-cf9DheUNJU)
- 2024-06-20 — Can we get the invite??? MH3 RCQ (7pTxCE5jfdo)
