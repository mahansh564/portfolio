# Summer Robotics Week 5 Blog Post Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the week 5 Summer Robotics Challenge build-log post (“ditch the headset”) and wire it into the collection, series nav, blog index, and homepage writing list.

**Architecture:** Static HTML post cloned from the week 4 shell. Body follows the approved control-story arc. Listing pages get a new top card; week 4 gains a next-week nav link. No CSS or site-chrome changes.

**Tech Stack:** Static HTML, existing `styles.css`, schema.org JSON-LD (BlogPosting). Voice pass via humanize skill against weeks 1–4.

**Spec:** `docs/superpowers/specs/2026-07-28-summer-robotics-week-5-design.md`

## Global Constraints

- Title: **week 5: ditch the headset** (`<h1>`: `ditch the headset`)
- Date: **28 jul 2026** / `2026-07-28`
- Leader–follower = physically move one arm; the other mirrors (not VR, not a separate remote)
- No command dumps, SDK names, or tuning knobs
- Customer research: abstract / funky; no names, no pitch
- No LinkedIn file unless separately requested
- Match weeks 1–4 voice; humanize before done
- Do not commit implementation until the user asks (unless they say otherwise during execution)

---

## File structure

| File | Responsibility |
|------|----------------|
| `blog/summer-robotics-week-5.html` | New post (head, body, nav, footer) |
| `blog/summer-robotics-week-4.html` | Add next-week nav → week 5 |
| `blog/collections/summer-robotics-challenge.html` | Week 5 card at top of list |
| `blog.html` | Week 5 card at top of summer robotics list (established pattern; needed for discoverability) |
| `index.html` | Week 5 card at top of writing list (same pattern) |

---

### Task 1: Create week 5 post HTML

**Files:**
- Create: `blog/summer-robotics-week-5.html`
- Reference: `blog/summer-robotics-week-4.html` (shell + voice)
- Reference: `docs/superpowers/specs/2026-07-28-summer-robotics-week-5-design.md`

**Interfaces:**
- Consumes: week 4 HTML structure (classes, meta pattern, series-note, footer)
- Produces: `blog/summer-robotics-week-5.html` with prev nav → `summer-robotics-week-4.html`

- [ ] **Step 1: Write the full post file**

