# Summer Robotics Challenge — Week 5 Blog Post Design

Date: 2026-07-28  
Status: approved for planning

## Goal

Ship a week 5 build-log post in the existing Summer Robotics Challenge series. Narrative center: ditch shaky VR teleop for leader–follower (move one arm by hand; the other mirrors), with “go to A5” as proof. Grasp training and quiet customer research are secondary beats.

## Scope

### In

- New post: `blog/summer-robotics-week-5.html`
- Collection update: add week 5 card at top of `blog/collections/summer-robotics-challenge.html`
- Series nav: link week 4 → week 5 (and week 5 → week 4)

### Out

- LinkedIn draft (unless requested later)
- Photos / media embeds
- Deep technical writeup (commands, SDKs, tuning knobs)
- Named customers, product pitches, or concrete go-to-market details

## Title & metadata

- Title: **week 5: ditch the headset** (page `<h1>`: `ditch the headset`)
- Date: **28 jul 2026** (`article:published_time` / JSON-LD: `2026-07-28`)
- Reading time: target ~5–7 min
- Tags: `robotics`, `week 5`
- Canonical / OG / JSON-LD: mirror week 4 pattern (`isPartOf` Summer Robotics Challenge collection)

## Narrative arc (control-story)

1. **Open** — VR teleop still shook; stop fighting the Quest.
2. **Switch** — Leader–follower: physically move one arm; the other copies. Plain English once; “leader–follower” as the short label. Not a separate remote, not VR.
3. **Proof** — “go to A5” works: the arm goes to that square.
4. **Side thread** — Grasp training in parallel; closer, not clean yet. One short beat, not a training log.
5. **Fog** — Abstract, slightly funky aside on talking to people / poking at the market without spilling beans. No names, no pitch.
6. **Close** — Week 4 was seeing; this week the arm takes orders. Grasp + demos still next.

## Voice & content rules

- Match weeks 1–4: lowercase title, short sentences, builder honesty, unfinished threads allowed.
- High-level only: what changed and why it mattered.
- No command dumps, device archaeology, or hyper-specific tuning detail.
- Humanize pass before considering the draft done (no AI-slop cadence).

## File / HTML structure

Copy the week 4 shell and adapt:

- Back link → collection
- `article-header` with collection label · week 5
- `series-note` (Robotics Nation / XLerobot challenge)
- `article` body with `h2` section breaks aligned to the arc above
- `week-nav`: prev → week 4; optionally note week 4 title
- Update week 4’s nav to include next → week 5

### Collection card (draft excerpt)

> vr teleop still shook, so i swapped to leader–follower. “go to a5” works. grasp training in parallel. also talking to people i’m not ready to name yet.

## Success criteria

- [ ] Week 5 page loads in the same style as prior weeks
- [ ] Collection lists week 5 first with correct link, date, excerpt, tag
- [ ] Week 4 ↔ week 5 navigation works
- [ ] Leader–follower is described accurately (one arm moves the other)
- [ ] Customer research reads playful/vague, not concrete
- [ ] No LinkedIn file unless separately requested

## Non-goals

- Changing series CSS or site chrome
- Rewriting prior weeks beyond nav links
- Committing implementation until the user asks (spec commit only at this stage)
