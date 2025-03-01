import { ethers } from 'ethers'
import { apiClient } from '@/lib/api'

// ABI interfaces for contracts
import MailyTokenABI from '../contracts/MailyToken.json'
import TrustCertificateABI from '../contracts/TrustCertificate.json'

/**
 * Configuration for the blockchain service
 */
export interface BlockchainConfig {
  providerUrl: string
  mailerTokenAddress: string
  trustCertificateAddress: string
  chainId: number
  privateKey?: string
}

/**
 * Certificate verification result
 */
export interface CertificateVerification {
  isValid: boolean
  campaignId: string
  metricsHash: string
  issuer: string
  timestamp: number
}

/**
 * Blockchain integration service for Maily
 * Provides functionality for interacting with blockchain contracts
 */
export class BlockchainService {
  private provider: ethers.providers.Provider
  private mailerTokenContract: ethers.Contract
  private trustCertificateContract: ethers.Contract
  private signer: ethers.Signer | null = null
  private connected: boolean = false
  private config: BlockchainConfig

  /**
   * Create a new blockchain service instance
   */
  constructor(config: BlockchainConfig) {
    this.config = config

    // Initialize provider
    this.provider = new ethers.providers.JsonRpcProvider(config.providerUrl)

    // Initialize contract instances
    this.mailerTokenContract = new ethers.Contract(
      config.mailerTokenAddress,
      MailyTokenABI.abi,
      this.provider
    )

    this.trustCertificateContract = new ethers.Contract(
      config.trustCertificateAddress,
      TrustCertificateABI.abi,
      this.provider
    )
  }

  /**
   * Connect to a wallet using private key
   */
  async connectWallet(privateKey: string): Promise<boolean> {
    try {
      this.signer = new ethers.Wallet(privateKey, this.provider)

      // Connect contracts to signer
      this.mailerTokenContract = this.mailerTokenContract.connect(this.signer)
      this.trustCertificateContract = this.trustCertificateContract.connect(this.signer)

      // Verify connection by getting network
      const network = await this.provider.getNetwork()

      // Check if we're on the correct network
      if (network.chainId !== this.config.chainId) {
        console.error(`Wrong network. Connected to ${network.chainId}, expected ${this.config.chainId}`)
        return false
      }

      this.connected = true
      return true
    } catch (error) {
      console.error('Failed to connect wallet:', error)
      this.connected = false
      return false
    }
  }

  /**
   * Connect to a wallet using Web3 provider (e.g. MetaMask)
   */
  async connectWeb3Provider(): Promise<boolean> {
    if (!window.ethereum) {
      console.error('No Web3 provider found')
      return false
    }

    try {
      // Request account access
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' })

      if (accounts.length === 0) {
        console.error('No accounts found')
        return false
      }

      // Create Web3Provider
      const web3Provider = new ethers.providers.Web3Provider(window.ethereum)
      this.provider = web3Provider

      // Get signer
      this.signer = web3Provider.getSigner()

      // Connect contracts to signer
      this.mailerTokenContract = this.mailerTokenContract.connect(this.signer)
      this.trustCertificateContract = this.trustCertificateContract.connect(this.signer)

      // Verify connection by getting network
      const network = await this.provider.getNetwork()

      // Check if we're on the correct network
      if (network.chainId !== this.config.chainId) {
        console.error(`Wrong network. Connected to ${network.chainId}, expected ${this.config.chainId}`)
        return false
      }

      this.connected = true
      return true
    } catch (error) {
      console.error('Failed to connect Web3 provider:', error)
      this.connected = false
      return false
    }
  }

  /**
   * Issue a trust certificate for a campaign
   */
  async issueCertificate(campaignId: string, metricsHash: string): Promise<string> {
    if (!this.signer || !this.connected) {
      throw new Error('Wallet not connected')
    }

    try {
      // Create transaction to issue certificate
      const tx = await this.trustCertificateContract.issueCertificate(
        campaignId,
        metricsHash
      )

      // Wait for transaction confirmation
      const receipt = await tx.wait()

      // Find certificate ID from event logs
      const event = receipt.events?.find(e => e.event === 'CertificateIssued')
      if (!event) {
        throw new Error('Certificate issuance failed')
      }

      return event.args.certificateId
    } catch (error) {
      console.error('Failed to issue certificate:', error)
      throw error
    }
  }

  /**
   * Verify a trust certificate
   */
  async verifyCertificate(certificateId: string): Promise<CertificateVerification> {
    try {
      const result = await this.trustCertificateContract.verifyCertificate(certificateId)

      return {
        isValid: result.isValid,
        campaignId: result.campaignId,
        metricsHash: result.metricsHash,
        issuer: result.issuer,
        timestamp: Number(result.timestamp)
      }
    } catch (error) {
      console.error('Failed to verify certificate:', error)
      throw error
    }
  }

  /**
   * Distribute tokens to a user
   */
  async distributeTokens(userId: string, amount: ethers.BigNumber): Promise<string> {
    if (!this.signer || !this.connected) {
      throw new Error('Wallet not connected')
    }

    try {
      // Create transaction to mint and distribute tokens
      const tx = await this.mailerTokenContract.mintAndDistribute(
        userId,
        amount
      )

      // Wait for transaction confirmation
      const receipt = await tx.wait()

      return receipt.transactionHash
    } catch (error) {
      console.error('Failed to distribute tokens:', error)
      throw error
    }
  }

