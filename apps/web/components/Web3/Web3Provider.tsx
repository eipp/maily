import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { ethers } from 'ethers';
import { MetaMaskProvider, useSDK } from '@metamask/sdk-react';

// Define the Web3 context type
interface Web3ContextType {
  account: string | null;
  chainId: string | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  provider: ethers.BrowserProvider | null;
  signer: ethers.JsonRpcSigner | null;
  connect: () => Promise<void>;
  disconnect: () => void;
}

// Create the Web3 context
const Web3Context = createContext<Web3ContextType>({
  account: null,
  chainId: null,
  isConnected: false,
  isConnecting: false,
  error: null,
  provider: null,
  signer: null,
  connect: async () => {},
  disconnect: () => {},
});

// Hook to use the Web3 context
export const useWeb3 = () => useContext(Web3Context);

// Web3 context provider component
const Web3ContextProvider = ({ children }: { children: ReactNode }) => {
  const { sdk, connected, connecting, provider, chainId, account, error } = useSDK();
  
  const [ethersProvider, setEthersProvider] = useState<ethers.BrowserProvider | null>(null);
  const [signer, setSigner] = useState<ethers.JsonRpcSigner | null>(null);

  // Initialize ethers provider when MetaMask provider is available
  useEffect(() => {
    if (provider && connected) {
      const newProvider = new ethers.BrowserProvider(provider as any);
      setEthersProvider(newProvider);
      
      // Get signer
      newProvider.getSigner().then(newSigner => {
        setSigner(newSigner);
      }).catch(err => {
        console.error('Error getting signer:', err);
      });
    } else {
      setEthersProvider(null);
      setSigner(null);
    }
  }, [provider, connected]);

  // Connect to MetaMask
  const connect = async () => {
    try {
      await sdk?.connect();
    } catch (err) {
      console.error('Error connecting to MetaMask:', err);
    }
  };

  // Disconnect from MetaMask
  const disconnect = () => {
    sdk?.disconnect();
  };

  return (
    <Web3Context.Provider
      value={{
        account,
        chainId,
        isConnected: connected,
        isConnecting: connecting,
        error: error ? error.message : null,
        provider: ethersProvider,
        signer,
        connect,
        disconnect,
      }}
    >
      {children}
    </Web3Context.Provider>
  );
};

// Main Web3Provider component that wraps the application
export const Web3Provider = ({ children }: { children: ReactNode }) => {
  return (
    <MetaMaskProvider
      debug={process.env.NODE_ENV === 'development'}
      sdkOptions={{
        dappMetadata: {
          name: 'Maily Web3',
          url: typeof window !== 'undefined' ? window.location.href : '',
        },
        checkInstallationImmediately: false,
        // Optional: Add more configuration options here
      }}
    >
      <Web3ContextProvider>{children}</Web3ContextProvider>
    </MetaMaskProvider>
  );
};

export default Web3Provider; 