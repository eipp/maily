import React, { useState } from 'react';
import { useWeb3 } from './Web3Provider';
import { ethers } from 'ethers';

interface SendTransactionProps {
  className?: string;
}

export const SendTransaction: React.FC<SendTransactionProps> = ({ className = '' }) => {
  const { isConnected, signer } = useWeb3();
  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [txHash, setTxHash] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isConnected || !signer) {
      setError('Please connect your wallet first');
      return;
    }

    if (!ethers.isAddress(recipient)) {
      setError('Invalid recipient address');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      setTxHash(null);

      // Convert amount from ETH to wei
      const weiAmount = ethers.parseEther(amount);
      
      // Send transaction
      const tx = await signer.sendTransaction({
        to: recipient,
        value: weiAmount,
      });

      setTxHash(tx.hash);
      setIsLoading(false);
      
      // Reset form
      setRecipient('');
      setAmount('');
    } catch (err) {
      setError('Transaction failed: ' + (err instanceof Error ? err.message : String(err)));
      setIsLoading(false);
    }
  };

  if (!isConnected) {
    return (
      <div className={`p-4 bg-gray-100 rounded ${className}`}>
        <p className="text-gray-600">Connect your wallet to send transactions</p>
      </div>
    );
  }

  return (
    <div className={`p-4 bg-white rounded border ${className}`}>
      <h3 className="text-lg font-medium mb-4">Send ETH</h3>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}
      
      {txHash && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded">
          Transaction sent! Hash: <br />
          <a 
            href={`https://etherscan.io/tx/${txHash}`} 
            target="_blank" 
            rel="noopener noreferrer"
            className="underline break-all"
          >
            {txHash}
          </a>
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="block text-sm font-medium mb-1">Recipient Address</label>
          <input
            type="text"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            placeholder="0x..."
            className="w-full p-2 border rounded"
            required
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">Amount (ETH)</label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.01"
            step="0.000001"
            min="0"
            className="w-full p-2 border rounded"
            required
          />
        </div>
        
        <button
          type="submit"
          disabled={isLoading}
          className={`w-full p-2 bg-blue-600 text-white rounded font-medium ${
            isLoading ? 'opacity-70 cursor-not-allowed' : 'hover:bg-blue-700'
          }`}
        >
          {isLoading ? 'Sending...' : 'Send Transaction'}
        </button>
      </form>
    </div>
  );
};

export default SendTransaction; 