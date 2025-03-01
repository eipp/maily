import Joi from 'joi';

/**
 * Validation schemas for campaign API endpoints
 */
export const campaignValidation = {
  /**
   * Validation schema for creating a campaign
   */
  createCampaign: Joi.object({
    name: Joi.string().required().max(100).messages({
      'string.empty': 'Campaign name is required',
      'string.max': 'Campaign name cannot exceed 100 characters',
    }),

    subject: Joi.string().required().max(200).messages({
      'string.empty': 'Campaign subject is required',
      'string.max': 'Campaign subject cannot exceed 200 characters',
    }),

    content: Joi.string().required().messages({
      'string.empty': 'Campaign content is required',
    }),

    fromName: Joi.string().required().max(100).messages({
      'string.empty': 'Sender name is required',
      'string.max': 'Sender name cannot exceed 100 characters',
    }),

    fromEmail: Joi.string().required().email().messages({
      'string.empty': 'Sender email is required',
      'string.email': 'Sender email must be valid',
    }),

    // Optional fields
    description: Joi.string().max(500),

    contentType: Joi.string().valid('html', 'text').default('html'),

    replyToEmail: Joi.string().email().messages({
      'string.email': 'Reply-to email must be valid',
    }),

    segmentId: Joi.string().uuid().messages({
      'string.guid': 'Segment ID must be a valid UUID',
    }),

    templateId: Joi.string().uuid().messages({
      'string.guid': 'Template ID must be a valid UUID',
    }),

    metadata: Joi.object().default({}),
  }),

  /**
   * Validation schema for updating a campaign
   */
  updateCampaign: Joi.object({
    name: Joi.string().required().max(100).messages({
      'string.empty': 'Campaign name is required',
      'string.max': 'Campaign name cannot exceed 100 characters',
    }),

    subject: Joi.string().required().max(200).messages({
      'string.empty': 'Campaign subject is required',
      'string.max': 'Campaign subject cannot exceed 200 characters',
    }),

    content: Joi.string().required().messages({
      'string.empty': 'Campaign content is required',
    }),

    fromName: Joi.string().required().max(100).messages({
      'string.empty': 'Sender name is required',
      'string.max': 'Sender name cannot exceed 100 characters',
    }),

    fromEmail: Joi.string().required().email().messages({
      'string.empty': 'Sender email is required',
      'string.email': 'Sender email must be valid',
    }),

    // Optional fields
    description: Joi.string().max(500),

    contentType: Joi.string().valid('html', 'text'),

    replyToEmail: Joi.string().email().allow(null).messages({
      'string.email': 'Reply-to email must be valid',
    }),

    segmentId: Joi.string().uuid().allow(null).messages({
      'string.guid': 'Segment ID must be a valid UUID',
    }),

    templateId: Joi.string().uuid().allow(null).messages({
      'string.guid': 'Template ID must be a valid UUID',
    }),

    metadata: Joi.object(),
  }),

  /**
   * Validation schema for scheduling a campaign
   */
  scheduleCampaign: Joi.object({
    scheduledAt: Joi.date().greater('now').required().messages({
      'date.greater': 'Scheduled date must be in the future',
      'any.required': 'Scheduled date is required',
    }),
  }),

  /**
   * Validation schema for failing a campaign
   */
  failCampaign: Joi.object({
    reason: Joi.string().required().max(500).messages({
      'string.empty': 'Failure reason is required',
      'string.max': 'Failure reason cannot exceed 500 characters',
    }),
  }),
};
