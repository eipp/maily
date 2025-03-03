import { ethers } from 'ethers';
import { logger } from '../utils/logger';
import { EmailVerificationABI } from '../contracts/EmailVerificationABI';
import { CertificateABI } from '../contracts/CertificateABI';
import { retry } from '../utils/retry';
import { BatchTransactionManager } from '../utils/batch_transaction';
import * as crypto from 'crypto';

// Environment variables
const POLYGON_RPC_URL = process.env.POLYGON_RPC_URL || 'https://polygon-rpc.com';
const EMAIL_VERIFICATION_CONTRACT_ADDRESS = process.env.EMAIL_VERIFICATION_CONTRACT_ADDRESS || '';
const CERTIFICATE_CONTRACT_ADDRESS = process.env.CERTIFICATE_CONTRACT_ADDRESS || '';
const WALLET_PRIVATE_KEY = process.env.WALLET_PRIVATE_KEY || '';
const MULTICALL_CONTRACT_ADDRESS = process.env.MULTICALL_CONTRACT_ADDRESS || '0x11ce4B23bD875D7F5C6a31084f55fDe1e9A87507'; // Polygon Multicall address
const GAS_PRICE_MULTIPLIER = Number(process.env.GAS_PRICE_MULTIPLIER || '1.1');
const MAX_GAS_PRICE = ethers.utils.parseUnits(process.env.MAX_GAS_PRICE || '100', 'gwei');
const RETRY_ATTEMPTS = Number(process.env.BLOCKCHAIN_RETRY_ATTEMPTS || '3');
const BATCH_SIZE_LIMIT = Number(process.env.BATCH_SIZE_LIMIT || '10');
const BATCH_PROCESSING_TIMEOUT = Number(process.env.BATCH_PROCESSING_TIMEOUT || '30000'); // 30 seconds

// Certificate types
export enum CertificateType {
  EMAIL_VERIFICATION = 0,
  SENDER_IDENTITY = 1,
  CONTENT_INTEGRITY = 2,
  DOMAIN_VERIFICATION = 3,
}

// Certificate status
export enum CertificateStatus {
  PENDING = 0,
  VERIFIED = 1,
  REVOKED = 2,
  EXPIRED = 3,
}

// Certificate interface
export interface Certificate {
  id: string;
  type: CertificateType;
  issuer: string;
  subject: string;
  issuedAt: number;
  expiresAt: number;
  status: CertificateStatus;
  metadataURI: string;
  signature: string;
}

// Email verification data
export interface EmailVerificationData {
  emailId: string;
  sender: string;
  recipient: string;
  subject: string;
  contentHash: string;
  timestamp: number;
}

/**
 * Blockchain service for interacting with the Polygon blockchain
 * for email verification and certificate management.
 */
export class BlockchainService {
  private provider: ethers.providers.JsonRpcProvider;
  private wallet: ethers.Wallet;
  private emailVerificationContract: ethers.Contract;
  private certificateContract: ethers.Contract;
  private batchManager: BatchTransactionManager;
  private pendingVerifications: Map<string, any> = new Map();
  private pendingCertificates: Map<string, any> = new Map();

  constructor() {
    // Initialize provider
    this.provider = new ethers.providers.JsonRpcProvider(POLYGON_RPC_URL);
    
    // Initialize wallet
    this.wallet = new ethers.Wallet(WALLET_PRIVATE_KEY, this.provider);
    
    // Initialize contracts
    this.emailVerificationContract = new ethers.Contract(
      EMAIL_VERIFICATION_CONTRACT_ADDRESS,
      EmailVerificationABI,
      this.wallet
    );
    
    this.certificateContract = new ethers.Contract(
      CERTIFICATE_CONTRACT_ADDRESS,
      CertificateABI,
      this.wallet
    );
    
    // Initialize batch transaction manager
    this.batchManager = new BatchTransactionManager(
      this.wallet,
      MULTICALL_CONTRACT_ADDRESS,
      {
        batchSizeLimit: BATCH_SIZE_LIMIT,
        processingTimeout: BATCH_PROCESSING_TIMEOUT
      }
    );
    
    logger.info('BlockchainService initialized with batch transaction support');
  }

  /**
   * Get the current gas price with optimization
   */
  private async getOptimizedGasPrice(): Promise<ethers.BigNumber> {
    try {
      const gasPrice = await this.provider.getGasPrice();
      const optimizedGasPrice = gasPrice.mul(Math.floor(GAS_PRICE_MULTIPLIER * 100)).div(100);
      
      // Cap at maximum gas price
      return optimizedGasPrice.gt(MAX_GAS_PRICE) ? MAX_GAS_PRICE : optimizedGasPrice;
    } catch (error) {
      logger.error('Error getting gas price:', error);
      return ethers.utils.parseUnits('50', 'gwei'); // Fallback gas price
    }
  }

