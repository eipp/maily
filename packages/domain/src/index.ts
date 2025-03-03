/**
 * Maily Domain Package
 * 
 * This package contains domain models, types, and business logic
 * that are shared across multiple services in the Maily platform.
 */

// Campaign domain
export * from './campaigns/Campaign';
export * from './campaigns/CampaignStatus';
export * from './campaigns/CampaignTypes';

// Contact domain
export * from './contacts/Contact';
export * from './contacts/ContactList';
export * from './contacts/ContactAttributes';

// Template domain
export * from './templates/Template';
export * from './templates/TemplateVersion';
export * from './templates/TemplateTypes';

// Auth domain
export * from './auth/User';
export * from './auth/Permission';
export * from './auth/Role';

// Common
export * from './common/Result';
export * from './common/Entity';
export * from './common/ValueObject';
export * from './common/Identifier';
export * from './common/DomainEvent';