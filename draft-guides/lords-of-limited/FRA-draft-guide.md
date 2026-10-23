# FRA — Reality Fracture (Lords of Limited)

## ⚠ Recency rule (read first)

**Update 2026-10-23: episode 500, *"Has Fixing Gone Too Far?"* (2026-10-12, `dDXD8ejDPpI`, 1h 23m),
is now the newest source and overrides 499 on conflict.** It runs about a 35-minute FRA segment (a
"community narratives: fact or fiction" round, card check-ins and two draft-log reviews) after a
500th-episode retrospective, which is not used here. It is a whisper.cpp (medium.en) transcript of the
Audioboom feed audio, again with no speaker labels; YouTube returned HTTP 403 on audio. Attributions are
given only where the transcript makes them clear (e.g. Ben's own "Blessed Ghoul is a mulligan" take from
499). Otherwise they read "one host". 17Lands figures added on 2026-10-23 come from
`data/cache/17lands_FRA_PremierDraft_1200d.json` (GIH WR / ALSA, set mean GIH ≈ 55.1%) and the pair
deck win rates from `17lands_arch_FRA_PremierDraft.json`. **Not distilled:** episode 501, the Ben
Weitz designer interview (2026-10-19, `L4x-0ioWBOQ`).

**Episode 499 is a post-play read.** Episode 499, *"How High Is Your
Ceiling?"* (2026-10-05, `5kb0DiBo9CE`), was recorded Sunday 2026-10-04, one week after the Arena
release. Ben Warney and Ethan Sachs had both played a lot of Arena (Ben: Bo3 the first days, then Bo1
after the rank reset; both on mobile, so no 17Lands logs). They say they had not looked at the 17Lands
data before recording, apart from noticing that W/U was on top.

**Not yet distilled:** the three earlier FRA episodes, *Our First Impressions* (2026-09-14,
`FbY7H0ZgnFY`), *Our Prerelease Guide* (2026-09-21, `oQ3xhbEdHPg`) and *Early Limited Format Guide*
(2026-09-28, `rFiFLet4Cf8`). Those were pre-release and early-access reads, so they would be weaker
evidence than this one. This file has no Supersessions section until they are added.

**Transcript source:** YouTube refused captions from this machine (HTTP 429) on 2026-10-08, so this was
transcribed locally with whisper.cpp (medium.en) from the podcast feed audio of the same episode
(Audioboom episode 499). There are no speaker labels. Attributions to Ben or Ethan come from context
and are marked where unsure. Card names were checked against the FRA card list.

**Where this file disagrees with 17Lands, read it as "how to make this card good", not "this card is
good".** The hosts say so themselves (format truth 3). Their favourite build-arounds have low GIH WR on
purpose: the number averages every deck that played the card, most of which did not set it up.

### Source timeline

| Date | Title | Phase | Weight |
|---|---|---|---|
| 2026-10-05 | 499: How High Is Your Ceiling? Reality Fracture Drafts (`5kb0DiBo9CE`, 1h 16m) | week one, post-play, two draft logs | Strong |
| 2026-10-12 | 500: Has Fixing Gone Too Far? (`dDXD8ejDPpI`, 1h 23m; FRA segment ~35 min) | week two, community-narrative fact-or-fiction + card check-ins + two draft logs | **Strongest so far** |

## Supersessions

Episode 499 → episode 500. Episode 500 wins.

- **"Colour rankings don't matter" → "blue is best" is fact, but don't chase it.** They hold the line
  less firmly than last week, and the open-lane rule stands: "an open colour pair is better than
  contested blue." The community "blue is best / Sultai format" narrative is "warped too far". 17Lands
  deck win rates by colour agree the gap is small: blue 55.0% vs red/green/white 54.1–54.2%.
