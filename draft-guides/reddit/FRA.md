# FRA — Reddit notes

## Post-release (Arena, 2026-09-29 → 10-04)

> Source: **r/lrcast** (primary) + **r/MagicArena** + **r/magicTCG**, 67 threads, 2,539 comments
> (top 30 per thread by score read, 1,453 in all), pulled 2026-10-04 via the arctic_shift archive
> API (`/api/posts/search?subreddit=…&after=2026-09-29`, then `/api/comments/search?link_id=…`, no
> auth, 7 s spacing). r/spikes was checked and had only Constructed threads. Raw NDJSON is in
> `data/cache/reddit_FRA_post/`. Threads posted on 10-03/04 are mostly comment-less because the
> archive had not ingested their replies yet.
>
> **Evidence class: post-play Arena anecdote.** This ranks above the prerelease notes below
> (Arena Draft, not paper Sealed, and many more players), but it is still anecdote. Trophy posts are
> survivorship-biased (nobody posts their 2-3 Rakdos deck), most takes are one player's run, and
> week-one opponents were soft. **Any 17Lands number overrides it.** GIH WR quoted below is 17Lands
> PremierDraft as of 2026-10-04 (set median ≈ 56.0%, common median 55.5%). Per-pair IWD is from
> `card-reference/briefs/FRA.md`.

### Format read / speed

- **Slow, and most players like it.** "Slowest set since DMU" (1wvtien, 187) matched the 17Lands
  turn-count chart. Several players
  decked naturally with no draw synergy: "first set that I've legitimately died to decking from just
  naturally drawing cards" (1ww7djx, RG with no card advantage).
- **Card advantage beats curve.** The top advice thread (1wvcsak, 129): "Use your removal on the
  right threats… Don't panic." Also: "Two words: Card. Advantage." (1wvyfpq) and "having things to
  do in the late game is more vital than a low curve" (1wwuvxs). Top comment in the format thread:
  "Cards with expensive activated abilities on them are the nuts. They resolve the wildest and
  longest standing boardstalls" (1wtvmtd, 59).
- **Straight aggro is weak; the aggro that works has fliers or burn.** Day-1 read (1wuh3uv): small
  ground creatures get "relentlessly 2 for 1'd" by **Mindseeker Oculus** and **Bestial Incursion**.
  "2/1 first strike just isn't very good in this value set" because of all the 2/3s and 1/3s
  (1wx8w5c). Counter-reports: a Boros fliers trophy, a mono-W **Codie, Ravenous Codex** trophy and BR
  low-curve 7-0s (1wx8w5c, 1wus5gp, 1wx80cl).
- **Prince or pauper: split.** Most say "pretty prince-y… saved by how plentiful the removal is"
  (1wwce6k) vs "my value piles are winning well above 50%" (1wvyfpq, 70).
- **Removal count.** Players want 5–7 removal spells (1wvyfpq). A 4-removal RG deck's 0-3 was blamed
  on exactly that (1ww2yig, 28). "Taking removal higher than pretty much anything besides a B+/A-"
  (1wvd5rj, 24).
- **Lands.** 17 is the usual default even with landcyclers, since surveil and mana sinks absorb flood
  (1wwuvxs). Dissent: "Flood is a killer this format so non-blue decks can have it rough" (1wvu5ng,
  44).

### Per-pair takes

- **W/U** — Cheap fliers and surveil. **Surveillance Phantasm** (58.7%, 3rd-best common): "a top
  common", "oppressive if you're playing an aggressive deck", best in multiples (1wu4ahf). One 7-2
  deck started with six. Trophy shape: fliers plus the creatures that prepare a 2/2 Cadet, "for proccing
  Surveil each turn" (1wvtien). **Prophesied End** is "C+/B- in the right deck" (1wvu1gi). Stall
  plan: **Tetsuko Umezawa, Fugitive** + **Ghalta the Immovable** + **Traxos, Academy Guardian**
  (1wuf6lf, 1wusrga).
