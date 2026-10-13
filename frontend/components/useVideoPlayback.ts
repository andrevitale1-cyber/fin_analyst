"use client";
import { useEffect, useState, type RefObject } from "react";

export default function useVideoPlayback(ref: RefObject<HTMLVideoElement | null>, enabled: boolean) {
  const [blocked, setBlocked] = useState(false);
  useEffect(() => {
    const video = ref.current;
    if (!video) return;
    video.muted = true;
    video.defaultMuted = true;
    video.setAttribute("muted", "");
    video.setAttribute("playsinline", "");
    video.setAttribute("webkit-playsinline", "");
    let visible = false;
    let disposed = false;
    let lastTime = video.currentTime;
    let lastProgress = performance.now();
    const sync = () => {
      if (enabled && visible && document.visibilityState === "visible") {
        void video.play().catch((error: DOMException) => {
          if (!disposed && visible && error.name !== "AbortError") setBlocked(true);
        });
      }
      else video.pause();
    };
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !visible) lastProgress = performance.now();
      visible = entry.isIntersecting;
      sync();
    });
    observer.observe(video);
    sync();
    // Safari can resolve play() and then stop the video without rejecting it.
    const progress = () => {
      if (Math.abs(video.currentTime - lastTime) < .01) return;
      lastTime = video.currentTime;
      lastProgress = performance.now();
      setBlocked(false);
    };
    const watchdog = window.setInterval(() => {
      if (enabled && visible && document.visibilityState === "visible" && !video.ended && performance.now() - lastProgress > 2500) setBlocked(true);
    }, 1000);
    video.addEventListener("timeupdate", progress);
    video.addEventListener("canplay", sync);
    document.addEventListener("visibilitychange", sync);
    document.addEventListener("touchend", sync, { passive: true });
    document.addEventListener("click", sync);
    window.addEventListener("pageshow", sync);
    return () => {
      disposed = true;
      observer.disconnect();
      window.clearInterval(watchdog);
      video.removeEventListener("timeupdate", progress);
      video.removeEventListener("canplay", sync);
      document.removeEventListener("visibilitychange", sync);
      document.removeEventListener("touchend", sync);
      document.removeEventListener("click", sync);
      window.removeEventListener("pageshow", sync);
      video.pause();
    };
  }, [ref, enabled]);
  return blocked;
}
