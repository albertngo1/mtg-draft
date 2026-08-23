# MSH — Numot draft notes

> Source: NumotTheNummy (Kenji Egashira) regular Arena draft VODs — **FULL-FORMAT COVERAGE, built 2026-08-23** from 35 captioned gameplay VODs spanning 2026-06-23 (release day) through 2026-08-10 (his last MSH draft before the channel moved on). Card/mechanic names corrected against `data/cache/17lands_MSH_PremierDraft_1200d.json` where confident; garbled auto-caption readings marked `(?)`.
>
> **One VOD remains uncaptioned and pending:** `YAyuBb6Pbkk` "SOLVING MARVEL SUPER HEROES DRAFT | June 24" — YouTube never generated auto-subs for it (`fetch.log`: "no auto-subs"). Add if captions ever land; low priority since it sits right inside the already-covered 6/23–6/24 release window.
>
> **One VOD is out of scope by contract:** `tBrpT0pf9Uw` "Is Pick-Two Draft Just Easy Wins?" (2026-08-04) is a **Pick-Two Draft** — you take 2 cards per pick instead of 1. Kenji himself frames it as a novelty variant, not the intended way to draft this format ("this again is not a format intended for pick two... the Hobbit is going to be a format intended for pick two"). Excluded per the channel's "regular Arena draft" scope; its picks/curve logic don't transfer to normal single-pick MSH drafting.
>
> Across 35 games' worth of gameplay Kenji logs a career **~62% win rate** in the format (his own tally, stated in the final 8/10 episode) — solidly above break-even, so his reads below are a strong signal, not a struggling drafter's excuses. Still: **17Lands GIH WR is the primary signal** — this guide only decodes it (see AGENTS.md).

## ⚠ Recency rule (read first)

