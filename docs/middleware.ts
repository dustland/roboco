export { middleware } from "nextra/locales";

export const config = {
  // Matcher ignoring `/_next/` and `/api/`
  matcher: [
    // Exclude specific paths
    "/((?!api|_next|auth|models|manifest.webmanifest|.*\\.(?:svg|png|jpg|jpeg|gif|urdf|stl|webp|js|rrd|ico)$).*)",
  ],
};
