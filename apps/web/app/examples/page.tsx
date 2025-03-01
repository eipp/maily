import { Suspense } from 'react';
import { UserProfile } from '@/components/examples/user-profile';
import { CampaignsList } from '@/components/examples/campaigns-list';
import { LoginForm } from '@/components/examples/login-form';

export const metadata = {
  title: 'GraphQL Examples | Maily',
  description: 'Example components demonstrating Apollo Client integration',
};

export default function ExamplesPage() {
  return (
    <div className="container py-8 space-y-10">
      <div>
        <h1 className="text-3xl font-bold mb-2">GraphQL Examples</h1>
        <p className="text-muted-foreground mb-8">
          Demonstrating different patterns for using Apollo Client with both client and server components
        </p>
      </div>

      <section>
        <h2 className="text-2xl font-semibold mb-6">Client Component Example</h2>
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-xl font-medium mb-4">User Profile (useQuery)</h3>
            <p className="text-muted-foreground mb-4">
              This component uses the Apollo Client <code>useQuery</code> hook to fetch data on the client side.
            </p>
            <UserProfile />
          </div>
          <div>
            <h3 className="text-xl font-medium mb-4">Login Form (useMutation)</h3>
            <p className="text-muted-foreground mb-4">
              This component demonstrates using the Apollo Client <code>useMutation</code> hook for form submission.
            </p>
            <LoginForm />
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold mb-6">Server Component Example</h2>
        <div>
          <h3 className="text-xl font-medium mb-4">Campaigns List (Server Component)</h3>
          <p className="text-muted-foreground mb-4">
            This component demonstrates fetching data from GraphQL directly in a React Server Component.
          </p>
          <Suspense fallback={<div className="p-8 border rounded-lg">Loading campaigns...</div>}>
            <CampaignsList />
          </Suspense>
        </div>
      </section>
    </div>
  );
}
