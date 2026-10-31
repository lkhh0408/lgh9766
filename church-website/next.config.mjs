/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  serverExternalPackages: ['sanitize-html'],
  experimental: {
    serverActions: { bodySizeLimit: '20mb' },
  },
};
export default nextConfig;
