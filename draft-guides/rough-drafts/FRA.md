# FRA — Rough Drafts notes

> Source: **Rough Drafts** (Samp — Sam Pardee) — 2 Reality Fracture episodes distilled: ep 80
> (Hot Topics preview, 11.7k words) and **ep 82 "Theorix Metamage" (2026-10-08, played, ~7.1k words,
> added 2026-10-08)**. Ep 81 "Campus Crier" (2026-10-01) is not distilled yet. Ep 82 was transcribed
> locally with whisper.cpp (medium.en) from the Libsyn podcast audio, because YouTube rate-limited
> caption downloads (HTTP 429) that day. Ep 80 was distilled 2026-09-27 from YouTube auto-caption
> transcripts. Card names are corrected against the printed FRA card list (Scryfall), uncertain readings marked `(?)`.
>
> **Ep 80 — pure preview, nothing played.** Episode 80 went up 2026-09-24, the day *before* the FRA
> prerelease (2026-09-25) and eight days before the Arena release (~2026-10-02). Samp played no
> Early Access or prerelease events before recording and says so up front: *"This is not a full set
> review. This is not really me grading the cards. I haven't even put a tier list together. This is
> questions I have going into the format."* He calls the set *"more difficult to evaluate than any
> in the past couple years"* and pushes his next episode to Fri/Sat 2026-10-02/03 to get games in
> first. Every note below is a **prediction from card text**. His own letter ranges are quoted where
> he gave them.
>
> **Not blind, but pre-data.** There is no 17Lands data for FRA yet. Samp points listeners to the
> Lords of Limited and Limited Level-Ups set reviews, so this is not the decorrelated blind read of
> the channel's HOB run either.

## ⚠ Recency rule (read first)

- **The newest episode wins on any conflict.** Episode 82 (2026-10-08) is the first FRA episode
  recorded after real games: about a week of Arena drafts, mostly in Sultai colours. It overrides the
  ep-80 preview wherever they disagree. See `## Supersessions`.
- **Episode 80 (Hot Topics) is a PREVIEW** recorded before anyone had played the set: zero drafts,
  no Early Access, no prerelease. By design it asks questions instead of giving answers. Weakest
  evidence class. On MSH, the Hot Topics episode was the one later episodes overturned most often
  (see `MSH.md`).
- **Expected next:** episode 81 around 2026-10-02/03, probably titled after **Ferocity of the Hunt**
  if the card *"actually pans out being good."* Whatever it says overrides this file.
- The last ~8 minutes (54:00 onward) are a **cube segment**. It is kept separate below and is not
  Limited advice.
- These notes **decode** the 17Lands data rather than ranking beneath it, once that data exists.
  See AGENTS.md.

### Source timeline

| # | Date | Episode | Phase | Played? | Weight |
|---|------|---------|-------|---------|--------|
| 80 | 2026-09-24 | Reality Fracture Hot Topics | Hot-Topics — preview, zero games, questions not answers | **No** (pre-prerelease, no Early Access) | **Weakest** |
| 81 | 2026-10-01 | Campus Crier | card-episode | Yes | *not distilled yet* |
| 82 | 2026-10-08 | Theorix Metamage | card-episode (graveyard/self-mill theory + colour hierarchy) | **Yes** (~1 week of Arena, heavy Sultai) | **Strongest so far** |

## Supersessions

Ep 80 preview → ep 82 (played), and the verdict.

- **"The format is not soupy" → he is "playing full Sultai a decent amount."** Ep 80 predicted that
  finding an open pair would beat card quality, with only green able to splash (into red). Ep 82: his
  green-black decks keep playing blue cards "because they're just good". He treats single-pipped
  Recursive Recruitment as a mono-colour card during the draft because it is so easy to splash.
  **Ep 82 wins.**
- **"Black is a slight step below the other colours" → black "really impressed me and really
  over-performed".** He now says blue is ahead of everything, not that black is behind. **Ep 82
  wins.**
- **Colour balance → a clear hierarchy.** Ep 80 expected an even 10-pair spread. Ep 82: **blue > black
  ≈ green >> red, white.** He biases away from red or white *as a base colour* early. **Boros is the one
  pair he does not want to be.** Red or white as the second colour beside a Sultai colour (W/U, U/R,
  G/R) is fine.
