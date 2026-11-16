"use client";

import { useAuth, useUser } from "@clerk/nextjs";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { hashRedditEmail, trackRedditConversion, trackRedditVisit } from "../lib/redditPixel";

export default function RedditPixel() {
  const pathname = usePathname();
  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  const email = user?.primaryEmailAddress?.emailAddress;
  const userId = user?.id;

  useEffect(() => {
    if (!isLoaded) return;
    let active = true;
    hashRedditEmail(email).catch(() => undefined).then(async hash => {
      if (!active) return;
      trackRedditVisit(pathname, hash);
      if (!userId) return;
      const token = await getToken();
      if (!token || !active) return;
      const base = process.env.NEXT_PUBLIC_API_BASE_URL || "https://api-finanalyzer.onrender.com";
      const response = await fetch(`${base}/api/conversions/reddit`, {method:"POST",
        headers:{Authorization:`Bearer ${token}`,"Content-Type":"application/json"},
        body:JSON.stringify({event:"SignUp",event_id:crypto.randomUUID()}),keepalive:true});
      if (!response.ok) return;
      const conversion = await response.json();
      if (active && conversion.event === "SignUp") trackRedditConversion("SignUp", {conversionId:conversion.conversionId}, hash);
    }).catch(() => {
      // Advertising failures must not interrupt login, checkout or the dashboard.
    });
    return () => { active = false; };
  }, [pathname, email, isLoaded, userId, getToken]);

  return null;
}