Create `blog/summer-robotics-week-5.html` with this content (adapt only if a humanize pass in Task 4 changes wording; structure must stay):

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Week 5: Ditch the Headset | Anshul Mahajan</title>
    <meta
      name="description"
      content="Week 5 of the Summer Robotics Challenge: ditch shaky VR teleop for leader–follower, get go-to-A5 working, keep training grasp, and talk to people off the record."
    />
    <meta name="author" content="Anshul Mahajan" />
    <meta name="robots" content="index, follow" />
    <link
      rel="canonical"
      href="https://anshulmaha.com/blog/summer-robotics-week-5"
    />

    <meta property="og:type" content="article" />
    <meta
      property="og:url"
      content="https://anshulmaha.com/blog/summer-robotics-week-5"
    />
    <meta
      property="og:title"
      content="Week 5: Ditch the Headset | Anshul Mahajan"
    />
    <meta
      property="og:description"
      content="Week 5: leader–follower instead of VR, go to A5 works, grasp training in progress, quiet conversations I am not ready to name."
    />
    <meta property="article:published_time" content="2026-07-28" />
    <meta property="article:author" content="Anshul Mahajan" />

    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"
      rel="stylesheet"
    />
    <link rel="icon" href="../favicon.ico" />
    <link rel="stylesheet" href="../styles.css" />

    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "Week 5: Ditch the Headset",
        "author": {
          "@type": "Person",
          "name": "Anshul Mahajan",
          "url": "https://anshulmaha.com"
        },
        "datePublished": "2026-07-28",
        "description": "Week 5 of the Summer Robotics Challenge: ditch shaky VR teleop for leader–follower, get go-to-A5 working, keep training grasp, and talk to people off the record.",
        "url": "https://anshulmaha.com/blog/summer-robotics-week-5",
        "isPartOf": {
          "@type": "CollectionPage",
          "name": "Summer Robotics Challenge",
          "url": "https://anshulmaha.com/blog/collections/summer-robotics-challenge"
        }
      }
    </script>
  </head>
  <body>
    <div class="container">
      <a href="collections/summer-robotics-challenge.html" class="back-link"
        >← summer robotics challenge</a
      >

      <header class="article-header">
        <p class="collection-label">
          <a href="collections/summer-robotics-challenge.html"
            >summer robotics challenge</a
          >
          · week 5
        </p>
        <h1>ditch the headset</h1>
        <div class="post-meta">
          <span class="post-date">28 jul 2026</span>
          <span class="post-reading-time">5 min read</span>
          <span class="tag">robotics</span>
          <span class="tag">week 5</span>
        </div>
      </header>

      <aside class="series-note">
        Part of my
        <a href="collections/summer-robotics-challenge.html"
          >Summer Robotics Challenge</a
        >
        build log: twelve weeks building embodied AI on the XLerobot, hosted by
        <a
          href="https://www.roboticsnation.org/"
          target="_blank"
          rel="noopener noreferrer"
          >Robotics Nation</a
        >.
      </aside>

      <article class="article">
        <p>
          Week 4 ended with a board I could finally trust and an arm I still
          could not. VR teleop followed me around the room, but the trajectories
          still shook like I was drawing with cold hands. I spent another stretch
          trying to smooth the Quest path. Then I stopped.
        </p>

        <p>
          The headset was not the bottleneck I wanted it to be. It was a
          distraction with a battery.
        </p>

        <h2>follow the other arm</h2>

        <p>
          I switched to leader–follower. Plain version: I have two arms. I grab
          one and move it by hand. The other copies. No headset theater, no
          floating controllers, no fighting latency between my wrist and a
          virtual one.
        </p>

        <p>
          It feels almost rude how obvious it is once you do it. The leader is
          just a physical joystick made of motors. The follower is the one that
          has to do the chess work later. I move the first. The second keeps up.
        </p>

        <h2>go to a5</h2>

        <p>
          The proof this week was boring on purpose. Tell the stack to go to A5.
          Watch the arm actually go there.
        </p>

        <p>
          That sentence would have been a joke two weeks ago. Perception was
          lying, teleop was drunk, and square names were decoration. Now the
          board localization from week 4 and a follower that takes orders can
          meet in the middle: a named square becomes a place in space, and the
          arm shows up.
        </p>

        <p>
          It is not a full pick yet. It is not a clean place. It is the first
          time “go there” stopped being aspirational.
        </p>

        <h2>grasp, almost</h2>

        <p>
          In parallel I kept training the grasp. Closer. Not clean. The kind of
          almost that makes you record one more episode instead of declaring
          victory on LinkedIn.
        </p>

        <p>
          So the week has a working go-to and a grasp that still argues. Fine.
          I would rather have one reliable motion primitive than a highlight
          reel of near-misses.
        </p>

        <h2>side channel</h2>

        <p>
          Also this week: conversations. The fuzzy kind. People who might care
          about what this becomes when it is not a chess demo on a lab bench.
          I am not unpacking that here. Beans stay in the can. Call it market
          sniffing with the windows cracked and the lights off.
        </p>

        <p>
          Building in public does not mean narrating every hallway chat. Some
          threads get a fog machine until they earn a proper sentence.
        </p>

        <h2>what I took from it</h2>

        <p>
          Week 4 was about seeing in millimeters. Week 5 was about admitting the
          Quest was making motion harder than it needed to be. Leader–follower
          gave me a path that does not shake just because my neck got tired.
        </p>

        <p>
          The arm can take a square name and go. Grasp is still in the gym.
          Somewhere off this page, the summer is not only a robot problem.
        </p>

        <p>
          Next: make the grasp boring, string go-to into pick-and-place, and
          keep the fog where it belongs until there is something worth naming.
        </p>

        <nav class="week-nav" aria-label="Series navigation">
          <a href="summer-robotics-week-4.html" class="week-nav-link week-nav-prev"
            >← week 4</a
          >
        </nav>
      </article>

      <footer class="article-footer">
        <p>
          <a href="collections/summer-robotics-challenge.html"
            >more from this series</a
          >
          ·
          <a href="mailto:mahajan.anshul04@gmail.com">email me</a>
        </p>
      </footer>
    </div>
  </body>
