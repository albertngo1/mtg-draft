# Tarkir: Dragonstorm (TDM) — Draft Guide

> Agent-primary reference, synthesized from 6 Lords of Limited episodes (Ben Warney & Ethan Sachs). This guide is the lead lens that **decodes** the 17Lands data — every GIH WR is archetype-conditional (trust where it transfers, discount where it inflates; see AGENTS.md). Synthesized from episodes current as of 2025-05-19.
>
> IMPORTANT TIMELINE NOTE: preview/crash-course and early-access episodes made predictions the retrospective "50 Takes" episode reversed. Where they conflict, trust the *late/retrospective* read. Biggest reversals: Snowmelt Stag (hyped → replacement-level), hybrid commons (touted as "delayed decision" picks → largely filler), Teamer devotee (stacked as fixing glue → do not play it).

## Recency rule (read first)

These notes span **2025-03-24 → 2025-05-19**, and the format evolved substantially over that window. Apply this rule on every conflict:

- **The newest episode wins.** On any disagreement, the later-published episode supersedes the earlier one.
- **Preview + early-access takes (03-24 → 04-07) are PREDICTIONS** made before or at first contact with the format — weakest possible evidence.
- **The 2025-05-19 "50 Takes in 50 Minutes" wrap-up (`50t`) is the single most authoritative source.** When it speaks, it settles the matter.
- **This guide decodes the 17Lands data rather than ranking beneath it.** Every GIH WR is archetype-conditional — use the guide to tell which archetype's deck a number came from: trust the WR where it transfers (cleanly-castable cards), discount it where it inflates (payoffs/multicolor). See AGENTS.md.

| Date | Episode / file | Phase | Weight |
|------|---------------|-------|--------|
| 2025-03-24 | Preview Crash Course (`4H7pjO1y4Eo`) | BLIND — predictions only | Weakest |
| 2025-04-07 | Early Access Dump (`YsMtK1eXVu4`) | Early access | Low |
| 2025-04-14 | Week 1 (`EL7L8ec_R0k`) | Early | Low–Medium |
| 2025-04-28 | Devotees Deep Dive (`WPizty-xUT0`) | Mid | Medium |
| 2025-05-05 | Designer Interview with Ben Whites (`nO4XEWWOaEY`) | Mid-late | Medium-high |
| 2025-05-19 | "TDM Goes Out in a Blaze of Glory!!" (`aR_oF5QEhMg`) | RETROSPECTIVE / wrap-up | **Most authoritative** |

## Source timeline

| Date | Episode title | Phase | Weight |
|------|--------------|-------|--------|
| 2025-03-24 | Here There Be Dragons!!! | Preview — blind predictions only | Weakest |
| 2025-04-07 | Is this even SLOWER than Aetherdrift??? | Early access | Low |
| 2025-04-14 | You Either Mardu or You Mar-don't!!! | Early (week 1) | Low–Medium |
| 2025-04-28 | Devotees Fix More Than Just Your Mana! | Mid | Medium |
| 2025-05-05 | Inside the Mind of the Lead Designer! | Mid-late | Medium-high |
| 2025-05-19 | TDM Goes Out in a Blaze of Glory!! | Retrospective / wrap-up | **Decisive (most authoritative)** |

## TL;DR meta read

- **Two poles dominate: Boros aggro and five-color dragon soup.** They are more common than the three-color clan decks. The format feels cube-like — ramp, aggro, control, and midrange all genuinely exist.
- **Forging your game plan matters more than reading signals or finding the "open clan."** There is no single dominant pick order. Even at week seven, picks one through five have multiple defensible answers.
- **White is the best color; black is the worst.** For starting preference Ben prefers red (most flexible), Ethan prefers blue/green (soup payoffs). Color power rankings matter less here than in most formats — follow the best card in the pack.
- **Green is the best base for powerful multicolor things**, but starting green without a payoff (e.g. the green regent) is a difficult sell.
- **The best dragons deck has a clear recipe:** dragons + exhales + Dragon Storm Globes + dragon storm spells. Take the uncommon dragons early and flesh out the bottom of your curve from there.
- **Rock-paper-scissors exists but is soft:** Boros aggro beats control, control beats ramp, ramp beats aggro — yet Jeskai mid-range and the various green beatdown decks also occupy real space. Do not assume only three viable decks.
- **Fixing is everywhere.** Gainlands, trilands, Evolving Wilds, monuments, devotees, Dragon Storm Globe, Rhor's Routine — you can consistently play three or more colors. This actually made lands low picks (non-land fixing beat land picks on power).

