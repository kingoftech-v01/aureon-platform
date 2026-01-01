/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // Assets are served from /static/marketing/ after collectstatic
  basePath: '',
  assetPrefix: process.env.NODE_ENV === 'production' ? '/static/marketing' : '',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://aureon.rhematek-solutions.com/api/v1',
  },
};

export default nextConfig;