</html>
```

- [ ] **Step 2: Smoke-check the file exists and key strings are present**

Run:

```bash
test -f blog/summer-robotics-week-5.html && \
  rg -n "ditch the headset|leader–follower|go to A5|28 jul 2026|summer-robotics-week-4" blog/summer-robotics-week-5.html
```

Expected: file exists; matches for title, leader–follower, go to A5 (or `go to a5` in heading), date, and prev link to week 4.

- [ ] **Step 3: Commit (only if user asked to commit; otherwise skip)**

```bash
git add blog/summer-robotics-week-5.html
git commit -m "$(cat <<'EOF'
Add Summer Robotics week 5 blog post.

EOF
)"
```

---

### Task 2: Wire series navigation (week 4 ↔ week 5)

**Files:**
- Modify: `blog/summer-robotics-week-4.html` (nav block near end of article)
- Modify: `blog/summer-robotics-week-5.html` only if Task 1 omitted prev link (should already have it)

**Interfaces:**
- Consumes: week 5 file from Task 1
- Produces: bidirectional week nav between week 4 and week 5

- [ ] **Step 1: Add next link on week 4**

Replace the week 4 nav block:

```html
        <nav class="week-nav" aria-label="Series navigation">
          <a href="summer-robotics-week-3.html" class="week-nav-link week-nav-prev"
            >← week 3</a
          >
        </nav>
```

with:

```html
        <nav class="week-nav" aria-label="Series navigation">
          <a href="summer-robotics-week-3.html" class="week-nav-link week-nav-prev"
            >← week 3</a
          >
          <a href="summer-robotics-week-5.html" class="week-nav-link week-nav-next"
            >week 5 →</a
          >
        </nav>
```

Keep the existing Greece note paragraph under the nav unchanged.

- [ ] **Step 2: Verify both directions**

Run:

```bash
rg -n "summer-robotics-week-5|week-nav-next" blog/summer-robotics-week-4.html
rg -n "summer-robotics-week-4|week-nav-prev" blog/summer-robotics-week-5.html
```

Expected: week 4 has `week-nav-next` → week 5; week 5 has `week-nav-prev` → week 4.

- [ ] **Step 3: Commit (only if user asked)**

```bash
git add blog/summer-robotics-week-4.html blog/summer-robotics-week-5.html
git commit -m "$(cat <<'EOF'
Link week 4 and week 5 series navigation.

EOF
)"
```

---

### Task 3: Update listing pages

**Files:**
- Modify: `blog/collections/summer-robotics-challenge.html` (insert card after `<div class="blog-list">`)
- Modify: `blog.html` (insert card at top of summer robotics `blog-list`)
- Modify: `index.html` (insert card at top of writing `blog-list`)

**Interfaces:**
- Consumes: week 5 title/date/excerpt from Task 1
- Produces: week 5 discoverable from collection, `/blog`, and homepage

- [ ] **Step 1: Collection card**

In `blog/collections/summer-robotics-challenge.html`, insert this as the first child of `<div class="blog-list">` (before the week 4 card):

```html
        <article class="blog-card">
          <a href="../summer-robotics-week-5.html" class="blog-card-title"
            >week 5: ditch the headset</a
          >
          <p class="blog-card-excerpt">
            vr teleop still shook, so i swapped to leader–follower. “go to a5”
            works. grasp training in parallel. also talking to people i’m not
            ready to name yet.
          </p>
          <div class="post-meta">
            <span class="post-date">28 jul 2026</span>
            <span class="post-reading-time">5 min read</span>
            <span class="tag">week 5</span>
          </div>
        </article>
```

- [ ] **Step 2: `blog.html` card**

In `blog.html`, insert as the first card inside the summer robotics collection `blog-list`:

```html
          <article class="blog-card">
            <a href="blog/summer-robotics-week-5.html" class="blog-card-title"
              >week 5 — ditch the headset</a
            >
            <p class="blog-card-excerpt">
              vr teleop still shook, so i swapped to leader–follower. “go to
              a5” works. grasp training in parallel. also talking to people i’m
              not ready to name yet.
            </p>
            <div class="post-meta">
              <span class="post-date">28 jul 2026</span>
              <span class="post-reading-time">5 min read</span>
              <span class="tag">week 5</span>
            </div>
          </article>
