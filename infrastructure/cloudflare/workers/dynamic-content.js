/**
 * Maily Dynamic Content Worker
 *
 * This Cloudflare Worker provides dynamic content processing at the edge.
 * It handles content personalization, A/B testing, geolocation-based content,
 * and other dynamic content features without requiring a round trip to the origin.
 */

// KV namespace bindings will be set in the Cloudflare dashboard
// - MAILY_TEMPLATES: Email templates
// - MAILY_USER_PREFS: User preferences
// - MAILY_EXPERIMENTS: A/B testing configurations
// - MAILY_GEO_CONTENT: Geolocation-specific content

// Content personalization configuration
const PERSONALIZATION = {
  // Personalization tokens
  tokens: {
    firstName: '{{firstName}}',
    lastName: '{{lastName}}',
    email: '{{email}}',
    company: '{{company}}',
    unsubscribeLink: '{{unsubscribeLink}}',
    viewInBrowserLink: '{{viewInBrowserLink}}',
    currentDate: '{{currentDate}}',
    currentYear: '{{currentYear}}',
  },
  // Default values for missing tokens
  defaults: {
    firstName: 'there',
    lastName: '',
    company: 'your company',
    currentDate: () => new Date().toLocaleDateString(),
    currentYear: () => new Date().getFullYear().toString(),
  },
};

// A/B testing configuration
const AB_TESTING = {
  // Cookie name for storing experiment assignments
  cookieName: 'maily_experiments',
  // Cookie expiration in days
  cookieExpiration: 30,
  // Default traffic allocation percentage
  defaultAllocation: 50,
};

// Geolocation content configuration
const GEO_CONTENT = {
  // Default region if geolocation fails
  defaultRegion: 'US',
  // Region mappings for simplification
  regionMappings: {
    'US': ['US', 'CA', 'MX'],
    'EU': ['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'SE', 'DK', 'NO', 'FI', 'CH', 'AT', 'IE', 'PT', 'GR', 'PL'],
    'APAC': ['JP', 'CN', 'KR', 'IN', 'AU', 'NZ', 'SG', 'MY', 'TH', 'VN', 'ID', 'PH'],
    'LATAM': ['BR', 'AR', 'CL', 'CO', 'PE', 'VE', 'EC', 'BO', 'PY', 'UY'],
    'MEA': ['AE', 'SA', 'QA', 'KW', 'BH', 'OM', 'EG', 'ZA', 'NG', 'KE'],
  },
};

// Content security configuration
const CONTENT_SECURITY = {
  // List of allowed domains for images
  allowedImageDomains: [
    'images.maily.com',
    'cdn.maily.com',
    'res.cloudinary.com',
    'imgur.com',
    'i.imgur.com',
  ],
  // List of allowed domains for links
  allowedLinkDomains: [
    'maily.com',
    'app.maily.com',
    'help.maily.com',
    'blog.maily.com',
  ],
  // Whether to allow external links
  allowExternalLinks: true,
  // Whether to add tracking parameters to links
  addTrackingParams: true,
};

/**
 * Main request handler
 */
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event));
});

/**
 * Handle the request
 * @param {FetchEvent} event - The fetch event
 * @returns {Promise<Response>} - The response
 */