- **U/B** — Seen as the best deck. "Every time I've played against blue black it's been strong"
  (1wtvmtd). It is not turbo-mill: "you shouldn't really self mill yourself. It's a tempo/value deck
  with an insane uncommon signpost" (1wvcmbe). That signpost is **Recursive Recruitment** (62.1%);
  one Dimir deck ran four of them plus 8 removal (1wvd5rj). The **Fblthp, Impossibly Lost** alt-win
  is real (1wx067s 6-3 self-mill; 1ww7djx 43–44-card UB decks), and players want 1–2 **Paradox
  Shaper** as the brake. One player's log: four blue decks went 7-2/7-1/6-3/6-3, three non-blue
  decks went 2-3/3-3 (1wvcsak).
- **B/R** — The most polarised pair. Trophies: "Insane 7-0 BR low curve" (1wx80cl), a Rakdos aggro
  Arena Direct trophy (1ww7djx), BR splashing blue for **Saheeli, Jewel of Avishkar** 7-0 (1wwd504),
  ~10-removal Rakdos/Mardu piles 7-0 (1wvd5rj, 1ww96te). Failures: "drafted it twice,
  went 2-3 both times… without [enablers for **Command the Stage**] it felt bad" (1wvtien). Build:
  low curve plus removal, Vicious Verse pings as reach. Swapping creatures for **Cast Away Doubt**
  made one BR deck "feel so much better" (1wvu5ng).
- **R/G** — "Make mana, cast Kiora." **Kiora of Fire and Ashes** and **Craftwork Crusher** are the
  "mythic uncommons". "RG heartwood kind of devoid of payoffs outside of rares" (1wv858p). Split on
  ramp: "RG stompy… In the late game I always ended up just going over the top" 7-1 (1wvc1hv) vs
  "RG ramp is a trap… Making a Heartwood token for 3 mana is terrible. The best RG decks are midrange
  beatdown with 1-2 top end cards" (1ww2yig). The 0-3 diagnosis was 8 accelerants, 4 removal and no
  card flow, so cut **Greenhouse Propagator** and **Something Worth Saving**.
- **G/W** — Lifegain is real but thin. "I keep losing to Green White counters + lifegain" (1wvcsak)
  vs "an insane life gain deck… 0-3 without gaining a single life" (1wtvmtd) and "Vigorbloom does feel
  like it lacks lifegain" (1wvcmbe). The curve people fear: T1 **Emergency Phytomedic**, T2
  two-drop, T3 **Unflinching Hortimancer** + Seed Suture (1wx8w5c). Mono-W variant: six Phytomedics
  plus **Codie, Ravenous Codex** copying every Seed Suture (1wus5gp).
- **W/B** — The worst pair on day 1, "5% less winrate then the average 2 color deck" (1wuh3uv). It
  wins as black removal plus white bodies: "BW midrange deck that went 7-1 without any meaningful
  bombs" (1wvcsak), BW(U) aggro 7-0 (1wvtien). It loses as a value pile: "my BW value pile didn't
  have a late game" (1wtnuj9, 3-3). **Tinybones, Pocket Nuisance** got a "Let's go, little guy!"
  off the early pick-rate chart (1wuj6a9) and a "bad" from another poster (1ww96te); the brief has it
  at +6.4 in W/B.
- **U/R** — "Not Every FRA Deck has to be designed for a Slog Fest. 7-1 with UR Prowess" (1wu4k8b):
  **Stingerquill Voxmancer**, **Variable Chaser**, **Geist of Saint Thalia** ("crazy fast starts"),
  red **Tetsuko Umezawa, Pursuer**. **Twinned Vision** is the glue. **Way of the Warlord** turns Jace
  into removal for 2-toughness creatures and Cadets (1wuj6a9).
- **B/G** — Graveyard grind. Rarely praised in posts, often the deck people lost to. **Primal
  Witchstalker** is named an A-tier uncommon beside red Kiora and Crusher (1wvc1hv). "Sultai comes
  together quite easily" (1wvcmbe). Best black common creature: **Apex Witchstalker**, then
  **Theorix Metamage** (1wuh3uv).
