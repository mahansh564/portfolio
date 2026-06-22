(function () {
  "use strict";

  var ICON_PLAY =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z" fill="currentColor"/></svg>';
  var ICON_PAUSE =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 5h4v14H6zm8 0h4v14h-4z" fill="currentColor"/></svg>';

  function formatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) return "0:00";
    var m = Math.floor(seconds / 60);
    var s = Math.floor(seconds % 60);
    return m + ":" + String(s).padStart(2, "0");
  }

  function setPlayingState(wrap, playing) {
    wrap.classList.toggle("vp--playing", playing);
    wrap.classList.toggle("vp--paused", !playing);
    var label = playing ? "Pause" : "Play";
    wrap.querySelectorAll(".vp__big-play, .vp__btn--play").forEach(function (btn) {
      btn.setAttribute("aria-label", label);
      btn.innerHTML = playing ? ICON_PAUSE : ICON_PLAY;
    });
  }

  function initPlayer(wrap) {
    var video = wrap.querySelector("video");
    if (!video || wrap.dataset.vpReady) return;
    wrap.dataset.vpReady = "1";

    video.removeAttribute("controls");
    video.setAttribute("tabindex", "0");

    var overlay = document.createElement("div");
    overlay.className = "vp__overlay";
    overlay.innerHTML =
      '<button type="button" class="vp__big-play" aria-label="Play">' +
      ICON_PLAY +
      "</button>" +
      '<div class="vp__bar">' +
      '<button type="button" class="vp__btn vp__btn--play" aria-label="Play">' +
      ICON_PLAY +
      "</button>" +
      '<div class="vp__progress" role="slider" aria-label="Seek" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" tabindex="0">' +
      '<div class="vp__track">' +
      '<div class="vp__buffer"></div>' +
      '<div class="vp__fill"></div>' +
      "</div>" +
      "</div>" +
      '<span class="vp__time">' +
      '<span class="vp__current">0:00</span>' +
      '<span class="vp__sep"> / </span>' +
      '<span class="vp__duration">0:00</span>' +
      "</span>" +
      (video.hasAttribute("loop")
        ? '<span class="vp__loop" aria-hidden="true">loop</span>'
        : "") +
      "</div>";

    wrap.appendChild(overlay);

    var bigPlay = wrap.querySelector(".vp__big-play");
    var btnPlay = wrap.querySelector(".vp__btn--play");
    var progress = wrap.querySelector(".vp__progress");
    var fill = wrap.querySelector(".vp__fill");
    var buffer = wrap.querySelector(".vp__buffer");
    var currentEl = wrap.querySelector(".vp__current");
    var durationEl = wrap.querySelector(".vp__duration");
    var scrubbing = false;

    function togglePlay() {
      if (video.paused || video.ended) {
        video.play();
      } else {
        video.pause();
      }
    }

    function updateTime() {
      var dur = video.duration || 0;
      var cur = video.currentTime || 0;
      var pct = dur ? (cur / dur) * 100 : 0;
      fill.style.width = pct + "%";
      progress.style.setProperty("--vp-thumb", pct + "%");
      progress.setAttribute("aria-valuenow", String(Math.round(pct)));
      progress.setAttribute("aria-valuetext", formatTime(cur) + " of " + formatTime(dur));
      currentEl.textContent = formatTime(cur);
      durationEl.textContent = formatTime(dur);
    }

    function updateBuffer() {
      if (!video.buffered.length || !video.duration) {
        buffer.style.width = "0%";
        return;
      }
      buffer.style.width = (video.buffered.end(video.buffered.length - 1) / video.duration) * 100 + "%";
    }

    function seekFromClientX(clientX) {
      var rect = progress.getBoundingClientRect();
      var ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
      if (video.duration) {
        video.currentTime = ratio * video.duration;
      }
      updateTime();
    }

    function onPointerDown(e) {
      scrubbing = true;
      progress.setPointerCapture(e.pointerId);
      seekFromClientX(e.clientX);
      wrap.classList.add("vp--scrubbing");
    }

    function onPointerMove(e) {
      if (!scrubbing) return;
      seekFromClientX(e.clientX);
    }

    function onPointerUp(e) {
      if (!scrubbing) return;
      scrubbing = false;
      wrap.classList.remove("vp--scrubbing");
      try {
        progress.releasePointerCapture(e.pointerId);
      } catch (_) {}
    }

    bigPlay.addEventListener("click", function (e) {
      e.stopPropagation();
      togglePlay();
    });
    btnPlay.addEventListener("click", function (e) {
      e.stopPropagation();
      togglePlay();
    });

    wrap.addEventListener("click", function (e) {
      if (e.target.closest(".vp__bar, .vp__big-play")) return;
      togglePlay();
    });

    progress.addEventListener("pointerdown", onPointerDown);
    progress.addEventListener("pointermove", onPointerMove);
    progress.addEventListener("pointerup", onPointerUp);
    progress.addEventListener("pointercancel", onPointerUp);

    progress.addEventListener("keydown", function (e) {
      if (!video.duration) return;
      var step = e.shiftKey ? 5 : 1;
      if (e.key === "ArrowRight") {
        video.currentTime = Math.min(video.duration, video.currentTime + step);
        e.preventDefault();
      } else if (e.key === "ArrowLeft") {
        video.currentTime = Math.max(0, video.currentTime - step);
        e.preventDefault();
      }
    });

    video.addEventListener("keydown", function (e) {
      if (e.key === " " || e.key === "k" || e.key === "K") {
        e.preventDefault();
        togglePlay();
      }
    });

    video.addEventListener("play", function () {
      setPlayingState(wrap, true);
    });
    video.addEventListener("pause", function () {
      setPlayingState(wrap, false);
    });
    video.addEventListener("ended", function () {
      setPlayingState(wrap, false);
    });
    video.addEventListener("timeupdate", updateTime);
    video.addEventListener("loadedmetadata", function () {
      updateTime();
      updateBuffer();
    });
    video.addEventListener("progress", updateBuffer);
    video.addEventListener("durationchange", updateTime);

    setPlayingState(wrap, !video.paused);
    updateTime();
  }

  document.querySelectorAll("[data-vp]").forEach(initPlayer);
})();