  /**
   * Get token balance for a user
   */
  async getTokenBalance(userId: string): Promise<string> {
    try {
      const balance = await this.mailerTokenContract.userRewards(userId)
      return ethers.utils.formatUnits(balance, 18) // 18 decimals
    } catch (error) {
      console.error('Failed to get token balance:', error)
      throw error
    }
  }

  /**
   * Get wallet token balance
   */
  async getWalletBalance(walletAddress: string): Promise<string> {
    try {
      const balance = await this.mailerTokenContract.balanceOf(walletAddress)
      return ethers.utils.formatUnits(balance, 18) // 18 decimals
    } catch (error) {
      console.error('Failed to get wallet balance:', error)
      throw error
    }
  }

  /**
   * Claim tokens for a user
   */
  async claimTokens(userId: string, walletAddress: string): Promise<string> {
    if (!this.signer || !this.connected) {
      throw new Error('Wallet not connected')
    }

    try {
      // Create transaction to claim tokens
      const tx = await this.mailerTokenContract.claimTokens(userId, walletAddress)

      // Wait for transaction confirmation
      const receipt = await tx.wait()

      return receipt.transactionHash
    } catch (error) {
      console.error('Failed to claim tokens:', error)
      throw error
    }
  }

  /**
   * Get a list of certificates for a campaign
   */
  async getCampaignCertificates(campaignId: string): Promise<string[]> {
    try {
      // Use the backend API to get certificates since querying events directly is complex
      const response = await apiClient.get(`/api/blockchain/campaign/${campaignId}/certificates`)
      return response.data.certificates || []
    } catch (error) {
      console.error('Failed to get campaign certificates:', error)
      throw error
    }
  }

  /**
   * Get verification details with backend enrichment
   */
  async getEnrichedVerification(certificateId: string): Promise<any> {
    try {
      const response = await apiClient.get(`/api/blockchain/certificates/${certificateId}`)
      return response.data.data
    } catch (error) {
      console.error('Failed to get enriched verification:', error)

      // Fallback to direct contract call
      return this.verifyCertificate(certificateId)
    }
  }

  /**
   * Check if user has a connected wallet
   */
  isConnected(): boolean {
    return this.connected && this.signer !== null
  }

  /**
   * Get the current wallet address
   */
  async getWalletAddress(): Promise<string | null> {
    if (!this.signer) return null

    try {
      return await this.signer.getAddress()
    } catch (error) {
      console.error('Failed to get wallet address:', error)
      return null
    }
  }
}

// Create a singleton instance with default config
let blockchainServiceInstance: BlockchainService | null = null

/**
 * Get the blockchain service instance
 */
export const getBlockchainService = (): BlockchainService => {
  if (!blockchainServiceInstance) {
    // Determine environment-specific configuration
    const isProd = process.env.NODE_ENV === 'production';

    // Load config from environment with production-ready defaults
    const config: BlockchainConfig = {
      providerUrl: process.env.NEXT_PUBLIC_BLOCKCHAIN_PROVIDER_URL ||
                  (isProd ? `https://polygon-mainnet.infura.io/v3/${process.env.INFURA_API_KEY}` :
                           `https://polygon-mumbai.infura.io/v3/${process.env.INFURA_API_KEY}`),
      mailerTokenAddress: process.env.NEXT_PUBLIC_MAILER_TOKEN_ADDRESS ||
                         (isProd ? '0x89205A3A3b2A69De6Dbf7f01ED13B2108B2c43e7' : // Production contract address
                                  '0x0000000000000000000000000000000000000000'), // Test contract address
      trustCertificateAddress: process.env.NEXT_PUBLIC_TRUST_CERTIFICATE_ADDRESS ||
                              (isProd ? '0x71C7656EC7ab88b098defB751B7401B5f6d8976F' : // Production contract address
                                       '0x0000000000000000000000000000000000000000'), // Test contract address
      chainId: parseInt(process.env.NEXT_PUBLIC_BLOCKCHAIN_CHAIN_ID || (isProd ? '137' : '80001')) // 137 for Polygon Mainnet, 80001 for Mumbai testnet
    }

    // Log configuration in development mode
    if (process.env.NODE_ENV !== 'production') {
      console.log('Blockchain configuration:', {
        ...config,
        privateKey: config.privateKey ? '[REDACTED]' : undefined
      });
    }

    blockchainServiceInstance = new BlockchainService(config)
  }

  return blockchainServiceInstance
}

// Smart contract interfaces for TypeScript type checking
export interface MailyToken extends ethers.Contract {
  userRewards(userId: string): Promise<ethers.BigNumber>
  balanceOf(address: string): Promise<ethers.BigNumber>
  mintAndDistribute(userId: string, amount: ethers.BigNumber): Promise<ethers.ContractTransaction>
  claimTokens(userId: string, wallet: string): Promise<ethers.ContractTransaction>
}

export interface TrustCertificate extends ethers.Contract {
  issueCertificate(campaignId: string, metricsHash: string): Promise<ethers.ContractTransaction>
  verifyCertificate(certificateId: string): Promise<CertificateVerification>
  revokeCertificate(certificateId: string): Promise<ethers.ContractTransaction>
}
