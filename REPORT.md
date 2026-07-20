# XLerobot Chess — Research Log

_Started: 2026-06-25_

Running notes on what works, what fails, and what we kept vs. deferred from [PLAN.md](./PLAN.md).

## Status

| Milestone | Status | Notes |
|-----------|--------|-------|
| M0 Scan pose sees full board | **pass (caveat)** | All 64 squares + A–H/1–8 labels in frame; back rank foreshortened |
| M1 50+ move demos | pending | |
| M2 ACT ≥70% center squares | pending | |
| M3 FEN + human move detect | pending | |
| M4 10 engine moves in a row | pending | |
| M5 Captures / wider squares | pending | |

## Work order (logical sequence — no fixed dates)

### Phase 0 — Hardware & scan pose (M0)

- [x] 0.1 `config.py` — camera path, robot id, joint safety clamp
- [x] 0.2 `scan_pose.py` — save / load / apply scan pose
- [x] 0.3 `setup_scan_pose.py` — teleop left arm, save pose + frame
- [x] 0.4 `verify_scan_pose.py` — return to pose, recapture frame
- [x] 0.5 **Bench:** run setup, confirm all 64 squares visible in `calibration/scan_frame.jpg`
- [x] 0.6 Log M0 pass/fail below

### Phase 1 — Demos (M1)

- [ ] `record_chess_demo.py` fork from VR recording script
- [ ] Record pick / place / e2→e4 episodes
- [ ] Dataset viz looks clean

### Phase 2 — ACT (M2)

- [ ] Train ACT on chess move dataset
- [ ] Policy eval mode; ≥70% on held-out center squares

### Phase 3 — Board perception (M3)

- [ ] Homography calibration + FEN from scan frame
- [ ] Detect one human move reliably

### Phase 4 — Game loop (M4)

- [ ] Stockfish + turn loop; 10 engine moves without illegal state

### Phase 5 — Hardening (M5, optional)

- [ ] Captures, wider squares, YOLO if FEN fails

## Log

### 2026-06-27 — Phase 0 prep

Added `chess_robot.py` connect flow aligned with `examples/7_xlerobot_teleop_joycon.py`:
restore cal file (ENTER), import from servos, or manual cal with clearer instructions.
Use `--calibrate` if min/max error; motors must be moved through full range while torque is off.

### 2026-06-28 — M0 scan pose: PASS (with caveat)

Saved `calibration/scan_pose.json` (left arm, 6 joints) and `verify_scan_pose.py` returned the
observer arm to it and recaptured `calibration/scan_frame.jpg` (artifacts in sync within ~1s).

- **Gate met:** full board in one frame — all 8 ranks (1–8) and files (A–H) visible, printed
  labels readable, starting position complete. M0 satisfied for a 4-corner homography.
- **Caveat:** view is oblique (wrist cam angled down from the left), so the **back rank (7–8) is
  foreshortened** — pieces there are smaller / more occluded than the front. Expect the per-square
  classifier to be weakest on ranks 7–8 in Phase 3. Board also sits right-of-center with wasted
  frame on the right; a flatter/more-centered pose would add pixels-on-board but isn't required.
- **Pose note:** `shoulder_pan` and `gripper` saved at exactly `100.0` — likely saturated at a
  joint/cal limit, so there's no headroom to pan further left from this pose.
- **Next if Phase 3 FEN struggles on back rank:** re-run `setup_scan_pose.py` with a flatter wrist
  tilt, or add the deferred fixed table cam (PLAN.md Phase 5 trigger).

### 2026-06-28 — Phase 3: homography PASS, texture-std occupancy FAILED → pivot to reference subtraction

Calibrated the board homography (`board/calibrate_board.py`, Tk corner picker; cv2 highgui is
unavailable — the env ships headless OpenCV, `GUI: NONE`). 4 corners → `board_calibration.json`;
`board_warp_debug.jpg` confirms a **square, full 8×8 top-down warp** with correct orientation
(a8 top-left, white on ranks 1–2). Homography calibration: good.

The **v1 occupancy heuristic (grayscale std of a center crop) does not work on this board.**
Measured center-crop std over the 32 known-empty vs 32 known-occupied start squares:

| group | std min | std median | std max |
|-------|---------|-----------|---------|
| empty (ranks 3–6) | 0.1 | **73.4** | 91.0 |
| occupied (ranks 1,2,7,8) | 22.1 | **57.0** | 99.1 |

Empty squares are **noisier than occupied** ones — they contain printed grid lines, rank/file
labels, and high-contrast checkerboard prints, while a piece surface is fairly uniform. The
feature is inverted and inseparable: at every threshold ~28/32 empty squares read as pieces. No
amount of `--empty-std-thresh` tuning recovers it.

**Pivot:** the observer arm is frozen → camera is fixed → use **empty-board reference
subtraction**. Capture the board once with no pieces, store per-cell reference; occupancy =
per-cell difference from the empty reference (printed pattern cancels, only pieces remain). Color
(w/b) by brightness once occupancy is reliable. Requires a one-time empty-board capture from scan
pose. (See `board/capture_empty_board.py` + reference-diff classifier in `fen_from_image.py`.)

### 2026-06-28 — Phase 3: reference subtraction works in the middle; edges fail (alignment + oblique geometry)