- **R/W** — "I haven't seen a single boros deck, and I don't think there's much reason to go into RW"
  (1wvu5ng). **Mabel, Valley Hero** was "a disappointment" even as a double (1wv9pd5). The Boros
  decks that won were fliers plus removal, not counters (1wx8w5c).
- **G/U** — Barely discussed, which fits it being the least-drafted pair. **Mind Meanderer** is "a
  'bomb' in this format" (1wtvui5) and one of three "mythic uncommons" (1wvyfpq). **Arcane
  Amphisbaena** wheels (1wtvmtd). **Kiora of Salt and Sand** is "very meh" (1wtvmtd). One Simic Jace
  trophy was posted (1wwxow2, no replies).

### Synergy & interaction tips

- **Kill your Jace to activate twice.** A token minused to 0 and then re-empowered is a new object
  and can activate again that turn. With a 3-loyalty token, −3 it first, *then* cast the empower
  card (1wvekrv, 81; 1ww7djx; 1wtvmtd). This doesn't work with **Sanctum Lurker** out.
- **A Jace on 1 is often better than a Jace on 2.** Don't surveil just because you can, and three
  turns of filtering often beat one draw (1ww7djx, 1wvc1hv).
- **Ways:** "they don't syngergize cause you still only get 1 jace activation" (1wvjy6w). Take the
  generically strong ones and play empower cards. **Way of the Pyromancer**: "only good turn 2, only
  good on the play" (1wvjy6w, 23).
- **Ajani + Jace.** **Ajani Unrelenting** makes a Cadet on *every* loyalty activation, including
  the Jace token's, so "an otherwise-irrelevant Jace on 1 loyalty" doubles its output (1wu4awf).
  **Way of the Mind Sculptor** draws off Ajani's big minuses (1wv41iw).
- **Fblthp timing.** The win is checked while the trigger resolves with 0–2 cards left. You don't
  have to fail a draw, and the opponent can't let you deck (1ww1m1c). On Arena, hold priority so you
  can answer the trigger with **Theorix Charm**'s mill mode (1wwscqy). **Hall of Echoes** copying
  Fblthp two turns running drew one deck out (1wx067s).
- **Splash direction.** Heartwood makes splashing green into red easier than the reverse. Green's
  gold cards are pip-heavy (**Kwia Vigorbloom** GWW, **Mind Meanderer** GUU) (1wu4fv0).
- **Two-card combos actually played:** **Divining Duelist** + the Special Guest Splinter Twin (1wtjx23,
  1wuyqab; "laborious as hell" to click through on Arena); **Loot, the Anomaly** + **Yuriko, Hope from the
  Shadows**, which makes Loot's negative power bigger, plus **Tetsuko Umezawa, Fugitive** for
  unblockable (1wvkey9, 1wusrga); **Mabel, Bitter Recluse** removes **Grim Repriser**'s finality
  counter (1wusrga, 146); **Way of the Mentor** + **Way of the Paradox** let you −1 every turn at no
  net loyalty (not infinite, one activation a turn) (1wvkey9); **Way of the Warlord** + **Teyo,
  Diamondblade Mage** (1wvkey9); **Arni, Humble Scribe** + **Lyra, Tolarian Archangel** (1wusrga);
  **Saheeli, Jewel of Avishkar** + **Draconic Visitor** (1wwd504). **Unsummon** a **Frostbite Pyromental** after combat to dodge its sacrifice
  (1wu25ib).

### Over- and underrated, per the community

Better than reviewers said:
- **Twinned Vision** — "The format's a grindfest so the grind common is good. Simple as." (1wx2rqq,
  80). 58.5%, 4th-best common. Play 2–3; it plays well in multiples.
- **Unsummon** — "straight up a great card in this set" (1wu25ib, 126). 4/4 Beasts, 5/5 Dragons and
  Cadets are everywhere, so bounce is close to removal, and it saves your creature from **Overwrite
  the Multiverse**. 57.8%, 7th-best common.
