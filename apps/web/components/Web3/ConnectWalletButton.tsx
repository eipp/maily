import React from 'react';
import { useWeb3 } from './Web3Provider';

interface ConnectWalletButtonProps {
  className?: string;
}

export const ConnectWalletButton: React.FC<ConnectWalletButtonProps> = ({ className = '' }) => {
  const { account, isConnected, isConnecting, connect, disconnect } = useWeb3();

  // Format the account address for display
  const formatAddress = (address: string) => {
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  return (
    <button
      onClick={isConnected ? disconnect : connect}
      disabled={isConnecting}
      className={`px-4 py-2 rounded-md font-medium transition-colors ${
        isConnected
          ? 'bg-green-100 text-green-800 hover:bg-green-200'
          : 'bg-blue-600 text-white hover:bg-blue-700'
      } ${isConnecting ? 'opacity-70 cursor-not-allowed' : ''} ${className}`}
    >
      {isConnecting
        ? 'Connecting...'
        : isConnected
        ? `Connected: ${formatAddress(account!)}`
        : 'Connect Wallet'}
    </button>
  );
};

export default ConnectWalletButton; 