"use client";
import { useEffect, type RefObject } from "react";

export default function useVideoPlayback(ref: RefObject<HTMLVideoElement | null>, enabled: boolean) {
  useEffect(() => {
    const video = ref.current;
    if (!video) return;
    video.muted = true;
    video.defaultMuted = true;
    video.setAttribute("muted", "");
    video.setAttribute("playsinline", "");
    video.setAttribute("webkit-playsinline", "");
    let visible = false;
    const sync = () => {
      if (enabled && visible && document.visibilityState === "visible") void video.play().catch(() => {});
      else video.pause();
    };
    const observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; sync(); });
    observer.observe(video);
    sync();
    video.addEventListener("canplay", sync);
    document.addEventListener("visibilitychange", sync);
    document.addEventListener("touchend", sync, { passive: true });
    document.addEventListener("click", sync);
    window.addEventListener("pageshow", sync);
    return () => {
      observer.disconnect();
      video.removeEventListener("canplay", sync);
      document.removeEventListener("visibilitychange", sync);
      document.removeEventListener("touchend", sync);
      document.removeEventListener("click", sync);
      window.removeEventListener("pageshow", sync);
      video.pause();
    };
  }, [ref, enabled]);
}
