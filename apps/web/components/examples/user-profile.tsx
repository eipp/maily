'use client';

import { useQuery } from '@apollo/client';
import { CURRENT_USER } from '@/graphql/queries';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
}

interface CurrentUserData {
  currentUser: User;
}

export function UserProfile() {
  const { loading, error, data } = useQuery<CurrentUserData>(CURRENT_USER);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>User Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Skeleton className="h-4 w-[250px]" />
            <Skeleton className="h-4 w-[200px]" />
            <Skeleton className="h-4 w-[150px]" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">Error loading user profile: {error.message}</p>
        </CardContent>
      </Card>
    );
  }

  const user = data?.currentUser;

  if (!user) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>User Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <p>No user data available. Please log in.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>User Profile</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <p className="font-medium">Name: <span className="font-normal">{user.firstName} {user.lastName}</span></p>
          <p className="font-medium">Email: <span className="font-normal">{user.email}</span></p>
          <p className="font-medium">Role: <span className="font-normal capitalize">{user.role}</span></p>
        </div>
      </CardContent>
    </Card>
  );
}
