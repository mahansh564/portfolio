# LinkedIn — Week 4 (seeing in millimeters)

Posted alongside: `blog/summer-robotics-week-4.html` ("seeing in millimeters")

**Status: draft**

---

my robot was hallucinating.

for weeks it saw chess pieces that weren't there. nudge the board a few pixels and it would put phantom pawns on empty squares. i kept trying to fix it by getting smarter about color and shadows. wrong approach.

the real fix was to stop caring what the board looks like and start measuring how tall things are. i put a depth camera overhead. a piece sticks up off the board, an empty square doesn't. depth doesn't care that a black rook sits on a dark square.

live mid-game position now: 64 out of 64 squares read right, no reference photo, no shadow-guessing. the whole "the board moved while i cleared it" class of bugs just disappeared.

(also skipped last week, was abroad, and came back to a gripper that still didn't fit. reprinted it, fits now. boring win, i'll take it.)

perception is finally reliable. motion is not. VR teleop still shakes when i try to record pick-and-place demos, so next week is one grasp i can actually trust.

Week 4 of the summer robotics hosted by Robotics Nation. Blog in comments ♟️

---

## Voice notes

- Opener: "my robot was hallucinating." — bold three-word hook, then unpack the phantom-pieces problem.
- Lead with the depth insight (measure height, not appearance) and the 64/64 payoff. No calibration archaeology, no device/jargon detail.
- Vacation skip demoted to a parenthetical instead of the opener.
- Closer: `Week X of the summer robotics hosted by Robotics Nation. Blog in comments ♟️`
