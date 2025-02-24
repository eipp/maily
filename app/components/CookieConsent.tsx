import React, { useEffect, useState } from 'react';
import CookieConsent, { Cookies } from 'react-cookie-consent';
import { useRouter } from 'next/router';
import Link from 'next/link';

interface CookiePreferences {
  essential: boolean;
  functional: boolean;
  analytics: boolean;
  marketing: boolean;
}

const CookieConsentBanner: React.FC = () => {
  const router = useRouter();
  const [showPreferences, setShowPreferences] = useState(false);
  const [preferences, setPreferences] = useState<CookiePreferences>({
    essential: true, // Essential cookies cannot be disabled
    functional: true,
    analytics: true,
    marketing: false,
  });

  // Load saved preferences
  useEffect(() => {
    const savedPreferences = Cookies.get('cookie-preferences');
    if (savedPreferences) {
      try {
        setPreferences(JSON.parse(savedPreferences));
      } catch (e) {
        console.error('Error parsing cookie preferences:', e);
      }
    }
  }, []);

  // Apply cookie preferences
  const applyCookiePreferences = (prefs: CookiePreferences) => {
    // Essential cookies are always enabled
    if (!prefs.functional) {
      Cookies.remove('user_preferences');
      Cookies.remove('language_preference');
    }
    
    if (!prefs.analytics) {
      // Remove analytics cookies
      Cookies.remove('_ga');
      Cookies.remove('_gid');
      Cookies.remove('_gat');
      window['ga-disable-UA-XXXXXXXX-X'] = true;
    }
    
    if (!prefs.marketing) {
      // Remove marketing cookies
      Cookies.remove('_fbp');
      Cookies.remove('_gcl_au');
    }
    
    // Save preferences
    Cookies.set('cookie-preferences', JSON.stringify(prefs), { expires: 365 });
  };

  const handleAcceptAll = () => {
    const allEnabled: CookiePreferences = {
      essential: true,
      functional: true,
      analytics: true,
      marketing: true,
    };
    setPreferences(allEnabled);
    applyCookiePreferences(allEnabled);
  };

  const handleRejectNonEssential = () => {
    const essentialOnly: CookiePreferences = {
      essential: true,
      functional: false,
      analytics: false,
      marketing: false,
    };
    setPreferences(essentialOnly);
    applyCookiePreferences(essentialOnly);
  };

  const handleSavePreferences = () => {
    applyCookiePreferences(preferences);
    setShowPreferences(false);
  };

  return (
    <>
      <CookieConsent
        location="bottom"
        buttonText="Accept All"
        declineButtonText="Reject Non-Essential"
        cookieName="cookie-consent"
        style={{
          background: '#2B373B',
          padding: '16px',
          alignItems: 'center',
          zIndex: 9999,
        }}
        buttonStyle={{
          background: '#4CAF50',
          color: 'white',
          fontSize: '14px',
          padding: '8px 16px',
          borderRadius: '4px',
        }}
        declineButtonStyle={{
          background: '#f44336',
          color: 'white',
          fontSize: '14px',
          padding: '8px 16px',
          borderRadius: '4px',
        }}
        expires={365}
        onAccept={handleAcceptAll}
        onDecline={handleRejectNonEssential}
      >
        <div className="cookie-consent-content">
          <p>
            We use cookies to enhance your experience. By continuing to visit this site you agree to our use of cookies.{' '}
            <Link href="/privacy/cookies" className="text-blue-400 hover:text-blue-300">
              Learn more
            </Link>
          </p>
          <button
            onClick={() => setShowPreferences(true)}
            className="text-blue-400 hover:text-blue-300 underline ml-2"
          >
            Customize Preferences
          </button>
        </div>
      </CookieConsent>

      {showPreferences && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[10000]">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">Cookie Preferences</h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">Essential Cookies</h3>
                  <p className="text-sm text-gray-600">Required for the website to function</p>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.essential}
                  disabled
                  className="h-4 w-4"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">Functional Cookies</h3>
                  <p className="text-sm text-gray-600">Enhanced functionality and preferences</p>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.functional}
                  onChange={(e) => setPreferences({ ...preferences, functional: e.target.checked })}
                  className="h-4 w-4"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">Analytics Cookies</h3>
                  <p className="text-sm text-gray-600">Help us improve our website</p>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.analytics}
                  onChange={(e) => setPreferences({ ...preferences, analytics: e.target.checked })}
                  className="h-4 w-4"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">Marketing Cookies</h3>
                  <p className="text-sm text-gray-600">Used for targeted advertising</p>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.marketing}
                  onChange={(e) => setPreferences({ ...preferences, marketing: e.target.checked })}
                  className="h-4 w-4"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-4">
              <button
                onClick={() => setShowPreferences(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleSavePreferences}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Save Preferences
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default CookieConsentBanner; 