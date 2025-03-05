const express = require('express');
const router = express.Router();
const { getAllFeatures, isFeatureEnabled } = require('../../../config/feature-flags');
const auth = require('../middleware/auth');

/**
 * @swagger
 * /api/features:
 *   get:
 *     summary: Get all feature flags for the current user
 *     description: Returns all feature flags and their status for the authenticated user
 *     tags: [Features]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: List of feature flags
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 features:
 *                   type: object
 *                   additionalProperties:
 *                     type: object
 *                     properties:
 *                       enabled:
 *                         type: boolean
 *                       description:
 *                         type: string
 */
router.get('/', auth, (req, res) => {
  // Get all features for the current user
  const features = getAllFeatures({
    userID: req.user.id,
    // Environment is determined automatically from process.env.NODE_ENV
  });
  
  res.json({ features });
});

/**
 * @swagger
 * /api/features/{featureName}:
 *   get:
 *     summary: Check if a specific feature is enabled
 *     description: Returns whether a specific feature is enabled for the authenticated user
 *     tags: [Features]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: featureName
 *         required: true
 *         schema:
 *           type: string
 *         description: Name of the feature to check
 *     responses:
 *       200:
 *         description: Feature status
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 enabled:
 *                   type: boolean
 */
router.get('/:featureName', auth, (req, res) => {
  const { featureName } = req.params;
  
  const enabled = isFeatureEnabled(featureName, {
    userID: req.user.id,
    // Environment is determined automatically from process.env.NODE_ENV
  });
  
  res.json({ enabled });
});

/**
 * @swagger
 * /api/features/public:
 *   get:
 *     summary: Get public feature flags
 *     description: Returns public feature flags that don't require authentication
 *     tags: [Features]
 *     responses:
 *       200:
 *         description: List of public feature flags
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 features:
 *                   type: object
 *                   additionalProperties:
 *                     type: boolean
 */
router.get('/public', (req, res) => {
  // For public features, we don't have a user ID, so percentage rollouts won't apply
  // Only fully enabled features in the current environment will be returned as true
  const allFeatures = getAllFeatures();
  
  // Convert to a simpler format for public consumption
  const publicFeatures = {};
  
  Object.keys(allFeatures).forEach(featureName => {
    // Only include features that should be publicly visible
    if (featureName.startsWith('public-')) {
      publicFeatures[featureName] = allFeatures[featureName].enabled;
    }
  });
  
  res.json({ features: publicFeatures });
});

module.exports = router; 