  /**
   * Verify an email on the blockchain
   * @param emailData Email verification data
   * @returns Transaction hash
   */
  async verifyEmail(emailData: EmailVerificationData): Promise<string> {
    try {
      logger.info(`Verifying email ${emailData.emailId} on blockchain`);
      
      // Encode function call data
      const encodedData = this.emailVerificationContract.interface.encodeFunctionData(
        'verifyEmail',
        [
          emailData.emailId,
          emailData.sender,
          emailData.recipient,
          emailData.subject,
          emailData.contentHash,
          emailData.timestamp
        ]
      );
      
      // Prepare transaction for batching
      const transaction = {
        to: EMAIL_VERIFICATION_CONTRACT_ADDRESS,
        data: encodedData
      };
      
      // Store pending verification for tracking
      this.pendingVerifications.set(emailData.emailId, emailData);
      
      // Add to batch and get result when processed
      try {
        const batchResult = await this.batchManager.addTransaction(transaction);
        
        // In a real implementation, we would parse the events to find the specific event for this email
        // For now, we'll just return the batch transaction hash
        logger.info(`Email ${emailData.emailId} verification added to batch, tx hash: ${batchResult.transactionHash}`);
        
        return batchResult.transactionHash;
      } catch (error) {
        // If batching fails, fall back to direct transaction
        logger.warn(`Batch processing failed for email ${emailData.emailId}, falling back to direct transaction`);
        
        // Remove from pending verifications
        this.pendingVerifications.delete(emailData.emailId);
        
        // Fallback to direct transaction
        return this.verifyEmailDirect(emailData);
      }
    } catch (error) {
      logger.error(`Error verifying email ${emailData.emailId} on blockchain:`, error);
      throw new Error(`Blockchain verification failed: ${error.message}`);
    }
  }
  
  /**
   * Direct (non-batched) verification fallback
   * @param emailData Email verification data
   * @returns Transaction hash
   */
  private async verifyEmailDirect(emailData: EmailVerificationData): Promise<string> {
    try {
      // Get optimized gas price
      const gasPrice = await this.getOptimizedGasPrice();
      
      // Estimate gas for the transaction
      const gasEstimate = await this.emailVerificationContract.estimateGas.verifyEmail(
        emailData.emailId,
        emailData.sender,
        emailData.recipient,
        emailData.subject,
        emailData.contentHash,
        emailData.timestamp
      );
      
      // Add 20% buffer to gas estimate
      const gasLimit = gasEstimate.mul(120).div(100);
      
      // Execute transaction with retry logic
      const tx = await retry(
        async () => this.emailVerificationContract.verifyEmail(
          emailData.emailId,
          emailData.sender,
          emailData.recipient,
          emailData.subject,
          emailData.contentHash,
          emailData.timestamp,
          {
            gasPrice,
            gasLimit,
          }
        ),
        RETRY_ATTEMPTS,
        1000
      );
      
      // Wait for transaction to be mined
      const receipt = await tx.wait();
      
      logger.info(`Email ${emailData.emailId} verified directly on blockchain, tx hash: ${receipt.transactionHash}`);
      
      return receipt.transactionHash;
    } catch (error) {
      logger.error(`Error in direct verification for email ${emailData.emailId}:`, error);
      throw new Error(`Direct blockchain verification failed: ${error.message}`);
    }
  }

