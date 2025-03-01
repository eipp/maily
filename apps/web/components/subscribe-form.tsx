'use client';

import * as React from 'react';
import { useFormState, useFormStatus } from 'react-dom';
import { subscribeToNewsletter } from '@/app/actions';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

// Initial state for form
const initialState = {
  success: false,
  errors: {},
  message: '',
};

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <Button
      type="submit"
      aria-disabled={pending}
      disabled={pending}
      className="w-full"
    >
      {pending ? 'Subscribing...' : 'Subscribe'}
    </Button>
  );
}

export function SubscribeForm() {
  const [state, formAction] = useFormState(subscribeToNewsletter, initialState);
  const [showSuccessMessage, setShowSuccessMessage] = React.useState(false);

  // Reset success message after 5 seconds
  React.useEffect(() => {
    if (state.success) {
      setShowSuccessMessage(true);
      const timer = setTimeout(() => setShowSuccessMessage(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [state.success]);

  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <h3 className="mb-4 text-xl font-semibold">Subscribe to our newsletter</h3>

      {showSuccessMessage ? (
        <div className="mb-4 rounded-md bg-green-50 p-4 text-green-700">
          <p>Thank you for subscribing! Check your email for confirmation.</p>
        </div>
      ) : (
        <form action={formAction} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="name" className="text-sm font-medium">
              Name
            </label>
            <Input
              id="name"
              name="name"
              placeholder="Enter your name"
              aria-describedby="name-error"
            />
            {state.errors?.name && (
              <p id="name-error" className="text-sm text-destructive">
                {state.errors.name}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              Email
            </label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="Enter your email"
              aria-describedby="email-error"
            />
            {state.errors?.email && (
              <p id="email-error" className="text-sm text-destructive">
                {state.errors.email}
              </p>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <input
              id="marketingConsent"
              name="marketingConsent"
              type="checkbox"
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <label htmlFor="marketingConsent" className="text-sm text-muted-foreground">
              I agree to receive marketing emails
            </label>
          </div>

          {state.message && !state.success && (
            <p className="text-sm text-destructive">{state.message}</p>
          )}

          <SubmitButton />
        </form>
      )}
    </div>
  );
}
