## 7. Social Systems

### 7.1 Communication Channels

|Channel|Command             |Scope                          |
|-------|--------------------|-------------------------------|
|Say    |`say <text>`        |Current room only. **v22 format:** speech renders `Name: message` in say-color — players and NPCs alike, no `[say]` prefix; the speaker receives their own broadcast (double vision is intentional; `echo off` is the remedy for the command echo, not the speech) |
|Yell   |`yell <text>`       |Current room + adjacent rooms  |
|Tell   |`tell <name> <text>`|Private, anywhere              |
|Party  |`party <text>`      |All party members              |
|Guild  |`guild <text>`      |All online guild members       |
|Zone   |`zone <text>`       |All players in current zone    |
|General|`general <text>`    |All players online (throttled) |
|Emote  |`emote <text>`      |Freeform action in current room|

All channels are logged server-side for moderation.

### 7.2 Parties

- 2–6 players
- Shared XP with party bonus multiplier (6-player party: ~70% of solo XP each — worthwhile for harder content)
- Party members' Vitality, Acuity, and Longevity visible in side panel UI

### 7.3 Guilds

- Up to 100 members
- Customizable ranks with permissions
- Guild bank (rank-gated access)
- Guild hall (purchasable instanced area with recall point, vendors, crafting station)
- Guild XP track (levels 1–20, passive bonuses for all members)

### 7.4 Reputation System

Reputation scores with major factions in each zone. Affects: NPC dialog, faction-exclusive vendors and quests, shop prices, access to restricted areas. Reputations are permanent. NPCs remember your history.

### 7.5 PvP Zones & Flagging

- Entering a PvP zone requires confirmation
- PvP kills grant PvP XP (separate track from normal XP) and have a chance to drop carried (not equipped) items
- **Bounty system:** Repeatedly killing the same player places a bounty on the killer
- Logging out in a PvP zone: character persists in world for 60 seconds before fading — killable during that window

-----

### 7.6 NPC Dialogue — The Listening Model (v19)

NPCs are not addressed; they **listen**. There is no `talk` or `ask` verb by ruling — dialogue is diegetic room speech: you say things aloud, and inhabitants who know something about what you said may answer. The mechanic is the fiction.

**Mechanics (all ruled v19):**

- Per-NPC keyword→response maps (`DialogueEntry` with lowercase single-word keywords, `DialogueResponse` pools). Matching is dumb word-level containment — no NLP. Unmapped NPCs stay silent.
- One utterance → each eligible NPC answers **once**. **Entry-first draw:** among an NPC's matched entries, one entry is chosen at random, then one response from its pool — each matched *topic* gets equal voice regardless of pool depth. Re-asking re-rolls.
- **No consecutive self-repeats:** an NPC avoids the response it gave last time when its pool offers an alternative.
- Multiple responders: **random shuffle per utterance**, delivered tick-staggered at **2 ticks between speakers** ("less than combat, a little more sociable, less interrupty"). Second and later speakers are introduced by position-aware **connective color** drawn from pooled templates ("{name} also looks up and answers." / "{name} chimes in, not to be left out.").
- Responses **broadcast to the room**, riding the standard `say` formatting — identical for asker and witnesses. Responses **always land**, even if the asker has left; if the asker is gone when the final response fires, that last speaker may add one lore-voiced **departure reaction** (Aldric snorts. "Youth," he mutters, to no one in particular.).
- **Greetings:** an NPC with a greeting entry emits one line the first time a given character enters its room — once per character, forever.
- **Discoverability:** examine-text hints on talkative NPCs, a `help` line, greetings demonstrating that NPCs speak, and room-broadcast answers teaching bystanders — discoverable, never announced.
- Authored dialogue carrying directional or locational claims is verified against the room graph before shipping (standing rule from issue #34).

The v19 roster: Aldric, Info Prime, Morra, Pella, Ferwick, Repairbot Prime, Seris, Veris. The Obelisk and the spheres remain silent by ruling — mystery preserved. Persistent NPC memory (Sirius-class entities) remains a future tier.

-----

