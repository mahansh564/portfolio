# LinkedIn — Week 1 (no display, no problem)

Posted alongside: `blog/summer-robotics-week-1.html` ("no display, no problem")

---

my robot did nothing impressive this week. good.

The plan was a moving arm. Reality was cables, a headless Jetson, and a camera feed that refused to show up over SSH.

Then I found the fun demo was running its vision model on the CPU, inside the control loop. The arm lurched once every ~10 seconds, hopelessly behind a pink cup.

So I moved the model off the control thread. Suddenly it tracked. Two orders of magnitude faster, same arm, same code.

Lesson: reference demos are written to be read, not to hold a real-time deadline.

Rusty, but the fresh eyes are still earning their keep.

Full writeup in comments 🤖

---

## Voice notes

- Opener: "my robot did nothing impressive this week. good."; shorter overall.
- Results kept vague on purpose ("two orders of magnitude") — granular stats live in the blog.
- Honest builder framing + the "fresh eyes" callback from week 0.
- One emoji, "in comments" CTA for the blog link.
