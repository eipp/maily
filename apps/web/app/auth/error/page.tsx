import { Metadata } from 'next';
import Link from 'next/link';
import { redirect } from 'next/navigation';

export const metadata: Metadata = {
  title: 'Authentication Error - Maily',
  description: 'An error occurred during authentication',
};

export default function AuthErrorPage({
  searchParams,
}: {
  searchParams: { [key: string]: string | string[] | undefined };
}) {
  const error = searchParams.error as string;
  
  // Map error codes to user-friendly messages
  const errorMessages: Record<string, string> = {
    'default': 'An unknown error occurred during authentication.',
    'configuration': 'There is a problem with the server configuration.',
    'accessdenied': 'You do not have permission to sign in.',
    'verification': 'The verification link has expired or has already been used.',
    'signin': 'Try signing in with a different account.',
    'oauthsignin': 'Try signing in with a different account.',
    'oauthcallback': 'Try signing in with a different account.',
    'oauthcreateaccount': 'Try signing in with a different account.',
    'emailcreateaccount': 'Try signing in with a different account.',
    'callback': 'Try signing in with a different account.',
    'oauthaccountnotlinked': 'To confirm your identity, sign in with the same account you used originally.',
    'emailsignin': 'The e-mail could not be sent.',
    'credentialssignin': 'Sign in failed. Check the details you provided are correct.',
    'sessionrequired': 'Please sign in to access this page.',
  };

  const errorMessage = error ? errorMessages[error] || errorMessages.default : errorMessages.default;

  return (
    <div className="text-center">
      <h2 className="mt-2 text-center text-3xl font-bold tracking-tight text-gray-900">
        Authentication Error
      </h2>
      
      <div className="mt-8">
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex justify-center">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">{errorMessage}</h3>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-center space-x-4">
          <Link
            href="/auth/signin"
            className="inline-flex items-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            Back to Sign In
          </Link>
          
          <Link
            href="/"
            className="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            Go to Homepage
          </Link>
        </div>
      </div>
    </div>
  );
}
