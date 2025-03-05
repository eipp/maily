/**
 * Standardized Contact model for use across all Maily services
 * 
 * This model represents contact data and is intended to be used by any service
 * that needs to interact with contact information.
 */

import { z } from 'zod';

/**
 * Contact status states
 */
export enum ContactStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  UNSUBSCRIBED = 'unsubscribed',
  BOUNCED = 'bounced',
  COMPLAINED = 'complained',
}

/**
 * Contact tags type
 */
export type ContactTag = string;

/**
 * Address schema definition
 */
export const AddressSchema = z.object({
  street1: z.string().optional(),
  street2: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  postalCode: z.string().optional(),
  country: z.string().optional(),
  type: z.enum(['home', 'work', 'other']).default('home')
});

/**
 * Phone schema definition
 */
export const PhoneSchema = z.object({
  number: z.string(),
  type: z.enum(['mobile', 'home', 'work', 'other']).default('mobile'),
  primary: z.boolean().default(false)
});

/**
 * Custom field schema definition
 */
export const CustomFieldSchema = z.object({
  key: z.string(),
  value: z.union([z.string(), z.number(), z.boolean(), z.null()]),
  type: z.enum(['string', 'number', 'boolean', 'date']).default('string')
});

/**
 * Contact consent schema definition
 */
export const ConsentSchema = z.object({
  marketing: z.boolean().default(false),
  transactional: z.boolean().default(true),
  thirdParty: z.boolean().default(false),
  timestamp: z.date(),
  source: z.string().optional(),
  ipAddress: z.string().optional(),
  userAgent: z.string().optional()
});

/**
 * Activity schema definition
 */
export const ActivitySchema = z.object({
  type: z.string(), // email_open, email_click, etc.
  timestamp: z.date(),
  campaignId: z.string().uuid().optional(),
  metadata: z.record(z.string(), z.any()).optional()
});

/**
 * Contact model schema definition
 */
export const ContactSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  firstName: z.string().optional(),
  lastName: z.string().optional(),
  fullName: z.string().optional(),
  status: z.nativeEnum(ContactStatus).default(ContactStatus.ACTIVE),
  source: z.string().optional(), // form, import, api, etc.
  tags: z.array(z.string()).default([]),
  listIds: z.array(z.string().uuid()).default([]),
  addresses: z.array(AddressSchema).default([]),
  phones: z.array(PhoneSchema).default([]),
  customFields: z.array(CustomFieldSchema).default([]),
  consent: ConsentSchema.optional(),
  activity: z.array(ActivitySchema).default([]),
  lastActivity: z.date().optional(),
  profileImage: z.string().url().optional(),
  createdAt: z.date(),
  updatedAt: z.date(),
  organizationId: z.string().uuid().optional(),
  metadata: z.record(z.string(), z.any()).optional()
});

/**
 * Type definitions derived from the schemas
 */
export type Address = z.infer<typeof AddressSchema>;
export type Phone = z.infer<typeof PhoneSchema>;
export type CustomField = z.infer<typeof CustomFieldSchema>;
export type Consent = z.infer<typeof ConsentSchema>;
export type Activity = z.infer<typeof ActivitySchema>;
export type Contact = z.infer<typeof ContactSchema>;

/**
 * Helper functions for working with Contact objects
 */
export const ContactHelpers = {
  /**
   * Creates the full name from first and last name
   */
  getFullName: (contact: Contact): string => {
    if (contact.fullName) {
      return contact.fullName;
    }
    
    if (contact.firstName && contact.lastName) {
      return `${contact.firstName} ${contact.lastName}`;
    }
    
    if (contact.firstName) {
      return contact.firstName;
    }
    
    if (contact.lastName) {
      return contact.lastName;
    }
    
    return '';
  },

  /**
   * Check if contact has a specific tag
   */
  hasTag: (contact: Contact, tag: ContactTag): boolean => {
    return contact.tags.includes(tag);
  },

  /**
   * Check if contact is active
   */
  isActive: (contact: Contact): boolean => {
    return contact.status === ContactStatus.ACTIVE;
  },

  /**
   * Check if contact is subscribed (active and has marketing consent)
   */
  isSubscribed: (contact: Contact): boolean => {
    return (
      contact.status === ContactStatus.ACTIVE &&
      contact.consent?.marketing === true
    );
  },

  /**
   * Get a custom field value
   */
  getCustomField: (contact: Contact, key: string): any => {
    const field = contact.customFields.find(field => field.key === key);
    return field ? field.value : undefined;
  },

  /**
   * Creates a default contact object
   */
  createDefault: (email: string, firstName?: string, lastName?: string): Contact => {
    const now = new Date();
    return {
      id: crypto.randomUUID(),
      email,
      firstName,
      lastName,
      fullName: firstName && lastName ? `${firstName} ${lastName}` : undefined,
      status: ContactStatus.ACTIVE,
      tags: [],
      listIds: [],
      addresses: [],
      phones: [],
      customFields: [],
      activity: [],
      createdAt: now,
      updatedAt: now,
      consent: {
        marketing: false,
        transactional: true,
        thirdParty: false,
        timestamp: now
      }
    };
  }
};

export default Contact;