- **Omit Variables creatures: expected D → "solidly C".** Theorix Metamage, Void Extrapolator and
  Paradox Shaper make his decks regularly, though he does not draft them highly.
- **Open question 5 (is there a Paradox Shaper loop deck?) answered:** it exists. He sees Paradox
  Shaper mainly as **insurance against decking**, not as a win condition. See below.

## Format speed / meta read

### Episode 82 update (2026-10-08, played — supersedes the ep-80 preview below on conflict)

**Thesis: the Sultai colours (blue, black, green) are well ahead of red and white, and the reason is
the graveyard.** The format is balanced overall, but the colours are not as balanced as people say.

- **Colour hierarchy: blue > black ≈ green >> red, white.** Part of blue's lead is that Arena drafters
  don't respect blue cards. He keeps getting **Mindseeker Oculus**, "pretty clearly the best common in
  the format", very late, and expects that to change within a couple of weeks.
- **Why self-mill works here: two separate payoffs.**
  - **Card advantage:** a full graveyard gives you new things to spend mana on, such as flashback
    (Twinned Vision, Recursive Recruitment, Bestial Incursion) and activated abilities from the yard
    (Theoretical Necromancer, Gallia, Tragic Host, Campus Crier). This is the blue-black side.
  - **Card selection:** milling lets you find and re-buy your best cards (raise-dead and regrowth
    effects). This is the black-green side. The canonical line is rebuying Craftwork Crusher.
  - In practice he is often full Sultai and gets both, which is why he thinks this space is so strong.
- **Why Omit Variables is the best prepared spell in the set.** The tension with prepared creatures
  is that you can't trade the creature until you've cast its spell. Omit Variables costs one mana
  ("one mana rounds to zero", since you often have one spare) and is **not timing-sensitive**: a full
  graveyard is a latent advantage. Seed Suture (G/W) and Vicious Verse (B/R) are different. They
  need a lifegain or noncombat-damage payoff already out to get full value, which makes those
  prepared creatures more awkward. Omit Variables also works as a free noncreature spell trigger for
  prowess, Saheeli, Jewel of Avishkar and Plan for All Outcomes.
- **Landcyclers:** he can't remember a deck this format without at least one. In graveyard decks they
  work like fetchlands that put themselves in the graveyard, which matters for Rewrite Regrets.
- **Don't play more than 40 cards in self-mill decks.** Play 41+ only if **all three** are true: no
  Fblthp, Impossibly Lost; no second Paradox Shaper (one is usually enough); and no strong
  finishers. The format is "so long on powerful cards that can win the game". At 10 cards left,
  Recursive Recruitment makes "10 tens". Extra cards just lower the chance of seeing your best ones.
  "Make the hard decisions, just play 40."
- **B/R: build it as spells-control, not beatdown.** If you end up B/R with a lot of red interaction,
  B/R spells (Twinned Vision, Command the Stage recursion, Grim Repriser), probably splashing blue, is
  "more consistent than the black-red beatdown deck the set implies".
- **White is the least graveyard-relevant colour.** He built one W/B deck after first-picking
  Kindred Judgment, carried by its black graveyard cards. Campus Crier and Generous Revival are white's
  graveyard cards.

### Episode 80 preview (2026-09-24, weakest — kept for the record)

**The thesis: FRA is a real 10-archetype set with an unusually deep, even spread of gold
uncommons. That means normal draft navigation: find the open colour pair. The format should not be
soupy. The only exception is green, whose Heartwood tokens let it splash red heavily.**

