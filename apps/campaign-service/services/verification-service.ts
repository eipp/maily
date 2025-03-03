/**
 * Campaign Verification Service
 * 
 * This service handles verification of campaigns, including blockchain verification,
 * certificate management, and verification workflows.
 */

import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import { logger } from '../utils/logger';
import { Campaign } from '../models/campaign';
import { Certificate, CertificateType, CertificateStatus } from '../models/certificate';
import { VerificationStatus } from '../models/verification';
import { prisma } from '../lib/prisma';
import { ApiError } from '../utils/errors';

// Environment variables
const API_SERVICE_URL = process.env.API_SERVICE_URL || 'http://api-service:8000';
const EMAIL_SERVICE_URL = process.env.EMAIL_SERVICE_URL || 'http://email-service:8002';
const VERIFICATION_WORKER_URL = process.env.VERIFICATION_WORKER_URL || 'http://verification-worker:8080';
const API_KEY = process.env.INTERNAL_API_KEY || '';

/**
 * Campaign Verification Service
 */
export class VerificationService {
  /**
   * Start verification process for a campaign
   * 
   * @param campaignId Campaign ID
   * @returns Verification status
   */
  async startVerification(campaignId: string): Promise<VerificationStatus> {
    logger.info(`Starting verification for campaign ${campaignId}`);
    
    try {
      // Get campaign
      const campaign = await prisma.campaign.findUnique({
        where: { id: campaignId },
        include: {
          certificates: true,
          verificationStatus: true,
        },
      });
      
      if (!campaign) {
        throw new ApiError('Campaign not found', 404);
      }
      
      // Check if verification is already in progress
      if (campaign.verificationStatus?.status === 'in_progress') {
        throw new ApiError('Verification already in progress', 409);
      }
      
      // Create or update verification status
      const verificationStatus = await prisma.verificationStatus.upsert({
        where: { campaignId },
        update: {
          status: 'in_progress',
          startedAt: new Date(),
          completedAt: null,
          error: null,
        },
        create: {
          id: uuidv4(),
          campaignId,
          status: 'in_progress',
          startedAt: new Date(),
        },
      });
      
      // Queue verification job
      await this.queueVerificationJob(campaign);
      
      return verificationStatus;
    } catch (error) {
      logger.error(`Error starting verification for campaign ${campaignId}:`, error);
      
      // Update verification status if it's an API error
      if (error instanceof ApiError) {
        await prisma.verificationStatus.update({
          where: { campaignId },
          data: {
            status: 'failed',
            completedAt: new Date(),
            error: error.message,
          },
        });
      }
      
      throw error;
    }
  }
  
