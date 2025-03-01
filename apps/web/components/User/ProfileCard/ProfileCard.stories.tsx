import type { Meta, StoryObj } from '@storybook/react';
import { ProfileCard } from './ProfileCard';

/**
 * The ProfileCard component displays user profile information with options to view and edit
 * user details. It supports both view and edit modes and integrates with the application's
 * authentication and user management systems.
 */
const meta: Meta<typeof ProfileCard> = {
  title: 'Components/User/ProfileCard',
  component: ProfileCard,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Display and edit user profile information with role-based permissions',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    onSave: {
      action: 'saved',
      description: 'Called when profile changes are saved'
    },
    onCancel: {
      action: 'cancelled',
      description: 'Called when editing is cancelled'
    },
    defaultEditing: {
      control: 'boolean',
      description: 'Whether to start in edit mode',
      defaultValue: false,
    },
    allowEditing: {
      control: 'boolean',
      description: 'Whether to show the edit button',
      defaultValue: true,
    },
  }
};

export default meta;
type Story = StoryObj<typeof ProfileCard>;

export const Default: Story = {
  args: {
    profile: {
      id: '1',
      name: 'Jane Doe',
      email: 'jane@example.com',
      role: 'Admin',
      avatarUrl: 'https://i.pravatar.cc/150?u=jane',
      department: 'Engineering',
      joinDate: '2023-01-15',
    },
    allowEditing: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Default profile view with user information and edit capabilities.',
      },
    },
  },
};

export const WithoutAvatar: Story = {
  args: {
    profile: {
      id: '2',
      name: 'John Smith',
      email: 'john@example.com',
      role: 'User',
      avatarUrl: null,
      department: 'Marketing',
      joinDate: '2024-03-10',
    },
    allowEditing: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Profile without an avatar image, showing the fallback initials.',
      },
    },
  },
};

export const ReadOnly: Story = {
  args: {
    profile: {
      id: '3',
      name: 'Alice Johnson',
      email: 'alice@example.com',
      role: 'Editor',
      avatarUrl: 'https://i.pravatar.cc/150?u=alice',
      department: 'Content',
      joinDate: '2023-11-22',
    },
    allowEditing: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Profile in read-only mode without edit capabilities.',
      },
    },
  },
};

export const EditingMode: Story = {
  args: {
    profile: {
      id: '4',
      name: 'Robert Brown',
      email: 'robert@example.com',
      role: 'Viewer',
      avatarUrl: 'https://i.pravatar.cc/150?u=robert',
      department: 'Sales',
      joinDate: '2024-01-05',
    },
    defaultEditing: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Profile in editing mode with form controls displayed.',
      },
    },
  },
};

export const WithValidationError: Story = {
  args: {
    profile: {
      id: '5',
      name: '', // Empty name to trigger validation
      email: 'invalid-email',
      role: 'User',
      avatarUrl: 'https://i.pravatar.cc/150?u=error',
      department: 'Support',
      joinDate: '2024-02-20',
    },
    defaultEditing: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Profile form showing validation errors for required fields and invalid email.',
      },
    },
  },
};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Profile card in loading state, displayed while fetching user data.',
      },
    },
  },
};
