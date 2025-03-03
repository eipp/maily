/**
 * Trust Verification Worker
 * 
 * This worker processes blockchain verification tasks for emails and certificates.
 * It handles transaction processing, certificate verification workflows, status updates,
 * and retry mechanisms for failed verifications.
 */

import { ethers } from 'ethers';
import { Queue, QueueScheduler, Worker } from 'bullmq';
import Redis from 'ioredis';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';

// Import services
import { BlockchainService } from '../../email-service/services/blockchain-service';
import { CertificateService } from '../../email-service/services/certificate-service';
import { EmailService } from '../../email-service/services/email-service';

// Import utilities
import { logger } from '../../email-service/utils/logger';
import { retry } from '../../email-service/utils/retry';

// Environment variables
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const QUEUE_NAME = process.env.VERIFICATION_QUEUE_NAME || 'trust-verification';
const CONCURRENCY = parseInt(process.env.VERIFICATION_CONCURRENCY || '5', 10);
const MAX_RETRIES = parseInt(process.env.VERIFICATION_MAX_RETRIES || '3', 10);
const RETRY_DELAY = parseInt(process.env.VERIFICATION_RETRY_DELAY || '60000', 10); // 1 minute
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:3000/api';
const API_KEY = process.env.API_KEY || '';

// Redis connection
const redisConnection = new Redis(REDIS_URL, {
  maxRetriesPerRequest: 3,
  enableReadyCheck: false,
});

// Create queue scheduler
const scheduler = new QueueScheduler(QUEUE_NAME, {
  connection: redisConnection,
});

// Create queue
const verificationQueue = new Queue(QUEUE_NAME, {
  connection: redisConnection,
  defaultJobOptions: {
    attempts: MAX_RETRIES,
    backoff: {
      type: 'exponential',
      delay: RETRY_DELAY,
    },
    removeOnComplete: true,
    removeOnFail: false,
  },
});

// Job types
enum JobType {
  EMAIL_VERIFICATION = 'email_verification',
  CERTIFICATE_ISSUANCE = 'certificate_issuance',
  CERTIFICATE_VERIFICATION = 'certificate_verification',
  CERTIFICATE_REVOCATION = 'certificate_revocation',
  TRANSACTION_MONITORING = 'transaction_monitoring',
}

// Job data interfaces
interface EmailVerificationJob {
  type: JobType.EMAIL_VERIFICATION;
  emailId: string;
  sender: string;
  recipient: string;
  subject: string;
  contentHash: string;
  timestamp: number;
}

interface CertificateIssuanceJob {
  type: JobType.CERTIFICATE_ISSUANCE;
  certificateType: number;
  issuer: string;
  subject: string;
  issuedAt: number;
  expiresAt: number;
  metadataURI: string;
  signature: string;
}

interface CertificateVerificationJob {
  type: JobType.CERTIFICATE_VERIFICATION;
  certificateId: string;
}

interface CertificateRevocationJob {
  type: JobType.CERTIFICATE_REVOCATION;
  certificateId: string;
  reason: string;
}

interface TransactionMonitoringJob {
  type: JobType.TRANSACTION_MONITORING;
  transactionHash: string;
  jobId: string;
  originalJobType: JobType;
}

type VerificationJob =
  | EmailVerificationJob
  | CertificateIssuanceJob
  | CertificateVerificationJob
  | CertificateRevocationJob
  | TransactionMonitoringJob;

// Initialize services
const blockchainService = new BlockchainService();
const certificateService = new CertificateService();
const emailService = new EmailService();

// Create worker
const worker = new Worker<VerificationJob>(
  QUEUE_NAME,
  async (job) => {
    const { data } = job;
    
    logger.info(`Processing job ${job.id} of type ${data.type}`);
    
    try {
      switch (data.type) {
        case JobType.EMAIL_VERIFICATION:
          return await processEmailVerification(data, job);
        
        case JobType.CERTIFICATE_ISSUANCE:
          return await processCertificateIssuance(data, job);
        
        case JobType.CERTIFICATE_VERIFICATION:
          return await processCertificateVerification(data, job);
        
        case JobType.CERTIFICATE_REVOCATION:
          return await processCertificateRevocation(data, job);
        
        case JobType.TRANSACTION_MONITORING:
          return await processTransactionMonitoring(data, job);
        
        default:
          throw new Error(`Unknown job type: ${data.type}`);
      }
    } catch (error) {
      logger.error(`Error processing job ${job.id}:`, error);
      
      // Update status in API
      await updateVerificationStatus(job.id, 'failed', {
        error: error.message,
        timestamp: Date.now(),
      });
      
      throw error;
    }
  },
  { connection: redisConnection, concurrency: CONCURRENCY }
);

/**
 * Process email verification job
 */