Captured `empty_board.jpg` and switched occupancy to per-cell diff vs the empty reference. Empty
middle ranks (3–6) now read correctly. But the start position still misreads. Added a `--debug` /
`--debug-dump` to `fen_from_image.py` (per-cell diff + brightness grids, warped live/empty, JET
diff heatmap with the 8×8 grid drawn). Real numbers on the bench frame:

- start-pos diff: **occupied** min/med/max = 7.7 / 63.2 / 146.2 ; **empty** = 0.0 / 9.6 / 45.9.
  Good separation in the bulk, but the tails overlap → no single threshold works.
- **h-file column false-positive** (empty cells h3–h6 ≈ 30–46, a-file ≈ 6–9): the warp's right
  edge samples **past the board** — the right corner clicks (h8/h1) were placed wide, so the
  h-column includes off-board table/arm.
- **Rank-1 white pieces missed** (a1=12.5, b1=7.7, h1=8.8): the oblique view projects near-piece
  *bodies* down past the board's bottom edge, so the footprint center-crop catches bare board. The
  heatmap confirms far black pieces smear up off the top edge too. This is the M0 oblique caveat.
- **Confound:** the diffed frames were from two different sessions (`scan_frame.jpg` 14:46 vs
  `empty_board.jpg` 15:30) — reference and live must come from one uninterrupted setup.

**Fix order:** (1) capture empty + populated frames back-to-back without moving anything;
(2) re-calibrate corners precisely (clip the h-file to the true board edge); (3) if rank 1 still
fails, the scan pose is too oblique — flatten it toward top-down or add the deferred fixed overhead
cam (PLAN Phase 5 trigger).

### 2026-06-28 — Phase 3: starting FEN CORRECT (camera re-angle + edge-diff occupancy + color split)

After re-angling the camera and re-calibrating, the alignment/geometry problems were gone (empty
ranks clean, front rank visible). The debug grids then exposed the *real* remaining issue, NOT a
bug: per-cell diff magnitudes alternated in a **checkerboard** — a **black piece on a dark square
barely changes mean brightness** (h8 diff 10 < empty-square noise 13), so brightness-diff occupancy
missed 6/32 back-rank pieces and no threshold could separate them.

Fix (cheap, no model — answers "why not just YOLO"): swap occupancy from mean-brightness diff to
**edge-content diff** (Sobel gradient-magnitude difference vs empty reference). Pieces add
silhouettes/highlights even on same-colour squares. Result on the bench frame:

- occupied edge-diff min/med/max = 4.5 / 21.9 / 43.7 ; empty = 0.0 / 2.3 / 3.7 → **0/64 misread**
  at thresh 4.0 (was 6/32 missed with brightness diff).
- One residual **color** error: d1 brightness 108 < old split 110 → white tagged black. Black
  pieces read 21–52, white 108–193, so recentered `piece_value_split` 110 → **80** (clean margin).

`fen_from_image.py --image calibration/start_frame.jpg` now prints the correct starting FEN
(`rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR`). **First half of M3 done.** Remaining: detect a human
move reliably (FEN-diff via detect_move.py). YOLO stays deferred — homography + edge-diff suffices.

### 2026-06-28 — Phase 3: move-detection harness + python-chess installed

Installed `python-chess` (1.11.2) into the **`lerobot` conda env** (not the uv `.venv`); that env
is where the board pipeline runs (has cv2 + lerobot too). Added `board/test_move_detection.py` — a
scan→move→scan harness with three modes: live (prompts), offline (two saved frames), and
`--simulate UCI` (real BEFORE scan + synthetic AFTER from a known move, asserts recovery — fully
hardware-free). Fixed a latent bug in `detect_move.py` (missing `sys.path` insert → couldn't import
the `board` package when run as a script).

Validated against the real `start_frame.jpg`:
- `detect_move.py` synthetic self-test → e2e4 OK.
- `test_move_detection.py --simulate e2e4` → vision read start correctly, recovered e2e4.
- `--simulate g1f3` → recovered Nf3.

Still needs a real on-bench two-photo run (actually move a pawn, capture after) to close M3 — the
only step `--simulate` can't cover is the AFTER-frame vision read of a physically moved piece.

### 2026-06-28 — Phase 3: occupancy hardened against small empty-vs-live misalignment

A re-captured calibration set broke occupancy: `empty_board.jpg` (18:17) and the live frame (18:14)
were taken 3 min apart, the board nudged slightly, and thin residual edges along high-contrast
square borders pushed 4 empty cells over the threshold (empty edge-diff max 3.7 → 13.8, overlapping
a low-contrast piece at 6.5 → no separating threshold).

Tested fixes offline on that misaligned pair: global phase-correlation alignment barely helped
(shift ~1 px, low confidence) — the residual isn't a clean translation. **Morphological opening
fixed it cleanly:** binarize the per-pixel gradient diff (>30), `MORPH_OPEN` 3×3 to delete 1–2 px
border lines, score = % surviving pixels. A piece is a solid blob that survives; a misalignment line
does not. Result on the previously-failing pair: empty 0.0–1.1, occupied 1.6–37.3 → **0/32 misread,
0/32 missed**, correct starting FEN. `occupancy_score` now returns this area-% (threshold renamed
`occupied_area_pct`, default 1.3). detect_move self-test + `--simulate e2e4` on the real frame still
pass. Don't skip clean capture discipline, but a 1–2 px nudge no longer breaks it.

### 2026-06-28 — Phase 3: soft start-gate + seed from known FEN (M3 perception accepted)

