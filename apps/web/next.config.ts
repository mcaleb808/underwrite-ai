import type { NextConfig } from "next";

// 'standalone' is for the docker-compose image; Vercel rejects it.
const nextConfig: NextConfig = {
  ...(process.env.VERCEL ? {} : { output: "standalone" }),
};

export default nextConfig;
