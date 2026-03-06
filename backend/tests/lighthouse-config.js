/**
 * Lighthouse Configuration
 * Aureon by Rhematek Solutions
 *
 * Configuration for CI/CD Lighthouse testing
 * Target: 95+ in all categories (Performance, Accessibility, SEO, Best Practices)
 *
 * Usage:
 *   npx lighthouse http://localhost:3000 --config-path=./lighthouse-config.js --output=json --output-path=./lighthouse-report.json
 *
 * For CI integration:
 *   npx lhci autorun --config=./lighthouserc.js
 */

module.exports = {
  ci: {
    collect: {
      // URLs to test
      url: [
        'http://localhost:3000/',
        'http://localhost:3000/login/',
        'http://localhost:3000/dashboard/',
      ],
      // Number of runs per URL (average is taken)
      numberOfRuns: 3,
      // Start server command (optional)
      startServerCommand: 'npm run start',
      // Wait for server to be ready
      startServerReadyPattern: 'Server is running',
      startServerReadyTimeout: 30000,
      // Puppeteer settings
      settings: {
        // Throttling settings for consistent results
        throttlingMethod: 'simulate',
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 1,
          requestLatencyMs: 0,
          downloadThroughputKbps: 10240,
          uploadThroughputKbps: 10240,
        },
        // Screen emulation
        formFactor: 'desktop',
        screenEmulation: {
          mobile: false,
          width: 1350,
          height: 940,
          deviceScaleFactor: 1,
          disabled: false,
        },
        // Locale
        locale: 'en-US',
        // Only audit specific categories
        onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
        // Skip audits that require network
        skipAudits: [
          'uses-http2', // Requires HTTPS
          'is-on-https', // Requires HTTPS in production
          'redirects-http', // Requires HTTPS
        ],
      },
    },
    assert: {
      // Assertions for each category
      assertions: {
        // Performance assertions
        'categories:performance': ['error', { minScore: 0.95 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'categories:best-practices': ['error', { minScore: 0.95 }],
        'categories:seo': ['error', { minScore: 0.95 }],

        // Core Web Vitals
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'first-contentful-paint': ['error', { maxNumericValue: 1800 }],
        'interactive': ['error', { maxNumericValue: 3800 }],
        'total-blocking-time': ['error', { maxNumericValue: 200 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],

        // Performance audits
        'speed-index': ['warn', { maxNumericValue: 3400 }],
        'server-response-time': ['warn', { maxNumericValue: 600 }],
        'render-blocking-resources': ['warn', { maxLength: 2 }],
        'uses-responsive-images': 'warn',
        'uses-optimized-images': 'warn',
        'uses-webp-images': 'warn',
        'uses-text-compression': 'warn',
        'uses-rel-preconnect': 'warn',
        'efficient-animated-content': 'warn',
        'duplicated-javascript': 'warn',
        'legacy-javascript': 'warn',
        'unused-javascript': 'warn',
        'unused-css-rules': 'warn',

        // Accessibility audits
        'color-contrast': 'error',
        'heading-order': 'error',
        'html-has-lang': 'error',
        'html-lang-valid': 'error',
        'image-alt': 'error',
        'link-name': 'error',
        'button-name': 'error',
        'input-image-alt': 'error',
        'label': 'error',
        'list': 'error',
        'listitem': 'error',
        'meta-viewport': 'error',
        'bypass': 'error', // Skip link
        'document-title': 'error',
        'duplicate-id-active': 'error',
        'duplicate-id-aria': 'error',
        'form-field-multiple-labels': 'warn',
        'frame-title': 'error',
        'valid-lang': 'error',
        'aria-allowed-attr': 'error',
        'aria-hidden-body': 'error',
        'aria-hidden-focus': 'error',
        'aria-required-attr': 'error',
        'aria-required-children': 'error',
        'aria-required-parent': 'error',
        'aria-roles': 'error',
        'aria-valid-attr-value': 'error',
        'aria-valid-attr': 'error',
        'tabindex': 'error',
        'focus-traps': 'error',
        'focusable-controls': 'error',
        'interactive-element-affordance': 'warn',
        'logical-tab-order': 'warn',
        'managed-focus': 'warn',
        'offscreen-content-hidden': 'warn',
        'use-landmarks': 'warn',
        'visual-order-follows-dom': 'warn',

        // SEO audits
        'viewport': 'error',
        'meta-description': 'error',
        'http-status-code': 'error',
        'font-size': 'error',
        'crawlable-anchors': 'error',
        'is-crawlable': 'error',
        'robots-txt': 'warn',
        'structured-data': 'warn',
        'hreflang': 'warn',
        'canonical': 'warn',
        'plugins': 'error',

        // Best practices audits
        'doctype': 'error',
        'charset': 'error',
        'no-document-write': 'error',
        'no-vulnerable-libraries': 'error',
        'js-libraries': 'warn',
        'notification-on-start': 'error',
        'geolocation-on-start': 'error',
        'password-inputs-can-be-pasted-into': 'error',
        'image-aspect-ratio': 'warn',
        'image-size-responsive': 'warn',
        'deprecations': 'warn',
        'errors-in-console': 'warn',
        'inspector-issues': 'warn',
      },
    },
    upload: {
      // Upload settings (configure for your CI)
      target: 'temporary-public-storage',
      // OR for lhci server:
      // target: 'lhci',
      // serverBaseUrl: 'https://your-lhci-server.example.com',
      // token: process.env.LHCI_TOKEN,
    },
  },
  // Extended Lighthouse config
  extends: 'lighthouse:default',
  settings: {
    // Audit settings
    formFactor: 'desktop',
    throttling: {
      rttMs: 40,
      throughputKbps: 10240,
      cpuSlowdownMultiplier: 1,
    },
    screenEmulation: {
      mobile: false,
      width: 1350,
      height: 940,
      deviceScaleFactor: 1,
    },
    emulatedUserAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    // Only test specific categories
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
    // Max wait time for page load
    maxWaitForLoad: 45000,
    // Output formats
    output: ['html', 'json'],
  },
};

/**
 * Mobile configuration preset
 * Use for testing mobile-specific pages
 */
module.exports.mobilePreset = {
  ...module.exports,
  settings: {
    ...module.exports.settings,
    formFactor: 'mobile',
    throttling: {
      rttMs: 150,
      throughputKbps: 1638.4,
      cpuSlowdownMultiplier: 4,
      requestLatencyMs: 562.5,
      downloadThroughputKbps: 1474.56,
      uploadThroughputKbps: 675,
    },
    screenEmulation: {
      mobile: true,
      width: 375,
      height: 667,
      deviceScaleFactor: 2,
    },
    emulatedUserAgent:
      'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
  },
};

/**
 * Accessibility-focused configuration
 * Use for comprehensive accessibility audits
 */
module.exports.a11yPreset = {
  extends: 'lighthouse:default',
  settings: {
    onlyCategories: ['accessibility'],
    // Include all accessibility audits
    onlyAudits: [
      'accesskeys',
      'aria-allowed-attr',
      'aria-command-name',
      'aria-hidden-body',
      'aria-hidden-focus',
      'aria-input-field-name',
      'aria-meter-name',
      'aria-progressbar-name',
      'aria-required-attr',
      'aria-required-children',
      'aria-required-parent',
      'aria-roles',
      'aria-toggle-field-name',
      'aria-tooltip-name',
      'aria-treeitem-name',
      'aria-valid-attr-value',
      'aria-valid-attr',
      'button-name',
      'bypass',
      'color-contrast',
      'definition-list',
      'dlitem',
      'document-title',
      'duplicate-id-active',
      'duplicate-id-aria',
      'form-field-multiple-labels',
      'frame-title',
      'heading-order',
      'html-has-lang',
      'html-lang-valid',
      'image-alt',
      'input-image-alt',
      'label',
      'link-name',
      'list',
      'listitem',
      'meta-refresh',
      'meta-viewport',
      'object-alt',
      'tabindex',
      'td-headers-attr',
      'th-has-data-cells',
      'valid-lang',
      'video-caption',
    ],
  },
};
