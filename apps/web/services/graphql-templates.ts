import { ApolloError } from '@apollo/client';
import {
  GET_TEMPLATES,
  GET_TEMPLATE
} from '@/graphql/queries';
import {
  CREATE_TEMPLATE,
  UPDATE_TEMPLATE,
  DELETE_TEMPLATE
} from '@/graphql/mutations';
import { executeQuery, executeMutation } from '@/lib/apollo-server';

/**
 * Templates GraphQL Service
 * Provides functions for interacting with template data through GraphQL
 */

export interface Template {
  id: string;
  name: string;
  description: string;
  content: string;
  thumbnail?: string;
  category?: string;
  createdAt: string;
  isPopular?: boolean;
}

export interface TemplatesData {
  templates: Template[];
}

export interface TemplateData {
  template: Template;
}

export interface TemplateFilters {
  category?: string;
  createdBy?: string;
  search?: string;
}

export interface TemplateInput {
  name: string;
  description?: string;
  content: string;
  category?: string;
}

/**
 * Fetch templates list with optional filtering and pagination
 */
export async function getTemplates(
  page: number = 1,
  pageSize: number = 10,
  filters?: TemplateFilters
): Promise<Template[]> {
  try {
    const data = await executeQuery<TemplatesData>(GET_TEMPLATES, {
      page,
      pageSize,
      filters
    });
    return data.templates;
  } catch (error) {
    console.error('Failed to fetch templates:', error);
    throw error;
  }
}

/**
 * Fetch a single template by ID
 */
export async function getTemplate(id: string): Promise<Template | null> {
  try {
    const data = await executeQuery<TemplateData>(GET_TEMPLATE, { id });
    return data.template;
  } catch (error) {
    if (error instanceof ApolloError && error.message.includes('not found')) {
      return null;
    }
    console.error(`Failed to fetch template ${id}:`, error);
    throw error;
  }
}

/**
 * Create a new template
 */
export async function createTemplate(template: TemplateInput): Promise<Template> {
  try {
    const response = await executeMutation<{ createTemplate: Template }>(
      CREATE_TEMPLATE,
      template
    );
    return response.createTemplate;
  } catch (error) {
    console.error('Failed to create template:', error);
    throw error;
  }
}

/**
 * Update an existing template
 */
export async function updateTemplate(
  id: string,
  template: Partial<TemplateInput>
): Promise<Template> {
  try {
    const response = await executeMutation<{ updateTemplate: Template }>(
      UPDATE_TEMPLATE,
      { id, ...template }
    );
    return response.updateTemplate;
  } catch (error) {
    console.error(`Failed to update template ${id}:`, error);
    throw error;
  }
}

/**
 * Delete a template
 */
export async function deleteTemplate(id: string): Promise<{ success: boolean; message: string }> {
  try {
    const response = await executeMutation<{
      deleteTemplate: { success: boolean; message: string }
    }>(DELETE_TEMPLATE, { id });
    return response.deleteTemplate;
  } catch (error) {
    console.error(`Failed to delete template ${id}:`, error);
    throw error;
  }
}