- **Blessed Ghoul: Ben "a mulligan" → Ben concedes it is "serviceable" as a one-of only in a deck with
  a bomb (an A) to dig for and recur.** The other host sees it as a lifegain-synergy piece (with
  Medic's Kitesail) and rates it like Unflinching Hortimancer. 17Lands: 54.1%, below average.
- **Infinite Coursework: Ben "so bad" → "it's a C"** (both hosts), playable when you need removal.
  17Lands: 55.8%, about average.
- **Ferocity of the Hunt: "good, terrifying" → mixed.** One host saw it impressive in a Sultai deck,
  re-buying Mindseeker Oculus. The other now files it under "plan B when the power isn't coming". 17Lands:
  52.8%, **contradicts** the 499 take.
- **Format speed: "long is not slow" (499) → stronger: "fiction, the format is not slow".** Games go long
  when both players engage, but they "can end in a hurry". They want "slow/fast" replaced by
  game-length / big-game-small-game language.

## Format speed / meta read

Both hosts put FRA in their **"GOAT tier"** of formats after one week. Their updated format truths:

1. **Colour rankings don't matter.** Take the most powerful card, with no soft forcing and no steering
   toward or away from any colour or wedge. Many P1P1s have two or three cards of equal power. In those
   packs, let the texture decide (what might wheel, which colour is flowing). Ethan sometimes takes a
   generically good mono-colour card such as Twinned Vision over an early gold card, because he does
   not trust himself to avoid over-weighting the gold card.
2. **What matters is reaching each card's ceiling.** The shape they recommend: about **5 cards that are
   good in any deck**, then about **10 uncommons with high ceilings** (build-arounds, or cards that
   support one plan well), then **8–10 commons that support those uncommons**. A high-ceiling card left
   without its support is "basically a dead card". With support it is an A. All bombs are beatable
   (Ben has beaten Ajani Unrelenting, Garruk, Veiled Butcher and others) **if** your deck is built this
   way.
3. **Use data with caution.** Quoting Samp from their Discord: 17Lands tells you which cards are good
   "with no work", i.e. in a random deck. It does not tell you how to reach a card's ceiling. They
   did learn from it: **Primal Witchstalker** (BG 2/1 menace, mill four, put a land onto the
   battlefield) was not on their radar until its uncommon GIH WR showed up, and it is now higher in
   their pick order. Their example the other way: Way of the Pyromancer sits near 52%, but strong
   players (they name Siggy / Mike Sigrist) are winning with it.
4. **Games go long, so be ready to grind. Long is not slow.** You still have to play to the board
   early. After the two-for-ones and three-for-ones are traded, the game goes long. Consequences:
   - **Mana sinks and repeatable advantages are premium.** Their poster child is **Theorist's Sanctum**
     (the blue rare land), a "B-level" card here because you have time to activate it.
   - **Basic landcyclers are better than Ben said last week.** Use them as the 22nd/23rd card that keeps
     you hitting land drops and can also be the threat that wins late (the blue 3/5 flyer). Do not use
     them as an excuse to run 16 lands.
   - **Board math is complex.** There are instant-speed counter effects, deathtouch, trample and more,
     and many players punt games on board.
   - **The longer the game, the more deck construction is rewarded.** Ethan's closing point: long
     games let you see more of your deck working together. That is why a well-built deck beats "some
     cards that are pretty good" so reliably.
5. **Let the draft tell you what to do.** Signals are strong: gold uncommons and clusters of one
   strategy's cards keep coming if a lane is open. Keep speculating through picks 4–7. With 10 real
   pairs and correctly pipped gold cards, an uncontested lane delivers all its niche pieces. **Do not
   hold onto an early bomb if its colour is not flowing:** "middling black cards plus a Garruk does
   not a good deck in this format make."
6. **Bonus truth: "draft cards, then decks."** Decide on a plan late. Each pair has several builds (W/U
   can be Cadets, butts with Ghalta the Immovable + Tetsuko, ETBs with Rescue Girl, or empower Jace
   with Way of the Healer). You cannot decide "I'm doing Tetsuko" from P1P3. Track what might wheel
   (Ghalta the Immovable often does) so you can move in if a second piece shows up.

**Empower Jace (strong opinions):**

- **Default: attack the opponent's Jace token.** Both hosts usually take the Jace off the board if
  they can. Games go long, so a dangling surveil 1 or draw is worth more than their life total.
  ("Eventually I will attack you for enough to kill you.") Deviate only when you can see the
  beatdown closing the game soon.
- **If Jace is part of your plan, you cannot fall behind on board.** Build so that you are never behind.
  Many opponents give up on attacking a Jace once it reaches 5–7 loyalty. Exploit that by planning
  bigger downticks.
- **Kill their Jace before they untap with Countersculpt mana up.** Countersculpt needs a Jace to
  behold.

**Removal is excellent.** Multiply by Zero was praised in particular. It answers creatures that carry
+1/+1 counters.

**Splashing is normal.** Ben has been "basically Jeskai or basically Jund" most drafts, using Room of
Refuge plus landcyclers to play the best cards from three open colours. This is partly week one: pick
orders are all over the place and powerful cards get passed.

### Episode 500 additions (2026-10-12)

- **Fixing (the episode title):** "has fixing gone too far?" Their answer is no. Landcyclers as cards
  21–23 plus duals make splashing easy, including double-pipped splashes (Kindred Judgment with about six
  white sources). One host is about 50/50 two-colour vs two-colour plus splash. **Landcyclers are drying
  up**: "you no longer get them for free" in pack three. They push back on "this is the creature version
  of Secrets of Strixhaven soup". An open two-colour lane loses no equity to splashers, and the designer
  said he wanted FRA to feel "cubey".
- **Format is bomb-heavy: fiction.** Bombs are answerable by well-built decks with plenty of removal
  ("unless they play three Ajanis").
- **Don't play filler two-drops: fact.** Void Extrapolator, Unflinching Hortimancer and Surveillance
  Phantasm need the right deck around them. Void Extrapolator is "actively harmful" outside threshold
  decks. 17Lands: Void Extrapolator 55.5% (above average; **contradicts** "terrible outside its deck" as an
  aggregate), Hortimancer 53.8%, Phantasm 57.2%.
- **"Plan B" when the power isn't coming:** after a pack-one opener with no power, pick B-level cards
  that keep the opponent off balance and end the game: Unsummon, Theorix Metamage, Unflinching
  Hortimancer, Medic's Kitesail. A deck whose best card is a B can't win a long game: "the game goes long
  for me? Cool, my cards are better."
- **Draft-log lessons:** (1) Take the best card for the first ~6 picks unless you've already met a power
  threshold. (2) Picks must fit the deck your best card wants. Rank Rat and Last Gasp (small-game black)
  don't go with Aerid Konstrari (big-game), so Saheeli, Jewel of Avishkar was the better P1P2. (3) A pile
  of B-level two-for-ones (W/B splash Vraska, the Cutting Glare, triple Hapatra, the Desert Fang, Flickering
  Hound) with no cohesive plan folded to blue Empower-Jace decks.

## Archetypes

- **R/W is bad: fiction (episode 500).** "Is it the weakest? Probably", but uncontested R/W beats contested
  U/B. Build it as **R/W control/grind**, not aggro: No Admittance and removal in the two-drop slot, Kiora
  of Fire and Ashes, Fateshaper Aspirant to rebuy, Rescue Girl loops protected by Teyo, Lightshield
  Expert. Mabel is "a red herring". One host gets pushed into Naya +1/+1 counters often (Yoshimaru into
  Blossom-Blessed Angel). The other worries those decks can't close. 17Lands: W/R is the lowest
  two-colour deck at 53.3% (W/U 56.4%), which **supports "probably the weakest"**.
- **Lifegain vs counters (white base):** usually start base white, then commit to **one** of +1/+1
  counters (comes together more often, because Yoshimaru, Beloved Companion goes late) or G/W lifegain
  (needs Way of the Paradox, Inspired Tethermage and a wheeled Hortimancer, so "the stars aligning").
  Never try both.

No colour or pair ranking, on purpose (truth 1). What they did say:

- **U/B (and W/B): rareless decks can win.** Ethan's 7-1 U/B draft log had **no rares**. It played a
  **small game**: five discard spells (two Rank Rat, Solve for Disappointment, two Tinybones, Pocket
  Nuisance), spot removal (Last Gasp, Multiply by Zero, Extended Absence) and **3–4 Theorix Metamage**
  as its evasive threats (3/3 fliers with threshold). Hand disruption is "brutal" against R/G ramp,
  which needs both its lands and its seven-drops. Ben had written off U/B before watching Siggy win
  with a "bad-looking" one. Both now say black-white commons and uncommons can hang too.
- **R/G (and Temur) ramp:** Heartwood Crafter is "terrifying" on turn one, but it needs top end
  (Craftwork Crusher) to ramp into. A deck of Heartwood Crafters is not a deck. Ben's best Temur draft
  had two Kiora of Fire and Ashes and two Craftwork Crusher.
- **R/G or Temur Jace ramp: "the dream team"** is **Way of the Pyromancer + Way of the Paradox +
  Inspired Tethermage**. Uptick Jace to add mana, gain life and make extra land drops, and grow
  Tethermage each time. Plan for All Outcomes adds another uptick.
- **W/U:** Ben noticed W/U is on top of the data. Ethan: Proft, Consulting Detective is a card you
  expect to come to you in W/U scry, not one to take early and lock in on.
- **G/W and W/x Seed Suture:** Danitha, Sword of Hope, Tomik, Orzhov Lawmage, Yoshimaru, Beloved
  Companion and Blossom-Blessed Angel are all Seed Suture payoffs. Each is only good if you have the
  Seed Suture creatures.
- **B/R noncombat damage / G/W lifegain:** the two Koths are free repeatable triggers, but only for
  those decks.
- **B/x sacrifice:** Way of the Deathbringer is its own sac outlet with disposable bodies (Rank Rat
  into Way of the Deathbringer is a good curve). It is not an empower-Jace card.

## Card notes

### Episode 500 notes (2026-10-12 — newest, override the 499 notes below)

`17L` = 17Lands Premier Draft GIH WR / ALSA, cache 2026-10-23 (set mean ≈ 55.1%).

- **Unsummon** — "undeniably good". One host calls it a hole in his game. It is maybe the second or
  third best common, but you can pick it as the eighth best "because nobody else gets it". You never move
  into blue for it, but any blue deck wants it. 17L: 57.3%, the #7 common (supports). ALSA 5.17 is
  mid-pack, not pick 10 (partly contradicts).
- **Cryotheory Adept** — "never wanna play it… card's not good." 17L: 53.2% (supports).
- **Divining Duelist** — only in draw-go blue control. 17L: 55.2%.
- **Icy Reception** — one host: "not great"; he "dances circles" around it. He reports that Defour rates it
  above Countersculpt ("insane") and that Sam Black is a big fan. It may still be blue's second-best
  common. **Contradicted:** 17L 57.7% / 5.13, the #5 common overall.
- **Surveillance Phantasm** — one host: only in a specific blue deck. The other: if you have Oculuses,
  your Phantasms are good, and he'd take it from pick 6 on. 17L: 57.2% / 4.81 (supports the higher take).
- **Sphinx's Approach** — "not happy about it". 17L: 56.0% / 7.41.
- **Semester Foreseer** — split: "clunky as all get out" vs "I like that card". 17L: 53.7%.
- **Protege's Awakening** — "fine", but only if you care about Empower Jace. One host prefers small
  incidental empowers (Campus Crier + No Admittance) to one big 4-mana divination. He says Samp is high on
  it and Defour thinks it's terrible. **Contradicted:** 17L 58.4%, the #3 common.
- **Undulating Witness** — maybe blue's #3 common. One host would take it over Icy Reception now that
  landcyclers disappear early. 17L: 55.7% vs Icy Reception 57.7% (**contradicts** the swap).
- **Fateshaper Aspirant** — always want one in white with Rescue Girl, good legends or counters. It's
  on the short list of white cards to splash. Take Prudent Fateseer over it early, but take it late in
  pack three if you lack one. 17L: 51.9% / 7.01 (**contradicts**; it goes last-pick late for a reason).
- **Campus Crier** — meets the playable-two-drop bar. 17L: 55.7%.
- **Blossom-Blessed Angel** — "win condition at common", and "the absolute business" in any +1/+1-counter
  deck. A 4/6 flying vigilance after Seed Suture. Best friends with Ghalta the Immovable. 17L: 55.9% / 4.97.
- **Academic Ascent** / **Predictive Preparations** / **Shatterwing Pegasus** — "never play" / "hoping to
  never play". 17L: 52.6% / 48.5% / 53.5% (supports).
- **Graft Surgeon** — fine in +1/+1-counter decks as a pick-8+ three-drop. 17L: 51.5%.
- **Hexhaven Battalion** — "very good as a land cycler". 17L: 57.4%.
- **Memory Trap** / **Surgical Precision** — "premium removal" / "good removal". 17L: 55.8% / 57.3%.
- **Unflinching Hortimancer** — don't spend a pick; very good in the right deck. 17L: 53.8%.
- **Medic's Kitesail** — Ethan's narrative "is it busted?": "fact, I think". "When it's right to play it,
  it is always a problem." White has few answers to equipment (Memory Trap). 17L: 54.3% / 7.07
  (**contradicts "busted"**).
- **Void Extrapolator** — "actively harmful" outside Omit Variables/threshold decks. 17L: 55.5%.
- **Flickering Hound** — "a very fun build-around, much like Rescue Girl", in R/W control or Abzan with
  Hapatras and Vraskas. One host took it P1P4 over Hexhaven Battalion with Vraska in the pile, and the deck
  lacked cohesion. **Strongly contradicted:** 17L 45.2% (n≈4k), one of the worst rares in the set.
- **Kindred Judgment** — "just Dune Blast, it's very good… a bomb rare". It's no longer a white signal,
  people now know. Splash it double-pipped with about 6 white sources. 17L: 61.4% (supports).
- **Ajani Resolute** — "kind of a problem in lifegain decks". If your deck wants Hortimancer, it wants
  this. **Contradicted:** 17L 52.6%, very weak for a mythic.
- **Twisted Fates** — "by far the best card" in a P1P2 pack. 17L: 56.9%.
- **Vraska, the Cutting Glare** — "one of the best rares in the set", passed P1P3 alongside Multiply by
  Zero. 17L: 62.4% / Multiply by Zero 58.9% (supports).
- **Bestial Incursion** — "terrible… the antithesis of what the format is about", a raw-rate card with no
  synergy. Not a green signal. **Contradicted:** 17L 56.2% / 4.81, above average.
- **Vigorbloom Charm** — best in a weak P1P5, but not great to splash. 17L: 56.4%.
- **Greenhouse Propagator** — "this card's great", especially in lifegain; incidental life matters.
  17L: 54.4% (**contradicts "great"**).
- **Woodwork Prodigy** — one host would take it over Last Gasp. The other is "not impressed at all".
  17L: 52.3% vs Last Gasp 56.8% (sides with the sceptic).
- **Clash of Elements** — the best card in a weak pick. 17L: 58.4% (supports).
- **Kiora of Salt and Sand** — one host would take it to move into U/G big Empower Jace off Aerid
  Konstrari. 17L: 53.7% / 6.41 (weak).
- **Paradox Shaper** — in a deck that doesn't use the stacking, it's just Omit Variables plus a 1/3, "not
  a good card". 17L: 54.9%.

### Episode 499 notes (2026-10-05)

- **Rescue Girl, First Responder** — the hosts' "us against the world" card (52.6% GIH). Ben calls it
  close to never-pass. Ethan is not on that train but re-evaluates his whole pile when he sees one.
  Loops: Plan for All Outcomes (lock the opponent out), the R/W Helix equipment, any Way enchantment,
  planeswalkers you downtick and replay, Fateshaper Aspirant, and Kiora of Fire and Ashes (one game
  ended with Kiora replayed every turn). **A+ when it hits, D/F when it doesn't.** It is a 1/3 flier on
  turn three, so you need to be on board early. Ethan has P1P1'd it and then not played it.
- **Ghalta the Immovable** — the classic "butts" build-around for W/U or W/B. It ranges from B+ to F
  in your deck. Speculate on it, but don't chase the support early. It often wheels.
- **Plan for All Outcomes** — the highest floor of their build-arounds (one of the best cards they saw
  all draft at P1P7). Removal that you can rebuy with Rescue Girl. Every first noncombat spell each turn
  upticks Jace, which makes repeated surveils in Jeskai and pairs with Way of the Pyromancer.
- **Traxos, Academy Guardian** — 1/5 flying vigilance for three when you've cast a noncombat spell
  this turn. A high floor (fine at four mana). The best enabler is a two-drop with Omit Variables cast
  on turn three, then Traxos on the same turn.
- **Way of the Pyromancer** — 52% GIH, and they say it is strong if you pick your spots. It is nuts on
  turn two when uncontested. Don't run it out and immediately lose it. Wait until you can protect it
  (for example turn four plus a three-drop). The drafter (Ethan (?)) would P1P1 it over Extended Absence with an empty pile.
- **Way of the Paradox** — part of the Jace ramp dream team with Way of the Pyromancer and Inspired
  Tethermage. You can play your whole deck's lands.
- **Inspired Tethermage** — **Ep 500 (10-12):** a needed piece for lifegain with Way of the Paradox. 17L: 51.6%. **Ep 499:** the mana sink for the Jace ramp deck. Tethermage's 6-mana Jace + Way of the Pyromancer uptick + Plan for All Outcomes uptick grows it several times a turn.
- **Ghalta the Unstoppable** — very strong. Usually costs 1–5 mana in a green deck. Go after it
  aggressively. Best in R/G ramp, also G/W.
- **Heartwood Crafter** — explosive on turn one in R/G ramp and still fine on turn four, but needs top
  end (Craftwork Crusher) to ramp into.
- **Danitha, Sword of Hope** — as good as the number of Seed Suture creatures you have. One host had
  No Admittance fizzled when the opponent targeted Danitha in response with a 1-mana white removal
  spell that gives a card (Memory Trap (?)), drawing off both.
  Ethan rates Proft, Consulting Detective above it (easier to trigger, better curve slot). Ben
  disagrees.
- **Koth of the Homestead** — free repeatable lifegain in a lifegain deck. Bad elsewhere.
- **Koth, the Geomancer** — free repeatable noncombat damage for B/R. Bad elsewhere.
- **Tomik, Orzhov Lawmage** — a 2/1 flier is below the format's power bar in a random deck. It needs
  big +1/+1-countered creatures to lift into the air.
- **Yoshimaru, Beloved Companion** — **Ep 500 (10-12):** one host's "most played and most drafted" card. It goes late and pushes him into Naya counters. Yoshimaru into Blossom-Blessed Angel makes a 4/6 flier. The other host has never played it. **Contradicted:** 17L 49.6%, the second-lowest white uncommon. **Ep 499:** 3-mana 2/2 looks too weak, but one extra counter pays for it. Outstanding with Blossom-Blessed Angel. Like Rescue Girl, you can't afford to fall behind with it.
- **Countersculpt** — "this card is nuts". Ben's best deck was a draw-go control deck with three of
  them. Ethan: take it over Twinned Vision even with no Jace support yet. "Cancel is not that bad in this
  format." It needs a Jace on the battlefield to be Counterspell rather than Cancel.
- **Hapatra, the Desert Frost** — Ben had it as unplayable. With **Loot, the Nexus** and four different
  powers among your creatures, it makes **infinite mana**. You still need a place to spend it (Inspired
  Tethermage, Wrecking Gecko).
- **Proft, Consulting Detective** — Ethan: not a card to lock in on early. It comes to you if you're W/U
  scry. Ben: easier to trigger than Danitha (empower Jace or Peer Review) and a better curve slot.
- **Way of the Cryomancer** — needs the whole empower-Jace package and the "don't be behind" rule. Its
  −3 copying a spell late is "way better than −3 draw a card" because it is a mana advantage.
- **Way of the Necromancer** — Ben's mea culpa: he praised it last week and now calls it unplayable.
- **Way of the Deathbringer** — **Ep 500 (10-12):** "its own thing": it doesn't build on Empower Jace. Pair it with Rank Rat and Gallia, Tragic Host. 17L: 51.3%. **Ep 499:** can be good if you have disposable bodies. It works as a self-contained sac outlet.
- **Titanbones, Towering Heart** — not a good card, but "an outstanding 22nd or 23rd card" in R/G Way of
  the Paradox or Seed Suture lifegain decks.
- **Primal Witchstalker** — moved up their pick order after the data: it hits land drops, ramps, fuels
  the graveyard, and menace pressures planeswalkers.
- **Multiply by Zero** — "amazing". The best card in a weak P1P2.
- **Theorix Metamage** — Ben had it as a "nothing burger". It is now the evasive threat of rareless U/B
  (often 3/3 flying). Never first-pick it, but see Archetypes.
- **Recursive Recruitment** — really good and very splashable. Ben has splashed it in W/B and U/R.
- **Generous Revival** — almost a W/B (or W/U) gold card. It needs specific targets such as Rescue
  Girl. Ben: similar power to Recursive Recruitment in the right home, but Recruitment has the higher
  floor and probably the higher ceiling.
- **Way of the Healer** — Ethan's P1P1 over Prudent Fateseer (close). Higher ceiling.
- **Prudent Fateseer** — great and flexible, close to Way of the Healer.
- **Blessed Ghoul** — **Ep 500 (10-12):** see Supersessions. 17L: 54.1%. **Ep 499:** Ben: "a mulligan every time my opponent has played it". Life totals rarely matter. It's a sideboard card or a last-slot filler, never worth a pick.
- **Screeching Soulbreaker** — Ben doesn't like it yet. Ethan does (unresolved).
- **Saheeli, Consul of Oversight** — not on their radar even with W/U on top. It is only 55.8% GIH.
- **Saheeli, Jewel of Avishkar** — **Ep 500 (10-12):** better than Rank Rat P1P2 next to Aerid Konstrari; a repeatable Soul Tether with Woodwork Prodigy and Heartwood tokens. 17L: 56.8% vs Rank Rat 55.0%. **Ep 499:** neither host loves it. Tapping out on turn four and hoping it survives is not a plan. It was only great in Ben's triple-Countersculpt deck, where he could cast it on turn six with counter backup.
- **Jace's Machinations** — "a cool card". Empower Jace 8 makes it the best enabler for the Kraken plan.
  Ethan took it P1P1 over Hapatra, the Desert Fang.
- **Hapatra, the Desert Fang** — by far the best card in Ethan's P1P3 pack. He regrets taking Way of the
  Warlord over it.
- **Living Library** — never worth a pick, but a correct 23rd card. It protects planeswalkers early. Its
  6-mana shuffle answers threats you don't want to kill (Sphinx of False Conclusions), and it makes
  Ghalta the Unstoppable cost five.
- **Tetsuko Umezawa, Fugitive** — a ceiling pick when the pack is weak. It pairs with Mindseeker
  Oculus (a 1-toughness creature becomes unblockable).
- **Mindseeker Oculus** — **Ep 500 (10-12):** "incredible". P1P1 over Proft, Consulting Detective in a weak pack: Proft has the higher ceiling, Oculus the higher floor. 17L: 59.8%, #1 common (supports). **Ep 499:** Ethan took it over Countersculpt in a weak draft, because a Jace deck has to play to the board.
- **Room of Refuge** — Ben took it P1P5 in a messy draft to lock up fixing. He cracks it often, while
  Ethan rarely does because he has better uses for the mana.
- **Ferocity of the Hunt** — **Ep 500 (10-12):** see Supersessions. Best on small two-for-one value creatures (Oculus, Rank Rat), not to save a big threat. 17L: 52.8%. **Ep 499:** good. "Terrifying" when the opponent has big green creatures.
- **Infinite Coursework** — **Ep 500 (10-12):** "it's a C" (see Supersessions). 17L: 55.8%. **Ep 499:** Ben: "so bad". Ethan has played it. Something has gone wrong if you're playing it.
- **Skilled Battlecarver** — R/W needs these late. Don't spend early picks on them.

## Source episodes

- 2026-10-05 — 499: How High Is Your Ceiling? Reality Fracture Drafts / *Reality Fracture Format Update
  (How High Is Your Ceiling?)* (`5kb0DiBo9CE`), 1h 16m, week-one post-play read plus two pack-one draft
  logs. Whisper transcript of the podcast-feed audio. YouTube captions were rate-limited.

- 2026-10-12 — 500: Has Fixing Gone Too Far? - Episode 500 / *Has Fixing Gone Too Far? // Episode 500!*
  (`dDXD8ejDPpI`), 1h 23m, a 500th-episode retrospective (not used), then community-narrative fact or
  fiction, card check-ins and two draft-log reviews. Whisper.cpp medium.en transcript of the Audioboom
  feed audio. YouTube audio returned HTTP 403.

Not yet distilled: 2026-09-14 (`FbY7H0ZgnFY`), 2026-09-21 (`oQ3xhbEdHPg`), 2026-09-28 (`rFiFLet4Cf8`),
2026-10-19 (`L4x-0ioWBOQ`, 501: the Ben Weitz designer interview).
