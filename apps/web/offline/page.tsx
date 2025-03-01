import { useTranslation } from 'next-i18next';

export default function OfflinePage() {
  const { t } = useTranslation('common');

  return (
    <div className="flex min-h-screen flex-col justify-center bg-gray-50 py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            {t('offline.title', 'You are offline')}
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            {t('offline.description', 'Please check your internet connection and try again.')}
          </p>
          <div className="mt-6">
            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              aria-label={t('offline.retry', 'Retry connection')}
            >
              {t('offline.retry', 'Retry connection')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