async function processEmailVerification(
  data: EmailVerificationJob,
  job: any
): Promise<any> {
  logger.info(`Verifying email ${data.emailId} on blockchain`);
  
  // Update status to in-progress
  await updateVerificationStatus(job.id, 'in_progress', {
    emailId: data.emailId,
    timestamp: Date.now(),
  });
  
  try {
    // Verify email on blockchain
    const txHash = await blockchainService.verifyEmail({
      emailId: data.emailId,
      sender: data.sender,
      recipient: data.recipient,
      subject: data.subject,
      contentHash: data.contentHash,
      timestamp: data.timestamp,
    });
    
    logger.info(`Email ${data.emailId} verification transaction submitted: ${txHash}`);
    
    // Add transaction monitoring job
    await verificationQueue.add(
      `tx-monitoring-${txHash}`,
      {
        type: JobType.TRANSACTION_MONITORING,
        transactionHash: txHash,
        jobId: job.id,
        originalJobType: JobType.EMAIL_VERIFICATION,
      }
    );
    
    // Update status to pending confirmation
    await updateVerificationStatus(job.id, 'pending_confirmation', {
      emailId: data.emailId,
      transactionHash: txHash,
      timestamp: Date.now(),
    });
    
    return { transactionHash: txHash };
  } catch (error) {
    logger.error(`Error verifying email ${data.emailId}:`, error);
    
    // Update status to failed
    await updateVerificationStatus(job.id, 'failed', {
      emailId: data.emailId,
      error: error.message,
      timestamp: Date.now(),
    });
    
    throw error;
  }
}

/**
 * Process certificate issuance job
 */
async function processCertificateIssuance(
  data: CertificateIssuanceJob,
  job: any
): Promise<any> {
  logger.info(`Issuing certificate for ${data.subject}`);
  
  // Update status to in-progress
  await updateVerificationStatus(job.id, 'in_progress', {
    subject: data.subject,
    certificateType: data.certificateType,
    timestamp: Date.now(),
  });
  
  try {
    // Issue certificate on blockchain
    const result = await blockchainService.issueCertificate({
      type: data.certificateType,
      issuer: data.issuer,
      subject: data.subject,
      issuedAt: data.issuedAt,
      expiresAt: data.expiresAt,
      metadataURI: data.metadataURI,
      signature: data.signature,
    });
    
    logger.info(`Certificate issued with ID ${result.id}, tx hash: ${result.txHash}`);
    
    // Add transaction monitoring job
    await verificationQueue.add(
      `tx-monitoring-${result.txHash}`,
      {
        type: JobType.TRANSACTION_MONITORING,
        transactionHash: result.txHash,
        jobId: job.id,
        originalJobType: JobType.CERTIFICATE_ISSUANCE,
      }
    );
    
    // Update status to pending confirmation
    await updateVerificationStatus(job.id, 'pending_confirmation', {
      certificateId: result.id,
      transactionHash: result.txHash,
      timestamp: Date.now(),
    });
    
    return {
      certificateId: result.id,
      transactionHash: result.txHash,
    };
  } catch (error) {
    logger.error(`Error issuing certificate for ${data.subject}:`, error);
    
    // Update status to failed
    await updateVerificationStatus(job.id, 'failed', {
      subject: data.subject,
      error: error.message,
      timestamp: Date.now(),
    });
    
    throw error;
  }
}

/**
 * Process certificate verification job
 */
async function processCertificateVerification(
  data: CertificateVerificationJob,
  job: any
): Promise<any> {
  logger.info(`Verifying certificate ${data.certificateId}`);
  
  // Update status to in-progress
  await updateVerificationStatus(job.id, 'in_progress', {
    certificateId: data.certificateId,
    timestamp: Date.now(),
  });
  
  try {
    // Verify certificate on blockchain
    const isValid = await blockchainService.verifyCertificate(data.certificateId);
    
    logger.info(`Certificate ${data.certificateId} verification result: ${isValid}`);
    
    // Get certificate details
    const certificate = await blockchainService.getCertificate(data.certificateId);
    
    // Update status to completed
    await updateVerificationStatus(job.id, 'completed', {
      certificateId: data.certificateId,
      isValid,
      certificate,
      timestamp: Date.now(),
    });
    
    return { isValid, certificate };
  } catch (error) {
    logger.error(`Error verifying certificate ${data.certificateId}:`, error);
    
    // Update status to failed
    await updateVerificationStatus(job.id, 'failed', {
      certificateId: data.certificateId,
      error: error.message,
      timestamp: Date.now(),
    });
    
    throw error;
  }
}

/**
 * Process certificate revocation job
 */
async function processCertificateRevocation(
  data: CertificateRevocationJob,
  job: any
): Promise<any> {
  logger.info(`Revoking certificate ${data.certificateId}`);
  
  // Update status to in-progress
  await updateVerificationStatus(job.id, 'in_progress', {
    certificateId: data.certificateId,
    timestamp: Date.now(),
  });
  
  try {
    // Revoke certificate on blockchain
    const txHash = await blockchainService.revokeCertificate(
      data.certificateId,
      data.reason
    );
    
    logger.info(`Certificate ${data.certificateId} revocation transaction submitted: ${txHash}`);
    
    // Add transaction monitoring job
    await verificationQueue.add(
      `tx-monitoring-${txHash}`,
      {
        type: JobType.TRANSACTION_MONITORING,
        transactionHash: txHash,
        jobId: job.id,
        originalJobType: JobType.CERTIFICATE_REVOCATION,
      }
    );
    
    // Update status to pending confirmation
    await updateVerificationStatus(job.id, 'pending_confirmation', {
      certificateId: data.certificateId,
      transactionHash: txHash,
      timestamp: Date.now(),
    });
    
    return { transactionHash: txHash };
  } catch (error) {
    logger.error(`Error revoking certificate ${data.certificateId}:`, error);
    
    // Update status to failed
    await updateVerificationStatus(job.id, 'failed', {
      certificateId: data.certificateId,
      error: error.message,
      timestamp: Date.now(),
    });
    
    throw error;
  }
}

