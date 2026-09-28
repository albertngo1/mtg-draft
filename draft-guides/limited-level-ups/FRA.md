# FRA — Limited Level-Ups draft notes

> Source: **Limited Level-Ups**. The host is **Alex**; co-host **Mark** joins on the set review. **8 Reality Fracture videos** so far (2026-09-18 → 2026-09-25), built 2026-09-27 from YouTube auto-captions. Card names are heavily mangled in the captions; every name below was matched against the FRA card list, and uncertain readings are marked `(?)`.
>
> The set review is split across six videos: Multicolor + Colorless, then one per colour. Commons and uncommons get an **A+→F letter grade** from both hosts, shown as `Alex X / Mark Y` where they split. Those grades are this channel's distinctive product.
>
> ⚠ **Gaps:**
> - **Blue (5/6, `ke_XTZAqxWI`) comes from a local whisper transcript, not YouTube captions.** YouTube refused this one video's captions from this machine (HTTP 429) for over a day, so the audio was transcribed locally with whisper.cpp (medium model) on 2026-09-23. That transcript has no speaker markers, so blue attributions lean harder on the I = Mark rule, and a few grades are marked `(?)`.
> - **Rares and mythics come from one separate video (09-25, `XPPMF-xrFjk`), recorded the day after early access.** YouTube captions worked for it (no whisper needed). Grades there already fold in a day of early-access play, and several were moved on air; moves are shown as `A → B`. Not graded: Gardenize and Omnipresence (skipped as constructed-only), and the 10 "special guest" reprints such as Austere Command (Mark said he'd add those to his tier list later).

## ⚠ Recency rule (read first)

- **Every grade here is a pre-play prediction.** FRA is not on Arena until 2026-10-02. Order of authority, weakest first: First Impressions (09-18, Alex solo, no grades) → per-colour set review (09-22) → rares + mythics review (09-25, after one day of early access). Later LLU videos (State of the Format, send-off) will supersede this file, and **17Lands GIH WR supersedes all of it** once there are samples (~2026-10-09).
- **The hosts distrust their own grades on this set.** Alex: "the conversation around the grades is absolutely more important than the grade itself." Mark: he won't trust most stats on this set because "there's so many ways you can use or misuse cards." They expect a large gap between top-player and all-player win rates, which makes 17Lands numbers noisier than usual.
- **Speaker attribution is best-effort.** It follows the rule verified on earlier LLU sets: in "I gave X / you gave Y", *I* is Mark and *you* is Alex. Splits where no such line was spoken are flagged. Auto-captions write "C plus" as "C++"; every case is read as C+.

### Source timeline

| Date | Episode | Phase | Weight |
|------|---------|-------|--------|
| 2026-09-18 | First Impressions For Draft + Sealed (LLU #261) (`I1PPajMb938`) | prerelease (blind read, no grades) | **Weakest** |
| 2026-09-22 | Set Review 1/6: MULTICOLOR + COLORLESS (`_LfIxIuRQI0`) | early (pre-play grades) | Weak-Medium |
| 2026-09-22 | Set Review 2/6: GREEN (`Gq7DmwSLcJk`) | early (pre-play grades) | Weak-Medium |
| 2026-09-22 | Set Review 3/6: RED (`rzZTGt7DQqw`) | early (pre-play grades) | Weak-Medium |
| 2026-09-22 | Set Review 4/6: BLACK (`svT3Ige5E3E`) | early (pre-play grades) | Weak-Medium |
| 2026-09-22 | Set Review 5/6: BLUE (`ke_XTZAqxWI`) — whisper transcript | early (pre-play grades) | Weak-Medium |
| 2026-09-22 | Set Review 6/6: WHITE (`BmIJbG1z69Q`) | early (pre-play grades) | Weak-Medium |
| 2026-09-25 | Rare + Mythic Limited Set Review (`XPPMF-xrFjk`) | early access (1 day of play) | Medium |

## Supersessions (grade/opinion flips between first-impressions and later reviews)

These are Alex's First Impressions calls (09-18) against the graded review four days later (09-22). There is no post-play data yet.

- **Mind Meanderer**: "I can confidently say is a banger" → **Alex B− / Mark C+**. Mark noted the fight isn't a "may", so a pump in response fizzles it.
- **Saheeli, Jewel of Avishkar**: "pretty good gold card" → **C, "a responsible C"**. The set has fewer spells than Strixhaven, where Murmuring Mystic finished around C+/B−.
- **Bloombrute**: expected "immediate impact a good amount of the time" → **Alex B− / Mark C**. Mark: you don't get the card every turn, and there are fewer Seed Suture cards than there look.
- **Kiora of Salt and Sand**: "really cool, unsure" → **Alex C / Mark C−**, and Alex said he'd been talked down a tier. Mark calls it an "upside trap": you sit on loyalty waiting for −8, which only happens when you're already winning.
- **Mabel, Valley Hero**: grouped with the "very strong gold cards" → **Alex B− / Mark C**. Alex conceded the counter only goes on creatures that entered this turn: "more Good-Fortune Unicorn than not."
- **Held up:** Surgical Precision ("one of the best commons") → Alex B− / Mark C+. Twisted Fates ("really pushed") → B. Compel Brutality ("really, really good") → C+. Craftwork Crusher ("a sicko") → **A−, the top grade in the review**.

## Format speed / meta read

- **Shaped by uncommons and rares.** There are only 71 commons, a pack can hold up to 6 rares, and a typical deck is roughly 13 uncommons, 3 rares and 8 commons. Merely "fine" filler bodies often won't make the cut, and digging effects gain value.
- **Echoed pairs as a signal.** Each pack has 3 echo-pair cards: one full pair plus half of another. When a passed pack is missing part of a pair, you can narrow down which side your neighbour took. About 95% of the paired uncommons are legendary creatures, so there are roughly 3 legends per pack. That makes "if you control a legend" discounts (Wrath of the Bloodmane) reliable.
- **4 toughness is the magic number.** It blocks most 2- and 3-drops and dodges red's 3-damage spell and black's −3/−3. Three-toughness four-drops with no ETB are risky, and the hosts mark down 4-drops that have neither an ETB nor protection.
- **Removal is cheap, instant and good.** Last Gasp, red's 3-damage spells, an edict, and deathtouch everywhere. Games trend board-stally and grindy rather than fast; the hosts are skeptical of the aggressive decks, especially RB.
- **Unsummon is "a shadow hanging over"** every token maker and big creature (Bestial Incursion, the Wildspeaker Beast, Edgar, Ghalta).
- **Empower Jace.** Mark's rule of thumb: Empower 3 ≈ draw a card, 2 ≈ two-thirds of one, 1 ≈ a third. There's less of it than it first appears (RB may have only 0–2 cards). Play patterns (Mark):
  - Early on, −3 to draw beats surveilling. Late, once you don't need lands, surveil is as good.
  - You can only activate once per turn. Empowering a Jace that still has loyalty adds no second activation, but empowering after it died does.
  - Against an opponent's Jace, send your most awkward-to-block attacker at it and everything else at face. Pushing it to zero is "functional life gain", but don't alpha-strike 15 power into a small Jace.
  - You need early 2-power creatures to pressure an opposing Jace.
- **Getting to 7–8 mana is easier than usual,** because Jace finds lands. Green ramp has real 6–7-drop targets, but Alex warns the payoff has to repay the lost tempo.
- **Colour ranking: the hosts disagree, and nobody calls a colour bad.** Mark has black as "the worst color, but not by much" and white as "second worst". Alex called red the weakest, then conceded after four good red commons in a row ("red's good… good burn, good top end"). In the blue episode, one host calls blue "my vote for best color at common/uncommon, but … not by much", and the other agrees.
- **Complexity.** Designer Ben White said feedback called the set too complex. RG (and to a degree GW) was made easy to play to compensate. Alex calls it a "skill testing set for deck building", and says to expect timeouts.
- **Early-access update (09-25).** "The format is grindy": plan on how to spend mana on turn 6+. The lack of aggressive 2-drops held up in play.
  - Cards with mana-sink activated abilities overperformed, e.g. Shatterwing Pegasus's team pump.
  - Packs and decks hold many rares, and long games mean you see more of your deck. The hosts still say the true bombs are mostly mythics.
  - Rare and gold costs are pip-heavy, so take the dual lands earlier than usual. Splashing works: one host splashed in 4 of 5 drafts using the duals and landcyclers. Nobody expects the format to become five-colour soup.
  - Decking happens with this much self-mill; one host beat a Garruk, Veiled Butcher deck by milling it out.
  - One host went 5-for-5 to five wins in early access (RG ×1, UW ×2, BG ×2). He calls RG "my vote for best", which hasn't been true for a long time, and was also impressed by UW and BG. He faced no RB or UB decks.

## Archetypes (10 two-color pairs, ranked)

The hosts give **no ranking**. Alex's First Impressions guess is about 60% of decks from the allied schools and 40% from the enemy pairs. The **schools** are on-rails: each has a hybrid common and a hybrid uncommon that share one prepared spell, plus a charm and another gold uncommon. The **enemy pairs** are broader, "know what makes a good midrange deck" decks with two gold uncommons each. Mark's advice: draft good stuff first, then decide how far to push the synergies. Grouped by how the hosts talk about them:

**Hosts positive**
- **RG Konstrari — ramp.** "An actual tried and true dedicated ramp deck." Craftwork Crusher (**A−**) "comes down on six pretty often." It's easy to play by design. The Heartwood tokens from Soul Tether also fix a splash.
- **GW Vigorbloom — lifegain + counters.** "Real and pretty scary"; Seed Suture is the prepared spell closest to worth its mana on its own. Vigorbloom Charm is B−. Mark's caveat: all the Seed Suture cards are gold, so you can't do it every turn.
- **WU Fatehold — surveil/scry flyers.** Mark thinks it may be one of the strongest decks, "because its cards all push the same way." Desperate Futurescribe is B−/B.
- **WB — attrition.** "Two really good gold cards": Twisted Fates (B) and Edgar, Ancient Bloodlord (C+). The sacrifice theme is thin.
- **UR — spells.** Alex's one stated hope from First Impressions. Pick a lane: red-based spells aggro or blue-based control. Mixing both payoff types makes a deck that's "not going to be very functional."

**Hosts neutral**
- **UB Theorix — self-mill to threshold.** It can be built as good-stuff control, turbo self-mill, or threshold creatures. Instant-speed mill turns threshold on mid-combat. Recursive Recruitment is Alex B− / Mark C+.
- **BG — graveyard midrange.** The "deathtouch + trample" theme is doubtful. Hapatra (B/B+) and Primal Witchstalker (B−/C+) are strong, and the green cards mill 4.
- **UG — Empower Jace.** "More of like a blue green base multicolor deck" that splashes Way enchantments. Kiora is an upside trap.

**Hosts skeptical**
- **RW — counters aggro.** Mabel (B−/C) was talked down, and Warrior's Blades is only C+/C.
- **BR Stingerquill — pings.** "The school [Mark] doubts most": the rewards are temporary or small, and you pay mana every turn. It has no good red two-drops besides Skilled Battlecarver (Mark: "if we had two good red two drops, I'd like the red black deck a lot more"). If it works, it works as grindy midrange, not burn-out. Stingerquill Charm (B−/B) is "probably the best charm."

## Card tips

Grades are from the 09-22 colour review unless noted; rares and mythics come from the 09-25 rares review and sit in a **Rares + mythics** block at the end of each section (in Multicolor, at the end of each pair, tagged (R)/(M)); `Alex X / Mark Y` where they split. Cards are ordered best to worst within each section.

### White (W)

- **Way of the Healer** — A− / B+ (likely Alex A− / Mark B+; no explicit I/you line). "The best of the Ways." With it out, "every time you activate Jace, it should just be a minus two." The best white uncommon.
- **Teyo, Lightshield Expert** — B. Flash hexproof plus a counter, or loyalty onto a walker, which can push Jace to a draw. "A lot of play to this card."
- **Your Fate Ends Here** — Alex B− / Mark B. Hits almost everything that matters, including mythic planeswalkers.
- **Tomik, Orzhov Lawmage** — B−. A 2-mana 2/1 flyer; its one-attacker-per-walker clause is mostly upside. "All around a very solid card."
- **Surgical Precision** — Alex B− / Mark C+. Much better than Marvel's Murdock's Crusade because the fallback mode cycles. Alex: "one of the best commons."
- **Memory Trap** — Alex B− / Mark C+. The standard O-Ring. "Good removal spell."
- **Hexhaven Battalion** — Alex B− / Mark C+. Three Cadets plus Empower Jace 2, with basic landcycling. "One of the better land cyclers we've ever seen," but below Imperial Oath.
- **Campus Crier** — C+. Don't use its graveyard empower to save a Jace; let Jace die and empower at end of turn. "Good common."
- **Prophesied End** — Alex C+ / Mark C. Fine in UW flyers and for closing games, and walkers make even control opponents attack. Mark: "I kind of like your grade more than mine."
- **Danitha, Sword of Hope** — Alex C+ / Mark C. Draws off RW Blades, tricks and Seed Suture. A deathtouch counter trick both draws and wins the fight.
- **Unflinching Hortimancer** — Alex C+ / Mark C− (C+ graded only for GW; attribution inferred). A ward-1 Ajani's Pridemate; "a pillar of green-white."
- **Rescue Girl, First Responder** — Alex C+ / Mark C−. A value engine for slow white decks with ETBs and Ways. Both call the grade "a little fake": it'll often be misused.
- **Koth of the Homestead** — Alex C+ / Mark D+. Needs about 11 Plains. Alex: "I'm probably a little bit too high on it."
- **Thalia, the Survivor** — C. A 3/4 lifelink whose tax is "potentially better than ward 1."
- **Academic Ascent** — C−. Alex: "I might be a little low on this."
- **Graft Surgeon** — C−. "Super perfect C− card."
- **Shatterwing Pegasus** — Alex C− / Mark D+. They'd like it far more if the pump cost 4.
- **Generous Revival** — C−. Its home is WB grind. It's a card the grade scale "lets down."
- **Saheeli, Consul of Oversight** — C−. Good only if a Jace token is reliably out when you cast it (curve it off Way of the Healer); otherwise it's "an Air Elemental."
- **Fateshaper Aspirant** — Alex C− / Mark D. "The definition of filler."
- **Yuriko, Blade of the Mighty** — Alex D+ / Mark D. Small body, weak immediate impact.
- **Yoshimaru, Beloved Companion** — Alex D / Mark D+. Weak on curve.
- **Ghalta the Immovable** — Alex D+ / Mark D−. Far worse than the green Ghalta; can rot in hand.
- **Predictive Preparations** — Alex D+ / Mark D−. A worse Travel Preparations.
- **Way of the Mentor** — Alex D− / Mark D. Lifegain decks want to beat down, not "create Divinations."
- **Refute Destiny** — sideboard (no letter). "Sideboard. Move on."

**Rares + mythics** (09-25 review; (M) = mythic)

- **Guiding Hydra** — A−. White's best rare or mythic: "we finally got a set where there's not busted white cards all over the place." Cast for 4 it's a 5/4 that puts a counter on each other creature every combat.
- **Liliana the Faultless** — Alex B+ / Mark B−. Soul Sister plus Mother of Runes. Mark had to force his opponent to tap out or use their last card to get around it: "I could see you being right."
- **Repurposed Enforcer** — B. Both hosts faced it and it did nothing, but the threat of a big Empower pushed them into conservative lines. Opponents block it, so it walks into your tricks.
- **Kindred Judgment** — Alex B− / Mark C+. A 7-mana wrath. No tribe is heavy enough to matter, so you can usually save one creature, or name nothing and wipe everything. Mark moved it up because slow formats reward wraths.
- **Enlightened Confidant** (M) — Alex C+ / Mark B−. A lifelink Dark Confidant. Gaining 1 life turns on the surveil, and it hands you back any land it bins. "Pretty good, not a bomb."
- **Lyra, Archangel of Dawn** — B− → C+ (both). Graded below the blue Lyra. The only other angel is the common 2/4 vigilance prepared angel. A single-pip 3-mana 3/3 flyer is still a good floor.
- **Gideon's Memorial** — C−, graded mostly on the discard mode (4 damage to an attacker or blocker). Siggy's RW deck hard-cast it to make tokens and ramp into Ajani Unrelenting.
- **Loyal Tutor** — build-around D. Only worth it with one broken planeswalker plus at least one more.
- **Flickering Hound** — Alex D+ / Mark D. A "dreamer card": four mana for a 2/2 with no immediate impact, but it can take over by blinking ETB creatures.
- **Ajani Resolute** (M) — D+. "The dreamer planeswalker"; its numbers suit constructed. No defense, a bad topdeck, and getting even one Pridemate is hard. Mark: "people are going to overrate this a lot."
- **Germinate Recruits** — Alex F / Mark D+ (?). Mark: "I'm willing to dream." It needs 2+ life gained in a turn to beat a flash 2/2, and the set hands out little lifegain. Best with Vigorbloom Charm: gain 3, draw, make three Cadets at instant speed.
- **Return to the Light Realms** (M) — F. "Probably one mana more than I would consider trying this."

### Blue (U)

*Whisper transcript. See the caveat at the top.* One host calls blue "my vote for best color at common/uncommon, but … not by much and … not with a high degree of confidence", and the other agrees. That's the opposite of Numot's read.

- **Countersculpt** — B (Mark moved up from B− to Alex's B). "A great set for Cancel": there are many good expensive things to counter, and at worst it's a Dissolve plus Empower Jace 1.
- **Plan for All Outcomes** — B (Alex moved up from C+ to Mark's B). Sorcery-speed tuck removal; "every spell is basically surveil 1 tacked on."
- **Mindseeker Oculus** — B−. "Great card." Empower 4 is usually better than 3.
- **Unsummon** — B−. "One of the best commons": the set's 4/4 and 5/5 tokens and big creatures make bounce strong.
- **Tetsuko Umezawa, Fugitive** — Alex B− / Mark C+. "Deceptively good": it also makes Jace-pressuring small creatures unblockable.
- **Traxos, Academy Guardian** — Alex B− / Mark C (both stayed put). Alex says prepared spells make the discount reliable; it's a great Jace protector.
- **Surveillance Phantasm** — C+. "By far the best template like this": a vigilant flier that enables itself and defends Jace. Don't attack after tapping out into the G/W +2/+2 reach/flying tricks.
- **Icy Reception** — C+. A Mana Leak for creatures, legends and Ways, or −5/−0, which matters with this much deathtouch.
- **Yuriko, Hope from the Shadows** — Alex C / Mark C+ (?). Blanks a deathtouch attacker or saves yours.
- **Arni, Humble Scribe** — Alex C+ / Mark C− (Mark: "I think I like your take"). A 3/2 looter for UB threshold and flashback.
- **Way of the Cryomancer** — Alex C+ / Mark D+. Alex: "one of the scariest just sitting in play." Mark: awkward to time; it wants 7–8 empower cards.
- **Infinite Coursework** — Alex C− / Mark C+. Aura lockdown; weak to the green untap trick and Unsummon.
- **Protege's Awakening** — Alex C / Mark C−. Only good if you can spend loyalty in big chunks (UG, e.g. with Kiora).
- **Perfected Theory** — Alex C / Mark D+. "Seems pushed" as a UR trick; Mark would cut it first.
- **Geist of Saint Thalia** — Alex C / Mark C−. Mostly a UR card.
- **Proft, Consulting Detective** — C. It can rarely be activated before turn 5 or so; "a little bit worse than it reads."
- **Hapatra, the Desert Frost** — Alex C / Mark C−. A "big Frost Lynx"; 3 toughness is rough here.
- **Ruric Thar, Biomagus** — Alex C− / Mark C. Fine, but not a high pick. (Numot's Sealed run disagrees: it won him two games.)
- **Divining Duelist** — C− / D+ (speakers unclear). Flexible filler.
- **Undulating Witness** — Alex C− / Mark D+. Probably the worst landcycler, but still some fixing.
- **Way of the Mind Sculptor** — Alex D+ / Mark C− (?). Either overkill card draw or what puts you over the top.
- **Fblthp, Impossibly Lost** — D+. Damaging a Jace doesn't count toward its trigger. "More interesting than good."
- **Sphinx's Approach** — D. The five-copy Sphinx tutor is a meme.
- **Cryotheory Adept** — Alex D+ / Mark D−. The prowess 2/1 doesn't hold up.
- **Yargle, Goliath of Otaria** — F (?). The joke 3/9.
- **Precise Redaction** — sideboard (no letter).

**Rares + mythics** (09-25 review; (M) = mythic)

- **The Theorist, Jace Beleren** (M) — A+ (Alex A → A+ to join Mark). Its floor is 4 mana for a 1/1 plus a card on every opponent draw step, and the +1 protects itself.
- **Sphinx of False Conclusions** — Alex A+ / Mark A. "Probably my vote for best rare in the set… I wish this was a mythic." A 4/2 flash flyer that loots on attack and returns as a token.
- **Seasoned Cryomancer** (M) — Alex B+ / Mark A− (Mark moved it into the A range). The discard choices are skill-testing. It's great to mill, since 5 mana to draw 2 from the graveyard is fine.
- **Lyra, Tolarian Archangel** — B−. The UR hybrid flashback looter (discard, draw two) triggers her angel without connecting. BB on turn 3 wants 10–11 blue sources.
- **Theorist's Proxy** — Alex C / Mark B−. The only Empower 3 card: a 2-mana Hard Evidence. Alex: "If it was four toughness, I'd be into it."
- **Variable Chaser** — C+, "middle of the road" with a wide floor and ceiling. A 3-mana 2/3 flying prowess whose wheel is very good in decks that dump their hand fast (UR aggro).
- **Jace's Machinations** — C+. A souped-up Divination: Empower 8 and instant-speed Jace activations. "Really hot" with UG Kiora's −8, but a topdecked copy digs only one card deep.
- **Diviner of Victory** — Alex C / Mark C+. Worse than the usual 3-mana bounce 2/2: double blue, mostly a 1/1, and it only hits MV 3 or less. It can bounce the big tokens. Best in UR or UW tempo.
- **Jace, Reality Sculptor** — C. The only rare walker. Play pattern: −3 first, then plus; the third Island matters a lot. "The worst [planeswalker] we've seen so far."
- **Chandra, Chill of Compliance** (M) — C. The mirror of Torch of Defiance and "a lot worse". The first +1 hits only about 1 time in 8 to 1 in 4, but it triggers your surveil payoffs every turn.
- **Cruel Calculations** — Alex D / Mark D+. You'd need about 7–8 UB prepared-spell mill cards; mostly "a 3-mana draw 3 that costs an extra mana in advance."
- **Samut, Tyrant of Naktamun** — Alex sideboard / Mark F. A 2/1 for 2; bring it in against multiple counterspells.

### Black (B)

- **Multiply by Zero** — B (both could see B+). "In the aggregate… still a great card."
- **Break Under Pressure** — B−. Mark started at B+ and tempered it. Alex: "I think we're too low on this card." It hits the intended target about 70% of the time.
- **Last Gasp** — Alex B− / Mark C+ (attribution by the speaker rule; a missing marker is possible). "Great rate, not much to say."
- **Extended Absence** — Alex C+ / Mark B−. The drain-1 lifts it from filler to "actively good." Alex: "I could be too low even."
- **Proft, Sinister Mastermind** — Alex B− / Mark C. Alex's grade is a build-around grade for UB/BG turbo-mill, with an expected cast around turn 6.
- **Mabel, Bitter Recluse** — C+. Good even drawn late; removing counters matters most against walkers.
- **Gallia, Tragic Host** — C+. Recurs with no finality counter. Good in UB.
- **Winter, Tormented Loner** — Alex C+ / Mark C− ("maybe I'd meet you in the middle"). Sacrifice a 1-loyalty Jace to make them sacrifice a real creature. Alex: most black decks will have fodder.
- **Rank Rat** — C. Weak in this set: little sac payoff, and a 1/1 can't pressure Jace.
- **Silence the Echo** — Alex C / Mark D+. Play one copy; multiples get clunky.
- **Screeching Soulbreaker** — Alex C / Mark D+. Alex sees a near-pillar of BR; Mark says it only pressures Jace for 1.
- **Apex Witchstalker** — Alex C / Mark C−. A land-cycling 6-drop; pairs with Rewrite Regrets.
- **Way of the Deathbringer** — Alex C / Mark C−. Reads as "draw a card, leave two loyalty"; few good sac targets.
- **Tinybones, Pocket Nuisance** — C. Pings on any discard, so it combos with Rank Rat and red rummagers.
- **Rewrite Regrets** — C (possibly higher ceiling). Reanimation targets include the land cyclers and Kiora of Fire and Ashes.
- **Danitha, Spear of Agony** — Alex C / Mark D → D+. Mark had forgotten Vicious Verse triggers it.
- **Solve for Disappointment** — C−. Weak as a late topdeck; Alex's grade assumes the attrition plan works.
- **Teyo, Diamondblade Mage** — C−. Better as a trick than as a body.
- **Rampart Hunter** — Alex D / Mark C−. Maybe only a 26th playable in a deep set.
- **Theoretical Necromancer** — D+ ("a theoretical D plus"). Four mana to do nothing to the board.
- **Loot, the Anomaly** — Alex D+ / Mark D. Plays as a vanilla 2/4. A UB/Tetsuko curiosity.
- **Cast Away Doubt** — Alex D / Mark D+. "We see these all the time. They're never good."
- **Massacre Girl, Most Wanted** — Alex D+ / Mark D. "Drain effects are very overrated."
- **Way of the Necromancer** — Alex F / Mark D−. "If not the worst, I think tied for the worst."
- **Terminal Criticism** — sideboard (no letter). "A smidge better to main deck, but not enough."
- **Yargle, Glutton of Urborg** — no grade heard (garbled in captions). "Just ain't it."

**Rares + mythics** (09-25 review; (M) = mythic)

- **Garruk, Veiled Butcher** (M) — A. One host watched it take over for seven turns and won only because the opponent decked.
- **Overwrite the Multiverse** (M) — A. Mark moved it up two grades after early access: on stalled boards he kept fearing it. Exiling three creatures also draws a card.
- **Lich's Relic** — A−. Crude Bent Blade (a B+ common) that targets instead of edicts. A Rescue Girl rebuy target.
- **Sanctum Lurker** — Alex A− / Mark B+. Your walkers survive at 0 loyalty. Turn 3 Lurker, +2 to drain, then −3 to draw and keep the 0-loyalty Jace. Mark: the body can't safely go to combat, and both effects need it alive.
- **Gideon the Oathless** — B. Like Graveyard Trespasser: ward–discard plus pings that add up (3 off a Hexhaven Battalion, 1 more per Jace activation).
- **Liliana the Repentant** — B− ("could see us being maybe too low"). Paired with green Marwin, the two 2-drops "just won the game on their own." The mill is mandatory, so watch your library.
- **Dark Matter Manipulator** — Alex B− / Mark C+. A 1/2 that mills 3 and later becomes a 3/2 or 5/2. Playable anywhere; better with graveyard payoffs.
- **Rise of the Deathbringer** — Alex C / Mark B−. An instant −3/−3 sweep you can set up around combat, or draw cards when ahead. Alex: "the more you talk about it, the more I think you're probably closer to right."
- **Vraska's Final Mercy** — C+. A sorcery-speed Infernal Grasp or lose 2 / Empower 6. BB is the cost.
- **Bloodline Recollector** (M) — Alex C / Mark C−. Its prepared instant (each player draws 3, loses 3) needs three creatures dying in one turn, checked at every end step. Pairs with the 2-mana sacrifice common.
- **Darklight Phoenix** (M) — C. A 4-mana 3/2 flying haste is fine alone. It returns only at beginning of combat, so creatures dying in combat don't count and you need pre-combat sacrifices.
- **Extrapolate the Impossible** — Alex F / Mark D−. Wish for two basics or two sideboard finishers; the black common landcycler is better.

### Red (R)

- **Kiora of Fire and Ashes** — Alex B / Mark B+ (attribution inferred; Alex said "I might be even a little too low"). Two must-kill threats, and a great RG ramp target, "far better than the UG Kiora."
- **Violent Echoes** — Alex B− / Mark B+ (Mark nearly gave A−). "Kill a 3-toughness creature, draw a card." It often won't cantrip against 4+ toughness.
- **Fulminous Forte** — B−. It meets Mark's "2 more damage than mana" burn rule, and the instant sweep hits the set's many 2/2 tokens.
- **No Admittance** — Alex B− / Mark C+. The top-graded red common.
- **Wrath of the Bloodmane** — Alex C+ / Mark C. With about 3 legends per pack it's often 2 mana; Mark said he should have joined Alex at C+.
- **Heartstring Puller** — C+ (Mark nearly B−). Mixed body sizes; a good target for the deathtouch hybrid trick.
- **Awaken the Inferno** — C+. Playable even if never cycled; a "premium top common" like WOE's Cut In. Alex expects it to be overlooked early.
- **Command the Stage** — Alex C+ / Mark C. "Probably the best payoff for pinging," and it points to RB as grindy midrange.
- **Pia, Determined Rebuilder** — C+. The floor is already good, and Heartwood tokens help its pump.
- **Jiang Yanggu, Alone** — C+ (both raised it from their first grade). Triggers on itself and gives card quality plus stats.
- **Marwyn, the Clearcutter** — Alex C / Mark C+. Good early stats and late card advantage.
- **Skilled Battlecarver** — C (both said it "could definitely be a C+"). Possibly red's only good 2-drop attacker.
- **Way of the Pyromancer** — Alex D+ → C / Mark C. On turn 2 it lets you cast a 4-drop on turn 3, and an up-ticking Jace demands an answer.
- **Blazing Crescendo** — Alex C / Mark C−. A clean 2-for-1 in low-curve red.
- **Tether Technician** — Alex C / Mark D+. They agreed to disagree; Mark says it's worse than DSK's Boilerbilges Ripper.
- **Way of the Warlord** — Alex C+ / Mark D+ (the biggest red split). Alex later said "C plus is probably a little bit high."
- **Gallia, the Merrymaker** — C−. The RW seeded uncommon; good with Mabel.
- **Koth, the Geomancer** — Alex C− / Mark D+. Heartwood ramp doesn't trigger landfall.
- **Tomik, Izzet Sparkmage** — Alex D+ / Mark C−. A "dorky stat line"; combos with Fulminous Forte.
- **Tetsuko Umezawa, Pursuer** — Alex C− / Mark D. Boom or bust; great with trample from Konstrari Charm.
- **Artifist Acumen** — Alex D+ / Mark D. Only for UR spells.
- **Chandra's Emberling** — Alex D / Mark D+. Starts too small; Mark wanted trample.
- **Winter, Team Player** — Alex D+ / Mark D. Needs too many things to line up.
- **Eardrum Rattler** — Alex D+ / Mark D−. The 1-mana activation "kills it." Its weakness is a big reason RB and UR look worse.
- **Arni, Renowned Champion** — D−. "Really really bad."
- **Essence Burn** — sideboard (no letter).

**Rares + mythics** (09-25 review; (M) = mythic)

- **Ajani Unrelenting** (M) — A+. Alex's pick for best rare in the set. Every loyalty activation makes a 2/2 Cadet, including Jace activations. Mark went 1–1 against it: "extremely hard to beat."
- **Chandra, Torch of Defiance** (M) — A. "Still great 10 years later."
- **Ajani's Anguish** — Alex B+ / Mark B. Fireball plus team trample, so cast it pre-combat and go face. A Pia tutor target and a Rescue Girl rebuy. Mark topdecked a win with it against LSV.
- **Curse-Marred Demon** — B. A 4-mana 4/4 flying trampler that tutors, then discards at random. The tutor choice is an interesting decision, and the body is good enough anytime.
- **Stingcaster Mage** (M) — Alex B− / Mark B. A red Snapcaster. You need many instant and sorcery targets, ideally removal. Counterspells and the attacking-creature removal are poor targets.
- **Master of Barbs** — B−. The BR "do the thing" payoff; "really really gross" with Ingris Stingerquill. Take it to be the aggressive RB shell.
- **Face Yourself** — C+. Copies either player's creatures with haste. They die at any end step where you don't control a planeswalker, so keep one; Plan for All Outcomes supplies a Jace. "I'm absolutely going to die to this a few times."
- **Samut, Hazoret's Champion** — Alex B− → C+ / Mark C+. A hasty 2/2 that trades easily; keeping it for the effect fights with attacking.
- **Pompous Battlemage** — C+ ("maybe supposed to be a C"). Reads like a good common. More of a constructed and cube card, and mostly for aggressive red.
- **Craterclaw Colossus** (M) — C+; a build-around grade would be in the B+ range. Seven mana is castable here, and one Heartwood token turns it from medium to strong. Some community tier lists had it at F; both hosts disagree.
- **Draconic Visitor** — C. It does nothing at once, but it turns artifact tokens into 5/5 dragons. Best with the RG hybrid uncommon that re-prepares itself: a dragon every turn.
- **Pyre Rhymer** — Alex C− / Mark C. A 3/3 prowess; the instant Molten Tide needs 3 Mountains to matter.
- **Identity Echo** — F. One host watched an early-access opponent use it to turn a 3/2 into a 2/3.

### Green (G)

- **Fblthp, Knows the Way** — Alex B / Mark A−. At 5 mana it's a 3/2 that draws three lands. Mark suggests adding an off-colour basic even when not splashing. Alex: "maybe I'm too low on it" as long as you're heavy green.
- **Jiang Yanggu, Never Alone** — Alex B− / Mark B. Five power and toughness across two bodies, and it untaps Heartwood tokens.
- **Way of the Wildspeaker** — Alex B− / Mark C+ (Mark: "I like your grade more than mine"). It turns every other empower card into a 4/4 threat. "One of the better uncommons to pick up early," but Unsummon hurts it.
- **Ruric Thar, Magecrusher** — Alex C+ → B− / Mark B−. A good ramp target; weak to deathtouch and edicts.
- **Marwyn, the Preserver** — Alex C+ / Mark B−. Good early stats and late card advantage with mill.
- **Compel Brutality** — C+. "Top green common territory." With a high-loyalty walker it hits for 4–6.
- **Bestial Incursion** — C+. Card advantage, and good when milled or discarded. Unsummon ruins it.
- **Arcane Amphisbaena** — Alex C / Mark C+. Mark: "the two drop of choice in a lot of decks."
- **Greenhouse Propagator** — Alex C+ / Mark C. Lifegain "sells me on it"; curves into Bloombrute.
- **Yoshimaru, Scrappy Stray** — Alex C+ / Mark C (both said it could land in the B range). Fight is weak and needs the bigger creature already out.
- **Loot, the Nexus** — Alex C+ / Mark C−. "Really darn solid," but hard to set up on purpose.
- **Pia, Aether Ascetic** — Alex C+ / Mark C−. Needs a top enchantment to tutor; don't take it early.
- **Something Worth Saving** — C. Digs for strong uncommons and rares. Play one, two at most.
- **Way of the Paradox** — C (synergy tag for UG walker decks). "Three mana Explore with more play."
- **Tethermage's Advantage** — Alex C / Mark C−. Mark dropped from a planned C+ once he counted how little empower some decks run.
- **Sureshot Sower** — Alex C / Mark C−. "Mostly just filler."
- **Vinelasher Adept** — Alex C / Mark C−. "One of the lesser land cyclers."
- **Budding Insurgent** — Alex C− / Mark D+. Alex's C− is a hedge in case Ways turn out central.
- **Wrecking Gecko** — Alex C− / Mark D+. "Not an embarrassing card to play."
- **Edgar, Moonlit Sovereign** — Alex C− / Mark D+. Two turns invested in one Unsummon target.
- **Ghalta the Unstoppable** — Alex C− / Mark D+ ("probably too low"). Castable for about 5 off a 4/4, but it can rot in hand.
- **Inspired Tethermage** — D+. "Too vanilla for too long."
- **Titanbones, Towering Heart** — Alex C− → D+ / Mark D. "Big dummy"; 3 toughness dies to everything.
- **Hunter's Axe** — Alex D / Mark D+. Does nothing on defense.
- **Restore with Empathy** — Alex D+ / Mark D. Needs a slow format and good bombs to rebuy.
- **Flourishing Grapple** — sideboard (no letter). Mark: not a disaster to maindeck in Bo1, since about 70% of opposing pairs have a target.

**Rares + mythics** (09-25 review; (M) = mythic)

- **Hungering Puppetbeast** — A. "Beefy and hard to kill." It grows by sacrificing artifacts and picks trample, hexproof or haste.
- **Verdant Kraken** — A. Makes a 3/3 Forest creature land on every player's upkeep, and the set has plenty of mana sinks for the extra mana.
- **Simulacrum Shaper** — A−. Solemn Simulacrum for one less.
- **Garruk, Curse Breaker** (M) — Alex B+ / Mark A−. Floor: a 4/4 trampler that draws a card and leaves a 2-loyalty walker. It's a fractured pair with Garruk, Veiled Butcher.
- **Carnivorous Cultivator** — B. A 2-mana 2/3 deathtouch; self-mill gets enough lands into the graveyard.
- **Tarmogoyf** (M) — C+. Counts both graveyards. A removal spell on the stack adds a card type (and a point of toughness) if that type wasn't already there.
- **Puppet Crafting** — build-around C. Needs 6–7 artifact or non-Aura enchantment targets; Eye of Jace is the best target.
- **Hexhaven Invigorator** (M) — Alex C+ / Mark D+. GGGG needs at least 12 green sources. Alex grades it for when you can cast it; Mark grades how often you will.
- **Gardenize**, **Omnipresence** (M) — no grades; skipped as constructed cards.

### Multicolor

**WU Fatehold**
- **Desperate Futurescribe** — Alex B− / Mark B. A Jace token enables its counter immediately. Mark: "just incredible."
- **Fatehold Charm** — C+ ("might even be too low… could creep into B−"; Alex later said he'd go higher).
- **Fatehold Chronologist** — C. Helps WU tempo flyers on both halves.
- **Prudent Fateseer** — C. It would have been very strong with flying on either side.
- **Denzilore Fatehold** (M) — A. The flash is "a little bit fake", since most surveils come from main-phase Jace activations. Mark's P1P1 in early access.
- **Proctor of Potential** (R) — B. It self-enables its return: cast a creature pre-combat to surveil, trade, then bring it back.

**UB Theorix**
- **Recursive Recruitment** — Alex B− / Mark C+. Board presence buys time for the flashback; Mark calls it splashable in BG.
- **Theorix Charm** — C+. More like two mana's worth; Mark is confident it doesn't reach B.
- **Paradox Shaper** — Alex C / Mark D+. An engine for a deck-yourself-to-zero plan.
- **Theorix Metamage** — Alex C− / Mark D+. Too understated on curve.
- **Void Extrapolator** — Alex D+ / Mark C−. Filler 2-drop.
- **Uldaros Theorix** (M) — Alex A+ / Mark A. Even rebuying a landcycler plus a trick is a huge six-drop.
- **Null Summoner** (R) — A. Better than Torment of Gollum. The exiled card is gone for good: killing it does not return the card.

**BR Stingerquill**
- **Stingerquill Charm** — Alex B− / Mark B. "Probably the best charm." Alex started at B and dropped it because the rest of BR is weak.
- **Grim Repriser** — C+. Good if you end up BR; not worth pivoting into pings for.
- **Hallway Heckler** — Alex D+ / Mark C−. Rummage is much weaker on a 3-drop.
- **Stingerquill Voxmancer** — Alex D+ / Mark C−. Fragile; only good with many payoffs.
- **Whiplash Wordsmith** — D+ ("somewhat optimistic"). Awful on defense.
- **Ingris Stingerquill** (M) — Alex A / Mark B+. A cheaper, flying Hellrider that also makes hasty Cadets. None of BR's four gold cards (two commons, the rare and this mythic) has a generic pip.
- **Stinging Vitriol** (R) — Alex C+ / Mark B−. Two damage plus Thoughtseize-style discard. RB aggro may want to cast its ping payoffs first.

**RG Konstrari**
- **Craftwork Crusher** — **A−** (both; "could go higher next week"). Compared to Titan of Industry. **The highest grade in the review.**
- **Heartwood Crafter** — Alex C+ / Mark B−. Soul Tether on turn 2 is strong. Great in an opening hand, weak as a topdeck.
- **Konstrari Charm** — C+. The counters + trample mode is "a very good combat trick" and the main use.
- **Woodwork Prodigy** — Alex C+ / Mark C. Endless Heartwoods with diminishing returns.
- **Konstrari Improviser** — C. Fixes the missing R/G source.
- **Aerid Konstrari** (M) — A ("could even see it making it to A+"). Makes Heartwood tokens on ETB and on death.
- **Tenured Tethermage** (R) — Alex A− / Mark B+ (Mark climbed during early access and may still join A−). A "major glow up on Wood Elves." Its instant-speed growth makes it a must-answer threat.

**GW Vigorbloom**
- **Vigorbloom Charm** — B−. "Probably the second-best charm"; the lifegain mode matters more in this set.
- **Bloombrute** — Alex B− / Mark C. Huge upside if it sticks; Mark says you don't get the card every turn.
- **Vigorbloom Vanguard** — C+. Only exciting in GW, or RW counters.
- **Blossom-Blessed Angel** — C ("may have graded a little too low"). A 3/5 flyer if the counter goes on itself.
- **Emergency Phytomedic** — C− (Alex: "maybe even C+").
- **Kwia Vigorbloom** (M) — Alex A → A− / Mark A−. "The worst sphinx by a decent amount, but not bad": no ETB, and there's plenty of removal and bounce.
- **Solarium Sentry** (R) — Alex B → B− / Mark B−. A 2-mana 3/3 lifegain body; in a grindy format a few 2-life triggers rarely decide games.

**WB**
- **Twisted Fates** — B. "A banger," likely one of the best uncommons; triple pips keep it with the WB drafter.
- **Edgar, Ancient Bloodlord** — C+. "Almost a pull to WB, but maybe not quite."
- **Blessed Ghoul** — Alex D / Mark D+. Undersupported synergy.
- **Vindictive Triumph** (R) — C+, a Murder rate. Cast it at end of turn to steal and attack with a cheap creature.

**UR**
- **Clash of Elements** — Alex B− / Mark B. Cheaper top-or-bottom removal. Against a token, don't choose top.
- **Twinned Vision** — Alex C / Mark C+. "The most gluey of glue cards."
- **Saheeli, Jewel of Avishkar** — C ("a responsible C"). Splashable into artifact-leaning decks.
- **Frostbite Pyromental** (R) — Alex D+ / Mark C (Mark: "very low confidence"). A card-drawing Ball Lightning; hard to connect in a controlling deck.

**BG**
- **Hapatra, the Desert Fang** — Alex B / Mark B+. The MV-6 land cyclers make it kill almost anything.
- **Primal Witchstalker** — Alex B− / Mark C+. The BG graveyard-midrange signpost.
- **Ferocity of the Hunt** — Alex D+ / Mark C−. Mark argued it up; Alex was convinced but kept his grade.
- **Vraska, the Cutting Glare** (R) — A− (Mark A → A−). The ETB needs six *lands*, and Heartwood tokens don't count. Recursion decks loop it.

**RW**
- **Mabel, Valley Hero** — Alex B− / Mark C (Alex conceded mid-discussion but stated no new grade).
- **Warrior's Blades** — Alex C+ / Mark C. Equip 3 is expensive. Alex compared it to the Hobbit's Crude Bent Blade.
- **Solitary Cell** (R) — Alex C+ / Mark C. Two-mana exile of a permanent with MV 3 or less; you almost never cut it from RW.
- **Charge the Sanctum** (common, missed from the colour videos) — D. Shows up in De'our's red aggro lists anyway.

**UG**
- **Mind Meanderer** — Alex B− / Mark C+. A flying Indrik Stomper; weaker if the format is full of deathtouch.
- **Kiora of Salt and Sand** — Alex C / Mark C− (Alex talked down a tier). "Upside trap."
- **Tam's Resistance** — C−. Better once UG has several ways to spend loyalty.
- **Avatar of Burgeoning Echoes** (M) — Alex B / Mark B → B+. A 2-mana 2/3 with landfall Empower 2; the −10 is "almost flavor text".
- **Tam, the Possibility** (R) — F. "People are going to be tricked by this."
- **Entrust the Spark** (R) — F.

**Three- and five-colour (rares)**
- **Karn, Gilded Guardian** — C−. Mark went D− → D → C−: a BG Heartwood deck can cast it for about 7. Alex's listed B− was a typo for C−.
- **Codie, Ravenous Codex** — Alex C− / Mark D+. Copies prepared spells; "if the stars align" in UB turbo-mill.
- **Vraska, Soul of Stone** — D+. Playable, but not worth adding a third colour for.

### Colorless / artifacts

- **Traxos, Scourge Eternal** — Alex C− / Mark C+. Mark rates it a 5/4 trampler that stays active if you keep casting creatures; Alex says it's still a 4-drop with no ETB.
- **Eye of Jace** — Alex C / Mark C−. It's great on turn 1 and a bad topdeck. Alex's First Impressions call: it could be "quite a bit better than it looks… or one of the worst cards in the set."
- **Archive Arbiter** — Alex C / Mark C− (attribution least certain). It can destroy a Jace, a removal enchantment or a Way.
- **Keeper of the Quiet Hour** — Alex C− / Mark C. Fine filler.
- **Medic's Kitesail** — C−. A flyer and lifegain engine for board stalls. Don't play a second copy.
- **Murmuring Volume** — C−. For multicolour or ramp decks, not a single splash.
- **Afterthought Sentry** — D+. Filler; RB may need the 2-drop.
- **Living Library** — Alex D+ / Mark D. "Very slow."

**Rares + mythics** (09-25 review; (M) = mythic)

- **The Echoverse Fulcrum** (M) — Alex C / Mark D+. A loot on ETB plus a wrath you pay in installments. Awkward: looting away land hurts the 7-mana plan. Remember that every opponent could have one.
- **Emrakul, the Exigent Doom** (M) — Alex D+ / Mark F. Mark: they can just sacrifice three lands to the ward, and they see it coming. Alex: fine as top end in a ramp deck.
- **Karn, Argent Defender** — sideboard (both). A constructed card.

### Lands

- **The 10 planeswalker duals (Fatehold / Konstrari / Stingerquill / Theorix / Vigorbloom Annex; Dedicated / Formidable / Innovative / Meticulous / Transformative Commons)** — C+ (graded as a cycle). "Sidewalk lands" that will often enter untapped. Alex wants about 2 fixing lands per deck.
- **Room of Refuge** — C+. Taken at about the same rate as the duals.
- **Hexhaven Dueling Arena** — Alex F / Mark D− ("the coward's D−").

**Rares + mythics** (09-25 review; (M) = mythic)

- **Deserted Beach / Haunted Ridge / Overgrown Farmland / Rockfall Vale / Shipwreck Marsh** — B− (both, as a cycle). Better than the common duals because they almost always enter untapped; fine to take mid-pack.
- **Theorist's Sanctum** — B−. An instant-speed Empower 2 on an Island; "happy to play this in every blue deck."
- **Hall of Echoes** — C−. Clears the bar for a colourless land in slower decks. Skip it in aggro or with heavy pips.
- **Roiling Canopy** — Alex F / Mark D− → F. No trigger until turn 7 even in mono-green, and the payoff is only +3/+3.

## Source episodes

- 2026-09-18 — Reality Fracture First Impressions For Draft + Sealed! | LLU #261 (I1PPajMb938)
- 2026-09-22 — Reality Fracture Limited Set Review! | Multicolor + Colorless | 1/6 (_LfIxIuRQI0)
- 2026-09-22 — Reality Fracture Limited Set Review! | Green | 2/6 (Gq7DmwSLcJk)
- 2026-09-22 — Reality Fracture Limited Set Review! | Red | 3/6 (rzZTGt7DQqw)
- 2026-09-22 — Reality Fracture Limited Set Review! | Black | 4/6 (svT3Ige5E3E)
- 2026-09-22 — Reality Fracture Limited Set Review! | Blue | 5/6 (ke_XTZAqxWI) — transcribed locally with whisper
- 2026-09-22 — Reality Fracture Limited Set Review! | White | 6/6 (BmIJbG1z69Q)
- 2026-09-25 — Reality Fracture Rare + Mythic Limited Set Review! (XPPMF-xrFjk)