  /**
   * Queue verification job
   * 
   * @param campaign Campaign
   */
  private async queueVerificationJob(campaign: Campaign): Promise<void> {
    try {
      // Send verification job to worker
      await axios.post(
        `${VERIFICATION_WORKER_URL}/verification/campaign`,
        {
          campaignId: campaign.id,
          userId: campaign.userId,
          name: campaign.name,
          content: campaign.content,
          metadata: campaign.metadata,
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
          },
        }
      );
      
      logger.info(`Queued verification job for campaign ${campaign.id}`);
    } catch (error) {
      logger.error(`Error queuing verification job for campaign ${campaign.id}:`, error);
      
      // Update verification status
      await prisma.verificationStatus.update({
        where: { campaignId: campaign.id },
        data: {
          status: 'failed',
          completedAt: new Date(),
          error: 'Failed to queue verification job',
        },
      });
      
      throw new ApiError('Failed to queue verification job', 500);
    }
  }
  
  /**
   * Get verification status for a campaign
   * 
   * @param campaignId Campaign ID
   * @returns Verification status
   */
  async getVerificationStatus(campaignId: string): Promise<VerificationStatus> {
    try {
      const verificationStatus = await prisma.verificationStatus.findUnique({
        where: { campaignId },
      });
      
      if (!verificationStatus) {
        throw new ApiError('Verification status not found', 404);
      }
      
      return verificationStatus;
    } catch (error) {
      logger.error(`Error getting verification status for campaign ${campaignId}:`, error);
      throw error;
    }
  }
  
  /**
   * Update verification status for a campaign
   * 
   * @param campaignId Campaign ID
   * @param status Status
   * @param error Error message (optional)
   * @returns Updated verification status
   */
  async updateVerificationStatus(
    campaignId: string,
    status: 'pending' | 'in_progress' | 'completed' | 'failed',
    error?: string
  ): Promise<VerificationStatus> {
    try {
      const verificationStatus = await prisma.verificationStatus.update({
        where: { campaignId },
        data: {
          status,
          completedAt: status === 'completed' || status === 'failed' ? new Date() : undefined,
          error: error,
        },
      });
      
      logger.info(`Updated verification status for campaign ${campaignId} to ${status}`);
      
      return verificationStatus;
    } catch (error) {
      logger.error(`Error updating verification status for campaign ${campaignId}:`, error);
      throw error;
    }
  }
  
  /**
   * Create certificate for a campaign
   * 
   * @param campaignId Campaign ID
   * @param type Certificate type
   * @param metadata Certificate metadata
   * @returns Created certificate
   */
  async createCertificate(
    campaignId: string,
    type: CertificateType,
    metadata: Record<string, any>
  ): Promise<Certificate> {
    try {
      // Check if campaign exists
      const campaign = await prisma.campaign.findUnique({
        where: { id: campaignId },
      });
      
      if (!campaign) {
        throw new ApiError('Campaign not found', 404);
      }
      
      // Create certificate
      const certificate = await prisma.certificate.create({
        data: {
          id: uuidv4(),
          campaignId,
          type,
          status: CertificateStatus.PENDING,
          metadata,
          issuedAt: new Date(),
        },
      });
      
      logger.info(`Created certificate ${certificate.id} for campaign ${campaignId}`);
      
      // Queue certificate issuance job
      await this.queueCertificateIssuanceJob(certificate);
      
      return certificate;
    } catch (error) {
      logger.error(`Error creating certificate for campaign ${campaignId}:`, error);
      throw error;
    }
  }
  
  /**
   * Queue certificate issuance job
   * 
   * @param certificate Certificate
   */
  private async queueCertificateIssuanceJob(certificate: Certificate): Promise<void> {
    try {
      // Send certificate issuance job to worker
      await axios.post(
        `${VERIFICATION_WORKER_URL}/verification/certificate/issue`,
        {
          certificateId: certificate.id,
          campaignId: certificate.campaignId,
          type: certificate.type,
          metadata: certificate.metadata,
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
          },
        }
      );
      
      logger.info(`Queued certificate issuance job for certificate ${certificate.id}`);
    } catch (error) {
      logger.error(`Error queuing certificate issuance job for certificate ${certificate.id}:`, error);
      
      // Update certificate status
      await prisma.certificate.update({
        where: { id: certificate.id },
        data: {
          status: CertificateStatus.FAILED,
          error: 'Failed to queue certificate issuance job',
        },
      });
      
      throw new ApiError('Failed to queue certificate issuance job', 500);
    }
  }
  
  /**
   * Get certificates for a campaign
   * 
   * @param campaignId Campaign ID
   * @returns Certificates
   */
  async getCertificates(campaignId: string): Promise<Certificate[]> {
    try {
      const certificates = await prisma.certificate.findMany({
        where: { campaignId },
      });
      
      return certificates;
    } catch (error) {
      logger.error(`Error getting certificates for campaign ${campaignId}:`, error);
      throw error;
    }
  }
  
  /**
   * Get certificate by ID
   * 
   * @param certificateId Certificate ID
   * @returns Certificate
   */
  async getCertificate(certificateId: string): Promise<Certificate> {
    try {
      const certificate = await prisma.certificate.findUnique({
        where: { id: certificateId },
      });
      
      if (!certificate) {
        throw new ApiError('Certificate not found', 404);
      }
      
      return certificate;
    } catch (error) {
      logger.error(`Error getting certificate ${certificateId}:`, error);
      throw error;
    }
  }
  
  /**
   * Update certificate status
   * 
   * @param certificateId Certificate ID
   * @param status Certificate status
   * @param transactionHash Blockchain transaction hash (optional)
   * @param error Error message (optional)
   * @returns Updated certificate
   */
  async updateCertificateStatus(
    certificateId: string,
    status: CertificateStatus,
    transactionHash?: string,
    error?: string
  ): Promise<Certificate> {
    try {
      const certificate = await prisma.certificate.update({
        where: { id: certificateId },
        data: {
          status,
          transactionHash,
          error,
          updatedAt: new Date(),
        },
      });
      
      logger.info(`Updated certificate ${certificateId} status to ${status}`);
      
      return certificate;
    } catch (error) {
      logger.error(`Error updating certificate ${certificateId} status:`, error);
      throw error;
    }
  }
  
  /**
   * Revoke certificate
   * 
   * @param certificateId Certificate ID
   * @param reason Revocation reason
   * @returns Revoked certificate
   */
  async revokeCertificate(certificateId: string, reason: string): Promise<Certificate> {
    try {
      // Check if certificate exists
      const certificate = await prisma.certificate.findUnique({
        where: { id: certificateId },
      });
      
      if (!certificate) {
        throw new ApiError('Certificate not found', 404);
      }
      
      // Check if certificate is already revoked
      if (certificate.status === CertificateStatus.REVOKED) {
        throw new ApiError('Certificate already revoked', 409);
      }
      
      // Update certificate status
      const updatedCertificate = await prisma.certificate.update({
        where: { id: certificateId },
        data: {
          status: CertificateStatus.REVOKING,
          revocationReason: reason,
          updatedAt: new Date(),
        },
      });
      
      // Queue certificate revocation job
      await this.queueCertificateRevocationJob(updatedCertificate, reason);
      
      return updatedCertificate;
    } catch (error) {
      logger.error(`Error revoking certificate ${certificateId}:`, error);
      throw error;
    }
  }
  
  /**
   * Queue certificate revocation job
   * 
   * @param certificate Certificate
   * @param reason Revocation reason
   */
  private async queueCertificateRevocationJob(certificate: Certificate, reason: string): Promise<void> {
    try {
      // Send certificate revocation job to worker
      await axios.post(
        `${VERIFICATION_WORKER_URL}/verification/certificate/revoke`,
        {
          certificateId: certificate.id,
          reason,
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
          },
        }
      );
      
      logger.info(`Queued certificate revocation job for certificate ${certificate.id}`);
    } catch (error) {
      logger.error(`Error queuing certificate revocation job for certificate ${certificate.id}:`, error);
      
      // Update certificate status
      await prisma.certificate.update({
        where: { id: certificate.id },
        data: {
          status: CertificateStatus.FAILED,
          error: 'Failed to queue certificate revocation job',
        },
      });
      
      throw new ApiError('Failed to queue certificate revocation job', 500);
    }
  }
  
  /**
   * Verify certificate
   * 
   * @param certificateId Certificate ID
   * @returns Verification result
   */
  async verifyCertificate(certificateId: string): Promise<{ isValid: boolean; details: Record<string, any> }> {
    try {
      // Get certificate
      const certificate = await prisma.certificate.findUnique({
        where: { id: certificateId },
      });
      
      if (!certificate) {
        throw new ApiError('Certificate not found', 404);
      }
      
      // Check if certificate has a transaction hash
      if (!certificate.transactionHash) {
        return {
          isValid: false,
          details: {
            error: 'Certificate not yet issued on blockchain',
            status: certificate.status,
          },
        };
      }
      
      // Verify certificate on blockchain
      try {
        const response = await axios.post(
          `${EMAIL_SERVICE_URL}/verification/certificate/verify`,
          {
            certificateId,
            transactionHash: certificate.transactionHash,
          },
          {
            headers: {
              'Content-Type': 'application/json',
              'X-API-Key': API_KEY,
            },
          }
        );
        
        return response.data;
      } catch (error) {
        logger.error(`Error verifying certificate ${certificateId} on blockchain:`, error);
        
        return {
          isValid: false,
          details: {
            error: 'Failed to verify certificate on blockchain',
            status: certificate.status,
          },
        };
      }
    } catch (error) {
      logger.error(`Error verifying certificate ${certificateId}:`, error);
      throw error;
    }
  }
  
  /**
   * Get verification metadata for a campaign
   * 
   * @param campaignId Campaign ID
   * @returns Verification metadata
   */
  async getVerificationMetadata(campaignId: string): Promise<Record<string, any>> {
    try {
      // Get campaign
      const campaign = await prisma.campaign.findUnique({
        where: { id: campaignId },
        include: {
          certificates: true,
          verificationStatus: true,
        },
      });
      
      if (!campaign) {
        throw new ApiError('Campaign not found', 404);
      }
      
      // Get certificates
      const certificates = campaign.certificates || [];
      
      // Calculate verification score
      const verificationScore = this.calculateVerificationScore(campaign, certificates);
      
      return {
        campaignId: campaign.id,
        verificationStatus: campaign.verificationStatus?.status || 'not_started',
        verificationScore,
        certificates: certificates.map(cert => ({
          id: cert.id,
          type: cert.type,
          status: cert.status,
          issuedAt: cert.issuedAt,
          transactionHash: cert.transactionHash,
        })),
        lastVerified: campaign.verificationStatus?.completedAt || null,
      };
    } catch (error) {
      logger.error(`Error getting verification metadata for campaign ${campaignId}:`, error);
      throw error;
    }
  }
  
  /**
   * Calculate verification score for a campaign
   * 
   * @param campaign Campaign
   * @param certificates Certificates
   * @returns Verification score (0-100)
   */
  private calculateVerificationScore(campaign: Campaign, certificates: Certificate[]): number {
    // If verification failed or not started, score is 0
    if (
      !campaign.verificationStatus ||
      campaign.verificationStatus.status === 'failed' ||
      campaign.verificationStatus.status === 'pending'
    ) {
      return 0;
    }
    
    // If no certificates, score is 0
    if (certificates.length === 0) {
      return 0;
    }
    
    // Calculate score based on certificate types and statuses
    let score = 0;
    const maxScore = 100;
    
    // Weight for each certificate type
    const weights = {
      [CertificateType.EMAIL]: 25,
      [CertificateType.SENDER]: 25,
      [CertificateType.CONTENT]: 25,
      [CertificateType.DOMAIN]: 25,
    };
    
    // Calculate score for each certificate type
    const typesPresent = new Set<CertificateType>();
    
    for (const cert of certificates) {
      // Only count valid certificates
      if (cert.status === CertificateStatus.VALID) {
        typesPresent.add(cert.type as CertificateType);
      }
    }
    
    // Add score for each type present
    for (const type of typesPresent) {
      score += weights[type];
    }
    
    return Math.min(score, maxScore);
  }
}

// Export singleton instance
export const verificationService = new VerificationService();