/**
 * Process transaction monitoring job
 */
async function processTransactionMonitoring(
  data: TransactionMonitoringJob,
  job: any
): Promise<any> {
  logger.info(`Monitoring transaction ${data.transactionHash}`);
  
  try {
    // Get transaction receipt
    const receipt = await blockchainService.getTransactionReceipt(data.transactionHash);
    
    // If receipt is null, transaction is still pending
    if (!receipt) {
      logger.info(`Transaction ${data.transactionHash} is still pending`);
      
      // Requeue the job with delay
      throw new Error('Transaction still pending');
    }
    
    // Check if transaction was successful
    if (receipt.status === 0) {
      logger.error(`Transaction ${data.transactionHash} failed`);
      
      // Update status to failed
      await updateVerificationStatus(data.jobId, 'failed', {
        transactionHash: data.transactionHash,
        error: 'Transaction failed on blockchain',
        timestamp: Date.now(),
      });
      
      return { success: false, receipt };
    }
    
    logger.info(`Transaction ${data.transactionHash} confirmed with ${receipt.confirmations} confirmations`);
    
    // Get block details
    const block = await blockchainService.getBlock(receipt.blockNumber);
    
    // Update status based on original job type
    switch (data.originalJobType) {
      case JobType.EMAIL_VERIFICATION:
        await updateVerificationStatus(data.jobId, 'completed', {
          transactionHash: data.transactionHash,
          blockNumber: receipt.blockNumber,
          blockTimestamp: block.timestamp,
          confirmations: receipt.confirmations,
          timestamp: Date.now(),
        });
        break;
      
      case JobType.CERTIFICATE_ISSUANCE:
        await updateVerificationStatus(data.jobId, 'completed', {
          transactionHash: data.transactionHash,
          blockNumber: receipt.blockNumber,
          blockTimestamp: block.timestamp,
          confirmations: receipt.confirmations,
          timestamp: Date.now(),
        });
        break;
      
      case JobType.CERTIFICATE_REVOCATION:
        await updateVerificationStatus(data.jobId, 'completed', {
          transactionHash: data.transactionHash,
          blockNumber: receipt.blockNumber,
          blockTimestamp: block.timestamp,
          confirmations: receipt.confirmations,
          timestamp: Date.now(),
        });
        break;
    }
    
    return {
      success: true,
      receipt,
      blockNumber: receipt.blockNumber,
      blockTimestamp: block.timestamp,
    };
  } catch (error) {
    // If transaction is still pending, requeue the job
    if (error.message === 'Transaction still pending') {
      // Throw error to trigger retry with backoff
      throw error;
    }
    
    logger.error(`Error monitoring transaction ${data.transactionHash}:`, error);
    
    // Update status to failed
    await updateVerificationStatus(data.jobId, 'failed', {
      transactionHash: data.transactionHash,
      error: error.message,
      timestamp: Date.now(),
    });
    
    throw error;
  }
}

/**
 * Update verification status in API
 */
async function updateVerificationStatus(
  jobId: string,
  status: 'pending' | 'in_progress' | 'pending_confirmation' | 'completed' | 'failed',
  details: any
): Promise<void> {
  try {
    await axios.post(
      `${API_BASE_URL}/verification/status`,
      {
        jobId,
        status,
        details,
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
      }
    );
    
    logger.info(`Updated verification status for job ${jobId} to ${status}`);
  } catch (error) {
    logger.error(`Error updating verification status for job ${jobId}:`, error);
    // Don't throw error here to avoid failing the job
  }
}

// Handle worker events
worker.on('completed', (job) => {
  logger.info(`Job ${job.id} completed successfully`);
});

worker.on('failed', (job, error) => {
  logger.error(`Job ${job.id} failed: ${error.message}`);
});

worker.on('error', (error) => {
  logger.error(`Worker error: ${error.message}`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down worker');
  await worker.close();
  await scheduler.close();
  await redisConnection.quit();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('SIGINT received, shutting down worker');
  await worker.close();
  await scheduler.close();
  await redisConnection.quit();
  process.exit(0);
});

// Export queue for adding jobs
export { verificationQueue, JobType };

// Export job type interfaces
export type {
  EmailVerificationJob,
  CertificateIssuanceJob,
  CertificateVerificationJob,
  CertificateRevocationJob,
  TransactionMonitoringJob,
  VerificationJob,
};