- **Konstrari Charm** — Reddit was "baffled" by its day-2 number (1wuh3uv). The follow-up thread
  settled on "2 counters + trample at instant speed is absolutely great", and its flier mode
  "randomly embarrasses a lot of bombs" (1wv9pd5). 57.0%.
- **Bestial Incursion** — "cracked", "quickly becoming my top common" (1wwd504). 56.9%.
- **Fblthp, Impossibly Lost** — "a real win condition, ESPECIALLY blue-black" (1wvcsak). 60.4%.
- The uncommons called bombs: **Kiora of Fire and Ashes** (62.2%), **Craftwork Crusher** (62.6%),
  **Primal Witchstalker** (60.0%), **Mind Meanderer** (57.8%).

Worse than hoped:
- **Way of the Pyromancer** — "complete trash and early 17lands data confirms it" (1wuj6a9). 52.2%.
- **Mabel, Valley Hero** — 51.2%. "You have to play it early… but as a 2/3 it's too small", and the
  counter only goes on a creature that entered this turn (1wv9pd5).
- **Ajani Resolute** — 52.9%. "Basically shouldn't go in any deck unless you are really hard into
  the life gain theme" (1wwd504).
- **Kwia Vigorbloom** — LR's A+ "seems like an insane overrate… So much removal hits it at common"
  (1wtvtg5) vs "the 13th highest win rate in the entire set" (1wvu5ng). Data: 62.9%.
- **Colour hosers in Bo1** — **Refute Destiny** (51.3%) and **Terminal Criticism** (51.1%): "in most
  games you're looking at killing a 1 loyalty Jace token and I don't think that's close to worth a
  card" (1wvu1gi). **Precise Redaction** gets anecdotes ("Three precise redactions is genuinely
  bananas", 1wvcsak) but too few games for a number.

Bombs:
- **Ajani Unrelenting** — 74.0%: "the highest-winrate card I can find in the last five years of
  17Lands data" (1wv41iw, 154). "Ajani'd" is now a verb (1wwdcp5). What beats it: 5+ toughness (a
  7/6 **Unflinching Hortimancer** survived the wipe and **Archive Arbiter** finished Ajani, 1wu4awf),
  counters, discard, or **Mabel, Bitter Recluse** after a minus (1wv7bjh). One Arena Direct player
  is "skipping bombs with less than 5 toughness" (1wwd504).
- **Uldaros Theorix** (69.7%): "very close to oops I win"; "The Dimir Sphinx carried me to 7-2 and I
  won every time I cast it" (1wvtien). **Sphinx of False Conclusions** (65.5%), "the 4/2 flier
  rebound bird", is the next card people say needs a plan (1wvyfpq).

### Sideboard and gameplay tips

- **Attacking Jace:** "who is the aggro?" (1wwbx1n, 37). Attack the token when no damage is wasted
  (3 power into 3 loyalty), and don't swing 3 power into a 1-loyalty token when you're ahead. Kill
  it at once if they have a Way out, **Way of the Pyromancer** especially. Players also report
  winning boards "because they prioritized my jace over me" (1wvcsak), and "sometimes the
  planeswalker is the distraction" (1wwuvxs).
- **Bo3:** the colour hosers are the sideboard plan (1wwuvxs). **Prophesied End** isn't a hoser and
  stays in the main deck.
- **Sweepers to play around:** **Kindred Judgment** ("Duneblast or better", 1wtvtg5), **The Echoverse
  Fulcrum**, **Overwrite the Multiverse**, and **Rise of the Deathbringer**, which is instant-speed
  (1wwuvxs).
- **Arena Direct (Sealed):** start from the fixing; two colours plus a double splash, or straight
  three, is fine (1wvoyg4). Echoed pairs: if an opponent shows one Garruk, it's roughly a coin flip
  they have the other (1wwqnlt). Don't run 41 cards when you have a bomb (1wx6c06).