- **The newest VOD wins on any conflict.** This file now spans the entire drafted lifespan of the format (release week through the format's last week before rotation to the next set). Read the arc, not just the top: several of Kenji's release-window predictions (below) are directly **superseded** by his settled, heavily-repeated conclusions from July onward. Where a take changed, both are kept with an explicit dated supersession note — never silently overwritten.
- **The single biggest supersession the full run reveals:** early on (6/23–6/25) Kenji reads MSH as a curve-out creature format where "removal is premium and scarce" and treats 4–5 color "soup" as fun-but-bad (bomb-heavy, removal-light, loses to clean curves). By late June this flips hard: **white has the best commons AND good bombs**, blue-white wins consistently *without* needing rares, and "soup" done right (white- or black-based, removal-dense, propped up by land cyclers) is a top-tier strategy rather than a meme. The early "soup is weak" read was really "removal-light soup is weak" — a lesson about deck construction, not about multicolor decks per se. See Archetypes below for the full arc.
- He name-drops the format's lead designer as **Dave Humphreys (?)** on release day — "historically one of the best limited set designers for ages." That optimism proved out; he never soured on the *format's design*, only on his own release-week variance.

### Source timeline

| Date | VOD | Phase | Weight |
|------|-----|-------|--------|
| 2026-06-23 | WORLD FIRST THANOS SNAP! (`TTP3-ngUZ5Y`) | Release day — predictions | Weakest |
| 2026-06-24 | Heroes, Villains... Insects? (`R4bqbX8IaWY`) | Release day 2 — predictions | Weakest |
| 2026-06-24 | *(PENDING — no captions available)* SOLVING MARVEL SUPER HEROES DRAFT (`YAyuBb6Pbkk`) | Release window | — not distilled |
| 2026-06-25 | Sometimes Crime Does Pay (`ZqLITy67hqY`) | Early | Weak |
| 2026-06-26 | Copying All Of My Creatures! (`uiAQ-zBAxlc`) | Early | Weak |
| 2026-06-27 | Can A Hero Save Me From Arena? (`bSn4DD6vqcM`) | Early | Weak |
| 2026-06-28 | These Games Are Unbelievable (`e6iJy9bHqOY`) | Early | Weak |
| 2026-06-29 | I Have A Wakandan Theme Deck! (`DNYBwblVNfk`) | Early | Weak |
| 2026-06-30 | HOW MANY RARES DO YOU HAVE?! (`1NAzgXl4_Lc`) | Early → settling | Medium — UW thesis confirmed live (first trophy) |
| 2026-07-07 | The Time Of "Soup" Has Arrived! (`T-ureegCmfk`) | Format settling | Medium-strong — white-base soup pivot |
| 2026-07-08 | THANOS SNAP IS STILL OP! (`1Das1PlIcLg`) | Settled, Contender Draft | Strong |
| 2026-07-09 | Infinite Removal Seems Good (`ypK3Orfo6jk`) | Settled, Contender | Strong |
| 2026-07-10 | MTG Arena Can Be Such A Scam (`xkGcRpkp5xc`) | Settled, Contender | Strong |
| 2026-07-11 | THESE RARES ARE INSANE!!! (`VkfK6VXL1uU`) | Settled, Contender | Strong |
| 2026-07-12 | THE FULL REVERSE SWEEP?! (`_WbqaH6xiEc`) | Settled, Contender | Strong |
| 2026-07-13 | This Is Easily My Best Marvel Draft (`i8MqSbpFDbE`) | Settled, Contender | Strong |
| 2026-07-14 | Breaking Marvel Draft AGAIN! (`1l3BLn_I6SA`) | Settled, Contender | Strong — Iron Fist/Speedball debut |
| 2026-07-15 | I Must Get The Fantastic Four! (`fCjrDzSGu5k`) | Settled, Premier | Strong |
| 2026-07-16 | Now THIS Is A Fun Marvel Deck! (`ZLx0TFQxJgw`) | Settled, Premier | Strong |
| 2026-07-17 | I Double Dog Daredevil You! (`fKvS8QgnOns`) | Settled, Premier | Strong |
| 2026-07-23 | I Literally Do Not Ever Lose! (`Yl62DUfA7Iw`) | Settled, Premier | Strong |
| 2026-07-24 | Big, Blue Bomb Bonanza! (`o6AO3L_OHSM`) | Settled, Premier | Strong |
| 2026-07-25 | The Perfect Villain Deck! (`LfijA4BEAJA`) | Settled, Premier | Strong |
| 2026-07-26 | Is The Lifegain Deck Real? (`XaPW6PzFSHI`) | Settled, Premier | Strong — closes the lifegain question |
| 2026-07-27 | I COULD'VE HAD 8 OF THEM?! (`ze2sWqbcaTk`) | Settled, Premier | Strong |
| 2026-07-28 | THE MONO BLACK BARON DREAM! (`ucOmC-172-I`) | Settled, Premier | Strong |
| 2026-07-29 | One-Mana And You WIN THE GAME (`r5rtDiM5Foc`) | Settled, Premier | Strong |
| 2026-07-30 | This Card DOMINATES Combat (`Rj5lo1VdZBk`) | Settled, Premier | Strong |
| 2026-07-31 | INFINITE TWO FOR ONES! (`kGJ2ibzI7bA`) | Settled, Premier | Strong |
| 2026-08-01 | Look At All These Skrull! (`4ZHghcQ4uM0`) | Settled, Premier | Strong |
| 2026-08-02 | Super Nummy Can't Hurt You (`hhmOwgWpIeU`) | Settled, Premier | Strong |
| 2026-08-03 | Just Trying To Spice Things Up (`lNMHhlT-fsU`) | Settled, Premier | Strong |
| 2026-08-04 | *(OUT OF SCOPE — Pick-Two Draft)* Is Pick-Two Draft Just Easy Wins? (`tBrpT0pf9Uw`) | — | Excluded |
| 2026-08-08 | Forever Tapping Your Dudes (`WyU_1HXFLsY`) | Format sunset, Contender | Strongest |
| 2026-08-09 | STILL FINDING NEW CARDS? (`G5vvNNeRxos`) | Format sunset, Contender | Strongest |
| 2026-08-10 | My Final Super Heroes Draft (`HwSD-JhUSWE`) | **Format-closing retrospective, Premier** | Strongest — explicit career win-rate given |

## Format speed / meta read

*Early-window read (6/23–6/25), weakest tier — kept for the record, see supersession note below each:*

- **Removal is premium and scarce.** Kenji's single most-repeated early read. He P1P2'd **Punishing Punch** over a signpost gold card on this basis, and both of his losing release-day drafts he blamed largely on being removal-light. **PARTIALLY SUPERSEDED:** this holds for green/red/most colors all format, but white turned out to have *abundant* good removal (Web Up, Murdock's Crusade, Cruel Alliance-adjacent, Super Villain Lockup, Helicarrier Strike) — see White archetype below. The real lesson: removal is scarce *outside white/black*, which is exactly why those two colors dominate the format.
- **Curving out + playing first is very strong.** Recurring lament: "playing first and curving out is OP." This held all format — see Pitfalls and the July-onward "curve discipline" notes below. **Confirmed repeatedly, never superseded.**
- **Two-drops are scarce and worth prioritizing.** Held all format. Later-format standouts: **Hawkeye, Young Avenger** ("just way above rate, 2/2 first strike reach"), **Stature** ("an incredibly solid one drop" — his stated P1P1-tier white 1-drop), **Black Widow** ("like another Ragavan" on turn 2), **Undercover Skrull** (ramp/fixing two-drop, "turn-two scroll(?) you're probably pretty happy" early, later "turn two Undercover Skrull is just game over a lot of the time").
- **Bomb rares decide a lot of games.** Held, but nuanced hugely by August: white turned out to have some of the *best* bombs too (Captain America, Wings of Freedom; Captain America, Super-Soldier; Captain Marvel, Earth's Protector), so "bomb-dependent" and "wins-without-bombs" are not opposed for white — it's simply deep at every rarity. Doctor Doom remains the single scariest bomb to face from any color ("I think Doctor Doom is the card I've lost to the most in this format... has like a 99% win rate versus me" — 7/8).
- **The format supports 10 archetypes and rewards navigation/pivoting.** Held all format — see "10 archetypes → awkward signals" reconfirmed repeatedly through July.
- **Soup / splash-heavy decks are very buildable thanks to abundant fixing.** Held, but the *quality verdict* flipped hard — see the big supersession callout above and the Archetypes section.
- **Land counts:** 17 lands stayed his default all format, with two real exceptions that recur: (a) 16 lands when running 3+ land cyclers/heavy cheap curve, (b) **18 lands** when the curve is stacked with individually-powerful 4-drops you always want to hit on time ("18 land, 41 cards... we just always want to hit our fourth land on time" — 7/23, a deck where "every single four-drop was either a bomb or drew extra cards or did both").
- **Villain curve-out (red-black) is a real, oppressive aggressive plan.** Held as a real threat to respect, but see the major supersession below: red-black is also his own explicitly-named **weakest color pair by win rate** to *draft*. It beats you when your removal is light; it is not a strategy he recommends building.

*Settled-format read (July onward, strongest tier):*

- **Blue-White is the best archetype in the format, repeated and independently confirmed across a dozen-plus drafts.** First stated 6/30 ("blue and white have what feel like the best commons... those are the colors easiest to win with when you don't have a pile of rares") and reconfirmed almost verbatim through his very last draft 8/10 ("is the final draft of this format just going to be me losing to stupid blue white? Cuz it very well might be" — and it was). His single strongest piece of evidence: his **first trophy of the format** (6/30) was an explicitly rare-less blue-white pile. See Archetypes below.
- **White is the best single color, full stop, but it is heavily contested.** "White being the best color, I don't anticipate it to be open very frequently" (7/13). When it's cut off, his stated fallback is a **white-scarce multicolor soup leaning on land cyclers** rather than forcing a worse color pair — not "take white or bust."
- **Red and black are, by his own explicit read, the weakest colors/color-pair** in the format when played as a straight curve-out plan without a removal-dense shell propping them up ("I think uh based on the stats red — I think red-black is like the lowest win rate color pair," 7/25). This is the flip side of the villain-curve-out threat above: it's dangerous to face, underwhelming to draft straight.
- **Political Triumph and Origin of the Avengers are format-warping one-card payoffs.** Both are repeatedly singled out by name as close to auto-win when they resolve early: "look at the difference in these games where we have a Political Triumph versus not — it's just actually wild" (7/29); "Origin of the Avengers is basically just another Political Triumph in this deck" (7/29).
- **A very good deck in a weak archetype can still lose to a mediocre deck in the format's best archetype.** His own blunt conclusion after his red-black villains deck (built around Doom Reigns Supreme, went 5-2) lost twice to blue-white: "a very good villain's deck might still be worse than a mediocre blue-white deck... potentially the way of the world" (7/25). Weight archetype tier, not just individual deck quality, when picking a lane.
- **Build-around payoff cards are consistently weaker than the generic removal/curve shell around them — even when you draft the enablers.** A running theme across the whole back half: Doom Reigns Supreme (drafted the "perfect deck" for it, resolved it fully exactly once across 16+ games — "I'll call this a failure"), Construct a Cosmic Cube ("the card's not good, it's just a fun card" — deck still went 6-1 on its shell), Thunderbolts Conspiracy ("more of a bad card than anything, but just good interaction, fine curve, and a couple bombs" — deck still won). Take build-arounds for fun, not for their expected win rate; the surrounding shell is what actually wins.
- **Lifegain is explicitly NOT a supported archetype/sub-theme**, unlike the format's other synergy lanes. Tested once as a deliberate experiment (7/26, Green-White +1/+1 counters + Archangel of Thoon): "how many ways are there to synergize with lifegain in this format? I can't actually think of too many... never drafting lifegain again... this deck is so one-dimensional." The adjacent +1/+1-counters sub-theme is real and functional (Doc Samson, Mr. Hyde) — it's specifically lifegain-as-a-payoff that has no support.
- **Contender Draft (when it periodically returns) is mechanically identical to Premier Draft** — same card pool, same opponents, just 2x entry (3,000 gems/20,000 gold vs. 1,500/10,000) and a much steeper top-end payout (7,200+ gems at 7 wins vs. ~2,200 in Premier). 3 wins ≈ half entry back, 4 wins ≈ money back — the same practical threshold as Premier, just scaled. Only worth it with a solid overall format win rate; a downswing costs much more per draft.

## Archetypes

*Reorganized for the full-format arc. Ranked roughly by how strongly and how repeatedly Kenji confirms each; "Only lightly sampled" material from the release-window first pass is folded in below rather than kept as a separate thin section.*

### White — the format's best color (multiple viable shells)
Not one archetype but a family, unified by white simply having the deepest, most consistently powerful card pool in the format at every rarity.

- **Blue-White tempo/flyers.** The most-repeated single archetype conclusion in the whole run. Community-validated too — Kenji calls out "the mathologists" rating it the winningest pair by multiple percentage points, and independently confirms it via results. Shell: cheap flyers (Falcon; Spider-Man, To the Rescue), a tapper package (Raft Security Officer + Super Villain Lockup, "great with security officers — tap them down first"), white's removal suite, Agent 13 (repeat MVP — clue generation "basically just soloing this game for us"), and Justice ("one of the best uncommons in the format... just so much value"). Wins consistently *without* bombs, though it also has some of the best bombs when they show up (Captain America cards, Captain Marvel).
- **White-based "soup" — take the best card, splash everything, lean on land cyclers.** The format's headline supersession (see above): by 7/7 Kenji is explicitly playing "base white, then often playing a bunch of other stuff" as his default plan for the rest of the format, and it works — 6-of-7-trophy streaks, a 21-22-match win streak logged 7/7. The engine: white supplies cheap, plentiful removal (unlike the early green/black soup piles that had none), and the format's abundant land cyclers (a land cycler in every color, plus Baxter Building, Quinjet, duals) make a 3-4-color manabase reliable off mostly basics. This is a *different* soup than the early-format one — it wins because it's removal-dense, not because it's bomb-dense.
- **Red-White "Political Triumph" aggro/curve-out.** A tight two-color aggressive shell (not soup) built around Political Triumph/Origin of the Avengers as one-card payoffs, cheap creatures (Stature, Hawkeye, Bullseye), and burn (Lightning Strike). "This is just red-white, beat you down" (7/29). Mulligan aggressively toward turn-1 Triumph or a real curve rather than keeping a hand that does nothing early.
- **Red-White "Iron Fist / Speedball" targeted-effects combo.** Debuted 7/14, became Kenji's stated favorite deck of the format by late July ("I've been playing a ton of red-white lately to really good effect... I've been dominating with that archetype," 7/31). See Card interactions below for the mechanics; needs ~5 real "target your own creature" enablers to be worth building (Take Up the Shield, Panther Pounce, Blazing Crescendo, Team Tactics) or it's not worth running Iron Fist/Speedball themselves.
- **Equipment (Captain America, First Avenger / Falcon's Wing Harness).** Explicitly NOT a well-supported standalone build-around — most equipment in the set is cheap (1-2 mana), so there's little payoff for stacking big-equipment synergy on its own ("honestly not worth building your deck around" — 8/9). Works fine as a light value add-on to a normal white curve deck, not as a plan.

### Blue-Red — artifacts / "ping" value
A real, repeatable archetype (not just "the lane Iron Man wants," as the release-window read had it). Shell: Hydra Assault Robot (pings on artifact/villain ETB), Hawkeye's Bow (equip; pings whenever the wearer becomes tapped — attacking OR ability-tapping both trigger it), Stark Industries Executive (tap for a ping + treasure), Futurist Forge (flicker-value engine), Hydraulic Helper (enabler, doesn't attack but powers everything else), Aerial Doombot as generic filler, Iron Man, Master of Machines as the color-pair signpost. "Hawkeye build around is pretty cool... one of my favorite decks I've drafted this format" (7/16), despite going only 2-3 that particular episode to mana screw — a good deck can still run bad, don't judge purely by result.

### Black-based multicolor "villains" soup — removal-dense, distinct from straight red-black
Kenji repeatedly built 4-5 color piles anchored in black (sometimes blue-black, sometimes black splashing white/red) that are functionally the same "removal + land cyclers" soup engine as the white version above, just black-anchored. Cruel Alliance is absurdly common (he logged passing four in a single pack-1 once — "I could have had eight Cruel Alliance"), and Villainous Hideout is a strong dedicated fixing land for villain-heavy builds. This is **not** the same as straight red-black curve-out aggro (his explicitly weakest color pair, above) — the black soup wins on removal density and card quality, not on a fast curve.

### Villain aggro / curve-out (red-black) — real threat, weak to draft
Still a real, punishing aggressive plan to face (see Format speed above), but Kenji's own read after actually drafting it (7/25, built around Doom Reigns Supreme) is that it's carried by generically good removal and villain-synergy value (Killmonger, Baron, Hydra Troopers/Agents of Hydra, Madame Hydra), not by its payoff bombs, and that it's simply a weaker lane than blue-white or white-soup even when well-drafted (5-2, "a very good villain's deck might still be worse than a mediocre blue-white deck").

### Green — Undercover Skrull ramp/soup and +1/+1 counters
- **Green-anchored soup via Undercover Skrull.** Reconfirmed as one of the best two-drops in the format outright: "turn two Undercover Skrull is just game over a lot of the time" (8/1). Green's abundant token/treasure fixing (Ant-Man's Army) and land cyclers support the same white/black-style removal-light-avoidance soup, this time green-black or green-white based.
- **+1/+1 counters is a real, functional sub-theme** (Doc Samson, Mister Hyde — "very, very good... Mr. Hyde went off"), but the **lifegain** half of the green-white counters/lifegain shell is explicitly NOT supported (see Format speed above — do not force it).
- **Blue-Green counters/connive** — the release-window archetype from the original thin pass (Ant-Man, Colony Commander; We Say Thee Nay!; Trickster's Stratagem; Hulkling), only lightly re-touched later. Treat as still mostly release-window evidence; nothing later contradicts it, but nothing substantially deepens it either.

### Mono-black "Baron" Boast combo — niche, high-ceiling build-around
First tried 7/28. Baron Helmut Zemo's **Boast** ability requires him to *attack* (not just be on the battlefield) to trigger; exiles cards off the top until 15+ black mana symbols are seen, and up to 3 of the exiled cards may be cast for free. Kenji's own live misread on the rules is worth internalizing (see Pitfalls). Verdict after one full build (3-3, "beaten by the cards, not the player" in the deciding loss): "I think this deck is good enough to average fourish wins... it's not pure meme, it's got a good engine" — the surrounding black removal/connive shell (heavy Cruel Alliance, Moonstone value off connive, Black Widow) carries the deck regardless of whether Baron ever pops off, consistent with the general build-around-payoff pattern above.

### 4-5 color "soup" / villain ramp — release-window archetype, verdict now superseded
*Kept for the historical record; see the big supersession callout in Format speed above.* What he drafted in the release-window VOD 1: abundant fixing into the best bombs regardless of color, splashing Dr. Doom, Thanos, Ka-Zar, Fin Fang Foom. Verdict at the time: "cool, not good" (4 wins) — bomb-heavy and interaction-light, lost to clean curve-outs. **This verdict does not describe soup in general** — it describes *removal-light* soup specifically. The July-onward white/black-anchored soup, built the same way but with real removal density, wins consistently. Don't read "soup is weak" out of this file; read "soup needs real interaction, same as any other deck."

### Blue-White (Simic-adjacent) +1/+1 counters — release-window archetype
What he drafted in release-window VOD 2: Ant-Man, Colony Commander; Hulkling, Burgeoning Bruiser; We Say Thee Nay!; Trickster's Stratagem (connive = counter). His verdict at the time (4 wins, "underperformed") was that he straddled the counters lane and the artifacts lane (Moon Girl and Devil Dinosaur, Iron Lad want artifacts, not counters) and committed to neither — see Pitfalls. Blue-Red remains the artifacts lane (confirmed repeatedly all format); blue-green is the counters lane.

## Card interactions & combos

*Release-window entries kept verbatim; new entries from the full run appended below, newest signal first.*

1. **Iron Fist + Panther Pounce.** Target Iron Fist, Living Weapon with Panther Pounce: the pump triggers a shot for 2, and Panther Pounce's pump also untaps him, letting him fire again (now bigger, e.g. for 3). A precise two-for-one burst combo, not just "Iron Fist untaps if he attacks alone" (see next entry).
2. **Iron Fist, Living Weapon — untap-on-solo-attack rule.** If Iron Fist attacks *alone*, he untaps and can be re-triggered by a second targeted effect that turn. Needs a real critical mass of "target your own creature" enablers to be worth building around — Kenji's own stated floor is "probably like five minimum" (Take Up the Shield, Panther Pounce, Blazing Crescendo, Team Tactics, even your own removal cast at your creature). With only 2 enablers post-draft he flagged the deck as genuinely risky to run.
3. **Speedball, New Warrior + Super Intelligence.** Super Intelligence on Speedball is close to unbeatable card advantage: unless the opponent has a non-targeted removal spell or a copy effect (Web Up, Photon Blast Barrage — these dodge the redirect), any targeted removal aimed at Speedball just draws you a card via redirect.
4. **Speedball — redirect mechanics.** Target Speedball with your own trick/removal (not a triggered effect), it gets +2/+2, and the effect redirects to the opponent. Works with your own removal spells, not just combat tricks — a real source of reach in a removal-heavy shell.
5. **Blazing Crescendo + Team Tactics + Speedball — the "combo kill."** Team Tactics' teamwork mode (1 mana: give a creature trample) stacked with Speedball's redirect and cheap Crescendo pumps can close games by turn 4-5. Kenji's stated favorite deck archetype of the format.
6. **Cosmic Cube (the attack-trigger card, distinct from Construct a Cosmic Cube — see Card tips) + Loki Laufeyson — sequencing rule.** You must activate Loki's copy *before* letting Cosmic Cube's free-cast trigger resolve. If you let Cosmic Cube cast its hit first, Loki can no longer copy it — the window closes.
7. **Doom Reigns Supreme needs a real sacrifice engine, not just "being in villain colors."** Resolving it fully requires double-triggering it (e.g. play + sacrifice Agents of HYDRA in the same turn). Across ~16 games with a deck built specifically for it, Kenji fully resolved it exactly once (7/27) after failing outright the episode before (7/25) — treat it as a real but genuinely hard-to-assemble payoff, not a build-around you can half-commit to.
8. **Night Nurse, Healer of Heroes + Surveillance Room (or any self-mill/discard).** Surveil or discard a permanent, then Night Nurse returns it "from anywhere" — functions as an immediate extra draw. Land cyclers that are creatures (green/red/black/blue versions) feed this; the white land cycler is the one exception, since it isn't itself a creature that dies the same way.
9. **Jessica Jones, Private Eye + Mister Hyde, Monster Within.** Jessica Jones activates by putting a stun counter on herself; Mister Hyde can remove +1/+1-type/stun counters, letting you reset and reactivate her repeatedly. "An excellent combo" when both are present — Jessica Jones is independently a strong card-advantage engine even without it.
10. **Captain America, Wings of Freedom + Patriot, Shield Wielder — hexproof loop.** Patriot can grant hexproof to another creature you control; Captain America can return the favor to Patriot. A real mutual-protection package in white hero decks.
11. **Thanos, the Mad Titan — the "snap."** 3-mana 4/4 deathtouch lifelink; paying WUBRG+colorless puts two counters on him and destroys each creature of the chosen parity (odd/even) — a one-sided wrath if your board is built around the off-parity. Land cyclers, treasures, and any-color sources (Baxter Building) all help pay the colorless pip. Confirmed working exactly as described multiple times across the run, including a "perfect" all-relevant-permanents-on-one-parity snap (7/8).
12. **Kang, Temporal Tyrant — extra-turn rule.** Grants an extra turn, but **power[-up] abilities cannot be activated during that bonus turn.** An opponent misplayed against Kang believing they could chain extra turns infinitely (misunderstanding the restriction) and conceded incorrectly (7/24) — know this restriction cold if you're the one casting it, and don't assume the same misplay from an opponent.
13. **Baron Helmut Zemo — Boast rules, precisely.** The Boast ability requires Baron to physically *attack* to trigger (not merely be on the battlefield) — Kenji's own initial misread. It exiles cards from the top of the library until 15+ black mana symbols have been seen among them, and you may cast **up to 3** of those exiled cards for free (not the whole pile) — a second point he initially misjudged.
14. **Taskmaster, Mercenary Mimic — copy rules, precisely.** Taskmaster copies a target creature's power/toughness and abilities but **keeps his own name** — a copied "whenever a [creature type] attacks" trigger that cares about the copied creature's name/type does not apply to Taskmaster unless he's genuinely that type. Also: judge the copied body's actual printed stats carefully — Kenji once turned what should have been a 3/5 into a 3/4 by misjudging which version of a creature he was copying.
15. **Absorbing Man + the opponent's permanents** — copies "up to one target artifact, non-enchantment, or land," and can copy the OPPONENT's stuff, not just yours. The copy lasts only "until your next turn," so a removal effect can catch the copied body in an awkward window.
16. **Fin Fang Foom + a spell targeting an artifact/land** — 4-mana 3/5 flyer; whenever you cast an instant/sorcery targeting an artifact or land, copy it (new targets) and grow Fin Fang Foom. Set this up with Ant-Man's Army (leaves a treasure) then targeting the treasure/an artifact creature.
17. **World War Hulk / enrage Hulks self-ping** — the big reach-trample Hulk line gets a +1/+1 counter and untaps when dealt damage while attacking; ping your own Hulk in combat to keep untapping/attacking. (Caption-garbled between "Incredible Hulk" and the printed Hulk cards; treat as "enrage Hulks reward being damaged."(?))
18. **Photon Blast Barrage X-count** — paying X=3 deals **4** instances of damage (the original split + copies), not 3. Combos with Hawkeye's Bow-style ping effects to guarantee minimum damage per instance, and with Loki Laufeyson (copy your next cheap instant/sorcery) for extra reach if you have the spell density.
19. **Doctor Doom indestructibility** — 6-mana, makes two extra 3/3 artifact-creature tokens and is indestructible as long as you control an artifact creature, plus draws a card / loses 1 each end step. Confirmed across the whole run as the single scariest bomb to face ("I think Doctor Doom is the card I've lost to the most in this format").
20. **Madame Masque / connive payoffs + "draw your second card"** — several black cards trigger on drawing your second card each turn; treasures/cantrips that draw extra turn it on. (Lightly referenced across the run; not deeply explored.)
21. **Power-up cards — evaluate and sequence by their activated cost, not their printed cost.** A recurring, near-verbatim rule stated twice independently: "I always just consider the power-up cards as their power-up cost and not their base cost, cuz that's generally where you want to be playing them" (6/30, 7/8). Play them on the turn you can also activate them, not earlier just to get a body down.

## Card tips

*Corrected against `data/cache/17lands_MSH_PremierDraft_1200d.json` where names differ from the auto-caption spelling. Two notable corrections: "Burrow Backup" is actually **Borough Backup**; "Undercover Scroll" is actually **Undercover Skrull** — both consistent caption mishearings across the entire run, now fixed everywhere below. `(?)` = still uncertain.*

### White (W)
- **Web Up** — Good O-Ring-style removal, reconfirmed constantly ("my two preferred first picks in this format" alongside Trickster's Stratagem). Never a wrong pick in white.
- **Murdock's Crusade** — Reconfirmed all format as one of white's best removal spells (exile-based); repeatedly rated above Helicarrier Strike.
- **Cruel Alliance** — Reconfirmed as premium, flexible removal (exile a small creature, or exile anything + gain 3 with teamwork) — and shockingly abundant; Kenji logged passing four copies in one pack 1.
- **Super Villain Lockup** — Tap-down removal-adjacent; explicitly strong paired with the Raft Security Officer tapper package ("tap them down first, then lock it up").
- **Helicarrier Strike** — Demoted relative to white's other removal: "the worst among white removal spells," only really worth it with Agent Maria Hill (teamwork payoff) support. Still fine as a cheap fifth or sixth removal spell.
- **Justice, Vance Astrovik** — "One of the best uncommons in the format... just so much value," reconfirmed emphatically and repeatedly all format.
- **Agent 13, Sharon Carter** — Reconfirmed constantly, frequently the named MVP of a whole draft's worth of games via repeated clue generation ("basically just soloing this game for us... how much card advantage did she give us? Like four clues").
- **Borough Backup** (previously mis-transcribed "Burrow Backup") — Ranked, in Kenji's own words on his very last two drafts, as **the single best land cycler in the format**: "it's the best land cycler by far, and just a very good card in general" (7/15); "we take that burrow every time... just the best land cycler" (8/8). An immediate two-for-one when hard-cast (makes hero tokens), plus flexible land cycling.
- **Night Nurse, Healer of Heroes** — "Excellent" across many episodes; returns any permanent from anywhere, land-cycling creatures and Surveillance Room feed it directly (see Card interactions). The white land cycler is the one exception — it isn't itself a creature and can't be gotten back the same way.
- **Political Triumph** — Elevated from "one of the better non-rare plans" (6/23 era) to one of the single most powerful cards in the format by mid-format consensus: "one mana white plan is insane... proven to be very strong," and later "look at the difference in these games where we have a Political Triumph versus not — it's just actually wild." Mulligan aggressively toward it in a deck built to use it.
- **Origin of the Avengers** — "Basically just another Political Triumph in this deck" — a second top-tier white team-pump payoff, worth rating alongside Triumph.
- **Take Up the Shield** — Confirmed strong across 5+ episodes ("excellent," "disgusting in this format") — an indestructible + lifegain-in-combat trick that punishes the format's creature-curve-out plans. Also a key Iron Fist/Speedball enabler.
- **Stature, Size Shifter** — Elevated to a stated P1P1-tier white 1-drop by late format: "just an incredibly solid one drop... first-pick-pickable cards are like Falcon, Stature, Spider-Man, even Herbie."
- **S.H.I.E.L.D. Spy Kit** — "Super efficient, one mana to both equip and play" — a strong, cheap equipment; caution against running too many copies of the equipment package without enough actual bodies (see Pitfalls).
- **Raft Security Officer** — "One of the best commons in the format... putting in a ton of work," a tapper that anchors the UW/tapper shell.
- **Hero in Training** — Reconfirmed constantly as an always-solid 3-mana value creature; "the most fun in this format" white base decks lean on it heavily.
- **Captain America, Wings of Freedom** (rare) — Evasive, ward, hard to block; combos with Patriot for mutual hexproof (see Card interactions) and, surprisingly, with Super-Soldier Serum (an aura he'd otherwise avoid — see below).
- **Captain America, Super-Soldier** (mythic) — A hero-lord effect ("each other hero you control gets +X/+X where X = its toughness") that ended games instantly when combined with Super Strength, an aura Kenji explicitly says he'd "generally never play" outside this specific critical-mass shell.
- **Captain Marvel, Earth's Protector** (mythic) — Big flyer bomb: "gone are the days of being happy with a 5-mana 4/4 flyer." Note: *not* the same card as Captain Mar-Vell, Space-Born or Ms. Marvel, Kamala Khan — auto-captions conflate these Marvel/Marvell names constantly, cross-check context before trusting a specific reading `(?)`.
- **Super-Soldier Serum** (aura) — Generally an anti-recommendation (auras are risky in this format — see Pitfalls), but explicitly playable as a "throw it on a random 2-drop and make them answer it or lose" bet, and genuinely strong with Captain America payoffs.
- **Avengers Assemble!** (mythic) — Team-pump payoff; wants a real hero count (~10+) to be worth it.
- **Mindstone** (`The Mind Stone`) — Flickers **non-creature** permanents (artifacts/enchantments), not creatures — good specifically with Futurist Forge and other ETB/activated artifacts, not a general blink enabler.
- **Doombot** (`Aerial Doombot`) — Generic cheap filler creature, seen constantly across colors as a curve-filler, not a build-around.

### Blue (U)
- **We Say Thee Nay!** — Took the connive/counter mode happily; a flexible counter that also feeds +1/+1/connive synergies.
- **Trickster's Stratagem** — "Just a very good blue card," repeated heavy praise all format; a repeat pick regardless of deck.
- **Wiccan, Rising Magician** — Good ETB-value re-buy piece; the cast-trigger is a *forced* flicker on a non-creature spell, so it can be awkward without a good blink target. Can't flicker itself.
- **Echo, Perceptive Prodigy** — Reconfirmed constantly all format as a top blue pickup — copies an activated/triggered ability, including land-cycling activations for extra value.
- **Iron Lad, Diverging Destiny** — Good specifically in the artifact (UR) deck; wants real artifact density.
- **Moon Girl and Devil Dinosaur** — Pulled toward the artifact lane; competes for the same slots as counters payoffs and needs both artifact density AND card-draw-doubling support — often loses out to Echo in the same shell.
- **S.H.I.E.L.D. Deployment Drone** — Real two-for-one flyer-plus-token, delighted to see it wheel late.
- **Atlantis Attacks** — Staple include; "always want at least one of these in my blue decks."
- **Cosmic Cube** — The attack-trigger card, distinct from Construct a Cosmic Cube (below): "whenever you attack, look at top 6 of your library, may cast a spell with mana value ≤ your greatest attacking power without paying its cost." Genuinely strong, not just cute; see the Loki sequencing note in Card interactions.
- **Construct a Cosmic Cube** — A DIFFERENT card from Cosmic Cube above (the two are easy to conflate from captions — confirmed as separate real cards): whenever you draw your second card each turn, make a 2/1 and add a plan counter; sacrifice at 4 counters for a strong payoff. Kenji's own final verdict: "the card's not good, it's just a fun card" — decks built around it win on their shell (Night Nurse + Surveillance Room recursion, generically good removal), not on the Cube itself.
- **Monica Rambeau** (MDFC, transforms to Photon) — A recurring strong opener/bomb; the front side is castable without needing double-white, and flips to the hexproof Photon side once you hit WW. Synergizes with Cosmic Cube's attack-trigger mode.
- **Jessica Jones, Private Eye** — A standalone card-advantage engine, independently strong ("MVP of the deck... it's actually wild how many cards Jessica Jones has drawn me") and combos with Mister Hyde (see Card interactions).
- **Vision Quest** — Universally praised across many episodes as "absurd/insane/nuts," a card-draw engine off attacking with artifact creatures (grabs from graveyard too — even 2 artifact creatures is enough to make it strong).
- **Loki Laufeyson** — Good removal-bait and copy-value engine, but explicitly needs real instant/sorcery density — "we ended up with four sorceries, no instants... these Lokis are actually kind of bad." Confirmed as a separate real card from **Kid Loki** and **Loki, God of Mischief**; caption transcripts don't reliably distinguish which specific Loki is meant `(?)`.
- **Herbie** (`H.E.R.B.I.E. Scout Unit`) — A recurring, extremely reliable role-player across nearly every color combination all format: a 4-mana 2-power flyer that draws a card. "Safe pick... will go into any of my decks."
- **Ephemerate** — Cute blink instant with real targets (Herbie, Hero in Training, Madame Masque, Tiger ETBs), but needs a genuinely blink-dense shell to be worth running over a straight card — passed on correctly when the deck wasn't built for it.
- **Rewrite History** — A recursion build-around (return an instant/sorcery, tap creatures) that repeatedly failed to make the final cut across multiple attempts — needs real spell density, same failure mode as Loki.

### Black (B)
- **Cruel Alliance** — see White above (this is a black card; listed there for removal-suite context, repeating the note here: extremely abundant and premium).
- **Hour of Defeat** — "Fantastic... some more removal," a solid catch-all destroy effect, reconfirmed all format.
- **Dr. Doom (Doctor Doom)** — Top-tier rare/mythic all format; "the card I've lost to the most... 99% win rate versus me." Indestructible token-army threat (see Card interactions). Worth splashing/building toward.
- **Thanos, the Mad Titan** — Splashable 4/4 deathtouch lifelink with a board-wipe power-up; the highlight bomb of the format's opening ("World First Thanos Snap") and confirmed working exactly as described repeatedly through August.
- **The Super Hero Civil War** — Confirmed as one of the single most commonly-drafted, highest-impact rares in the format — Kenji faced it from **four different opponents in one draft session** (8/1) and cast it himself constantly. "Absurd/disgusting... one of the best rares in the set, not close," though genuinely awkward to cast/sequence.
- **Killmonger, Scourge of Wakanda** — "One of the best uncommons," confirmed repeatedly; removal (sac → destroy a non-land permanent) plus a growing body. **Needs real sacrifice fodder to be worth it** — a recurring pitfall (don't run him without enough expendable creatures).
- **Baron Helmut Zemo** — Boast build-around; see Card interactions #13. Confirm this is distinct from **Baron Strucker, HYDRA Overlord**, a separate villain card also referred to as "Baron" in some drafts `(?)`.
- **Moonstone, Harsh Mistress** — "Acres so much insane value" specifically in a connive-dense shell (multiple connive triggers = repeated Moonstone payoffs); functionally became "a Moonstone combo deck" in one Baron build.
- **Jessica Jones, Private Eye** — see Blue above (some drafts run her in black-heavy shells).
- **Black Widow** — "Like another Ragavan" on turn 2, snowballs hard if unanswered. Two distinct printings exist (Black Widow, Double Agent / Black Widow, Super Spy) — which specific one is meant is not always clear from captions `(?)`.
- **Kingpin's Enforcers** — Fine repeatable token/sac-outlet piece in black graveyard/villain shells.
- **Death to Our Enemies** — Build-around that wants to be cast early on curve, not as a late topdeck (its counter-based ramp wants to start accruing turns ASAP); a genuine build-around, not auto-include.
- **Villainous Hideout** (land) — Strong, repeatedly-praised dedicated fixing land specifically for villain-heavy decks ("put in work this game" — multiple episodes).

### Red (R)
- **Crimson Operative** — "Nice red common," wheels hard (3-4 copies seen in some drafts), a 3/2 prowess artifact that impulse-draws on ETB. Explicitly "not that good *without* removal" — a value body, not a finisher.
- **Punishing Punch** — His marquee early-format green-adjacent(?) take, P1P2'd over a signpost gold card because "removal is premium." Single [color], instant-speed, deals 2×power. Reconfirmed as premium removal throughout.
- **Photon Blast Barrage** / **Repulsor Blast** — Red's core removal suite. Photon Blast is better than its "X-for-Y" math looks (see Card interactions #18) but bad into high toughness.
- **Lightning Strike** — Solid, reliable stock burn all format; de-prioritized only when bigger payoffs are available. Straightforward good removal.
- **Bullseye, Death Dealer** — A rummage/damage engine ("discard a card, draw a card, deal 2 to anything") that scales up hard with Hawkeye's ping synergies. Repeatable value/reach piece in red-white aggro.
- **The Sentry, Golden Guardian** — Genuinely powerful but risky, especially into open blue mana ("always a scary proposition" — vulnerable to counterspells) and a real problem for grindy removal-based decks that lack a way to interact with an evasive, hard-to-answer threat: "my deck is not good versus Sentry... I dislike Sentry, but it is a very powerful card."

### Green (G)
- **Punishing Punch** — see Red above; his marquee early P1P2 take, kills almost anything at instant speed for one mana.
- **Go Nuts!** — "One-mana removal" (fight effect) and a counter-maker; a repeat high pick. Needs 3+ power already on board to pay the teamwork mode.
- **Ka-Zar of the Savage Land** — "Fantastic/amazing," multiples seen; a 5-mana play-lands-from-top engine that snowballs card advantage on its own ("already drawn us effectively two cards" just off playing lands).
- **Ant-Man's Army** — "Very good common," the format's premier fixing/soup glue — ramp, fixing, splash-enabler, artifact-count, all in one card. Multiple copies commonly run in soup decks.
- **Undercover Skrull** (previously mis-transcribed "Undercover Scroll" throughout the early captions — corrected here and everywhere below) — Elevated across the run from "premium two-drop fixer" to an outright format-best 2-drop: "turn two Undercover Skrull is just game over a lot of the time" (8/1).
- **Restorative Technique** — "Kind of nice" — 3 mana, gain 2, fetch a basic, put a +1/+1 counter; fixing + lifegain + a counter in one card, a real role-player in green-white counters shells.
- **Doc Samson, Super Psychiatrist** — "Very, very good," a strong payoff/enabler in +1/+1-counters shells.
- **Mister Hyde, Monster Within** — Proliferate/counter-doubling payoff; "went off" in real games. Combos with Jessica Jones (see Card interactions).
- **Squirrel Girl** (`The Unbeatable Squirrel Girl`) — Confirmed as a genuine bomb across multiple episodes: makes a 1/1 squirrel on ETB and attack, plus a snowballing X-token ability; "turn two Squirrel Girl is so good" when it comes down early via a cheat/reduction effect.
- **Guerrilla Gorilla** (previously mis-transcribed "Gorilla Gorilla") — Reconfirmed a strong green common, "when you're in green, you definitely want to have at least one Gorilla."

### Multicolor / gold
- **Killmonger, Scourge of Wakanda** — see Black above.
- **Iron Man, Master of Machines** — The blue-red artifact signpost; only good when you're genuinely committed to the artifact plan.
- **Hulk, Gamma Goliath** / big enrage Hulks — Big reach-trample beaters that punish being damaged (see Card interactions #17). "Hulk is great," won games as an above-rate chonker throughout the run.
- **Fin Fang Foom** — 4-mana 3/5 flyer with a spell-copy engine (see Card interactions #16); a strong gold/villain top-end when built around, inconsistent results otherwise ("I just haven't had as much good experience with it as, say, Justice").
- **Ant-Man, Colony Commander** — The GU counters signpost; "asks for a lot of mana and work for a minor payoff" — fine, not exciting. Never elevated beyond this lukewarm read across the whole run.
- **Hercules, Prince of Power** — Solid, unexciting 3-drop role-player.
- **Doom Reigns Supreme** — Villain go-wide rare/mythic; genuinely powerful when it fully resolves but hard to assemble on purpose (see Card interactions #7) — treat as a strong card, not a deck plan.
- **Storm, Force of Nature** / **Storm, Windrider** — Two distinct Storm cards. Force of Nature: "whenever Storm deals combat damage to a player, the next instant/sorcery you cast this turn costs as Storm" (a fun build-around, low sample, mark value uncertain `(?)`). Windrider: a solid flyer body seen more often as a straightforward include.
- **Kang the Conqueror** / **Kang, Temporal Tyrant** — Two distinct Kang cards. The extra-turn Temporal Tyrant has an important restriction (see Card interactions #12).
- **The Vision** / **Viv Vision, Teen Synthezoid** — Two distinct Vision cards, both real. Viv Vision's ability triggers on attacking regardless of current power, so it pairs well with post-attack pump tricks like Blazing Crescendo.
- **The Mighty Thor, Jane Foster** — Strong reset/anthem-adjacent piece, did significant work as a payoff in several UR/UW artifact-adjacent decks.
- **Jennifer Walters** (transforms to She-Hulk, Jade Defender) — 6/6 reach trample, opponent can't cast spells on your turn, damage-redirect; can be cast directly as the back face if you have the mana (does not require casting the front side first). Reconfirmed constantly as one of the single best threats in the format, "so disgusting," largely resistant to non-enchantment-removal answers.

### Colorless / artifacts / lands
- **Baxter Building** — Any-color fixing AND a card-draw engine most players (including Kenji himself, repeatedly) forget to actually use — "how long have I been forgetting about the card draw?" A strong stall-breaker; also pays Thanos's colorless activation pip.
- **Dependable Quinjet** — Fixing vehicle, cuttable once a deck has enough fixing elsewhere.
- **Captain America's Shield** (equipment) — Grants indestructibility and is itself very hard to remove; explicitly devastating left unanswered, especially against mono-colored opponents who lack a specific enchantment/exile answer ("versus mono red is just nigh unbeatable"). Cannot be answered by damage-based removal (e.g. Hulk Smash-style effects).
- **Mjölnir, Hammer of Thor** (equipment) — A strong, splashable bomb-tier equipment; only seen once in the sampled run, treat as a low-sample but clearly powerful data point.
- **Special guest / bonus-sheet cards** — A recurring format quirk: cards outside the base MSH pool (e.g. Final Showdown — a board wipe; Monstrous Rage; Chaos Warp; Dig Through Time; Path to Exile; Teferi's Protection) can appear in packs and swing games unexpectedly. Don't be surprised by an unfamiliar card mid-draft; it may not be in the base set's card pool at all.

## Pitfalls

*Release-window entries kept verbatim; new entries from the full run appended, ordered roughly by how often the pattern recurred.*

- **Main-phase-kill a creature before it can get an indestructible/protection equipment.** His single most costly early punt: held removal on a threat intending to use it at instant speed, but the opponent's black equipment granted indestructible first and the kill spell bricked. In a format with indestructible-granting equipment (Captain America's Shield especially), don't slow-roll removal on a threat that can be protected.
- **Don't over-respect, but DO play around the few format-warping commons/equipment.** Read the small synergy text on villains/heroes and on equipment before combat — Captain America's Shield alone has caused multiple blowouts across the run.
- **Don't straddle two synergy lanes.** A deck drifting between +1/+1 counters and artifacts (Moon Girl/Iron Lad want artifacts; the rest want counters) commits to neither and underperforms. Pick a lane and feed it.
- **Loki / spell-copy cards need real spell density.** Don't draft spell-copy payoffs (Loki Laufeyson, Photon Blast chains, Fin Fang Foom, Rewrite History) without enough instants/sorceries to fuel them — a repeated, multi-episode failure mode.
- **Count copies correctly on X-spells.** Photon Blast Barrage at X=3 makes 4 damage instances (original + 3 copies), not 3.
- **Mind Absorbing Man's copy duration.** The copy lasts only "until your next turn," and copying the opponent's permanent can leave a removable body in a bad window.
- **Don't over-value cute rares over curve.** Cut a "cool but not good" rare for a plain two-drop more than once, concluding "the two drops are just going to be better."
- **Don't misclassify hero vs. villain in combat math** — several cards care about the typing; check before you sac/block/trigger.
- **Don't trust early-access results as your Arena baseline** — the field plays differently and tighter; recalibrate rather than assuming your early-access win rate predicts your ladder win rate.
- **Splash discipline in soup decks: splash for removal and a couple of bombs, not for a pile of fatties with no early game.** The format's deep fixing makes splashing easy, but a removal-light, bomb-heavy soup pile still loses to clean curve-outs — the exact failure mode of the release-window soup decks (see Archetypes).
- **Don't speculatively take a flashy off-color bomb over a premium on-color removal spell you know you'll play.** A repeated, self-acknowledged leak in his own drafting late in the run: passed a Web Up for MODOK twice in close succession, regretted both, ended up not even playing the off-color bomb ("Baited by the Modok. Maybe I can get hooked up with some crazy white bomb or blue bomb in pack three" — followed immediately by not getting there). If you're already committed to a color, take the removal you'll play over a speculative splash-bomb.
- **Don't chase personal completionist/meme goals (e.g. "collect all four Fantastic Four cards") at the cost of real deck quality.** Explicitly self-flagged: "this is not the right deck to support it, but to hell with it all" — fine as a deliberate, acknowledged fun-run, but don't let it happen by accident.
- **Mulligan aggressively toward your deck's single most important payoff/curve slot, not just toward "keepable."** In a Political-Triumph-centric deck: "I will probably aggressively mulligan at least one time... until we either have Triumph on turn one or a decent curve out with something to do on turn two." A generically fine 7-card hand that does nothing until turn four is often a mulligan in this format's curve-out-punishing meta.
- **Read a build-around card's exact rules text before committing picks to it.** Baron's Boast requires an actual attack, not just being on the battlefield, and only frees 3 of the exiled cards, not the whole pile — a costly initial misread. Kang, Temporal Tyrant's extra turn disallows power[-up] activations. Taskmaster keeps his own name when copying, which breaks tribal/typal triggers you might expect to carry over. Verify the actual text, not the remembered gist, especially on build-around rares/mythics.
- **Don't over-commit to "removal is scarce" reads in colors where it isn't.** The release-window "removal is premium and scarce" read was accurate for green/red/most colors but never applied to white or black, which both turned out to have deep, cheap removal suites all format.

## vs Lords of Limited

MSH is Tier-1 (actively drafted), so per the contract this section flags **only genuine conflicts** with `draft-guides/lords-of-limited/MSH-draft-guide.md`. The comparison below is preserved from the original release-window build (2026-06-24, when Numot's sample was only 2 drafts and both sources were still pre-17Lands prediction-tier) — it has **not** been re-checked against the LoL file now that Numot's coverage spans the full format (35 drafts through 2026-08-10). That re-check is future work, not part of this pass (this distill touched only `MSH.md` and `general-tips.md`, never the LoL file). Treat the bullets below as dated release-window snapshots, not as reflecting Numot's settled, full-format positions — cross-reference the Archetypes/Format-speed sections above (which are current) before trusting anything here as still accurate.

Where they agreed at release-window time (removal is scarce/premium, two-drops are the scarce slot, Killmonger is the best gold uncommon, Ant-Man's Army is great fixing/glue, Dr. Doom/Thanos/Civil War are top bombs, Echo/Wiccan do free work, blue-red = the artifact lane that needs nobody else in it, Iron Man dies and the deck folds, soup is buildable off abundant fixing) nothing was noted.

- **Format-defining vector — slow/grindy vs aggressive curve-out.** **LoL: "slow format, board stalls, flooding hurts less than screwing," games go long.** / **Numot (release-window): his loudest lived lesson is "playing first and curving out is OP" — he lost repeatedly to clean 2→3→4 villain curves before any stall formed.** Not a flat contradiction (LoL also notes flying/trample close games), but the *emphasis* differed sharply at the time. **Numot's full-format record now sides with both**: red-black curve-out remained a real, punishing threat all format (see Format speed above), but his own settled read is that blue-white/white-soup — not fast curve-outs — is the format's best *strategy to draft*, which is closer to LoL's slower-format framing than his own release-window emphasis suggested.
- **Soup / 5-color.** **LoL: doesn't frame soup as a headline plan — ranks the two-color pairs and treats heavy splashing as a fixing convenience.** / **Numot (release-window): actively predicted "I'm going to draft nothing but Ant-Man's Army five-color decks, screw your synergies," and built 4–5 color piles both VODs — results undercut him at the time (4 wins, removal-light, "cool, not good").** **Full-format update:** Numot's own results reversed hard by July — white- and black-anchored soup (removal-dense, not the early bomb-heavy version) became one of his best-performing strategies, run to trophy-streak level. This still isn't quite LoL's framing (LoL ranks color pairs; Numot's mature view is "take the best card, splash on land-cycler fixing"), but the two are no longer as far apart as the release-window snapshot suggests — worth a fresh read-through against LoL's actual soup/fixing framing next time this section gets revisited.
- **Lightning Strike.** No conflict — both rate it underwhelming (misses 4-toughness). Listed only to confirm cross-source agreement.
- **Ant-Man, Colony Commander.** Both lukewarm ("a lot of mana and work for a minor payoff") — agreement, not conflict. Numot's full-format sample never moved off this lukewarm read either.
- *(Most LoL card verdicts weren't checkable at release-window-only sample size. With 35 Numot drafts now distilled above, a proper conflict pass against the LoL file is likely to surface real disagreements — flagged here as the next worthwhile action on this section, not attempted in this pass.)*

## Source episodes

- 2026-06-23 — WORLD FIRST THANOS SNAP! | Marvel Super Heroes Premier Draft (`TTP3-ngUZ5Y`)
- 2026-06-24 — Heroes, Villains... Insects? | Marvel Super Heroes Premier Draft (`R4bqbX8IaWY`)
- 2026-06-24 — *(PENDING — still no captions)* SOLVING MARVEL SUPER HEROES DRAFT | June 24 (`YAyuBb6Pbkk`)
- 2026-06-25 — Sometimes Crime Does Pay (`ZqLITy67hqY`)
- 2026-06-26 — Copying All Of My Creatures! (`uiAQ-zBAxlc`)
- 2026-06-27 — Can A Hero Save Me From Arena? (`bSn4DD6vqcM`)
- 2026-06-28 — These Games Are Unbelievable (`e6iJy9bHqOY`)
- 2026-06-29 — I Have A Wakandan Theme Deck! (`DNYBwblVNfk`)
- 2026-06-30 — HOW MANY RARES DO YOU HAVE?! (`1NAzgXl4_Lc`)
- 2026-07-07 — The Time Of "Soup" Has Arrived! (`T-ureegCmfk`)
- 2026-07-08 — THANOS SNAP IS STILL OP! (`1Das1PlIcLg`)
- 2026-07-09 — Infinite Removal Seems Good (`ypK3Orfo6jk`)
- 2026-07-10 — MTG Arena Can Be Such A Scam (`xkGcRpkp5xc`)
- 2026-07-11 — THESE RARES ARE INSANE!!! (`VkfK6VXL1uU`)
- 2026-07-12 — THE FULL REVERSE SWEEP?! (`_WbqaH6xiEc`)
- 2026-07-13 — This Is Easily My Best Marvel Draft (`i8MqSbpFDbE`)
- 2026-07-14 — Breaking Marvel Draft AGAIN! (`1l3BLn_I6SA`)
- 2026-07-15 — I Must Get The Fantastic Four! (`fCjrDzSGu5k`)
- 2026-07-16 — Now THIS Is A Fun Marvel Deck! (`ZLx0TFQxJgw`)
- 2026-07-17 — I Double Dog Daredevil You! (`fKvS8QgnOns`)
- 2026-07-23 — I Literally Do Not Ever Lose! (`Yl62DUfA7Iw`)
- 2026-07-24 — Big, Blue Bomb Bonanza! (`o6AO3L_OHSM`)
- 2026-07-25 — The Perfect Villain Deck! (`LfijA4BEAJA`)
- 2026-07-26 — Is The Lifegain Deck Real? (`XaPW6PzFSHI`)
- 2026-07-27 — I COULD'VE HAD 8 OF THEM?! (`ze2sWqbcaTk`)
- 2026-07-28 — THE MONO BLACK BARON DREAM! (`ucOmC-172-I`)
- 2026-07-29 — One-Mana And You WIN THE GAME (`r5rtDiM5Foc`)
- 2026-07-30 — This Card DOMINATES Combat (`Rj5lo1VdZBk`)
- 2026-07-31 — INFINITE TWO FOR ONES! (`kGJ2ibzI7bA`)
- 2026-08-01 — Look At All These Skrull! (`4ZHghcQ4uM0`)
- 2026-08-02 — Super Nummy Can't Hurt You (`hhmOwgWpIeU`)
- 2026-08-03 — Just Trying To Spice Things Up (`lNMHhlT-fsU`)
- 2026-08-04 — *(OUT OF SCOPE — Pick-Two Draft, not a regular Arena draft)* Is Pick-Two Draft Just Easy Wins? (`tBrpT0pf9Uw`)
- 2026-08-08 — Forever Tapping Your Dudes (`WyU_1HXFLsY`)
- 2026-08-09 — STILL FINDING NEW CARDS? (`G5vvNNeRxos`)
- 2026-08-10 — My Final Super Heroes Draft (`HwSD-JhUSWE`)