## Archetype / color-pair tiers

Ordering below is the **05-19 retrospective** verdict.

| Clan / deck | Tier | Game plan | Signature cards | Notes |
|-------------|------|-----------|-----------------|-------|
| **Teamer / Five-Color Dragon Soup** | **S** (slightly above Mardu) | Ramp into dragons; Dragon Storm Globes + dragon storm spells to chain big flyers | Dragon Storm Globe, Encroaching Dragon Storm, dragons (common + uncommon), Rhor's Routine, exhales | Most powerful ceiling. Dragon Storm Forecaster (?) package (2 forecasters + 2 globes + Boulderorn Dragons) as 22nd–23rd cards. Start from a high-power green or red card. |
| **Jeskai ("Just Sky") Control / Mid-range** | **S-/A+** (ahead of Mardu on clans; Ben's late-format preference) | Blue-based interactive control or Flurry-enabled tempo; exhales + counter magic + Coreway Mountain Monastery (?) | Dispelling Exhale, Riverwalk Technique (?), Spectral Denial, Jeskai Devotee, Sonic Shrier (?), Jess Sky Shrine Keeper (?), Wingblade Disciple | Counter magic was historically good in this format. Jeskai mid-range plays to the board + keeps opponent off balance; very different from early-format Jeskai attempts. |
| **Boros Aggro / Mardu go-wide** | **A** (most consistent, best for lower-powered starts) | Go wide with Mobilize tokens + pump effects; double spell for Flurry value | Mardu Devotee, Salt Road Packbeast (?), Shock Brigade, War Effort (?), Sharpshooter (?), Seize Opportunity, Molten Exhale | Designer confirmed Mardu is slightly too strong and needed to keep "soup" decks honest. Mardu mid-range worse than pure Boros; straight Boros outperforms three-color Mardu. |
| **Sultai Renew / BG Counters** | **B** | Put +1/+1 counters on creatures, go tall, protect the queen with Snakeskin Veil | Champion of Ducson (?), Snakeskin Veil, Renew payoffs, Caustic Exhale | Designer's in-hindsight target for a slight power buff; Black-Green gold cards could use extra juice. A real off-ramp when cut from soup. |
| **Abzan Endure** | **C** | ETB-heavy, +1/+1 counters, grind | Endure creatures, Abzan Devotee | Fell flat compared to other clans. Pretty big gap between Teamer/Jeskai and Abzan/Sultai. Abzan was the most distinct clan alongside Mardu but underperformed. |
| **Off-color beatdown / niche** | **C** | Various: RG trample aggro (power-matters), BG go-tall, Wingblade Disciple double-spell tempo | Wild Ride, Wingblade Disciple, Champion of Ducson, Coreway Mountain Stalwart (?) | Rewarding for experienced pilots. The format's 20-viable-decks space — not always available but a big edge when it is. |

**Clan rankings (50t verdict):** Teamer 1st, Jeskai 2nd, Mardu 3rd, then a big gap before Sultai 4th, Abzan 5th (last). Note: Mardu as a standalone color pair (Boros) outperforms three-color Mardu.

## TDM format principles

**1. Game plan > signal reading.**
The format does less hand-holding than most. Most draft formats put you in a color pair by pack one's end; TDM leaves you genuinely choosing between "deep green into dragon soup," "green beatdown," "green into weird red-green," and more. Knowing which off-ramp to take when your primary plan is cut is deep format knowledge — invest reps.

**2. Individual card power > synergy.**
This is not a synergy format in the traditional "enable-payoff" sense. Cards ask to be in the right *game plan* (e.g., Wild Ride is narrow but not bad — it just needs its home), not to fill specific mechanical slots. Exception: the dragon soup deck has a real recipe and the exhales want behold triggers. But there is no equivalent of "get Rooster Drakes, then prioritize flying enablers."

**3. Fixing is free — don't prioritize lands highly.**
The six-plus categories of mana fixing mean trilands and gainlands are fine, but taking them in the first few picks costs you card power. This is a counterintuitive lesson the hosts had to learn: even in a three-color format, the non-land fixing was dense enough to down-rank land picks.

**4. Take the best card, picks 1–8; plan your off-ramp by pick 12–15.**
The hardest drafts are ones that don't start with power — you end up guessing. When you open a high-powered card (Mering River Regent (?), Carrick Guardian (?), Warden of the Grove (?)), commit to following it and build the home around it. Off-ramps (Champion of Ducson (?), Wingblade Disciple, RG trample package) are worth knowing cold so you can slot into them when your primary lane closes.

**5. Don't miss land drops.**
The format explicitly rewards reaching your curve. Dragon Storm Globe, monuments, and devotees all help. Never operate without hitting your lands on curve.

**6. The magic toughness number is three.**
Two-damage effects (Twinbolt, Channel Dragonfire — both confirmed underperformers) do not kill the things you need to kill. Prioritize removal that deals 3+ damage or is a full exhale.

**7. Sorcery vs. instant speed is a huge deal.**
The hosts noted multiple times that cards failing their function because they are sorcery speed is a recurring trap (Channel Dragonfire being the clearest example). Internalize which removal is instant-speed before picking.

**8. Hybrid commons/uncommons were filler.**
Entering the format Ben and Ethan expected hybrid cards to be high picks that let you delay your color commitment. In practice the fixing was so abundant that you did not need them, and the cards themselves weren't powerful enough. Take them when they are the best card in the pack; do not pick them for fixing.

**9. The lower your draft's overall power, the more you should lean Boros/Mardu aggro.** The higher your draft's power, the more you should lean Teamer/soup. Jeskai is the good centrist point.

## Card notes by color

Only non-obvious evaluations and trajectory changes are listed. Cards the hosts treated as obvious first-picks (Carrick Guardian (?), Mering River Regent (?), Elba Storm Slayer (?), Warden of the Grove (?)) are omitted as assumed A+.

### White

| Card | Take | Source |
|------|------|--------|
| **Salt Road Packbeast (?)** | Best common in white. Absurdly high ceiling. **Key:** play it for as cheaply as possible (wait for cost reduction), not as quickly as possible (don't force turn 4). Miles better than comparable green three-drops. | 50t |
| **Mardu Devotee** | Best common in white and one of the best in the format. Format-defining. Take as many as you can if you're in white-based aggro. | 50t |
| **Storm Plane Detainment (?)** | Strong competitor for best white common (only Mardu Devotee edges it out by "public outcry"). Premium removal. | 50t |
| **War Effort (?)** | Strong enchantment for Boros/Mardu go-wide. Designer confirmed it's "the right level of strong for a four-mana build-around." Not broken, but excellent when on plan. | EL7L8ec, nO4 |
| **White exhale (life-gain exhale)** | Excellent splash for off-color decks; top removal even though it doesn't fit white's primary go-wide plan. The life gain is load-bearing. | 50t |
| **Sun Pearl Kiran (?)** | Underplayed by the hosts. Does a lot: picks up Mobilize tokens, picks up sagas at chapter three. A sneaky performer. | 50t |
| **Dalovan Encampment (?)** | Best white utility land (makes Mobilize tokens when attacking). Playable, but most utility lands are low picks in this format. | 50t |

### Blue

| Card | Take | Source |
|------|------|--------|
| **Sibig Appraiser (?)** | Best blue common, and clearly so. Blocks early aggression, hits land drops, finds dragons. Designer explicitly wanted it to be one of the best commons. Moved from skeptical early takes to consensus top common. | 50t, nO4 |
| **Dispelling Exhale** | Second-best exhale in the format (behind Molten Exhale). Counter magic that scales: paying four for it was genuinely oppressive. Best with dragons for Behold discount. | 50t |
| **Riverwalk Technique (?)** | "Imperial Oath Award" winner — clunky-looking overperformer. Best four-mana counterspell the hosts have seen in limited. Most blue decks want exactly one. | 50t |
| **Spectral Denial (?)** | Good counter magic but below Dispelling Exhale and Riverwalk Technique. Would have been ranked #1 entering the format; finished #3. | 50t |
| **Sonic Shrier (?)** | Premium uncommon dragon; take very early. | 50t |
| **Jess Sky Shrine Keeper (?)** | Premium uncommon dragon; take very early. | 50t |
| **Mering River Regent (?)** | Mythic-level rare. Ben never opened it all format and lost to it constantly. The "most obnoxious rare" on his list. | 50t |
| **Narcissist Rebuke (?) + Focus the Mind (?)** | Individually neither is a particularly high pick; the hosts got too high on them in week one from a good early experience. Do not overvalue either in isolation. | 50t |
| **Kisha Skimmer (?)** | Fine as a 2/2 flyer in blue-green, but never reached the power level of similar uncommons from other formats. The "graveyard matters" archetype built around it and Essence Anchor (?) fell flat. | 50t |

### Black

| Card | Take | Source |
|------|------|--------|
| **Caustic Exhale** | Best black common, probably best black removal. Very good. | 50t |
| **Dragons Prey (?)** | Strong competitor for best black common. Also excellent removal. | 50t |
| **Aggressive Negotiations (?)** | A Coercion variant that was surprisingly important — and historically good (last comparable was Toll of the Invasion in WAR). Key to mid-range black decks not auto-losing to bomb rares (Urani (?), Elspeth, Mering River Regent). Take it when in black mid-range. | 50t |
| **Worthy Cost (?)** | Sacrifice outlet that also answers planeswalkers (an important niche given the format's busted rares). Situational but real. | 50t |
| **Feral Death Gorger (?)** | Three-mana 3/5 deathtouch common black dragon. Ben was high on it early, dialed back. Designer loves it. Beats all other dragons in combat; respectable. The exile-two-cards from graveyard mode is a "grinds my gears" complaint for Ethan — it randomly savages your Harmonize/Renew cards. | 50t, nO4 |
| **Caustic Exhale / Dragon's Prey** | Black's best tools, but the overall black commons are weak. Ben warns you can go "deep into black" and find four atrocious cards in a pack. Avoid unless hooked on gold cards or rare power. | 50t |

### Red

| Card | Take | Source |
|------|------|--------|
| **Molten Exhale** | Best exhale in the format, best red common. A+. | 50t |
| **Jeskai Devotee** | "Golden Egg Award" — the common that glued the most archetypes together. The single card whose pick value rose the most over the format. Manifixes (!) and flexes across Boros, Jeskai control, Jeskai tempo, RG aggro. Take as many as you can in any red deck. Also causes annoying Arena pauses as opponents wonder "what's that single red mana?" | 50t |
| **Shock Brigade (?)** | Premium 1-drop. Designer specifically said he would not nerf it. Take highly in Boros/Mardu. | nO4 |
| **Seize Opportunity (?)** | Red card-advantage spell ("Elkin Bottle (?)"). Real card in the format. | nO4 |
| **Wild Ride** | Narrow "give biggest creature haste, sacrifice at end of turn" effect. Best in: Jeskai tempo with Wingblade Disciple, or as a combo with Meticulous Artisan (?) for "cast on turn 4, attack for 7/4 haste"). Not a build-around but a real role-player in its correct home. The designer was worried about it being broken — glad it was not. | 50t, WPizty |
| **Channel Dragonfire (?)** | Underperformed. Sorcery speed means you cannot steal a playback; the 1-mana deal-2 is frequently embarrassed by toughness-3 bodies. | 50t |
| **Breaching Dragon Storm (?)** | Looked like a "random cascade" throwaway. Was actually rock-solid in the right dragons deck. One of the format's cards that "usually is bad, but wasn't." | 50t |
| **Coreway Mountain Stalwart (?)** | Good in Jeskai mid-range low-curve double-spell decks. Undervalued by the market. | 50t |

### Green

| Card | Take | Source |
|------|------|--------|
| **Sagu Wildling (?)** | Best green common. Clearly ahead of Inoch Wayfairer (?) for the hosts; team Wildling firmly established late-format. | 50t |
| **Champion of Ducson (?)** | Teal-green (?) 4/2 trample; Renew it from graveyard to put a +1/+1 counter + trample on a creature. The best non-rare Renew cost in the format. Sleeper early in the format, now caught up. Best offramp for green decks cut from soup. | 50t |
| **Snakeskin Veil** | Powerhouse in a bomb-heavy format. One-mana hexproof protects your threats, counters exhales with pure efficiency. Ethan's renaissance card of the format — took him a long time to accept combat tricks, now "primo primo." | 50t |
| **Dragon Storm Globe** | The Manalith variant that was actually excellent. Key enabler for the dragon soup deck; accelerates mana, fixes colors, a payoff in dragons decks via its own dragon synergy. Low pick early in the format → consensus first-tier role-player. | 50t |
| **Rhor's Routine (?)** | Three-mana rampant growth. Not bad but clearly below Dragon Storm Globe in the ramp slot; would rather have a Globe in the dragon soup deck. | 50t |
| **Inoch Wayfairer (?)** | Hyped in the preview/early-access episodes as a premium fixer. Settled as mediocre. *Superseded* — do not take highly on the basis of early takes. | EL7L8ec |
| **Saron's Resolve (?)** | Excellent modal combat trick in green. "+3/+3 or destroy a flyer" was relevant enough that it was borderline worth playing even in decks that don't want tricks; closest thing to Plummet + Giant Growth in one. | 50t |
| **Snowmelt Stag (?)** | *Superseded* — heavily hyped in preview, settled at replacement level by week one. | EL7L8ec |

### Multi-color / Colorless

| Card | Take | Source |
|------|------|--------|
| **Dragon Storm Forecaster (?)** | "Looked cute, was actually excellent" in the five-color soup deck with Dragon Storm Globes. Ideal configuration: ~2 Forecasters, 2 Globes, 2 Boulderorn Dragons. Not a synergy engine so much as a density play — each piece is independently strong. | 50t |
| **Boulderorn Dragon (?)** | Excellent role-player as the 22nd–23rd card in dragon soup; enters as a 4/4 off the Forecaster or a 5/5 off a Globe. Looks underpowered; plays strong. | 50t |
| **Monuments (cycle)** | Good mana-fixing and color-filtering. Ranked: Mardu 1st, Jeskai 2nd, Sultai 3rd, Teamer 4th, Abzan 5th. Not game-winners. The hosts entered the format overrating them and settled on: take for fixing, never take highly. | 50t |
| **Devotees (cycle)** | Mana-fixing creatures. Mardu Devotee is the best (top common), Jeskai Devotee is the golden-egg glue. **Teamer Devotee: do not play it.** The format's biggest "C-minus stat, why do you hate it?" debate — but the 50t episode is unequivocal: it is not good; stop putting it in your decks. | 50t |
| **Coreway Mountain Monastery (?)** | Best rare utility land and it's not close. Jeskai control's card-engine in the late game. A real reason to draft a control deck. Most other utility lands are irrelevant (take-aways: utility lands largely dead in this power era). | 50t |

## Draft signals

**Good signals:**
- Exhales table late → your exhale color is being undervalued or the seat is open; exhales are almost always taken early when people are in those colors.
- Dragon Storm Globe and common dragons in pack two → the dragon soup deck is open; pick up aggressively.
- Mardu Devotee in picks 5–8 → white aggro is open or being cut; commit.
- Jeskai Devotee late → red-based decks are thin at the table.

**Bad signals / traps:**
- Opening a Dragon Storm Globe P1P1 is great — but drafting three of them and no dragons is a real failure mode the hosts hit multiple times.
- Seeing lots of hybrids late does NOT signal open clan lanes; the cards themselves are weak.
- Green-heavy early pack does not tell you whether to be soup, beatdown, or something else — green is genuinely that flexible/ambiguous.

**Signals philosophy (50t verdict):** This format was more about forging your own path than reading signals. Even picks 1–5 have multiple defensible answers. The exception is picks 6–12: when what you are doing "dries up" and a path opens, the signal is clear and real.

## Supersessions (early take → settled take)

Recency rule applied — newest episode wins.

| Card / topic | Early take (episode) | Settled take (50t unless noted) | Confidence |
|---|---|---|---|
| **Snowmelt Stag (?)** | Premium card, heavily hyped (preview) | Replacement-level common | High |
| **Inoch Wayfairer (?)** | Premium mana-fixer, first-pick discussion (early-access) | Mediocre; Sagu Wildling clearly better | High |
| **Hybrid commons/uncommons** | "Delayed decision" picks — high priority in 3-color format | Mostly filler; fixing too abundant to matter | High |
| **Sibig Appraiser (?)** | Dismissed or ignored in early rankings | Blue's best common, explicitly a designer-intended format pillar | High |
| **Dragon Storm Globe** | Low pick / novelty (preview/early) | Core piece of the best deck, consistently excellent | High |
| **Breaching Dragon Storm (?)** | Unplayable "random cascade" | Rock-solid in dragon soup | High |
| **Teamer Devotee** | Treated as fixing glue in 3-color format | Do not play it; C-minus performer | High |
| **Encroaching Dragon Storm (?)** | Overrated early (large "go get two lands" effect) | Real card but correctly evaluated; not as busted as initial hype | Medium |
| **Monuments** | High-priority picks for mana base | Fine for fixing; never high picks | High |
| **Narcissist Rebuke (?) + Focus the Mind (?)** | Too high week 1 after a good early pairing | Neither card is a high pick individually | Medium |
| **Channel Dragonfire (?)** | Passable cheap removal | Underperformed; sorcery speed hurts badly | High |
| **Constrictor Sage (?)** | Expected to be format-defining | Did not work; fell flat | High |
| **Essence Anchor (?)** | Expected to be a powerful build-around uncommon | Totally flat; not enough juice for the power level | High |
| **Wild Ride** | Dismissed as nearly unplayable (D on LR scale) | Real card in its correct home (Jeskai tempo, trample beatdown) | Medium |
| **Clan power order** | Unknown / Mardu assumed dominant (preview) | Teamer 1 > Jeskai 2 > Mardu 3 >> Sultai 4 > Abzan 5 | High |
| **White is the best color** | Unknown (preview) | Confirmed; but red is the preferred *starting* color for flexibility | High |

## Live disagreements (hosts on record at 50t)

These points reflect genuine unresolved preference differences as of the final episode. Both positions are reasonable.

- **Overall clan preference:** Ben's heart is Camp Teamer; his head suspects Camp Mardu may be technically better. At the Arena Open he intends to start red. Ethan is firmly Camp Teamer and leans Jeskai mid-range as a practical landing spot.
- **Mardu vs. Teamer:** The 50t verdict gives Teamer first in the clan power ranking. Ben disagrees slightly — suspects for tournament play where consistency matters, Boros/Mardu's lower variance might edge out soup.
- **Clan rankings specifics:** Ben would put Jeskai ahead of Mardu; Ethan's official ranking has Teamer 1, Mardu 2, Jeskai 3. They converge that there is a big gap between those three and Sultai/Abzan.
- **Whether this is a top-tier format:** Ethan had a "phoenix-from-the-ashes" journey and is a genuine fan. Ben acknowledges too many games decided by bombs/busted rares for his taste; rates the gameplay experience "fine" rather than great. Both agree it was an exceptionally interesting drafting and podcasting format.

## Mechanics quick reference

| Mechanic | Clan | How it works | Draft relevance |
|----------|------|--------------|-----------------|
| **Mobilize** | Mardu (WBR) | When creature attacks, create a tapped attacking 1/1 Warrior token; it gets sacrificed at end of turn | The most format-impactful mechanic. Powers go-wide; tokens need a pump effect (War Effort (?), etc.) to maximize. |
| **Harmonize** | Teamer (URG) | Can cast the card from graveyard for harmonize cost; tap untapped creatures to reduce cost by their power | Most powerful mechanic on paper; never quite became the engine deck. Feral Death Gorger (?) exiles harmonize cards — annoying. |
| **Endure** | Abzan (WBG) | ETB puts +1/+1 counters or creates a Spirit token; cannot be blanked by instant-speed removal | Present but Abzan fell flat overall. Carsey Revenant (?) + Hardened Battle Veteran (?) gets three counters for a 6-power flyer — rare combo that overperforms. |
| **Flurry** | Jeskai (UWR) | Triggers when you cast your second spell in a turn | Best in Wingblade Disciple builds; enabled by cheap spells, Jeskai Devotee's off-color activation, and spells like Seize Opportunity. |
| **Renew** | Sultai (UBG) | Exile creature from graveyard at sorcery speed to put counters on creatures | Best non-rare Renew cost: Champion of Ducson (?). The rest were too expensive to matter. |
| **Omens** | All | Like Adventures but shuffle back into library instead of exile | The "headline mechanic" because they are stapled to dragons; made having and casting dragons natural. Every deck wants to be in the Omen/dragon space if possible. |
| **Behold** | All exhales | Show/control a dragon as an additional cost for a discount on exhale spells | Core reason to put dragons in non-dragon decks; unlocks half-cost exhales. |

## Caption caveats

These transcripts are auto-captions and card names are heavily mangled. Names annotated (?) above are reconstructed from context. High-confidence corrections used without annotation (Molten Exhale, Caustic Exhale, Snakeskin Veil, Dragon Storm Globe, Wild Ride, Champion of Ducson (?), Shock Brigade). If a name looks odd it is probably a caption garble — cross-reference with the official TDM card list.

Most-garbled names in these transcripts: "Tarquir / Tarkier / Tarure / Tar" (= Tarkir), "Jess Guy / Just Sky / Jesse" (= Jeskai), "Mering River Regent / Marang River Regent (?)" (= likely Marang River Regent), "Feral Death Gorgger / Gorger" (= Feral Death-Gorger (?)), "Coreway Mountain Monastery" (= likely Koray Mountain Monastery (?)), "Sibig Appraiser" (possibly Sibi or Sibig Appraiser — the designers confirm it is intentional that this is one of the best commons), "Boulderorn Dragon" (= likely Boulderborn Dragon (?)). 

## Source episodes

| Shorthand | File | Date | Title |
|-----------|------|------|-------|
| `preview` | `4H7pjO1y4Eo.txt` | 2025-03-24 | TDM Preview Crash Course |
| `ea` | `YsMtK1eXVu4.txt` | 2025-04-07 | Early Access Info Dump |
| `wk1` | `EL7L8ec_R0k.txt` | 2025-04-14 | Week 1 |
| `dev` | `WPizty-xUT0.txt` | 2025-04-28 | Devotees Deep Dive |
| `design` | `nO4XEWWOaEY.txt` | 2025-05-05 | Designer Interview (Ben Whites) |
| `50t` | `aR_oF5QEhMg.txt` | 2025-05-19 | "TDM Goes Out in a Blaze of Glory!!" — 50 Takes in 50 Minutes |
