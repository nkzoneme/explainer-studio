# Story shapes: turn a sourced report into a story someone finishes

Read at Stage 3 of `explainer-research`, before the outline. It adds four things to the script rules: three treatments, the Story card, the script lint and the cold read.

**Why (measured 18/11/2026 with `kit/tools/qa_script.py` on our own scripts).** The rule "contrast turns at least 1.0 per minute" was already in the skill. Two approved scripts had 0.27 and 0.78; one ran 322 s without a single turn word; both had sentences of 31–42 words and questions in pairs. Every fact was sourced and every fact was read out in order: a report. A rule nobody runs is not a rule, and counts alone do not make a story, so the lint runs the counts and the cold read judges the story.

Evidence tags: **[data]** a large sample or a platform statement; **[practice]** a named creator's documented method; **[untested]** advice with no evidence behind it, kept as a hypothesis. No source we found ties any script rule to measured retention, so every [practice] and [untested] rule below is logged as an experiment in the channel's `LEARNINGS.md` and judged on our own curves. Sources: `REFERENCE_REPOS.md`.

## 1. Three treatments, then one (before the outline)

Write three treatments of the same facts. They are three different films, not three titles on one film: each has its own **shape** (§3), its own **device** and its own **form**. Make one the bold one you would not have picked first. Each treatment is five lines:

- name, shape, device and form in a few words;
- the first 10 seconds, exactly: what is on screen, what is said;
- the person the film follows, what they want, what stands in the way;
- the peak: the one scene that pays the title's promise, and what the viewer sees there;
- beats in one line (`hook → … → peak → ending`).

Put the recommendation first with its reason in one clause. They go into `BRIEF.md` under `## Treatments`; the operator picks at G1+G2. Build nothing for a treatment that was not picked. (Adapted from HyperFrames `references/story.md` §2: "A pitch where all three are plain cuts between scenes has not tried the forms.")

| Device | What the viewer sees |
|---|---|
| A moment in someone's day | a named person, a time stamp, the message or alarm that starts it |
| The object is the explanation | one machine, building, aircraft or network drawn so it reads as what it is; the camera tours through it and every number comes from it |
| The result first | the wreck, the bill or the blackout plays first, then the film rewinds |
| One object travels | a single thing (a password, a part, a dollar, a packet) is followed from hand to hand to the end |
| Two rooms | the same hour seen from two sides (attacker and defender, engineers and accountants) until they meet |
| A number lands | one real number earned by a scene, then made physical at true scale |
| A myth turned over | the explanation everyone repeats, built up fairly, then cracked by one document |

| Form | What the viewer sees |
|---|---|
| A flight through one world | one large map, cutaway or desk; each idea is a stop on the camera's route |
| Object-to-object chain | every shot ends on the thing that opens the next |
| One diagram that grows | the simplest true picture, one part added per beat when it is named; never the finished diagram at once |
| A clock | a running time stamp; chapters are hours or days; the stakes rise with the clock |
| Split screen to one | two tracks side by side that collapse into the one that matters |
| Match cuts | one shape holds while the world around it changes (a dial, a clock, a wheel) |

An explainer's spine is one concrete example worked through from start to finish, not a tour of facts. Start where the viewer already is (a person, a place, a thing they own) and bring the abstract part in as the answer to their question.

## 2. The Story card (required at the top of SCRIPT.md)

`qa_script.py` fails a script without it. Fill every slot with a real line, not a label.

```markdown
## Story card
- Promise: <what the title and thumbnail make the viewer expect to see or learn, in their words>
- First 10 s: <what the pictures literally show from 0:00 to 0:10>
- Person: <named person or body> wants <goal> but <obstacle>
- Peak: <the one scene that pays the promise, and the picture in it> at <m:ss> (chapter N)
- Shape: <T1 … T5 or a named one>; the last two videos on this channel used <…> and <…>
- Stakes ladder: ch1 <what is at risk> → ch2 <…> → … (one clause per chapter, each larger or closer than the one before)
- Re-hooks: <m:ss what> ; <m:ss what> ; <m:ss what>
```

Three checks no script can skip:

1. **The first 10 s show the promise's object, and the peak shows it again, paid.** The most common leak found in a batch of animated explainers was a cold open that showed the problem while the title and thumbnail promised the payoff [practice: BusyBee3333 `retention-pass`]. The hook opens the loop; it never answers it.
2. **The peak sits in the last 45 % of the film** and is the biggest picture of the film, once [practice: HyperFrames `story.md` §4 puts a launch film's payoff 60–80 % in; untested for 10-minute films].
3. **The shape differs from the channel's last two videos** (also the inauthentic-content rule: no template run).

## 3. Five shapes for an incident or a failure (10–12 minutes)

Beat times are starting points built from the sources in §5 [untested as a set].

- **T1 Cold open, then rewind.** 0:00 the worst moment, with a time stamp and a named person · 0:20 stakes and the promise · 0:45 rewind: who they are, what normal looked like · 2:00 the first warning, ignored (BUT) · 3:00 re-hook: the true scale · 3:00–6:00 it spreads, each step THEREFORE · 6:00 re-hook: who was really behind it · 6:00–8:30 the response and one wrong decision · 8:30 peak: the real cause · 10:00 consequence · last 30 s ending.
- **T2 Investigation.** 0:00 one fact that makes no sense · 0:30 the three questions the film will answer, as a ladder · 1:30 what was promised and the first engineer · 4:00 the first failed test and the official explanation · 6:00 re-hook: evidence that contradicts it · 6:00–9:00 the real cause, found · 9:00 the bill and the decision · peak answers the opening fact.
- **T3 Countdown.** 0:00 the outcome and the deadline · then chapters as time stamps · every stamp raises the stake · re-hooks at chapter boundaries · the peak lands at zero. For single-day incidents.
- **T4 Myth, then reversal.** 0:00 the popular explanation · 0:45 build it so the viewer agrees · 3:00 the first crack · 3:00–6:00 the evidence piles up · 6:00 full reversal (the peak can sit here if the second half is its consequence) · 6:00–10:00 what really happened, following one person · ending on what it changes now.
- **T5 Two tracks.** Alternate the two sides every 60–90 s · they meet at about 7:30 (the peak) · aftermath to the end. For stories with two named parties.

## 4. Ten hook mechanisms (pick a different one from the last video)

| # | Mechanism | An engineering failure | A security incident |
|---|---|---|---|
| 1 | Worst moment first | "At 4:40 a.m. the control room lost every sensor at once." | "At 2:14 a.m. every screen in the hospital went black." |
| 2 | Impossible fact | "The ship was too big for the port it was built to serve." | "A four-digit code protected a city's water." |
| 3 | Named person, goal, obstacle | "One engineer had to prove the weld would hold." | "The night operator had ninety seconds to decide." |
| 4 | A number, then why | "Forty-one seconds. That is how long the backup lasted." | "Six thousand passwords. One spreadsheet." |
| 5 | Myth flipped | "Everyone blames the storm. The inspection report says otherwise." | "It was not a hack. It was a default password." |
| 6 | Nobody knows | "Nobody knew which valve had failed." | "Nobody at the company knew the account still existed." |
| 7 | Inside the room | "Inside the meeting where they chose to launch anyway." | "Inside the chat where the price was set." |
| 8 | Countdown | "They had eleven minutes of power." | "The backups would be gone in four hours." |
| 9 | Result first, then rewind | "By morning the line was closed. Here is the first mistake." | "By Monday the tills were dead. It started with one email." |
| 10 | The ignored warning | "Three reports said the part would not fit." | "The vendor had warned every customer two weeks before." |

The examples show the form only: their times and numbers are invented. A real hook uses only lines from the claims table. The hook ends on the promise sentence, in words close to the title. The film names its hook mechanism in `STATUS.md` so the data loop can compare them.

## 5. Engagement rules (added to the script rules; each is an experiment)

| # | Rule | Tag | Source |
|---|---|---|---|
| E1 | BUT or THEREFORE between every two beats; an "and then" link is cut or reordered. `qa_script.py` lists them. | [practice] | Parker and Stone, via secondary coverage |
| E2 | A named person with a goal and an obstacle is on screen and in the voice by 0:20, including system-level incidents (the on-call engineer, the night operator, the test pilot). Never an invented person: use a real role when no name is public. | [practice] | George Blackman's hook = character, concept, stakes (secondary recaps) |
| E3 | Re-hooks at about 3:00, 6:00 and 9:00: a new fact, an escalation or a reversal the hook did not promise. This replaces the single re-engagement at 40–50 %. | [practice] | MrBeast production handbook, written for spectacle videos at 2022 scale |
| E4 | The first three minutes move through at least three different times or places. | [practice] | same handbook ("cover multiple days in the first three minutes") |
| E5 | Every chapter ends on a question, a reversal or a new threat, never on its own summary. | [untested] | yaxeen/storytelling-skills; Blackman |
| E6 | Stakes escalate: the Story card's ladder gives one clause per chapter, each larger or closer than the last. | [untested] | synthesis |
| E7 | No stretch over 60 s of pure explanation without a person, a conflict or a surprise. | [untested] | synthesis; OpenMontage "never 3 consecutive steps of pure explanation" |
| E8 | Every number gets a human-scale comparison in the same sentence or the next (the number, then a thing the viewer already knows the size of), both from the claims table. | [untested] | synthesis; video_explainer narration prompt "use specific numbers" |
| E9 | State what the viewer believes, then break it, at least once in the first third. | [practice] | Veritasium's misconception-first teaching (secondary) |
| E10 | The ending is abrupt: payoff, one line of consequence, the pitch. | [practice] | MrBeast handbook; already our ending rule |

Numbers that sound precise and are not: "65 % of viewers decide in 3 s", "the first 42 seconds", "pattern interrupt every 60–90 s", "AI narration loses 35 % in 45 s" all trace to marketing pages with no study behind them. Do not write them into a brief as facts.

## 6. Titles: frames with data behind them

One large study exists: vidIQ, more than 4 million videos uploaded in 2026, views relative to the average video (1.0x), observational, no control for topic or channel size [data, correlational].

| Frame | Relative views | Incident-explainer use |
|---|---|---|
| Caught on camera | over 4x | only when real footage is the film |
| Turning X into Y | over 3x | "How a Loose Bolt Turned Into a Six-Week Shutdown" |
| Nobody / no one knows | over 2.5x | "Nobody Knew Which Valve Had Failed" |
| Inside X | 2.5x | "Inside the Meeting That Approved the Launch" |
| Banned, forbidden, illegal | over 2x | only when literally true |
| How X did a surprising thing | nearly 2x | our first title family, keep |
| A specific superlative | over 1.5x | "The Most Expensive Typo in Banking" |
| X days, hours or years | nearly 1.5x | "40 Days Without Running Water" |
| Plain how-to | 1.07x | avoid |
| **Ends in a question mark** | **0.82x** | at most one of the five candidates |

Thumbnail rules (faces, three words, contrast) have no large-sample evidence either way; two analyses of 16 thousand and 507 thousand videos found little. Keep our 160 px test and the rule that the thumbnail's object appears in frame 0 and at the peak; treat the rest as taste.

**Reading the numbers.** YouTube says half of all channels sit between 2 % and 10 % impressions click-through rate, and that new videos or videos under 100 views "can see an even wider range" [data: YouTube Help 7628154]. Do not touch a title or thumbnail before about 1,000 impressions from one traffic source. Under 500 impressions the package was never tested.

## 7. Script lint (before the cold read, before any voice)

```
python3 kit/tools/qa_script.py research/<video>/SCRIPT.md --channel <slug>
```

Exit 1 blocks G2. It fails on: a sentence over 30 words, a first sentence over 15, contrast turns under the style's minimum, more questions per chapter than the style allows or two in a row, an ad-read word in the first 60 s, a missing Story card slot. It warns on: stretches over 75 s with no turn, "and then" links, a chapter ending on a summary, a chapter with fewer than two numbers, a peak outside 55–90 % of the runtime, re-hooks more than 4 minutes apart. Every warning is either fixed or answered in one line in the G2 risk sheet.

## 8. Cold read (a fresh agent, text only, before G2)

The writer cannot read the script as a stranger. Start one `explainer-worker` that gets **only** the spoken lines (`python3 kit/tools/qa_script.py SCRIPT.md --spoken research/<video>/spoken.txt` writes them, one blank line between chapters), the title and the thumbnail concept in one line. No research, no claims table, no Story card. Its whole brief:

```
You are a viewer who clicked on "<title>" (thumbnail: <concept in one line>). Read only <spoken.txt>: it is the narration of a video, in order.
1. In one sentence: what did the title promise you? Quote the first line that starts paying it, and the line that pays it in full.
2. Who is this story about, what do they want, and what stands in the way? Quote the line where you learned each. Write "never" if the script does not say.
3. Mark the three places where you would stop watching. For each: quote the line, say why in one clause (a list, a document read aloud, backstory, a number with no scale, nothing at stake), and write the exact replacement or cut.
4. List every stretch of four or more sentences in a row that only explains (no person acting, no conflict, no surprise): first and last line quoted.
5. For each chapter end (a blank line in the file): does it make you want the next line? yes or no, and the fix when no.
Notes only, in the order above. No praise, no summary, no score out of 10.
```

The writer fixes every "never" in answer 2 and every stop point in answer 3, or says in the G2 risk sheet why it stays. One round; a second only when answer 2 still says "never". The cold read never sees the sources, so it cannot check facts: the fact-check stays a separate gate.
