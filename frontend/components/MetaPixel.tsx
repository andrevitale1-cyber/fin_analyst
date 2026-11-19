"use client";

import { useUser } from "@clerk/nextjs";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { loadMetaPixel, trackMetaPageView, trackMetaSignup } from "../lib/metaPixel";

export default function MetaPixel() {
  const pathname = usePathname();
  const { user, isLoaded } = useUser();

  useEffect(() => { loadMetaPixel(); }, []);
  useEffect(() => { trackMetaPageView(); }, [pathname]);
  useEffect(() => {
    if (isLoaded && user?.createdAt) trackMetaSignup(user.id, user.createdAt.getTime());
  }, [isLoaded, user]);

  return null;
}
