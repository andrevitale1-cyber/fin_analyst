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
    const sync = () => {
      if (enabled && visible && document.visibilityState === "visible") {
        void video.play().then(() => {
          if (!disposed) setBlocked(false);
        }).catch((error: DOMException) => {
          if (!disposed && visible && error.name !== "AbortError") setBlocked(true);
        });
      }
      else video.pause();
    };
    const observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; sync(); });
    observer.observe(video);
    sync();
    const playing = () => setBlocked(false);
    video.addEventListener("playing", playing);
    video.addEventListener("canplay", sync);
    document.addEventListener("visibilitychange", sync);
    document.addEventListener("touchend", sync, { passive: true });
    document.addEventListener("click", sync);
    window.addEventListener("pageshow", sync);
    return () => {
      disposed = true;
      observer.disconnect();
      video.removeEventListener("playing", playing);
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
