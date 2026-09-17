import type { NextConfig } from "next";

// Dynamically extract origin from NEXT_PUBLIC_API_URL environment variable
const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8050/api/v1";
let dynamicApiOrigin = "";
try {
  const parsed = new URL(rawApiUrl);
  dynamicApiOrigin = parsed.origin;
} catch {
  dynamicApiOrigin = "";
}

const cspHeader = `
    default-src 'self';
    script-src 'self' 'unsafe-eval' 'unsafe-inline';
    style-src 'self' 'unsafe-inline';
    img-src 'self' blob: data: https:;
    media-src 'self' blob: data: http: https:;
    font-src 'self' data:;
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    connect-src 'self' blob: data: http: https: ws: wss:;
`;

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: cspHeader.replace(/\s{2,}/g, " ").trim(),
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