```

- [ ] **Step 3: `index.html` card**

In `index.html`, insert as the first card under `<h2>writing</h2>` / `.blog-list`:

```html
        <article class="blog-card">
          <a href="blog/summer-robotics-week-5.html" class="blog-card-title"
            >week 5 — ditch the headset</a
          >
          <p class="blog-card-excerpt">
            ditched the quest for leader–follower, got go-to-a5 working, and
            kept a few conversations off the record — week five of the build
            log.
          </p>
          <div class="post-meta">
            <span class="post-date">28 jul 2026</span>
            <span class="tag">robotics</span>
          </div>
        </article>
```

- [ ] **Step 4: Verify listings**

Run:

```bash
rg -n "summer-robotics-week-5|ditch the headset" \
  blog/collections/summer-robotics-challenge.html blog.html index.html
```

Expected: each file has a week 5 link and title; collection/blog excerpts mention leader–follower / go to a5 / people not ready to name.

- [ ] **Step 5: Commit (only if user asked)**

```bash
git add blog/collections/summer-robotics-challenge.html blog.html index.html
git commit -m "$(cat <<'EOF'
List week 5 on collection, blog, and homepage.

EOF
)"
```

---

### Task 4: Humanize pass + final verification

**Files:**
- Modify: `blog/summer-robotics-week-5.html` (prose only, if needed)
- Optionally tweak excerpts in listing files if wording changes

**Interfaces:**
- Consumes: draft from Tasks 1–3
- Produces: voice-matched final copy

- [ ] **Step 1: Humanize the article body**

Read `blog/summer-robotics-week-4.html` (and optionally week 2) as voice samples. Apply the humanize skill to the week 5 `<article>` prose:

- Kill AI tells (rule-of-three stacks, “It’s not X, it’s Y”, promotional fog, em-dash spam, “delve/landscape/robust”)
- Keep every beat from the spec arc
- Keep leader–follower explanation accurate (one arm moves; other copies)
- Keep customer section vague

- [ ] **Step 2: Open locally and click through**

Run:

```bash
open blog/summer-robotics-week-5.html
```

Manually confirm:

1. Styles load (`../styles.css`)
2. Back link → collection
3. Prev nav → week 4
4. From week 4, next nav → week 5
5. Collection / blog / index cards link to week 5

- [ ] **Step 3: Spec checklist**

Confirm against `docs/superpowers/specs/2026-07-28-summer-robotics-week-5-design.md` success criteria:

- [ ] Week 5 page matches prior style
- [ ] Collection lists week 5 first with correct link/date/excerpt/tag
- [ ] Week 4 ↔ week 5 navigation works
- [ ] Leader–follower described accurately
- [ ] Customer research playful/vague
- [ ] No LinkedIn file created

- [ ] **Step 4: Commit all remaining changes (only if user asked)**

```bash
git add blog/summer-robotics-week-5.html blog/summer-robotics-week-4.html \
  blog/collections/summer-robotics-challenge.html blog.html index.html
git commit -m "$(cat <<'EOF'
Ship Summer Robotics week 5 blog post and listings.

EOF
)"
```

---

## Spec coverage (self-review)

| Spec requirement | Task |
|------------------|------|
| New `blog/summer-robotics-week-5.html` | Task 1 |
| Title / date / metadata / JSON-LD | Task 1 |
| Control-story arc + voice rules | Task 1 + Task 4 |
| Leader–follower accuracy | Task 1 + Task 4 |
| Vague customer aside | Task 1 + Task 4 |
| Collection card | Task 3 |
| Week 4 ↔ week 5 nav | Task 2 |
| No LinkedIn | Global + Task 4 checklist |
| blog.html / index.html listings | Task 3 (established pattern beyond narrow spec; required for same discoverability as prior weeks) |

## Placeholder scan

No TBD/TODO steps. Full HTML and card markup included. Commits gated on user request.