async function handleRequest(event) {
  const request = event.request;
  const url = new URL(request.url);
  const path = url.pathname;

  // Handle different endpoints
  if (path.startsWith('/api/content/template/')) {
    return await handleTemplateRequest(event);
  } else if (path.startsWith('/api/content/personalize/')) {
    return await handlePersonalizeRequest(event);
  } else if (path.startsWith('/api/content/experiment/')) {
    return await handleExperimentRequest(event);
  } else if (path.startsWith('/api/content/geo/')) {
    return await handleGeoContentRequest(event);
  } else if (path === '/api/content/health') {
    return new Response(JSON.stringify({ status: 'healthy' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // Handle unknown endpoints
  return new Response(JSON.stringify({ error: 'Not Found' }), {
    status: 404,
    headers: { 'Content-Type': 'application/json' },
  });
}

/**
 * Handle template requests
 * @param {FetchEvent} event - The fetch event
 * @returns {Promise<Response>} - The response
 */
async function handleTemplateRequest(event) {
  const request = event.request;
  const url = new URL(request.url);
  const path = url.pathname;

  // Extract template ID from path
  const templateId = path.split('/').pop();

  if (!templateId) {
    return new Response(JSON.stringify({ error: 'Template ID is required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  try {
    // Get template from KV
    const template = await event.env.MAILY_TEMPLATES.get(templateId, { type: 'json' });

    if (!template) {
      return new Response(JSON.stringify({ error: 'Template not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Apply security measures to template
    const secureTemplate = applyContentSecurity(template);

    return new Response(JSON.stringify(secureTemplate), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error(`Error fetching template: ${error.message}`);

    return new Response(JSON.stringify({ error: 'Internal Server Error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

/**
 * Handle personalize requests
 * @param {FetchEvent} event - The fetch event
 * @returns {Promise<Response>} - The response
 */
async function handlePersonalizeRequest(event) {
  const request = event.request;

  // Only allow POST requests
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method Not Allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json', 'Allow': 'POST' },
    });
  }

  try {
    // Parse request body
    const requestData = await request.json();

    if (!requestData.content || !requestData.userId) {
      return new Response(JSON.stringify({ error: 'Content and userId are required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Get user preferences from KV
    const userPrefs = await event.env.MAILY_USER_PREFS.get(requestData.userId, { type: 'json' }) || {};

    // Personalize content
    const personalizedContent = await personalizeContent(
      requestData.content,
      userPrefs,
      requestData.additionalData || {}
    );

    return new Response(JSON.stringify({ content: personalizedContent }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error(`Error personalizing content: ${error.message}`);

    return new Response(JSON.stringify({ error: 'Internal Server Error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

/**
 * Handle experiment requests
 * @param {FetchEvent} event - The fetch event
 * @returns {Promise<Response>} - The response
 */
async function handleExperimentRequest(event) {
  const request = event.request;
  const url = new URL(request.url);
  const path = url.pathname;

  // Extract experiment ID from path
  const experimentId = path.split('/').pop();

  if (!experimentId) {
    return new Response(JSON.stringify({ error: 'Experiment ID is required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  try {
    // Get experiment configuration from KV
    const experiment = await event.env.MAILY_EXPERIMENTS.get(experimentId, { type: 'json' });

    if (!experiment) {
      return new Response(JSON.stringify({ error: 'Experiment not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Get user ID from query parameter or cookie
    const userId = url.searchParams.get('userId') || getCookieValue(request, 'maily_user_id');

    if (!userId) {
      return new Response(JSON.stringify({ error: 'User ID is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Determine which variant to show
    const variant = determineExperimentVariant(userId, experimentId, experiment);

    // Get variant content
    const variantContent = experiment.variants[variant].content;

    // Create response with experiment assignment cookie
    const response = new Response(JSON.stringify({
      variant,
      content: variantContent,
      experimentId,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

    // Set cookie with experiment assignment
    const experimentCookie = getCookieValue(request, AB_TESTING.cookieName);
    const experiments = experimentCookie ? JSON.parse(decodeURIComponent(experimentCookie)) : {};
    experiments[experimentId] = variant;

    response.headers.set('Set-Cookie', `${AB_TESTING.cookieName}=${encodeURIComponent(JSON.stringify(experiments))}; Path=/; Max-Age=${AB_TESTING.cookieExpiration * 86400}; SameSite=Lax`);

    return response;
  } catch (error) {
    console.error(`Error handling experiment: ${error.message}`);

    return new Response(JSON.stringify({ error: 'Internal Server Error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

/**
 * Handle geo content requests
 * @param {FetchEvent} event - The fetch event
 * @returns {Promise<Response>} - The response
 */
async function handleGeoContentRequest(event) {
  const request = event.request;
  const url = new URL(request.url);
  const path = url.pathname;

  // Extract content ID from path
  const contentId = path.split('/').pop();

  if (!contentId) {
    return new Response(JSON.stringify({ error: 'Content ID is required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  try {
    // Get geo content from KV
    const geoContent = await event.env.MAILY_GEO_CONTENT.get(contentId, { type: 'json' });

    if (!geoContent) {
      return new Response(JSON.stringify({ error: 'Geo content not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Get user's country from CF request
    const country = request.cf ? request.cf.country : GEO_CONTENT.defaultRegion;

    // Determine region based on country
    const region = determineRegion(country);

    // Get content for region, or default if not found
    const regionContent = geoContent[region] || geoContent.default;

    if (!regionContent) {
      return new Response(JSON.stringify({ error: 'No content available for this region' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({
      region,
      country,
      content: regionContent,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error(`Error handling geo content: ${error.message}`);

    return new Response(JSON.stringify({ error: 'Internal Server Error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

/**
 * Personalize content with user data
 * @param {string} content - The content to personalize
 * @param {Object} userPrefs - User preferences
 * @param {Object} additionalData - Additional data for personalization
 * @returns {string} - Personalized content
 */
async function personalizeContent(content, userPrefs, additionalData) {
  // Combine user preferences and additional data
  const data = { ...userPrefs, ...additionalData };

  // Replace tokens with user data or defaults
  let personalizedContent = content;

  for (const [key, token] of Object.entries(PERSONALIZATION.tokens)) {
    const value = data[key] ||
                 (PERSONALIZATION.defaults[key] instanceof Function ?
                  PERSONALIZATION.defaults[key]() :
                  PERSONALIZATION.defaults[key]);

    // Replace all occurrences of the token
    const regex = new RegExp(escapeRegExp(token), 'g');
    personalizedContent = personalizedContent.replace(regex, value);
  }

  return personalizedContent;
}

/**
 * Apply content security measures
 * @param {Object} template - The template object
 * @returns {Object} - Secure template
 */
function applyContentSecurity(template) {
  if (!template || !template.content) {
    return template;
  }

  let secureContent = template.content;

  // Sanitize image sources
  secureContent = secureContent.replace(/<img[^>]+src="([^"]+)"[^>]*>/gi, (match, src) => {
    if (isAllowedImageDomain(src)) {
      return match;
    }
    // Replace with placeholder or remove
    return `<img src="https://cdn.maily.com/placeholder.png" alt="Image removed for security" />`;
  });

  // Sanitize links
  secureContent = secureContent.replace(/<a[^>]+href="([^"]+)"[^>]*>(.*?)<\/a>/gi, (match, href, text) => {
    if (isAllowedLinkDomain(href)) {
      // Add tracking parameters if enabled
      if (CONTENT_SECURITY.addTrackingParams) {
        const separator = href.includes('?') ? '&' : '?';
        href = `${href}${separator}utm_source=maily&utm_medium=email&utm_campaign=${template.id || 'campaign'}`;
      }
      return `<a href="${href}">${text}</a>`;
    }

    if (CONTENT_SECURITY.allowExternalLinks) {
      // Add rel="noopener noreferrer" for external links
      return `<a href="${href}" rel="noopener noreferrer" target="_blank">${text}</a>`;
    }

    // Remove link but keep text
    return text;
  });

  // Remove script tags
  secureContent = secureContent.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');

  // Create a copy of the template with secure content
  return {
    ...template,
    content: secureContent,
  };
}

/**
 * Determine experiment variant for a user
 * @param {string} userId - The user ID
 * @param {string} experimentId - The experiment ID
 * @param {Object} experiment - The experiment configuration
 * @returns {string} - The variant name
 */
function determineExperimentVariant(userId, experimentId, experiment) {
  // Check if experiment is active
  if (!experiment.active) {
    return 'control';
  }

  // Get variants and their weights
  const variants = Object.keys(experiment.variants);
  const weights = variants.map(v => experiment.variants[v].weight || AB_TESTING.defaultAllocation);

  // Normalize weights to sum to 100
  const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
  const normalizedWeights = weights.map(weight => (weight / totalWeight) * 100);

  // Generate a deterministic hash from user ID and experiment ID
  const hash = cyrb53(`${userId}-${experimentId}`);
  const percentage = hash % 100;

  // Determine variant based on percentage and weights
  let cumulativeWeight = 0;
  for (let i = 0; i < variants.length; i++) {
    cumulativeWeight += normalizedWeights[i];
    if (percentage < cumulativeWeight) {
      return variants[i];
    }
  }

  // Fallback to control
  return 'control';
}

/**
 * Determine region based on country code
 * @param {string} country - The country code
 * @returns {string} - The region
 */
function determineRegion(country) {
  for (const [region, countries] of Object.entries(GEO_CONTENT.regionMappings)) {
    if (countries.includes(country)) {
      return region;
    }
  }

  return GEO_CONTENT.defaultRegion;
}

/**
 * Check if an image domain is allowed
 * @param {string} url - The image URL
 * @returns {boolean} - Whether the domain is allowed
 */
function isAllowedImageDomain(url) {
  try {
    const domain = new URL(url).hostname;
    return CONTENT_SECURITY.allowedImageDomains.some(allowedDomain =>
      domain === allowedDomain || domain.endsWith(`.${allowedDomain}`)
    );
  } catch (e) {
    return false;
  }
}

/**
 * Check if a link domain is allowed
 * @param {string} url - The link URL
 * @returns {boolean} - Whether the domain is allowed
 */
function isAllowedLinkDomain(url) {
  try {
    // Allow relative URLs
    if (url.startsWith('/')) {
      return true;
    }

    // Allow mailto: and tel: links
    if (url.startsWith('mailto:') || url.startsWith('tel:')) {
      return true;
    }

    const domain = new URL(url).hostname;
    return CONTENT_SECURITY.allowedLinkDomains.some(allowedDomain =>
      domain === allowedDomain || domain.endsWith(`.${allowedDomain}`)
    );
  } catch (e) {
    return false;
  }
}

/**
 * Get cookie value from request
 * @param {Request} request - The request
 * @param {string} name - The cookie name
 * @returns {string|null} - The cookie value
 */
function getCookieValue(request, name) {
  const cookieHeader = request.headers.get('Cookie');
  if (!cookieHeader) {
    return null;
  }

  const cookies = cookieHeader.split(';');
  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.trim().split('=');
    if (cookieName === name) {
      return cookieValue;
    }
  }

  return null;
}

/**
 * Escape string for use in regular expression
 * @param {string} string - The string to escape
 * @returns {string} - The escaped string
 */
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Simple hash function (cyrb53)
 * @param {string} str - The string to hash
 * @param {number} seed - The seed
 * @returns {number} - The hash
 */
function cyrb53(str, seed = 0) {
  let h1 = 0xdeadbeef ^ seed;
  let h2 = 0x41c6ce57 ^ seed;

  for (let i = 0, ch; i < str.length; i++) {
    ch = str.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }

  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507);
  h1 ^= Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507);
  h2 ^= Math.imul(h1 ^ (h1 >>> 13), 3266489909);

  return 4294967296 * (2097151 & h2) + (h1 >>> 0);
}
