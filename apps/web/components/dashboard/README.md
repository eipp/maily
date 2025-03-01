# Contact Intelligence Dashboard Components

This directory contains components for the Contact Intelligence Dashboard feature, which provides advanced contact list management, health visualization, and list cleaning capabilities.

## Components

### ContactIntelligenceDashboard

The main dashboard component that integrates all contact intelligence features. It provides a tabbed interface for viewing different aspects of contact health and management.

```tsx
import { ContactIntelligenceDashboard } from './dashboard/contact-intelligence-dashboard';

// Usage
<ContactIntelligenceDashboard userId="user_123" />
```

**Props**:
- `userId`: (string) - Required. The ID of the user whose contacts to display.
- `listId`: (string) - Optional. Filter contacts by list ID.
- `initialTab`: (string) - Optional. Set the initially active tab. Default: 'health'.

### ContactHealthVisualization

A component for visualizing contact health metrics using interactive charts and graphs.

```tsx
import { ContactHealthVisualization } from './dashboard/contact-health-visualization';

// Usage
<ContactHealthVisualization healthScore={healthScore} />
```

**Props**:
- `healthScore`: (HealthScore) - Required. An object containing health metrics:
  ```ts
  interface HealthScore {
    overall: number;
    email_validity: number;
    engagement: number;
    deliverability: number;
    consent_level: string;
    domain_reputation: number;
    last_evaluated: string;
  }
  ```

## API Integration

The components use the following API endpoints:

- `GET /api/contacts` - Get contacts with filtering
- `GET /api/contacts/{contact_id}/health` - Get contact health metrics
- `POST /api/contacts/{contact_id}/validate` - Validate a contact
- `GET /api/contacts/{contact_id}/lifecycle` - Get contact lifecycle metrics
- `GET /api/contacts/{contact_id}/blockchain-verifications` - Get blockchain verifications
- `POST /api/contacts/{contact_id}/verify-blockchain` - Create a blockchain verification
- `GET /api/contacts/{contact_id}/compliance` - Get compliance data
- `POST /api/contacts/{contact_id}/run-compliance-checks` - Run compliance checks
- `POST /api/contacts/clean-list` - Clean a contact list

See the [API Documentation](../../../docs/api/api-documentation.md) for details on these endpoints.

## Examples

### Basic Dashboard

```tsx
import { ContactIntelligenceDashboard } from './dashboard/contact-intelligence-dashboard';

export default function ContactsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Contact Intelligence</h1>
      <ContactIntelligenceDashboard userId="current_user_id" />
    </div>
  );
}
```

### Standalone Health Visualization

```tsx
import { useState, useEffect } from 'react';
import { ContactHealthVisualization } from './dashboard/contact-health-visualization';

export default function ContactHealthPage({ contactId }) {
  const [healthScore, setHealthScore] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHealthScore() {
      try {
        const response = await fetch(`/api/contacts/${contactId}/health`);
        const data = await response.json();
        setHealthScore(data.data.health_scores);
      } catch (error) {
        console.error('Error fetching health score:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchHealthScore();
  }, [contactId]);

  if (loading) return <div>Loading health data...</div>;

  return (
    <div className="max-w-xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">Contact Health</h2>
      {healthScore && <ContactHealthVisualization healthScore={healthScore} />}
    </div>
  );
}
```

## Styling

These components use Tailwind CSS for styling. You can customize the appearance by modifying the Tailwind classes or by wrapping the components with your own styled containers.

## Contributing

When enhancing these components, please maintain the existing patterns:

1. Use TypeScript interfaces for props
2. Implement proper loading states
3. Handle errors gracefully
4. Follow the existing styling conventions
5. Update this README when adding new components
