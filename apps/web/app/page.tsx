import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-r from-blue-500 to-purple-600 text-white">
      <div className="max-w-4xl px-6 py-12 text-center">
        <h1 className="mb-6 text-5xl font-bold">Welcome to Maily</h1>
        <p className="mb-8 text-xl">
          The next-generation email marketing platform powered by artificial intelligence.
        </p>
        <div className="flex flex-col space-y-4 sm:flex-row sm:space-x-4 sm:space-y-0">
          <Link
            href="/dashboard"
            className="rounded-lg bg-white px-6 py-3 text-lg font-medium text-blue-600 shadow-lg transition-all hover:bg-gray-100"
          >
            Go to Dashboard
          </Link>
          <Link
            href="/auth/login"
            className="rounded-lg border border-white bg-transparent px-6 py-3 text-lg font-medium text-white transition-all hover:bg-white/10"
          >
            Login
          </Link>
        </div>
      </div>
    </div>
  );
}
