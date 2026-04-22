import type { NextConfig } from "next";

// 'standalone' produces a self-contained server.js for the local
// docker-compose image. Vercel does its own function bundling and breaks if
// 'standalone' is set, so omit it when building on Vercel.
const nextConfig: NextConfig = {
  ...(process.env.VERCEL ? {} : { output: "standalone" }),
};

export default nextConfig;
