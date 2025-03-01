import { NextPage } from 'next';
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import CollaborativeCanvas from '../../components/Canvas/CollaborativeCanvas';
import { useAuth } from '../../hooks/useAuth';

const CanvasPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const { isAuthenticated, isLoading } = useAuth();
  const [canvasLoading, setCanvasLoading] = useState(true);
  const [canvasData, setCanvasData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(`/login?return_to=${encodeURIComponent(router.asPath)}`);
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    // Only fetch canvas data if we have an ID
    if (id && isAuthenticated) {
      // Fetch canvas data
      setCanvasLoading(true);
      setError(null);

      fetch(`/api/v1/canvas/${id}/state`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`Error fetching canvas: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          setCanvasData(data);
        })
        .catch(err => {
          console.error('Error loading canvas:', err);
          setError(err.message);
        })
        .finally(() => {
          setCanvasLoading(false);
        });
    }
  }, [id, isAuthenticated]);

  // Show loading state while authentication is being checked
  if (isLoading || !isAuthenticated) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-[calc(100vh-100px)]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={canvasData?.name || 'Canvas'}>
      <div className="h-[calc(100vh-80px)]">
        {canvasLoading ? (
          <div className="flex justify-center items-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading canvas...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex justify-center items-center h-full">
            <div className="text-center max-w-md p-6 bg-red-50 rounded-lg">
              <h2 className="text-xl font-semibold text-red-700 mb-2">Error Loading Canvas</h2>
              <p className="text-red-600">{error}</p>
              <button
                className="mt-4 px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
                onClick={() => router.push('/canvas')}
              >
                Back to Canvas List
              </button>
            </div>
          </div>
        ) : (
          <CollaborativeCanvas
            canvasId={id as string}
            initialState={canvasData?.state}
          />
        )}
      </div>
    </Layout>
  );
};

export default CanvasPage;
