import React from 'react';
import type { AppProps } from 'next/app';
import Web3Provider from '../components/Web3/Web3Provider';
import '../styles/globals.css';

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <Web3Provider>
      <Component {...pageProps} />
    </Web3Provider>
  );
}

export default MyApp; 