import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a self-contained server.js for container deployment
  output: "standalone",

  // Proxy /api/v1/* to the backend service so NEXT_PUBLIC_API_URL can be ""
  // In containers: BACKEND_URL=http://nl2sql-backend:8000
  // In local dev:  BACKEND_URL=http://localhost:8000 (or use .env.local)
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
