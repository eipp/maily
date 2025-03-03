# Web3 Integration for Maily

This document outlines the Web3 integration for the Maily application, which enables blockchain functionality through MetaMask and ethers.js.

## Overview

The Web3 integration provides the following capabilities:
- Connect to MetaMask wallet
- Display wallet information (address, chain ID)
- Send transactions
- Interact with smart contracts (future enhancement)

## Components

### 1. Web3Provider

The `Web3Provider` component is the core of the integration. It:
- Wraps the application with MetaMask SDK
- Provides a context for Web3 functionality
- Manages connection state and errors

Location: `components/Web3/Web3Provider.tsx`

### 2. ConnectWalletButton

A reusable button component that:
- Allows users to connect/disconnect their wallet
- Shows connection status
- Displays a shortened version of the connected address

Location: `components/Web3/ConnectWalletButton.tsx`

### 3. SendTransaction

A component that demonstrates sending ETH transactions:
- Allows users to specify recipient and amount
- Handles transaction submission
- Shows transaction status and errors

Location: `components/Web3/SendTransaction.tsx`

## Usage

### Basic Setup

To use Web3 functionality in a component:

```tsx
import { useWeb3 } from '../components/Web3/Web3Provider';

const MyComponent = () => {
  const { account, isConnected, connect } = useWeb3();
  
  return (
    <div>
      {isConnected ? (
        <p>Connected: {account}</p>
      ) : (
        <button onClick={connect}>Connect Wallet</button>
      )}
    </div>
  );
};
```

### Wrapping Your Application

Wrap your application with the Web3Provider:

```tsx
import Web3Provider from '../components/Web3/Web3Provider';

const MyApp = ({ Component, pageProps }) => {
  return (
    <Web3Provider>
      <Component {...pageProps} />
    </Web3Provider>
  );
};

export default MyApp;
```

## Dependencies

- `ethers@6.7.1`: Modern, flexible Ethereum library
- `@metamask/sdk-react@0.15.0`: Official MetaMask SDK for React

## Testing

A test page is available at `/web3-test` that demonstrates all Web3 functionality.

## Future Enhancements

- Smart contract interaction utilities
- Support for multiple wallets (WalletConnect, Coinbase Wallet)
- Token balance display
- NFT integration
- Transaction history

## Security Considerations

- Always validate user input before sending transactions
- Use appropriate error handling for failed transactions
- Consider implementing transaction confirmation modals
- Never expose private keys or sensitive information

## Resources

- [Ethers.js Documentation](https://docs.ethers.org/v6/)
- [MetaMask SDK Documentation](https://docs.metamask.io/sdk/)
- [Web3 Security Best Practices](https://consensys.github.io/smart-contract-best-practices/) 