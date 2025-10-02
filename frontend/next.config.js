/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://orca-app-jubw8.ondigitalocean.app',
  },
  reactStrictMode: true,
}

module.exports = nextConfig
