/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  // NOTE: no rewrites — all API calls go through the Axios client in
  // src/lib/api.ts with an absolute NEXT_PUBLIC_API_URL base. A rewrite here
  // would re-evaluate that env var at build time and fail the Vercel build
  // if the value is ever malformed.
};

module.exports = nextConfig;