Live scan was clean on alignment (empty cells ~0) but missed 2 pieces — b8 (black on a dark square,
low contrast) and **c1 (white bishop on a DARK square — HIGH contrast, still missed** because a
bright uniform piece has weak interior edges in the center crop). occupied min (0.3) sat below the
noisiest empty (0.4): no threshold separates them. This is the floor of difference-from-empty
perception on worst-case pieces; chasing it further is overfitting noise.

Resolution (architecturally correct): **vision reads *changes*, not the static start.** The game
always begins from the standard position, so seed the tracked `python-chess` board from START_FEN;
a square misread the same way in every scan cancels out of the before→after diff, so these misses
are harmless for move detection. Implemented `matches_start_within_tolerance`: **tolerate misses
(piece→empty, up to 4), reject hard errors (wrong colour, or phantom = empty→piece)** — a phantom
would corrupt the diff. NB: classification is colour/orientation-independent — an earlier
"tolerate same-colour pieces" idea was wrong (c1 disproved it). `scan_board.py`/`fen_from_image.py`
now report via `report_start_status`; `chess_board_from_state` seeds start under the soft check.
`scan_board.py` gained `--debug`/`--occupied-area-pct`. Verified: exact/missed/phantom/wrong-colour/
too-many unit cases all behave; real frame still exact; `--simulate e2e4` still recovers the move.

**M3 perception accepted.** Remaining to close M3: one on-bench scan→move→scan run proving a real
played move is detected (the AFTER-frame read of a physically moved piece — only `--simulate` gap).

### 2026-06-28 — Phase 4: game loop scaffolded (step5_play)

Scaffolded `step5_play/{chess_engine,game_loop}.py` (M3 closed). Followed the repo's
`stepN_` dir convention rather than PLAN's older `play/` name.

- `chess_engine.py`: `ChessEngine` over `python-chess`'s UCI driver
  (`chess.engine.SimpleEngine.popen_uci`) — no `stockfish` pip pkg needed, just the
  binary. Reduced `Skill Level` (default 3) + per-move think-time. Binary resolves via
  `STOCKFISH_PATH` → `which` → common paths; missing binary raises `EngineUnavailable`
  with an apt hint. **Stockfish binary is NOT installed yet** (apt candidate 14.1) —
  `sudo apt install stockfish` is the remaining dep to actually run the engine.
- `game_loop.py`: alternate-turn orchestrator, one script, `--mode {sim,live}`.
  Tracked `python-chess` Board seeded from start (vision reports *changes* only, per
  the M3 design). Backends: `SimBackend` (occupancy from the tracked board, human moves
  typed as UCI — fully hardware-free) and `CameraBackend` (observer-arm scan + step3
  perception + `detect_move` for human moves, and re-scan verification of the robot's
  own move). Players: `ManualPlayer` (human moves the robot's piece by hand — exercises
  the *full* loop before ACT exists), `PolicyPlayer` (Phase-2 ACT seam, wraps
  step4_record `PolicyActionSource`, NotImplementedError today), `NullPlayer` (sim).
  Special moves (castling/en-passant/under-promotion): v1 defers *robot execution*
  (`_warn_if_special`); *detection* of human special moves works via python-chess.

Validated hardware-free: engine + game_loop both degrade cleanly to the install hint
with no binary; driving `GameLoop` with a stub engine in sim ran full turn-taking,
SAN/UCI printing, a capture (Nxh7), human UCI parsing, and resign. **To close M4:**
install Stockfish, then `--mode live --player manual` for 10 engine moves (closes M4
independently of ACT); `--player policy` waits on Phase 2.

### 2026-06-28 — Phase 1: VR teleop wired via telegrip (input + IK only)

