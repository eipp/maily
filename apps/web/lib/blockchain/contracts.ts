import { ethers } from 'ethers';

// TrustCertificate ABI (simplified - actual ABI would be more detailed)
const TRUST_CERTIFICATE_ABI = [
  "function issueCertificate(address marketer, uint256 campaignId, bytes32 metricsHash) external returns (bytes32)",
  "function verifyCertificate(bytes32 certificateId) external view returns (bool, tuple(address marketer, uint256 campaignId, bytes32 metricsHash, uint256 timestamp, bool revoked, string revocationReason))",
  "function generateMetricsHash(uint256 openRate, uint256 clickRate, uint256 deliveryRate, uint256 unsubscribeRate) external pure returns (bytes32)",
  "function revokeCertificate(bytes32 certificateId, string reason) external",
  "event CertificateIssued(bytes32 indexed certificateId, address indexed marketer, uint256 indexed campaignId, bytes32 metricsHash, uint256 timestamp)",
  "event CertificateRevoked(bytes32 indexed certificateId, string reason, uint256 timestamp)"
];

// Config
export const BLOCKCHAIN_CONFIG = {
  trustCertificateAddress: process.env.NEXT_PUBLIC_TRUST_CERTIFICATE_ADDRESS || '0x0000000000000000000000000000000000000000',
  rpcUrl: process.env.NEXT_PUBLIC_ETHEREUM_RPC_URL || 'https://mainnet.infura.io/v3/your-project-id',
  network: process.env.NEXT_PUBLIC_ETHEREUM_NETWORK || 'mainnet'
};

// Contract factory
export function getBlockchainProvider() {
  return new ethers.providers.JsonRpcProvider(BLOCKCHAIN_CONFIG.rpcUrl);
}

export function getTrustCertificateContract(signerOrProvider: ethers.Signer | ethers.providers.Provider) {
  return new ethers.Contract(
    BLOCKCHAIN_CONFIG.trustCertificateAddress,
    TRUST_CERTIFICATE_ABI,
    signerOrProvider
  );
}

// Helper functions for common operations
export async function generateMetricsHash(
  provider: ethers.providers.Provider,
  metrics: {
    openRate: number;
    clickRate: number;
    deliveryRate: number;
    unsubscribeRate: number;
  }
) {
  const contract = getTrustCertificateContract(provider);

  // Convert rates to integers (assuming rates are percentages with 2 decimal places)
  const openRateInt = Math.floor(metrics.openRate * 10000);
  const clickRateInt = Math.floor(metrics.clickRate * 10000);
  const deliveryRateInt = Math.floor(metrics.deliveryRate * 10000);
  const unsubscribeRateInt = Math.floor(metrics.unsubscribeRate * 10000);

  return await contract.generateMetricsHash(
    openRateInt,
    clickRateInt,
    deliveryRateInt,
    unsubscribeRateInt
  );
}

export async function issueCertificate(
  signer: ethers.Signer,
  marketerAddress: string,
  campaignId: string,
  metrics: {
    openRate: number;
    clickRate: number;
    deliveryRate: number;
    unsubscribeRate: number;
  }
) {
  const contract = getTrustCertificateContract(signer);

  // Generate metrics hash
  const metricsHash = await generateMetricsHash(signer.provider!, metrics);

  // Convert campaign ID to numeric format
  const campaignIdNumber = ethers.BigNumber.from(campaignId);

  // Issue certificate
  const tx = await contract.issueCertificate(
    marketerAddress,
    campaignIdNumber,
    metricsHash
  );

  // Wait for transaction
  const receipt = await tx.wait();

  // Extract certificate ID from event
  const event = receipt.events?.find(e => e.event === 'CertificateIssued');
  if (!event) {
    throw new Error('Certificate issuance event not found');
  }

  return {
    certificateId: event.args?.certificateId,
    transactionHash: receipt.transactionHash,
  };
}

export async function verifyCertificate(
  provider: ethers.providers.Provider,
  certificateId: string
) {
  const contract = getTrustCertificateContract(provider);

  const [valid, data] = await contract.verifyCertificate(certificateId);

  return {
    valid,
    data: {
      marketer: data.marketer,
      campaignId: data.campaignId.toString(),
      metricsHash: data.metricsHash,
      timestamp: new Date(data.timestamp.toNumber() * 1000),
      revoked: data.revoked,
      revocationReason: data.revocationReason
    }
  };
}

export async function revokeCertificate(
  signer: ethers.Signer,
  certificateId: string,
  reason: string
) {
  const contract = getTrustCertificateContract(signer);

  const tx = await contract.revokeCertificate(certificateId, reason);
  const receipt = await tx.wait();

  return {
    success: receipt.status === 1,
    transactionHash: receipt.transactionHash
  };
}
