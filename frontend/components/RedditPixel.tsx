"use client";

import { useUser } from "@clerk/nextjs";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { hashRedditEmail, trackRedditVisit } from "../lib/redditPixel";

export default function RedditPixel() {
  const pathname = usePathname();
  const { user, isLoaded } = useUser();
  const email = user?.primaryEmailAddress?.emailAddress;

  useEffect(() => {
    if (!isLoaded) return;
    let active = true;
    hashRedditEmail(email).catch(() => undefined).then(hash => {
      if (active) trackRedditVisit(pathname, hash);
    });
    return () => { active = false; };
  }, [pathname, email, isLoaded]);

  return null;
}