  /**
   * Issue a certificate on the blockchain
   * @param certificate Certificate data
   * @returns Transaction hash and certificate ID
   */
  async issueCertificate(certificate: Omit<Certificate, 'id'>): Promise<{ id: string, txHash: string }> {
    try {
      logger.info(`Issuing certificate for ${certificate.subject}`);
      
      // Generate a temporary certificate ID for tracking
      // In production, this would be handled more robustly
      const tempCertId = `temp-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;
      
      // Encode function call data
      const encodedData = this.certificateContract.interface.encodeFunctionData(
        'issueCertificate',
        [
          certificate.type,
          certificate.issuer,
          certificate.subject,
          certificate.issuedAt,
          certificate.expiresAt,
          certificate.metadataURI,
          certificate.signature
        ]
      );
      
      // Prepare transaction for batching
      const transaction = {
        to: CERTIFICATE_CONTRACT_ADDRESS,
        data: encodedData
      };
      
      // Store pending certificate for tracking
      this.pendingCertificates.set(tempCertId, {
        certificate,
        timestamp: Date.now()
      });
      
      // Add to batch and get result when processed
      try {
        const batchResult = await this.batchManager.addTransaction(transaction);
        
        // In a real implementation, we would parse the events to find the specific event for this certificate
        // For now, we'll use a deterministic approach to simulate the certificate ID
        // This would be replaced with actual event parsing in production
        const simulatedCertificateId = `cert-${hashString(`${certificate.subject}-${certificate.issuedAt}-${batchResult.transactionHash}`)}`;
        
        logger.info(`Certificate for ${certificate.subject} added to batch, simulated ID: ${simulatedCertificateId}, tx hash: ${batchResult.transactionHash}`);
        
        // Remove from pending certificates
        this.pendingCertificates.delete(tempCertId);
        
        return {
          id: simulatedCertificateId,
          txHash: batchResult.transactionHash
        };
      } catch (error) {
        // If batching fails, fall back to direct transaction
        logger.warn(`Batch processing failed for certificate issuance, falling back to direct transaction`);
        
        // Remove from pending certificates
        this.pendingCertificates.delete(tempCertId);
        
        // Fallback to direct transaction
        return this.issueCertificateDirect(certificate);
      }
    } catch (error) {
      logger.error(`Error issuing certificate:`, error);
      throw new Error(`Certificate issuance failed: ${error.message}`);
    }
  }
  
  /**
   * Direct (non-batched) certificate issuance fallback
   * @param certificate Certificate data
   * @returns Transaction hash and certificate ID
   */
  private async issueCertificateDirect(certificate: Omit<Certificate, 'id'>): Promise<{ id: string, txHash: string }> {
    try {
      // Get optimized gas price
      const gasPrice = await this.getOptimizedGasPrice();
      
      // Estimate gas for the transaction
      const gasEstimate = await this.certificateContract.estimateGas.issueCertificate(
        certificate.type,
        certificate.issuer,
        certificate.subject,
        certificate.issuedAt,
        certificate.expiresAt,
        certificate.metadataURI,
        certificate.signature
      );
      
      // Add 20% buffer to gas estimate
      const gasLimit = gasEstimate.mul(120).div(100);
      
      // Execute transaction with retry logic
      const tx = await retry(
        async () => this.certificateContract.issueCertificate(
          certificate.type,
          certificate.issuer,
          certificate.subject,
          certificate.issuedAt,
          certificate.expiresAt,
          certificate.metadataURI,
          certificate.signature,
          {
            gasPrice,
            gasLimit,
          }
        ),
        RETRY_ATTEMPTS,
        1000
      );
      
      // Wait for transaction to be mined
      const receipt = await tx.wait();
      
      // Get certificate ID from event logs
      const event = receipt.events?.find(e => e.event === 'CertificateIssued');
      const certificateId = event?.args?.certificateId;
      
      logger.info(`Certificate issued directly with ID ${certificateId}, tx hash: ${receipt.transactionHash}`);
      
      return {
        id: certificateId,
        txHash: receipt.transactionHash,
      };
    } catch (error) {
      logger.error(`Error in direct certificate issuance:`, error);
      throw new Error(`Direct certificate issuance failed: ${error.message}`);
    }
  }

  /**
   * Revoke a certificate on the blockchain
   * @param certificateId Certificate ID
   * @param reason Revocation reason
   * @returns Transaction hash
   */
  async revokeCertificate(certificateId: string, reason: string): Promise<string> {
    try {
      logger.info(`Revoking certificate ${certificateId}`);
      
      // Get optimized gas price
      const gasPrice = await this.getOptimizedGasPrice();
      
      // Estimate gas for the transaction
      const gasEstimate = await this.certificateContract.estimateGas.revokeCertificate(
        certificateId,
        reason
      );
      
      // Add 20% buffer to gas estimate
      const gasLimit = gasEstimate.mul(120).div(100);
      
      // Execute transaction with retry logic
      const tx = await retry(
        async () => this.certificateContract.revokeCertificate(
          certificateId,
          reason,
          {
            gasPrice,
            gasLimit,
          }
        ),
        RETRY_ATTEMPTS,
        1000
      );
      
      // Wait for transaction to be mined
      const receipt = await tx.wait();
      
      logger.info(`Certificate ${certificateId} revoked, tx hash: ${receipt.transactionHash}`);
      
      return receipt.transactionHash;
    } catch (error) {
      logger.error(`Error revoking certificate ${certificateId}:`, error);
      throw new Error(`Certificate revocation failed: ${error.message}`);
    }
  }

  /**
   * Get certificate details from the blockchain
   * @param certificateId Certificate ID
   * @returns Certificate details
   */
  async getCertificate(certificateId: string): Promise<Certificate> {
    try {
      logger.info(`Getting certificate ${certificateId}`);
      
      const certificate = await this.certificateContract.getCertificate(certificateId);
      
      return {
        id: certificateId,
        type: certificate.certificateType,
        issuer: certificate.issuer,
        subject: certificate.subject,
        issuedAt: certificate.issuedAt.toNumber(),
        expiresAt: certificate.expiresAt.toNumber(),
        status: certificate.status,
        metadataURI: certificate.metadataURI,
        signature: certificate.signature,
      };
    } catch (error) {
      logger.error(`Error getting certificate ${certificateId}:`, error);
      throw new Error(`Failed to retrieve certificate: ${error.message}`);
    }
  }

  /**
   * Verify a certificate on the blockchain
   * @param certificateId Certificate ID
   * @returns Verification status
   */
  async verifyCertificate(certificateId: string): Promise<boolean> {
    try {
      logger.info(`Verifying certificate ${certificateId}`);
      
      const isValid = await this.certificateContract.verifyCertificate(certificateId);
      
      logger.info(`Certificate ${certificateId} verification result: ${isValid}`);
      
      return isValid;
    } catch (error) {
      logger.error(`Error verifying certificate ${certificateId}:`, error);
      throw new Error(`Certificate verification failed: ${error.message}`);
    }
  }

  /**
   * Get certificates by subject
   * @param subject Certificate subject (e.g., email address, domain)
   * @returns Array of certificate IDs
   */
  async getCertificatesBySubject(subject: string): Promise<string[]> {
    try {
      logger.info(`Getting certificates for subject ${subject}`);
      
      const certificateIds = await this.certificateContract.getCertificatesBySubject(subject);
      
      logger.info(`Found ${certificateIds.length} certificates for subject ${subject}`);
      
      return certificateIds;
    } catch (error) {
      logger.error(`Error getting certificates for subject ${subject}:`, error);
      throw new Error(`Failed to retrieve certificates: ${error.message}`);
    }
  }

  /**
   * Get transaction receipt
   * @param txHash Transaction hash
   * @returns Transaction receipt
   */
  async getTransactionReceipt(txHash: string): Promise<ethers.providers.TransactionReceipt> {
    try {
      return await this.provider.getTransactionReceipt(txHash);
    } catch (error) {
      logger.error(`Error getting transaction receipt for ${txHash}:`, error);
      throw new Error(`Failed to get transaction receipt: ${error.message}`);
    }
  }

  /**
   * Get transaction details
   * @param txHash Transaction hash
   * @returns Transaction details
   */
  async getTransaction(txHash: string): Promise<ethers.providers.TransactionResponse> {
    try {
      return await this.provider.getTransaction(txHash);
    } catch (error) {
      logger.error(`Error getting transaction details for ${txHash}:`, error);
      throw new Error(`Failed to get transaction details: ${error.message}`);
    }
  }

  /**
   * Get current block number
   * @returns Current block number
   */
  async getBlockNumber(): Promise<number> {
    try {
      return await this.provider.getBlockNumber();
    } catch (error) {
      logger.error(`Error getting block number:`, error);
      throw new Error(`Failed to get block number: ${error.message}`);
    }
  }

  /**
   * Get block details
   * @param blockNumber Block number
   * @returns Block details
   */
  async getBlock(blockNumber: number): Promise<ethers.providers.Block> {
    try {
      return await this.provider.getBlock(blockNumber);
    } catch (error) {
      logger.error(`Error getting block details for ${blockNumber}:`, error);
      throw new Error(`Failed to get block details: ${error.message}`);
    }
  }
  
  /**
   * Flush all pending transactions in the batch manager
   * @returns Batch transaction result or null if no pending transactions
   */
  async flushPendingTransactions(): Promise<any> {
    try {
      logger.info('Flushing pending blockchain transactions');
      return await this.batchManager.flushBatch();
    } catch (error) {
      logger.error('Error flushing pending transactions:', error);
      throw error;
    }
  }
}

/**
 * Utility function to hash a string
 * @param input String to hash
 * @returns First 16 characters of the hash
 */
function hashString(input: string): string {
  return crypto.createHash('sha256').update(input).digest('hex').substring(0, 16);
}

/**
 * Flush any pending blockchain transactions
 * @returns True if successful
 */
export async function flushPendingTransactions(): Promise<boolean> {
  try {
    const service = new BlockchainService();
    await service.flushPendingTransactions();
    return true;
  } catch (error) {
    logger.error('Failed to flush pending transactions:', error);
    return false;
  }
}

// Export singleton instance
export const blockchainService = new BlockchainService();
