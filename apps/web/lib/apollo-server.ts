import { DocumentNode } from 'graphql';
import { createServerApolloClient } from './apollo-client';

/**
 * Helper function to execute GraphQL queries in server components
 *
 * @param query GraphQL query document
 * @param variables Variables for the query
 * @returns Query result data
 */
export async function executeQuery<T = any, V = Record<string, any>>(
  query: DocumentNode,
  variables?: V
): Promise<T> {
  try {
    const client = createServerApolloClient();
    const { data, errors } = await client.query({
      query,
      variables,
    });

    if (errors) {
      console.error('GraphQL errors:', errors);
      throw new Error(`GraphQL errors: ${errors.map(e => e.message).join(', ')}`);
    }

    return data as T;
  } catch (error) {
    console.error('Failed to execute GraphQL query:', error);
    throw error;
  }
}

/**
 * Helper function to execute GraphQL mutations in server actions
 *
 * @param mutation GraphQL mutation document
 * @param variables Variables for the mutation
 * @returns Mutation result data
 */
export async function executeMutation<T = any, V = Record<string, any>>(
  mutation: DocumentNode,
  variables?: V
): Promise<T> {
  try {
    const client = createServerApolloClient();
    const { data, errors } = await client.mutate({
      mutation,
      variables,
    });

    if (errors) {
      console.error('GraphQL errors:', errors);
      throw new Error(`GraphQL errors: ${errors.map(e => e.message).join(', ')}`);
    }

    return data as T;
  } catch (error) {
    console.error('Failed to execute GraphQL mutation:', error);
    throw error;
  }
}