Wired real VR teleop into `step4_record` using the external **telegrip** package
(`~/telegrip`, editable install in the `lerobot` conda env) instead of this repo's
`examples/8_xlerobot_teleop_vr.py` (user's choice). New `step4_record/telegrip_teleop.py`
(`TelegripActionSource`), selected by `record_chess_demo.py --teleop telegrip` (default;
`hold` keeps the old still-arm stub). `PolicyActionSource` (eval) is still the Phase-2 seam.

Key architectural constraint: telegrip's `RobotInterface` opens the SO100 serial ports
itself, but `ChessXLerobot` already owns both `/dev/ttyACM*` (swapped dual-arm buses) and a
port can't be opened twice. So telegrip runs with **`enable_robot=False`** — it boots the VR
WebSocket server + headless pybullet IK and integrates controller motion into
`control_loop.robot_interface.right_arm_angles` (6 joints, **degrees**) but never touches
hardware. Our record loop reads that array each tick and commands the real right arm through
`ChessXLerobot` (while holding the observer arm at scan pose). telegrip is booted on a
background asyncio thread; readiness = control loop running AND right-arm IK solver present.

Units bridge: XLerobot arms are `RANGE_M100_100` / gripper `RANGE_0_100` (`use_degrees=False`,
to keep the saved normalized scan pose valid); telegrip is degrees. Convert via the robot's
OWN calibration (per-joint affine, exact inverse of `MotorsBus._normalize`), seeding telegrip
from the live arm (norm→deg) and commanding from telegrip (deg→norm) through the same map so
absolute-zero offset cancels. Round-trip verified exact; gripper 22.5°→50/100.

Validated hardware-free in the `lerobot` env: headless telegrip boots in-process with
`enable_robot=False`, robot_interface + both IK solvers initialize, FK/`solve_ik` return real
values, seed write/read-back works, clean async shutdown. **Found + fixed a telegrip bug:** the
installed `config.yaml` sets `urdf_path: URDF/SO100/urdf/so100.urdf` (extra `urdf/` segment); the
real file is `URDF/SO100/so100.urdf`. With the wrong path pybullet IK silently fails
(`ik_solvers` stay None → arm never moves). `TelegripActionSource.open()` overrides `urdf_path`
and now asserts the right-arm IK solver exists. **Remaining (needs bench + Quest):** confirm the
units/axis mapping by jogging slowly, then record demos → M1.

### 2026-06-28 — Phase 1: telegrip teleop was shaky → output smoothing + faster IK loop

First on-bench VR teleop was too jittery to grasp pieces. Causes: pybullet IK jitter
frame-to-frame, noisy VR controller pose, and a 20 Hz (telegrip) vs 30 Hz (record loop)
beat — all passed straight to the servos. `max_relative_target=8` (normalized) doesn't
help: it only caps large jumps, not the small ±jitter that causes shake.

Fix in `TelegripActionSource`: (1) EMA-smooth the 5 arm-joint targets in command space
(`filtered += a*(target-filtered)`, default `a=0.35`, tunable via `--smoothing`); gripper
left UNsmoothed so grasp/release stays crisp; EMA seeded from the live arm pose so frame 0
isn't a jump. (2) Lower telegrip `send_interval` 0.05→0.02 (50 Hz IK) for finer integration.
Offline sim: per-tick command-step std 2.37→0.67 (3.5× smoother), ~1 unit steady-state lag.
On bench, drop `--smoothing` toward 0.2 if still jittery, raise toward 0.6 if too laggy.

### 2026-06-28 — Phase 1: telegrip laggy + wrist_flex stuck → fixed wrong grip origin

After smoothing, teleop was still laggy and wrist_flex wouldn't pitch down. Root cause: telegrip
captures its control **origin** from `right_arm_angles` at the instant the grip is squeezed. We
only seeded once on the first recorded frame, so if the operator gripped during the "press ENTER"
setup wait, telegrip rooted everything at the **zero pose**. That makes the commanded target a huge
offset from the real arm → `max_relative_target=8` forces a slow crawl (= "laggy"), and joints like
wrist_flex never reach their target within the episode (= "won't come down").

Fix: `TelegripActionSource` is now **mode-aware**. While NOT gripping (idle), it continuously
mirrors the live arm pose into telegrip's `right_arm_angles` (norm→deg) and commands the real arm to
hold — so a grip-press always captures origin = real pose. While gripping (POSITION_CONTROL),
telegrip drives and we read/smooth/command as before; the EMA is reset on each release so the first
gripped frame starts from the real pose (no jump). Safe because telegrip only writes
`right_arm_angles` in POSITION_CONTROL, so the idle sync never fights it. Operator must use the
**RIGHT controller's** grip. Verified with a fake telegrip: idle holds + syncs; gripped tracks
wrist_flex through its range.

If wrist_flex is STILL one-sided after this, the remaining suspect is telegrip's URDF wrist joint
limits vs our calibration zero (a per-joint constant offset) — needs a quick bench calibration, not
a code change. Lag knob: raise `--smoothing` toward 0.5–0.6 (less lag), lower toward 0.2 (smoother).

### 2026-06-28 — Phase 1: Feetech "no status packet" aborted recording → retries + skip-frame

A dropped Feetech response ("Failed to sync read 'Present_Position' on ids [1..6] after 1 tries.
There is no status packet!") crashed the whole record session. Two software hardenings:
`chess_robot` Present_Position sync reads now use `num_retry=3` (the error's "1 tries" = the old
num_retry=0), and the record loop catches per-frame `ConnectionError`/`RuntimeError`, skips that
frame, and aborts only after `MAX_CONSEC_COMM_FAILURES=10` in a row. Note the loop reads present
position twice per tick (get_observation + send_action's max_relative_target clamp), so bus load is
high at 30 fps — `--fps 20` reduces it. Retries mask but don't cure a physical fault: if it persists,
check the affected arm's daisy-chain cable, power (brownout under load), and that no other process
holds the port.

### 2026-06-30 — Phase 3: occupancy retuned for the overhead HEAD cam

Switched the board camera from the side wrist cam to the overhead head cam (`BOARD_CAMERA =
HEAD_CAMERA`, wider top-down view; far rank slightly cut off). Occupancy via `scan_board.py`
broke: from the new viewpoint the gradient-only diff against the empty board could not see the
FAR black rank. A dark piece on a dark square adds ~no brightness and, seen obliquely, is hollow
to the gradient (edges only on its silhouette) so it survives morphological opening as a thin ring
— black squares scored ~0–9%, `a8` read 0.0, occupied/empty medians overlapped (10.4 vs 11.3).
Two changes (validated on the calibrated start warp `extra/board_warp_debug.jpg` vs the head-cam
`empty_board.jpg`, both 1280×720):

1. **Occupancy mask = gradient-diff OR brightness-diff** (`_BRIGHT_DIFF_PX = 45`). A dark piece on
   a *light* square (and cream-on-dark) swings brightness hard even with no interior texture, so
   the union fills the silhouette. Empty squares still cancel in the reference and stay ~0.
   Occupied median rose 17 → 86%, empty stayed ~0.
2. **Center crop tightened 0.5 → 0.42** in `_center_crop`. The 50% crop on the outer files (a/h)
   caught the printed border / rank-file label strips + sub-pixel board nudge → empty a-file cells
   read 7–12% (phantom pieces); 42% clears that border noise (empty max 12 → 1.6%).

Default `occupied_area_pct` raised **1.3 → 5.0** everywhere (`fen_from_image`, `scan_board`,
`game_loop`). Result on the start position: 0 false positives, all colours correct, only `a7`/`b8`
(dark-on-dark far corner) read empty — tolerated misses that cancel in the before→after move-diff.
Remaining straggler is inherent: dark pieces on dark far-rank squares. Phase-5 lever if it bites
mid-game = learned/YOLO per-square classifier (see `classify_cell` TODO).

**Follow-up (same day), validated on a real live scan `calibration/scan_live.jpg`:** the first live
frame still threw 2 HARD errors. Two more fixes:

3. **Colour split 80 → 105** (`classify_cell_ref` / `--piece-value-split`). A black rook with corner
   glare read median brightness 88 and was called white. Black pieces span ~21–88, cream pieces
   ~121–204 here, so 105 sits in the gap.
4. **Open kernel 3×3 → 5×5** (`_OPEN_KERNEL`). A piece in the row nearer the camera leans up across
   the grid line, leaving a silhouette sliver on the empty square behind it (empty `c3` read 12.5%
   from the c2 piece). A 5×5 open erases the 1–2px sliver while solid piece cells survive. Kernel
   must stay ODD — a 4×4 anchor shift spawned its own edge false-positives.

Live result: "Matches START within tolerance", 0 hard errors, only `b8`/`f8`/`h8` (dark far-rank)
read empty (tolerated, cancel in move-diff). Empty-vs-empty board → 0 phantom pieces.

> Footgun: the live pipeline (`WristCamera`) grabs 1280×720, and the calibration + `empty_board.jpg`
> are 1280×720. The saved `scan_frame.jpg`/`start_frame.jpg` are 1920×1080 (from `check_camera.py`)
> — warping those with the 1280-calibrated homography misaligns every cell and yields garbage
> occupancy. Always calibrate, capture-empty, and scan at the SAME resolution.

<!-- Add dated entries as you run experiments -->

### 2026-07-14 — Phase 3: new head central camera (Orbbec Gemini 335) — recalibrated, 64/64

New head central camera: **Orbbec Gemini 335** (RGB-D). It claims 8 `/dev/video*` nodes and
shuffled every device number (old wrist `/dev/video0` and head `/dev/video4` now hit the Orbbec's
depth/IR streams). `config.py` now uses stable `/dev/v4l/by-id/` symlinks; the Orbbec's RGB stream
is `...-video-index0` (YUYV/MJPG up to 1920×1080 — the other indices are Z16 depth / IR, unusable
with cv2). Captures at 1280×720 through the existing `WristCamera` path unchanged.

**Recalibration** (`board_calibration.json`; old one backed up to
`extra/board_calibration_oldwristcam_backup.json`): corner picking by hand was ~15–20px off, which
neither `cornerSubPix` (window too small) nor RANSAC could recover. What worked:
`findChessboardCornersSB` on a (7,3) sub-pattern (the fold seam between ranks 4/5 breaks full 7×7
detection), nearest-intersection identity assignment via a rough homography (cells ~50px, so <25px
rough error is unambiguous), then expand to all 81 intersections with `cornerSubPix` + RANSAC
refit — median residual 0.1–0.5px. Calibrate on the EMPTY board if possible: the full pattern is
visible and the frame doubles as `empty_board.jpg`.

**Classifier changes for the near-overhead view** (`fen_from_image.py`):

1. **Adaptive per-pixel brightness cutoff** (`_BRIGHT_DIFF_MIN_PX=12` floor,
   `_BRIGHT_DIFF_REF_FRAC=0.25` × empty-ref median, replacing fixed `_BRIGHT_DIFF_PX=45`;
   `_GRAD_DIFF_PX` 30 → 20). Overhead, a black piece sits ENTIRELY inside its dark square — no
   light background behind the silhouette — so its brightness diff is ~15–20 levels and the fixed
   45 cutoff missed it outright (b8 scored 0.0%, d8 5.7%). Dark squares (ref median ~45) now get a
   ~12–15 cutoff; light squares (~200) keep a strict ~50.
2. **Center crop back 0.42 → 0.5**: border residue that motivated 0.42 is gone with the sub-pixel
   recalibration, and the wider crop lifts the weakest occupied cell 26.9 → 32.2%.
3. **`occupied_area_pct` default 5.0 → 27.0** (`DEFAULT_OCCUPIED_AREA_PCT` in `fen_from_image`,
   imported by `scan_board` / `game_loop`). With adaptive thresholds, a neighbour's pawn head
   leaning into a cell corner scores up to ~21% (c3/e3 — real piece pixels, no cutoff removes
   them); weakest true piece is 32%. 27 splits the measured gap. A center-coverage gate was tried
   and rejected: leaning far-rank pieces have near-zero center coverage too (d8 = 3.1%).

Result on the bench: start position **64/64 exact** ("Occupancy matches START exactly", FEN
correct) — the old oblique wrist view never got past tolerated dark-far-rank misses. Empty board:
0 phantoms. `test_move_detection --simulate e2e4` on the real frame: recovered. Margin: occupied
min 33.0% vs empty max 21.2% at thresh 27.

> Footgun: the board moved ~3px between the pieces-on calibration and the cleared-board recapture
> (clearing pieces nudges it). Always recalibrate + recapture `empty_board.jpg` in the SAME session
> as the frames you scan, and don't lean on the board.

### 2026-07-15 — Robust perception rebuild: status audit + Layer-B seam wiring closed

Audited the "robust (SOTA-grade) chess board perception" plan (per-frame ArUco/grid/ECC
localization + learned per-square CNN, motivated directly by the 3px footgun above). Found the
bulk of it **already implemented and unit-tested** from an earlier session, just never logged here
and not fully wired together:

- **Layer A** (`grid_calibration.py`, `board_locator.py`'s `aruco+grid → grid → ecc → static`
  ladder, `generate_markers.py`, `register_markers.py`) — code complete, wired into
  `fen_from_image.py` / `scan_board.py` / `game_loop.py` (`--static-calibration` opts back out),
  50 offline tests passing (`test_board_locator.py`, `test_marker_workflow.py`,
  `test_calibration_compatibility.py`, `test_perception_integration.py`). **Not yet active on the
  real board**: `board_calibration.json` is still schema v1 (no `aruco` block) — the markers were
  never printed/stuck/registered. Generated the printable sheet now
  (`calibration/aruco_markers_a4.png`, 30mm markers, 300 DPI A4) — printing, sticking, and running
  `register_markers.py` is a bench task for a person, not something an agent can do.
- **Layer B** (`square_classifier.py`'s SquareNet/CnnSquareClassifier, `collect_squares.py`,
  `train_square_classifier.py`, `eval_square_classifier.py`) — code complete and tested, but
  **completely unwired**: `board_state_from_image` only ever ran the v1 heuristic, `config.py` had
  none of the planned `CLASSIFIER_MODE`/`CNN_CONF_THRESHOLD`/`SQUARE_MODEL_PATH` constants, and
  `detect_move` had no abstention mechanism.

Closed the wiring gap today (two independent subagents, then hand-wired the glue):

1. `config.py`: added `SQUARE_MODEL_PATH`, `CLASSIFIER_MODE = "heuristic"` (default, zero behavior
   change), `CNN_CONF_THRESHOLD = 0.80`.
2. `fen_from_image.board_state_from_image` gained `classifier_mode` (`heuristic`/`cnn`/`ensemble`),
   `cnn_conf_threshold`, and an optional `uncertain_out` mutable-set output param — return type
   stays `dict[str, str | None]` in every mode. `cnn` mode uses the CNN label above the confidence
   threshold, falls back to the heuristic per-cell below it (marking that square in
   `uncertain_out`), and falls back entirely to heuristic (one warning) if the model file / torch
   is unavailable — the expected state right now, since no model has been trained. `ensemble` mode
   is **heuristic-authoritative "shadow" mode**: returns the heuristic answer always, but also runs
   the CNN alongside it and logs every disagreement (crop + CSV row) to
   `step3_board/dataset/disagreements/` — the training-data-mining loop from the plan.
3. `detect_move.detect_move` gained `uncertain: frozenset[str] = frozenset()`: uncertain squares
   can't veto an otherwise-matching move (pass 1 only requires agreement on the non-uncertain diff)
   but still break ties between multiple pass-1 survivors (pass 2) — unless narrowing would zero
   out the candidate set, in which case the wider pass-1 set stands. Zero behavior change when
   `uncertain` is empty (always true while `CLASSIFIER_MODE` is `heuristic`).
4. Wired `step5_play/game_loop.py`'s `CameraBackend`: each `_scan()` now passes a fresh
   `uncertain_out` set into `board_state_from_image` and stashes it as `self._last_uncertain`;
   `read_human_move` / `after_robot_move` forward it into `detect_move(..., uncertain=...)`. In the
   default `heuristic` mode this set is always empty — a documented no-op until `CLASSIFIER_MODE`
   is switched.

Full suite: `conda activate lerobot && python -m pytest step3_board/ -q` → **61 passed** (50
pre-existing + 6 new classifier-seam tests + 5 new abstention tests), no regressions. Rewrote
`step3_board/README.md` to describe both layers, the seam, and the current status instead of the
stale v1-only description.

**Still genuinely pending, all needing bench time** (not code): print
`calibration/aruco_markers_a4.png` at 100% scale, stick the 4 markers, run `register_markers.py`
(closes the "move the board mid-game" acceptance test); collect a real Layer-B dataset via
`collect_squares.py` (empty sweeps + start frames + a couple of replayed games, ≥6 sessions / ≥3
lighting conditions per the plan's target); train + evaluate; run a shadow (`ensemble`) game before
ever flipping `CLASSIFIER_MODE` to `"cnn"`.

### 2026-07-15 — Architecture: retired the observer-arm / scan-pose model (fixed cam + either-arm + rest pose)

The "observer arm (left) holds a scan pose so its wrist camera sees the board" design (PLAN.md
Phase 0, the original architecture) never matched the bench for long: the board camera moved from
the left wrist to the fixed overhead head cam back on 2026-06-30 (see that entry above), which
already made "observer arm" a misnomer — the arm wasn't observing anything anymore, just sitting
still to stay out of frame. Today's change makes the model match reality and documents it as the
new source of truth everywhere (README, step READMEs, PLAN.md superseding note, code):

- **Board reading**: the fixed central head camera (`BOARD_CAMERA`, Orbbec Gemini 335) always
  sees the whole board. Nothing moves to see it — there is no "observer arm" anymore.
- **Either arm plays**: both arms are players; whichever ends up closer to the target square
  executes the move. This pass only *documents* that model — the closer-arm selector is not
  implemented (still a `PolicyPlayer`/ACT seam, same status as before).
- **Rest pose replaces scan pose**: `calibration/rest_pose.json` holds both arms' joint angles,
  clear of the head camera's view. Both arms return here before every scan instead of just the
  left arm returning to a wrist-cam-aiming pose. `robot_io.py` (new, at the exp root, replacing
  `step1_scan_pose/scan_pose.py`) owns `load_rest_pose`/`save_rest_pose`/`move_arms_to_rest_pose`
  plus the renamed `BoardCamera` (was `WristCamera`) and generalized (both-arm) torque/lock
  helpers. `move_arms_to_rest_pose` is a safe warn-and-skip no-op until a rest pose is captured
  via `python robot_io.py --save-rest-pose` — it never drives to guessed joint angles.
- **Deleted** `step1_scan_pose/` and `step2_verify_scan_pose/` (scan-pose finder + verifier —
  meaningless once there's no scan pose to find or verify).
- **Directories renumbered** to match the new 3-step flow: `step3_board` → `step1_board`
  (perception is step 1 now — nothing upstream of it needs a scan pose), `step4_record` →
  `step2_record`, `step5_play` → `step3_play`.
- `chess_robot.py` moved from `step1_scan_pose/` to the exp root (it's shared infra, not part of
  a deleted step).

Verified after the rename: `conda activate lerobot && python -m pytest step1_board/ -q` → **61
passed**, no regressions. `game_loop.py --mode sim` and offline `fen_from_image.py` 64/64 checks
still pass (see Verification in the retire-scanpose-model plan). Out of scope here: implementing
the actual closer-arm selection/execution logic — that's still future ACT work.

### 2026-07-15 — Colour split 105 → 80 (queenside white back rank flipped to black)

First real `game_loop.py --mode live` run surfaced two *separate* issues, isolated one at a time:

1. **Grid-locator drift (mid-game).** With the default per-frame `BoardLocator`, the start scan
   matched exactly, but `corner_shift` grew monotonically (11.8 → 18.5 → 23.4px, `tier=grid
   markers=0`) as pieces filled the middle ranks — grid re-detection only holds "when middle ranks
   clear" (`board_locator.py`). The live warp (drifting grid H) then misaligned against the empty
   reference (static H), leaking piece edges into neighbours: robot `e2e4` diffed as `['e2','e4','e5']`
   and a human turn as `['e6']` → `detect_move` raised on both. **Static calibration H is accurate
   here** (`--static-calibration` warps live + empty identically): `fen_from_image --debug` on
   `board_frame.jpg` → 0/32 errors, so the grid tier was *adding* error, not correcting it. Proper
   fix for board-bump robustness is still the ArUco markers (unprinted); until then
   `--static-calibration` is the more reliable geometry on a fixed board.

2. **Colour split too high (start position).** Under `--static-calibration` the start check then
   failed with HARD errors on `b1/c1/d1` (white read as black; white=13/black=19). A fresh live
   capture reproduced it exactly. Per-cell median brightness on the current **Orbbec head cam**:
   black pieces 22–51, white pieces 102–212, with a left→right lighting gradient dimming the
   queenside white back rank to `b1=103 c1=103 d1=102` — just under the old `piece_value_split=105`.
   Occupancy itself was perfect (0/32; occupied min 39% vs empty max 25%), so this was purely the
   colour decision hugging the bottom of the white cluster.

**Change:** `piece_value_split` default 105 → **80** (new `PIECE_VALUE_SPLIT` constant in
`fen_from_image.py`, used by `classify_cell_ref` and the `--piece-value-split` CLI). 80 is the
mid-gap of the two current-camera populations (≥29 margin each side). The 105 value was deliberate
on the **old Microdia wrist cam** (2026-07-13: a black rook with corner glare read 88); on the
Orbbec black tops out ~51 so it no longer applies. Documented in-code that if a glare spike ever
pushes a black piece near 80, no fixed threshold separates cleanly — switch to
`CLASSIFIER_MODE="cnn"` rather than re-chasing the number.

**Verified:** both the previously-failing fresh capture (`board_frame_live.jpg`) and the earlier
`board_frame.jpg` now report "Occupancy matches START exactly" under `--static-calibration`; no
lint errors.

### 2026-07-15 — Depth-based occupancy prototype: 64/64 on a live mid-game position, no empty reference

Decision point: RGB heuristic keeps producing phantom pieces (every incident above is a variant of
"appearance-diff proxy broke"). The Gemini 335 exposes **raw Z16 depth and GREY IR over plain
V4L2** — no pyorbbecsdk needed (`/dev/video0` Z16, `/dev/video2` GREY, both 1280x800, pixel-aligned
with each other; RGB stays on `/dev/video6`). Depth temporal noise measured at **0.4mm median /
1.4mm p95** against 20–90mm pieces — a 10–30x SNR where the RGB heuristic fights for 1.5x.

Built and validated `step1_board/depth_occupancy.py` (new), all on the bench tonight:

1. **Geometry**: one-time SIFT RGB→IR homography on the board plane (60 RANSAC inliers), composed
   with the existing `board_calibration.json` — the depth frame inherits the RGB grid, and stays
   valid under board slides because the RGB calibration is what gets refreshed. Saved as
   `calibration/depth_calibration.json` (`--register` re-fits it).
2. **Plane fit in the ORIGINAL depth frame** (inverse depth is linear in pixels for a 3D plane;
   fitting in warped coords adds a rational-function bias — measured ±20mm of fake tilt).
3. **Orthographic foot-projection**: back-project every pixel to 3D, drop vertically onto the
   plane, bin by the *foot*. This exactly killed the parallax phantoms (piece bodies leaning one
   rank away from the camera: d5 pawn→d6, c4→c5, e6 bishop→e7, whole back rank→rank 2). Naive
   per-square height stats produced 10+ phantoms; foot-projection: zero.
4. **Intrinsics matter**: at the fx=640 spec guess, elevated piece surfaces spilled one square
   south at the image periphery (g6/h6 false positives off the g7/h7 pawns). Swept fx against a
   hand-verified position: margin plateaus at +0.20 for fx 500–575, degrades above 610. Shipped
   fx=575 (empirical); replace with factory intrinsics via pyorbbecsdk eventually. Cross-check:
   implies ~38mm squares — measure the physical board to confirm.

**Result (live mid-game position, pieces on 24 squares): 64/64 occupancy correct, 64/64 colour
correct** via `board_state_depth_fused` (depth decides occupancy, RGB median split decides colour
on occupied squares only). Margin: weakest true piece 0.33 area fraction (a pawn on e7 almost
fully occluded behind the e6 bishop — only its bottom ~12mm visible, *impossible* for any RGB
diff) vs worst empty square 0.14; threshold 0.25. **No `empty_board.jpg` needed at all** — the
same-session-recapture footgun class is gone: grid lines are flat, so misalignment produces zero
height signal by construction.

Known limits / next steps:
- Fully occluded squares (no depth pixels at all) are undetectable in a single frame — same
  "safe miss" category as the RGB heuristic's tolerated misses; move-diff logic already handles it.
- fx=575 is empirical on one camera pose; if the head cam ever moves much closer/farther, re-sweep
  or read factory intrinsics.
- Not yet wired into `game_loop.py` — `board_state_depth_fused` has the same return contract as
  `board_state_from_image`, so it can slot in as a third `CLASSIFIER_MODE` or run shadow-mode
  alongside the heuristic first (recommended: one full game logging disagreements before switching).
- Prototype artifacts (raw captures, probe scripts) in the session scratchpad, not committed.

**Update (same evening): wired into the game loop.** `game_loop.py --mode live --perception depth`
runs the full game on depth occupancy + RGB colour: `CameraBackend(perception="depth")` branches
`_scan()` into `capture_depth()` + `board_state_depth_fused()`, loads `depth_calibration.json` at
startup (fails fast if unregistered), and skips the empty-board-reference requirement entirely.
Depth mode uses the stored board calibration for geometry (no per-frame BoardLocator — recalibrate
if the board moves; ArUco markers remain the plan for that). `--perception rgb` stays the default,
byte-identical behaviour. Verified: `_scan()` smoke test through the real code path (motors
stubbed) read the freshly reset start position 64/64 with correct colours. Suite: 59 passed; the 2
failures (`test_board_locator_acceptance`, `test_calibration_compatibility::..._from_existing_seed`)
are pre-existing — they reproduce with the depth files removed and diff stale saved frames against
the recalibrated homography.

### 2026-07-20 — Bad `aruco+border` fallback + register_markers not committing grid H

`game_loop.py --mode live` aborted at start: occupancy `white=14, black=32`, HARD phantoms on
empty centre squares (`a3/a5/b4/…`), locator `corner_shift≈39px`. Not a colour-split issue —
RGB empty-ref vs live warp disagreed because geometry was wrong.

**Cause (two stacked bugs):**

1. **`calibrate_board.py --capture` with pieces on / bad seed.** Markers visible →
   `homography_from_aruco_and_label_border` seeds auto-calibrate; grid polish often finds a good
   fit (~60 pts, ~1.2px) but `validate_calibration_fit` rejects it when seed→grid corner shift
   exceeds `_MAX_SEED_CORNER_SHIFT_CELLS` (0.4). Fallback is `source=aruco+border` with a fake
   `residual_px=0.0` (4 points only). `board_warp_debug.jpg` then shows yellow lines well off the
   printed grid — do not treat that log line as success.

2. **`register_markers.py` refined the grid but did not write `fit.homography`.** It only merged
   the `"aruco"` block, leaving the stale seed H in `board_calibration.json`. Markers were mapped
   in the *refined* board space; `empty_board.jpg` was still warped with the *old* H → live
   `BoardLocator` (ArUco→registered board coords) vs empty-ref mismatch → phantoms. Folding-board
   seam also needs `--max-grid-residual 2.0` (measured ~1.2–1.4px; default 0.8 aborts).

**Fix:**

- `register_from_frame` now commits refined `homography`, `corners_px`, and
  `calibration_method=grid+aruco-register` alongside the ArUco block (same frame as
  `--also-empty-ref`).
- Recalibration skill / README / `.cursor/rules/exp2-chess-calibration.mdc`: prefer Path A —
  empty board → `register_markers.py --capture --also-empty-ref --max-grid-residual 2.0`; do
  **not** re-run `calibrate_board.py --capture` after a good registration (it can overwrite with
  `aruco+border` again).

**Verified:** after Path A, `scan_board.py` → `tier=aruco+grid markers=4 residual=1.36px
corner_shift=3.2px`, **Occupancy matches START exactly.**
