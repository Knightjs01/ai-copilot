/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [{ source: "/shadow/for-you", destination: "/shadow", permanent: true }];
  },
};

module.exports = nextConfig;
