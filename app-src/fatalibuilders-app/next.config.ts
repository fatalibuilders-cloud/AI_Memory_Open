import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  serverExternalPackages: ["argon2", "@electric-sql/pglite", "pg", "exceljs", "pdfkit"],
};

export default nextConfig;
