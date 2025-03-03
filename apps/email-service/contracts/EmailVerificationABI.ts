/**
 * Email Verification Contract ABI
 * 
 * This module provides the ABI (Application Binary Interface) for the Email Verification
 * smart contract deployed on the Polygon blockchain. The contract is used to verify
 * emails and store verification records on the blockchain.
 */

export const EmailVerificationABI = [
  // Events
  {
    "anonymous": false,
    "inputs": [
      {
        "indexed": true,
        "internalType": "string",
        "name": "emailId",
        "type": "string"
      },
      {
        "indexed": true,
        "internalType": "address",
        "name": "verifier",
        "type": "address"
      },
      {
        "indexed": false,
        "internalType": "uint256",
        "name": "timestamp",
        "type": "uint256"
      }
    ],
    "name": "EmailVerified",
    "type": "event"
  },
  {
    "anonymous": false,
    "inputs": [
      {
        "indexed": true,
        "internalType": "address",
        "name": "previousOwner",
        "type": "address"
      },
      {
        "indexed": true,
        "internalType": "address",
        "name": "newOwner",
        "type": "address"
      }
    ],
    "name": "OwnershipTransferred",
    "type": "event"
  },
  {
    "anonymous": false,
    "inputs": [
      {
        "indexed": true,
        "internalType": "address",
        "name": "verifier",
        "type": "address"
      },
      {
        "indexed": false,
        "internalType": "bool",
        "name": "isAuthorized",
        "type": "bool"
      }
    ],
    "name": "VerifierStatusChanged",
    "type": "event"
  },
  
  // View Functions
  {
    "inputs": [
      {
        "internalType": "string",
        "name": "emailId",
        "type": "string"
      }
    ],
    "name": "getEmailVerification",
    "outputs": [
      {
        "components": [
          {
            "internalType": "string",
            "name": "sender",
            "type": "string"
          },
          {
            "internalType": "string",
            "name": "recipient",
            "type": "string"
          },
          {
            "internalType": "string",
            "name": "subject",
            "type": "string"
          },
          {
            "internalType": "string",
            "name": "contentHash",
            "type": "string"
          },
          {
            "internalType": "uint256",
            "name": "timestamp",
            "type": "uint256"
          },
          {
            "internalType": "address",
            "name": "verifier",
            "type": "address"
          },
          {
            "internalType": "uint256",
            "name": "verificationTimestamp",
            "type": "uint256"
          }
        ],
        "internalType": "struct EmailVerification.EmailRecord",
        "name": "",
        "type": "tuple"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "owner",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "name": "authorizedVerifiers",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "string",
        "name": "emailId",
        "type": "string"
      }
    ],
    "name": "isEmailVerified",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  
  // State-Changing Functions
  {
    "inputs": [],
    "name": "renounceOwnership",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "newOwner",
        "type": "address"
      }
    ],
    "name": "transferOwnership",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "verifier",
        "type": "address"
      },
      {
        "internalType": "bool",
        "name": "isAuthorized",
        "type": "bool"
      }
    ],
    "name": "setVerifier",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "string",
        "name": "emailId",
        "type": "string"
      },
      {
        "internalType": "string",
        "name": "sender",
        "type": "string"
      },
      {
        "internalType": "string",
        "name": "recipient",
        "type": "string"
      },
      {
        "internalType": "string",
        "name": "subject",
        "type": "string"
      },
      {
        "internalType": "string",
        "name": "contentHash",
        "type": "string"
      },
      {
        "internalType": "uint256",
        "name": "timestamp",
        "type": "uint256"
      }
    ],
    "name": "verifyEmail",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  
  // Constructor
  {
    "inputs": [],
    "stateMutability": "nonpayable",
    "type": "constructor"
  }
];