- **Kill Kiora of Fire and Ashes before 8 mana** (1wtk6zj, 86).

### Where Reddit agrees and disagrees with the 17Lands data

**Agrees**
1. **Slow, card-advantage format**, so grind commons beat their grades. Brief: 9.68 turns, 52.1% on
   the play; **Twinned Vision** 58.5%.
2. **W/U and U/B are the best decks, and blue is where to be** (57.1% / 56.8%). Reddit's "U/B is
   tempo-value, not mill" matches the brief's **Theorix Metamage** at only +1.3 in U/B.
3. **R/G is "cast Kiora or Crusher", not Heartwood synergy.** The 0-3 RG thread's cut list also
   matches the per-pair data: **Greenhouse Propagator** (−1.3) and **Something Worth Saving** (−2.8)
   both under-perform in R/G relative to set-wide. These are small effects.
4. **Ways:** run two or three; **Way of the Pyromancer** is bad (52.2%); **Way of the Warlord** is
   best in U/R (+5.6 in-pair per the brief).
5. **R/W is bottom** (53.7%), and **Mabel, Valley Hero** is one of the set's weakest gold cards
   (51.2%).
6. **Colour hosers aren't Bo1 main-deck cards** (51.3%, 51.1%). **G/W payoffs are thin.**
   Fblthp is good in evasive blue decks (+7.7 W/U, +8.1 U/B).

**Disagrees** (trust the number)
1. **B/R.** Reddit's trophy feed is full of BR 7-0s, but 17Lands has B/R tied bottom (53.6%), with
   black playing 2.5pp worse there than set-wide. That's survivorship bias. The "Rakdos removal pile"
   works better as U/B or Grixis.
2. **Three colours.** Reddit says the set "was designed more for 3 color decks", "my best sets have
   included a splash", "four color removal / card draw slop" trophies (1wvcmbe, 1wvcsak). 17Lands
   folds splashes into the base pair, and true three-colour decks win 53.6% vs 55.4% for two-colour.
   Every three-colour combination with white is ≤52.5% (Mardu 47.2%, Naya 51.8%, Bant 51.9%, Jeskai
   52.2%). Jund (55.4%), Grixis (55.1%) and Sultai (54.8%) hold up. A splash is fine; a full third
   colour costs you. The non-blue common duals are negative in their home pairs (brief).
3. **White.** "Avoiding white unless it's wide open" (1wvyfpq), "White is bad" (1wx947t). But W/U is
   the joint-best pair and white is the half carrying it (brief). White is bad *outside* W/U: W/B and
   R/W are bottom four, and every white three-colour deck is bad.
4. **Surgical Precision** — "absolutely ass" (1wtvmtd) vs 57.3% GIH, 12th-best common, IWD +2.6. A
   third of creatures have 4+ toughness (brief), and one poster counted 17 of 21 four-mana creature
   cards with 4+ toughness or extra bodies (1wu96pg). Take it.
