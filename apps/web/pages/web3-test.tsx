import React from 'react';
import { ethers } from 'ethers';
import Web3Provider from '../components/Web3/Web3Provider';
import ConnectWalletButton from '../components/Web3/ConnectWalletButton';
import { useWeb3 } from '../components/Web3/Web3Provider';

// Component that displays Web3 information
const Web3Info = () => {
  const { account, chainId, isConnected, error } = useWeb3();

  return (
    <>
      {error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      ) : null}
      
      <div className="bg-gray-100 p-4 rounded mb-4">
        <h2 className="text-xl font-semibold mb-2">MetaMask Connection</h2>
        <p><strong>Status:</strong> {isConnected ? 'Connected' : 'Not connected'}</p>
        <p><strong>Account:</strong> {account || 'Not connected'}</p>
        <p><strong>Chain ID:</strong> {chainId || 'Unknown'}</p>
      </div>
      
      <div className="bg-gray-100 p-4 rounded">
        <h2 className="text-xl font-semibold mb-2">Ethers.js Version</h2>
        <p>{ethers.version}</p>
      </div>
    </>
  );
};

// Main page component
export default function Web3TestPage() {
  return (
    <Web3Provider>
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Web3 Integration Test</h1>
        
        <div className="mb-6">
          <ConnectWalletButton />
        </div>
        
        <Web3Info />
      </div>
    </Web3Provider>
  );
} 