- **Relief first: full ten archetypes.** The allied pairs are the Hexhaven colleges and carry loud
  themes (WU "sky surveil" is *"very loud"*). The enemy pairs are the Echoverse Lorwyn-five
  planeswalkers and carry light themes (BG "trample plus deathtouch" is *"not really a theme of a
  deck, that's just a thing you can do"*). **What matters is that every pair gets two gold uncommons
  and one gold rare**, so the louder college themes should not skew navigation the way Lorwyn
  Eclipsed's did. He predicts the field over-drafts the colleges because their themes are easier to
  read. He does not plan to.
- **The gold uncommons are the headline.** *"Almost all of the gold cards in this format, all 20 at
  uncommon, look extremely strong. They look like the best cards in the format."* He rates this set's
  gold cards above Duskmourn's, March of the Machine's and Murders at Karlov Manor's. They should
  paper over any mono-colour imbalance, which was the failure of MSH's 10 weak "nephew" signposts.
  - Weakest gold cards: **WU and GW**, *"a notch below"*. Both pairs have well-supported themes
    (surveil; lifegain + counters), so they need their gold cards less.
  - Strongest: **black's gold cards**, *"maybe the strongest of the bunch."*
  - **Weakest charm is paired with the strongest gold uncommon:** Konstrari Charm + Craftwork Crusher
    in RG.
- **Colour balance guess: black is "a slight step below the other colours"** in mono-colour
  cards. The gold cards should cover that gap.
- **Empower Jace is the big unknown and the most skill-testing mechanic in years.** Reading "empower
  Jace 3+" as "draw a card" is *"correctly shortcutting"* but misses the nuance:
  - **One loyalty activation per turn.** Multiple empower cards on one turn do not give multiple
    draws. Diminishing returns, so there is a cap on how much you want (unlike the ring tempts you,
    or start your engines, where "eight or zero" was right).
  - **Sequencing questions:** −1 surveil now, or bank loyalty for a −3 draw? Split two empower cards
    across turns, or stack them? When should you attack the opponent's Jace, and when should you
    let your own die?
  - **Trick:** take your Jace to exactly 0, then cast another empower card the same turn to get a
    second activation.
  - **Comparisons:** amass (too much of it is a liability; he ran into that in HOB), but amass had
    haste-by-counters and this does not. **War of the Spark** is the better model: *"it really
    rewarded the snowball effect of getting on board early"* so you can pressure their walker and
    protect yours.
- **Fixing is good. The format is still not soupy.** Common taplands that enter untapped if you
  control a planeswalker (e.g. Fatehold Annex) replace a basic in ~56% of packs. Midnight Hunt rare
  duals (Deserted Beach) show up at about half of tables. There are Room of Refuge, the
  Murmuring Volume manalith and a full basic-landcycler cycle. **But there are only ~12 gold rares +
  ~6 gold mythics, mostly correctly double-pipped, no rainbow mana dork (nothing like Undercover
  Skrull) and no converge-style payoff.** The gold uncommons are cheap interaction and 2–3 drops,
  not top-end worth stretching for. **"You are going to get more heavily rewarded for finding an
  open color pair than you will relying on card quality."**
- **The one asymmetric splash: green → red via Heartwood.** The RG prepared spell (Soul Tether)
  makes a Heartwood token (an R/G mana rock). It appears on three cards below rare, all playable in
  mono-green: Konstrari Improviser, Woodwork Prodigy and Heartwood Crafter. So **green decks can
  splash, even double-splash, red**, chiefly for Craftwork Crusher. Red decks get the two hybrids
  but not Heartwood Crafter, so the reverse splash is weaker. *"The really heavy multicolor decks
  are really only available to green and it's really just for red."* He plans to do this *"from the
  get-go of the format."*
- **Graveyard sub-themes enabled by ten real pairs:** UB self-mill (Omit Variables, threshold),
  Sultai loops (Paradox Shaper + Bestial Incursion flashback + Something Worth Saving), and
  Grixis/BR spells (Command the Stage recursion, Twinned Vision flashback). He doesn't know how to
  build these yet. He calls them the part of the set he is most excited to explore.
- **Controlling the battlefield should matter a lot**, because of the Jace-pressure dynamic. That
  is why Unsummon and cheap creatures that trade are on his watch list.

## Archetypes

No ranking. He has played zero drafts. These are the per-pair reads he did give:

| Pair | Theme | Read |
|---|---|---|
| **RG — Konstrari** | Heartwood artifacts / ramp | The most interesting pair to him: weakest charm, but **Craftwork Crusher looks like the best uncommon in the set**, and green's Heartwood lets base-green decks double-splash it. |
| **BR — Stingerquill** | noncombat damage to the opponent | Theme *"looks a little finicky… a little bit A plus B"*, but **both gold uncommons are B-range** (Stingerquill Charm, Grim Repriser), so it is still a fine lane. Also has a Grixis-spells graveyard angle via Command the Stage. |
| **UB — Theorix** | self-mill / graveyard | Either **Grixis spells or Sultai graveyard**. Possibly a mill-your-whole-library loop deck around Paradox Shaper. |
| **UG** | empower Jace | *"The blue green theme just is empower Jace."* Rewards for a high-loyalty Jace (the Kiora card). Candidate home for Way of the Mind Sculptor and Way of the Paradox control shells. |
| **WU — Fatehold** | sky surveil | *"Very loud"* and well supported. Gold cards a notch below the rest. |
| **GW — Vigorbloom** | lifegain + +1/+1 counters | Well supported (Surgical Precision, Unflinching Hortimancer, Medic's Kitesail). Gold cards a notch below the rest. |
| **BG** | trample + deathtouch | Light theme. Ferocity of the Hunt is the glue. |
| Other enemy pairs | Lorwyn-five Echoverse | Not discussed beyond "light themes, balanced gold cards". |

## Card notes

### Episode 82 notes (2026-10-08, played — override the ep-80 notes below)

Hedges are his. Where a card also has an ep-80 note further down, this one is newer.

- **Mindseeker Oculus** — "pretty clearly the best common in the format". He keeps getting it very
  late on Arena and expects that to stop soon.
- **Theorix Metamage** — expected D, now "solidly C". It makes his decks regularly, though he doesn't
  take it highly. With threshold it is a 3/3 flier, so a two-drop → Theoretical Necromancer → Metamage
  curve can end the game fast in Dimir.
- **Void Extrapolator** — same verdict as the Metamage: expected D, now solid C.
- **Paradox Shaper** — his favourite of the Omit Variables three. It re-prepares every turn, so every
  turn you get a free 1-mana noncreature trigger (Saheeli, Jewel of Avishkar; Plan for All Outcomes;
  prowess). It can put graveyard cards on the bottom of your library. **Mainly decking insurance in grindy
  games, not a win condition.** If you are turbo-milling toward a Fblthp win, he wants two.
- **Primal Witchstalker** — "the best enabler below rare in the set". Just a really good card.
- **Something Worth Saving** — the Cache Grab template, which is "baseline C anytime it's printed".
  It's the #1 green common in the data. He doesn't take it that highly because extra copies have
  diminishing returns, but the first one or two are very good in almost any green deck that isn't
  beating down.
- **Theorix Charm** — he uses the mill-3-draw mode a lot, at instant speed to turn on threshold mid-
  combat or to set up a Fblthp win. It counts itself, so it puts four cards in your graveyard.
- **Rewrite Regrets** — "very strong", unlike Zombify (an F in SOS). The empower Jace 2 matters: it is
  close to Zombify plus a card. Consistent targets are the landcyclers (Vinelasher Adept, Apex
  Witchstalker), planeswalkers and bombs. Pairs with Proft, Sinister Mastermind: discard it to kill
  something, then reanimate a 3-mana 5/5 menace.
- **Proft, Sinister Mastermind** — he likes it a decent amount. On Arena you can rebuy it with
  Theoretical Necromancer at instant speed and discard it as a combat trick.
- **Theoretical Necromancer** — "maybe the most important black graveyard card". It gives both card
  advantage and card selection. When milled, it's a free 4-mana raise dead. "I want two copies in every
  single black deck." The 3-mana 4/1 body is good too: 4 power trades with Beast tokens and pressures
  planeswalkers.
- **Gallia, Tragic Host** — a 2-mana 2/1 menace is a good rate on its own, and free when milled.
  Menace matters more in the small-board games black decks create.
- **Blessed Ghoul** — he plays **one** when milling a lot because it often lands in the graveyard for
  free. Never multiples. It loops with Murmuring Volume.
- **Recursive Recruitment** — "phenomenal". He almost never wants to cast the front side. Flashback
  regularly makes two 5/5s or 8/8s. **During the draft he treats it as a mono-colour card**, because
  single-pipped U/B is easy to splash in Sultai.
- **Twinned Vision** — "just phenomenal", taken highly. When milled, it's a free Divination from the
  graveyard. It is also the reason B/R spells works.
- **Cryotheory Adept** — "not great", but a two-drop that does something free from the graveyard.
  Its ability is sorcery-speed only (he got that wrong in a game).
- **Bestial Incursion** — when milled, it's a free six-mana 4/4 trample that is "more or less draw a
  card".
- **Hapatra, the Desert Fang** — "just great". X is often 6 because of the landcyclers. Something Worth
  Saving and Primal Witchstalker turn it on cheaply.
- **Restore with Empathy** — he hasn't played it yet. "Looks really bad, but it's definitely playable"
  as another way to rebuy your best card (Craftwork Crusher).
- **Marwyn, the Preserver** — fine. Play it when you need a two-drop. It gets better when you can
  pitch lands to Murmuring Volume and return them.
- **Command the Stage** / **Grim Repriser** — janky B/R recursion that comes back free when milled.
  Grim Repriser also likes Omit Variables as a prowess trigger.
- **Campus Crier** — in a milling deck, free empower Jace 2s from the graveyard.
- **Generous Revival** — not tried yet. He could see splashing it in Esper with good cheap rare
  targets (Paradox Shaper loops, Vraska, Gideon, Sanctum Lurker).
- **Fblthp, Impossibly Lost** — its GIH WR is **inflated**: every copy drawn counts. In a Fblthp
  library-out win you draw it several times, so winning games are over-counted. Still "pretty good":
  it plays like Chart a Course with suspend, which suits a card-draw effect. **Always pair it with
  Tetsuko Umezawa, Fugitive** (makes it unblockable). With Paradox Shaper, milling your library
  becomes a real win condition.
- **Murmuring Volume** — a loop engine with Blessed Ghoul and Marwyn, the Preserver.

### Episode 80 notes (2026-09-24 preview)

Every note in this section is a pre-play prediction. Hedges and letter ranges are his own. Where he said he has
questions, that is the note.

### White

- **Surgical Precision** — {1}{W} sorcery: destroy a toughness-4+ creature and gain 1, **or** draw a
  card and gain 2. Compared to Murdock's Crusade (MSH) and Destroy Evil (DMU), which were both near
  the top commons. The template was *"already like C+/B−"*, and a cantrip buyout mode on top is *"kind
  of ridiculous."* **"This should be a top common."** Caveat: in a leaner format the toughness-4
  mode may miss more often. The lifegain feeds GW.
- **Hexhaven Battalion** — six-mana three 2/2 Cadets + empower Jace 2, basic landcycling {2}. **Best
  of the landcycler cycle** by his read (with the red one), but *"more worse than Imperial Oath than
  people are giving it credit for"*: the tokens lack vigilance and it is double-pipped, so it is
  harder to splash. *"Still looks solid."*
- **Medic's Kitesail** — two-mana equipment, +1/+0, flying, gain 1 on attack. Kitesails are *"never
  unplayable, never top commons."* The upside here is the lifegain trigger with Unflinching
  Hortimancer, especially in GW. *"Something I think we will be casting a little more than we think
  we will"*, especially in best-of-three sideboarding.
- **Unflinching Hortimancer** — the two-mana 2/1 ward 1 Ajani's Pridemate variant. Named only as
  the Kitesail payoff that becomes *"a huge threat."*
- **Way of the Healer** (?) — *"there is a white one that just gives your Jace −2: make a 2/2 and
  surveil 1"*. He files it among the Way enchantments that are *"clearly strong."* Identified from
  the description; he did not name it.

### Blue

- **Mindseeker Oculus** — three-mana 2/1, empower Jace 4. His worked example. *"Our brains go, oh
  this is like Bilbo"*: a three-mana 2/1 cantrip with a later surveil. It is **worse than that** with
  multiples on one turn (one activation per turn), and **better** with planeswalker-matters cards.
  He does not know which it will be.
- **Unsummon** — {U} instant bounce, the first straight reprint in years. Compares it to Aetherdrift's
  Bounce Off (a top common). **"Unsummon's going to be great if my prediction is right"** that
  controlling the board matters: use it to strip loyalty from their Jace by removing a blocker, or to
  protect yours by removing an attacker. *"I'm really excited to draft a bunch of copies."*
- **Plan for All Outcomes** — four-mana enchantment: owner puts a nonland permanent on top or bottom
  (their choice), then empower Jace 1 on your first noncreature spell each turn. It is weaker than
  the usual top-or-bottom spell because top means *top*, not second from the top. Range given:
  **"C−/D+ level removal to B level removal"** depending on how much the empower Jace upside
  matters. Multiples make your Jace huge.
- **Way of the Mind Sculptor** — five mana, empower Jace 5, draw whenever you remove 2+ loyalty. *"A
  five mana draw two, which is not good"*, but it could produce a lot of value over time. **Expect
  bad data**: *"people are just going to put them in random decks."* He thinks it has a home in a
  grindy UG/Sultai control shell.

### Black

- **Rank Rat** — two-mana 1/1, each opponent discards. Named only as the classic partner for
  Ferocity of the Hunt: trade it with their 4/4, it comes back, they discard again.

### Red

- **Awaken the Inferno** — five-mana sorcery: 6 damage to a creature or planeswalker + a +1/+1
  counter, basic landcycling {2}. Compared to Wilds of Eldraine's Cut In (a top common) plus a mana:
  *"a lot worse but… a reasonable card to put in your deck."* It is one of the two best landcyclers
  (with white's).
- **Command the Stage** — three-mana sorcery: a 2/2 Cadet, +1/+1 counter on your other Wizard tokens.
  It returns from the graveyard to your hand at upkeep if an opponent took noncombat damage last
  turn. *"Kind of clunky"* on the front, but free recursion in a BR/UR graveyard-spells deck with
  self-mill. Pairs with Twinned Vision's discard.
- **Way of the Pyromancer** — two mana, empower Jace 2, your walkers gain +1: add {R}. It read weak,
  then like a mana rock. But using it for mana every turn means you are not drawing off your Jace.
  *"These are really hard to evaluate."*
- **Heartstring Puller** (?) — *"a four mana red common that is a 3/1 trample that comes with the
  2/2 Cadet"*. Identified from the description. It is his favourite Ferocity of the Hunt target:
  trample + deathtouch pushes 3 through, it returns, and you get another Cadet.

### Green

- **Bestial Incursion** — four-mana 4/4 trample token, flashback {5}{G}. It is Midnight Hunt's
  Shadowbeast Sighting (one of that format's best green commons) with two upgrades. **"Does look
  like a top common… definitely not the best common… between C+ and B−."** It is fine in RG
  beatdown and *"very strong if you can mill it"* in UG/BG/Sultai self-mill.
- **Arcane Amphisbaena** — two-mana 1/1 deathtouch, empower Jace 2. *"So on the borderline of clearly
  good and clearly bad."* It protects your Jace more efficiently than anything (*"it just always
  trades"*) but does not pressure theirs. **"A litmus test for how much empower Jace really
  matters."**
- **Way of the Paradox** — three mana, empower Jace 5, gain 1 and an extra land drop per loyalty
  activation. Clunky and doesn't affect the board, but it cantrips via Jace. Same verdict as Mind
  Sculptor: expect poor data. He suspects there is *"something here in a control shell that wants to
  get to like 10 mana."* Possibly worth splashing in UB.
- **Something Worth Saving** — {1}{G} instant: mill four, take a permanent, gain 1 (the Cache Grab /
  Malevolent Rummage template). Identified from the description. It is the Sultai self-mill enabler
  that puts Bestial Incursion in the graveyard.
- **Heartwood Crafter** — green one-drop 1/1 that taps for colourless (not for spells from your
  hand), with the Soul Tether Heartwood prepared spell. Named only by description. It is the
  mono-green-only piece of the Heartwood red-splash engine.

### Hybrid

- **Ferocity of the Hunt** — {1}{B/G} flash aura: +1/+0 and deathtouch, returns the creature when
  it dies. **"The common that I'm most excited to play with"** and the front-runner for episode 81.
  He thinks it beats Fake Your Own Death (C to C+ in its sets) because deathtouch is better than the
  second point of power: you usually cast it to win a combat. Synergies at common: trample
  (Heartstring Puller), Rank Rat, and re-buying Craftwork Crusher's ETB in RG. Range: **"C, C+, maybe
  B−"**. *"Not going to be a top common"*, but he expects to draft a lot of them.
- **Tam's Resistance** — {1}{G/U} sorcery: +1/+1 counter, vigilance, empower Jace 4. **"I think this
  is a sleeper common."** It rounds to counter + vigilance + draw, and the vigilance matters for
  attacking their Jace while defending yours. Range: **"C to B−"**, *"going to be a player."*
- **Fatehold Chronologist** — {1}{W/U} 1/2 flyer that enters prepared. Peer Review makes a 2/2
  Cadet + surveil 1. It curves into itself (two-drop, then a three-mana Grey Ogre). His question:
  is efficiency enough in a format where empower Jace always gives you something to spend mana
  on? The comparable SOS curve-into-itself four-drop was *"nothing special"*. But this is a
  two-drop, and two-drops that smooth the opening (Avatar's Messenger Hawk) overperformed.
  Listed as a question, not a verdict. Worry: *"a little bit too small ball."*
- **Konstrari Improviser** — {1}{R/G} 2/2, enters prepared, Soul Tether makes a Heartwood. Same
  smooth-the-curve argument as Chronologist. It is one of the three Heartwood enablers that let
  green splash red.
- **Woodwork Prodigy** — the three-mana hybrid 3/3 that re-prepares each upkeep (Heartwood maker).
  Described, not named. It is the second Heartwood enabler.
- **Twinned Vision** — {1}{U/R} instant: draw one, or two if cast from the graveyard; flashback with
  a discard. *"Looks like a really really strong spell"*, a Think Twice variant playable across
  every U or R deck. It pairs with Command the Stage.
- **Paradox Shaper** — {1}{U/B} 1/3 that re-prepares each upkeep. Omit Variables mills 3, and {2}
  puts a graveyard card on the bottom. *"Does not look bad"*, and the 1/3 body survives combat. It is
  the centre of a possible loop-your-library UB/Sultai deck.

### Multicolor and gold

- **Craftwork Crusher** — {3}{R}{R}{G}{G} 7/5 trample, ETB choose two of: 4 damage to a creature or
  walker, a 2/2 Cadet, draw. *"Looks completely obscene… looks like the best uncommon."* He calls it
  a *"downshifted Titan of Industry"*. You must build to cast a double-pipped seven-drop, and that is
  the reason green decks stretch into red.
- **Stingerquill Charm** — {B}{R}: 3 damage to any target / first strike + deathtouch / hasty 2/2
  Cadet. **B-range.** One of the reasons BR is fine despite its finicky theme.
- **Grim Repriser** — {B}{R} 2/2 prowess that returns with a finality counter for {B}{R} if an
  opponent took noncombat damage this turn. **B-range.**
- **Konstrari Charm** — {R}{G}: 6 to a flyer / two counters + trample / add {C}{C}{C}. *"I think
  this is the weakest charm"*, but not bad: *"basically just a very good combat trick in red green."*
- **Kiora of Salt and Sand** (?) — *"a number of rewards for getting a Jace to a high loyalty with
  the uh Ciora card, which I think looks pretty strong."* Ambiguous: the caption says "Ciora", and
  Kiora of Salt and Sand (UG, walker −8) is the most likely match. Avatar of Burgeoning Echoes (UG,
  walker −10) also fits the description.

### Colorless, artifacts and lands

- **Fatehold Annex** — the example from the common dual cycle: enters tapped unless you control a
  planeswalker. The cycle replaces a basic in ~56% of packs.
- **Deserted Beach** — example of the Midnight Hunt rare dual reprints. About two and a half of the
  cycle per draft table.
- **Room of Refuge** — common choose-a-colour tapland (Shimmerdrift Vale-style). {5}, sacrifice:
  two +1/+1 counters at sorcery speed.
- **Murmuring Volume** — three-mana any-colour manalith with a {2} rummage. *"Not going to be like a
  format-defining manalith in the slightest"*, below Potion Trove / Dragonstorm Globe, but it does
  its job when you want it.

## Open questions he set himself

These are the episode's actual output. Check each one against episode 81+.

**Ep 82 answered #5:** yes, the loop deck exists, but Paradox Shaper is mainly insurance against
decking. The better U/B is graveyard value inside Sultai (often full three colours). Grixis spells is a
B/R-control fallback, not the main build.

1. How much empower Jace do you want before one-activation-per-turn makes extra copies dead?
2. When should you attack the opponent's Jace, and when should you go face? When should you let
   your own Jace die?
3. Do cheap curve-into-themselves prepared two-drops (Fatehold Chronologist, Konstrari Improviser)
   matter, or does the slow Jace value make efficiency irrelevant?
4. Are the Way enchantments (especially Mind Sculptor and Paradox) real in slow control decks,
   whatever their aggregate data says?
5. Is there a mill-your-library Paradox Shaper loop deck, and is Grixis spells or Sultai graveyard
   the better UB build?

## Cube segment (not Limited advice)

The last ~8 minutes are cube picks, recorded after the outro. They are listed here so they are not
lost, and **deliberately kept out of `## Card notes`** so they don't show up as Limited notes on
the card reference. Geist of Saint Thalia (his favourite FRA cube card; a cleaner Baral), Guiding
Hydra (a modern Metallic Mimic-style counters card and a Breya/Glass Gear Hulk target), Sphinx of
False Conclusions (*"kind of a sleeper"* blue value blocker), Stingerquill Voxmancer (low-power cube
glue), Theorix Charm (quench / −2/−2 / mill-3-draw for graveyard cubes), Lich's Relic (Stoneforge
target that doubles as removal).

## Caption garble

These auto-captions transcribe speech, so card and personal names are mangled. The corrections
used above are listed here so the readings can be audited.

- **"Constra / Constari"** → **Konstrari** (Konstrari Charm, Konstrari Improviser).
- **"Twin Vision"** → **Twinned Vision**; **"pure review"** → **Peer Review** (Fatehold
  Chronologist's prepared spell).
- **"Medics Kite Sale"** → **Medic's Kitesail**; **"Unflinching Honormancer"** → **Unflinching
  Hortimancer**; **"Beastial Incursion"** → **Bestial Incursion**.
- **"Gist of St. Talia"** → **Geist of Saint Thalia**; **"Mcus / Mais"** → Mikaeus, the Lunarch; **"Bright Glass Gear Hulk"** → Brightglass Gearhulk; **"stinger quill"** → **Stingerquill**.
- **"Ciora"** → Kiora (?), card not certain. See Kiora of Salt and Sand above.
- **"cash grab malevolent rumble style"** → the Cache Grab / Malevolent Rummage template
  (Something Worth Saving).
- Set names: **"Hex Haven"** → Hexhaven; **"Stricks Haven"** → Strixhaven; **"Lurin Eclipse"** →
  Lorwyn Eclipsed; **"Dusour / Duskorn"** → Duskmourn; **"Murders at Carlo Manor"** → Murders at
  Karlov Manor; **"Undercover Scroll"** → Undercover Skrull (MSH).
- Host handles: **"Blue Sky Pratt"**, **"SAMP6"**, **"sampp_mtg"**, all Sam Pardee. **"Mark
  Anderson"** (?): the Limited Level-Ups co-host Mark, surname unverified.

**Ep 82 (whisper transcript) garble:** **"soul tie / Soltai"** → **Sultai**; **"fibble fip"** →
**Fblthp**; **"Therix meta mage"** → **Theorix Metamage**; **"Cryo Theory Adept"** → **Cryotheory
Adept**; **"Marwin"** → **Marwyn, the Preserver**; **"craftworks/craftwood crusher"** → **Craftwork
Crusher**; **"kindred vision"** → **Kindred Judgment** (?) (described as "the crazy board wipe");
**"Sam Pratt"** → Samp (host); **"Sam Black"** in ep 82 is the real Sam Black ("the person to go to"
for Paradox Shaper mill-out decks), not the host.

## Source episodes

- Episode 80 — 2026-09-24 — Reality Fracture Hot Topics (`6nlNgC1BEE4`) — *preview, recorded before
  prerelease, zero games played*
- Episode 82 — 2026-10-08 — Theorix Metamage (`ST6ahmQdFkU`) — *played (~1 week of Arena); graveyard
  theory + colour hierarchy; whisper.cpp transcript of the Libsyn audio*
- Episode 81 — 2026-10-01 — Campus Crier (`uKBtX0S0Ea4`) — *not distilled yet*