5. **Self-preparing uncommons.** Reddit (and the brief's Prepared section) call **Stingerquill
   Voxmancer**, **Paradox Shaper** and **Woodwork Prodigy** engines. Their GIH is 54.0 / 55.7 / 52.8,
   at or below the set median (55.7%). **Command the Stage** ("incredibly good", 1wtuq7o; "consistent value" at
   the prerelease) is 49.6%, near the bottom of the set.
6. **Landcyclers.** Reddit ranks the white and red ones good and blue and black bad (1wvcmbe). All
   five sit at 56.0–57.4%, and blue **Undulating Witness** (56.3%) is level with or above **Apex
   Witchstalker** (56.0%).
7. **Last Gasp** "underperforming" (one poster, 1wu96pg) vs 57.3% overall. It is pair-dependent:
   +5.7 in U/B, +0.9 in B/R (brief).
8. **Mabel, Bitter Recluse** — "1/1 deathtouch is literally always good" (1wusrga) vs 54.6%, below
   median. **Way of the Cryomancer**, listed among the good Ways (1wvjy6w), is 53.2%. The data's best
   Ways are **Way of the Mind Sculptor** (58.5%) and **Way of the Healer** (57.1%).
9. **Day-1 reads aged badly.** Reddit's day-1 thread had U/R and R/W joint second-worst behind W/B
   (1wuh3uv). U/R has since climbed to 5th (55.4%).
10. **Attacking Jace** (not a 17Lands number): the brief says attack it; Reddit leans "who's the
    beatdown?" and often goes face.

## Prerelease (paper Sealed, 2026-09-25 → 27)

> Source: **r/lrcast** + **r/magicTCG**, 22 threads, ~840 comments, pulled 2026-09-27 via the
> arctic_shift archive API (`arctic-shift.photon-reddit.com/api/{posts,comments}/search`, no auth;
> rate-limits after ~2 fast calls, 7 s spacing works). Top ~30 comments per thread by score.
>
> **Evidence class: prerelease anecdote.** Almost everything below is from paper Sealed on
> 2026-09-25/26/27 plus a little Early Access. Sealed is bombier and slower than Draft, samples are
> single players, and 3-0 posts are survivorship-biased. Ranks below the expert guides; any
> 17Lands number overrides it. Its one edge is that it is the only **post-play** source that
> exists before the Arena release (2026-10-02).

### Format read (prerelease consensus)

- **Slow and grindy.** The most repeated claim across every thread. Many matches went to time;
  "removal and evasion at a premium"; "whoever wins is the last player with cards in hand".
  Several posters: "much slower than Hobbit".
- **Sealed is bomb-swingy.** Echoed-pair seeding puts two rares/mythics (sometimes both Garruks)
  in one pack. "Every other opponent had 2–3 planeswalkers." Counter-reports exist: several
  0–1-rare decks went 3-0 or 4-0 (bomb-free Simic 4-0, Grixis removal pile 6-0, Boros aggro 3-0).
- **A go-under aggro deck is real.** Multiple 3-0s with cheap red prowess / Boros / Stingerquill
  burn; one BR deck took an opponent 19→0 in a turn with Vicious Verse + the Tomik uncommon.
  The recipe: cheap flyers + prowess + tricks, win before sphinxes and walkers land.
- **Removal-heavy control also 3-0s.** "Remove everything, chump, board wipe, win with walkers."
  The black board wipe was called "a cheat code".
- **Colours:** red most often named strongest; blue "has the best commons"; one poster found
  black's average creature "below cost" and switched to red. Pre-play guesses were all over the
  place and none held consensus.

### Attacking Jace tokens

Consensus from a 34-comment thread + prerelease reports:

- **Default: no.** Attack face unless you have a reason. Aggro decks ignore tokens.
- **Yes when:** the token is at **3+ loyalty** (denies a draw), the opponent has a **Way** enchantment
  giving it a real ability, they have surveil payoffs, or you are the control deck in a grindfest.
- Players with a 3+ Jace usually cash it for the draw immediately, so "deny the draw" rarely comes
  up in practice.
- Split experience on value: some say opponents *undervalue* a sticking Jace; others say opponents
  spending resources on tokens handed them the game. Depends on Jace density in your deck.

### Card notes

- **Craterclaw Colossus** — "a game ender" when it lands; also "sat 3 turns waiting for land #N".
  Several say it needs artifacts/Heartwood tokens and is awful without them.
- **Curse-Marred Demon** — Split. "4 mana 4/4 trample that can tutor" called the best card in a
  3-0 Boros deck; others: "not a bomb", "eats removal immediately", the tutor gambled away cards.
- **Way enchantments** — Prerelease MVPs repeatedly: **Way of the Deathbringer** ("directly
  responsible for 5 of my 6 wins"), **Way of the Warlord** (won 2 games), **Way of the Wildspeaker**,
  **Way of the Cryomancer** (forking Hexhaven Battalion won a game), **Way of the Pyromancer**
  (turn-4 plays on turn 3; "reads as a 2-mana planeswalker"). Community rank: green Garruk Way and
  white Liliana Way best; Ajani Ways and black Liliana Way "borderline unplayable". Warning: one
  Jace activation per turn, so Ways have diminishing returns — 2, max 3, per deck. Expect low GIH WR
  from misuse.
- **The Theorist, Jace Beleren** — "absolutely crushing" when it lands; one opponent drew two copies
  every game and won on card advantage.
- **Garruk pair (both)** — at the top tables all weekend; called "just stupid" in Sealed. In Draft
  the pair is split, and taking one signals the other colour to the next seat.
- **Screeching Soulbreaker** (2B 1/4 flier, drain 1) — "did way better than expected at chipping
  through", recurs Command the Stage.
- **Command the Stage** — "consistent value" in two separate 3-0 decks.
- **Skilled Battlecarver** — "insane over-performer", very hard to block; won more games than the
  demon in one deck.
- **Medic's Kitesail** — "an all-star", constant chip damage.
- **Tam's Resistance** — good 2-drop for a slow format: cantrip + leaves a Jace.
- **Face Yourself** — widest reviewer disagreement in the set (F− to A). Prerelease: "won at least
  one game by itself" in a removal-heavy Grixis deck; others call it a hard-to-cast Divination.
  Best in board stalls, dead against 5+ toughness.
- **Solve for Disappointment** — "felt way better in Early Access than I thought".
- **Clash of Elements** — praised in a red 3-1 report (comment truncated).
- **Living Library** — mixed; "early blocker, late 'move out of my way'" won two matches for one
  player; most thought it a weak 2-mana wall.
- **Lich's Relic** — "feels awesome", two independent reports.
- **The black 3/2 that keeps walkers at 0 loyalty + gives Jace a +** — "broke multiple people's
  brains", "way stronger than you'd think".
- **Fblthp, Impossibly Lost** — "legit win condition", especially in multiples.
- **Kiora** (7 power on turn 5 via Way ramp) and **Ghalta** — won "so many games" in bomb-free Simic.
- **Titanbones** — one Early Access player: "20–30 power so easily"; a prerelease opponent: "never
  did anything impactful". Unresolved.
- **Loot, the Anomaly** — LR gave D. A contrarian C+ post got flattened (99-upvote reply: "a vanilla
  2/4 for 3 is close to an F"). Reddit agrees with LR.
- **Germinate Recruits** — overpicked on Draftsim's simulator because Draftsim's own helper rates it
  3.4; Reddit: "not worth talking about".
- **Rescue Girl** (white 1/3 bouncer, nickname) — "plays much better than it reads" with good ETBs;
  combo outlet; also fixes a missed land drop by bouncing an untapped land.
- **Diviner Duelist** — common half of a literal Splinter Twin combo (Twin is on the Special Guests
  sheet). Pulled off at least once at a prerelease.

### Combos seen in real games

- **Loot the Nexus (G) + Hapatra the Desert Frost (U)** — infinite mana/untaps (Loot must tap for 4).
  Executed at two separate prereleases, pumping **Wrecking Gecko** for lethal. Both uncommons.
- **Ghalta + Tetsuko Umezawa** — also works with the blue 1/5; Tetsuko alone turns on several
  big-butt blue/white creatures.
- **Saheeli, Jewel of Avishkar + Draconic Visitor**; **Tenured Tethermage → Draconic Visitor** for
  three 5/5 dragons.
- **Red fireball enchantment + Rescue Girl** — "expect your board to be decimated".

### Meta notes on sources

- Reddit trusts **LLU** most ("generally close to where sets end up") and **Draftsim** least. Matches
  the repo's decision to hide Draftsim/AZ grades for FRA.
- LLU's D+ on **Vraska's Final Mercy** is a typo: the video says C+ and their site was amended.
- Aggregator post (11 review sources, 0–100 index): consensus is tight on the top 44 cards; 67 of 280
  cards have IQR ≥ 20. Highest disagreement: Face Yourself, Frostbite Pyromental, Hexhaven Invigorator.
