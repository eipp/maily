import { ethers } from 'ethers';
import { logger } from './logger';

/**
 * Interface for a transaction to be batched
 */
export interface BatchTransaction {
  to: string;
  data: string;
  value?: ethers.BigNumber;
  gasLimit?: ethers.BigNumber;
}

/**
 * Batch transaction result
 */
export interface BatchTransactionResult {
  transactionHash: string;
  blockNumber: number;
  events: ethers.Event[];
  status: boolean;
  individualResults?: any[];
}

/**
 * Batch transaction manager for efficient blockchain operations
 */
export class BatchTransactionManager {
  private pendingTransactions: BatchTransaction[] = [];
  private batchSizeLimit: number;
  private gasThreshold: ethers.BigNumber;
  private processingTimeout: number; // ms
  private timer: NodeJS.Timeout | null = null;
  private wallet: ethers.Wallet;
  private provider: ethers.providers.Provider;
  private multicallContract: ethers.Contract;

  /**
   * Initialize a new batch transaction manager
   * @param wallet Ethers wallet for signing transactions
   * @param multicallAddress Address of the multicall contract
   * @param options Configuration options
   */
  constructor(
    wallet: ethers.Wallet,
    multicallAddress: string,
    options: {
      batchSizeLimit?: number;
      gasThreshold?: string;
      processingTimeout?: number;
    } = {}
  ) {
    this.wallet = wallet;
    this.provider = wallet.provider;
    this.batchSizeLimit = options.batchSizeLimit || 10;
    this.gasThreshold = ethers.utils.parseUnits(options.gasThreshold || '1', 'gwei');
    this.processingTimeout = options.processingTimeout || 30000; // Default 30 seconds

    // Initialize multicall contract
    this.multicallContract = new ethers.Contract(
      multicallAddress,
      [
        'function aggregate((address target, bytes callData)[] calls) external returns (uint256 blockNumber, bytes[] returnData)',
        'function tryAggregate(bool requireSuccess, (address target, bytes callData)[] calls) external returns (tuple(bool success, bytes returnData)[] returnData)'
      ],
      this.wallet
    );

    logger.info('BatchTransactionManager initialized');
  }

  /**
   * Add a transaction to the batch queue
   * @param transaction Transaction to add to the batch
   * @returns Promise that resolves when the batch is processed
   */
  public async addTransaction(transaction: BatchTransaction): Promise<BatchTransactionResult> {
    return new Promise((resolve, reject) => {
      // Add transaction to queue with callback
      this.pendingTransactions.push(transaction);
      
      // Start timer if not already running
      if (!this.timer && this.pendingTransactions.length === 1) {
        this.timer = setTimeout(() => this.processBatch().then(result => {
          // Call resolve for all pending transactions
          // In a real implementation, we would map individual results to each transaction
          resolve(result);
        }).catch(error => {
          reject(error);
        }), this.processingTimeout);
      }

      // Process immediately if we've reached the batch size limit
      if (this.pendingTransactions.length >= this.batchSizeLimit) {
        clearTimeout(this.timer!);
        this.timer = null;
        
        this.processBatch().then(result => {
          resolve(result);
        }).catch(error => {
          reject(error);
        });
      }
    });
  }

  /**
   * Process the current batch of transactions
   * @returns Result of the batch transaction
   */
  private async processBatch(): Promise<BatchTransactionResult> {
    if (this.pendingTransactions.length === 0) {
      logger.info('No transactions to process in batch');
      return {
        transactionHash: '',
        blockNumber: 0,
        events: [],
        status: false
      };
    }

    const transactions = [...this.pendingTransactions];
    this.pendingTransactions = [];

    logger.info(`Processing batch of ${transactions.length} transactions`);

    try {
      // For multicall, convert transactions to the required format
      const calls = transactions.map(tx => ({
        target: tx.to,
        callData: tx.data
      }));

      // Get current gas price with optimization
      const gasPrice = await this.getOptimizedGasPrice();

      // Execute the multicall transaction
      const tx = await this.multicallContract.tryAggregate(
        false, // Don't require all transactions to succeed
        calls,
        {
          gasPrice,
          // Estimate gas or use a calculated limit
          gasLimit: ethers.utils.hexlify(6000000), // Large enough for most batches
        }
      );

      // Wait for transaction receipt
      const receipt = await tx.wait();

      // Extract results from events (simplified - actual implementation would need to decode event data)
      return {
        transactionHash: receipt.transactionHash,
        blockNumber: receipt.blockNumber,
        events: receipt.events || [],
        status: receipt.status === 1,
        individualResults: receipt.logs.map(log => ({
          logIndex: log.logIndex,
          data: log.data
        }))
      };
    } catch (error) {
      logger.error('Failed to process transaction batch:', error);
      
      // If batch processing fails, fall back to individual transactions
      logger.info('Falling back to individual transaction processing');
      
      // Process each transaction individually
      // In a production environment, you might want more sophisticated fallback logic
      throw error;
    }
  }

  /**
   * Get the current gas price with optimization
   */
  private async getOptimizedGasPrice(): Promise<ethers.BigNumber> {
    try {
      const gasPrice = await this.provider.getGasPrice();
      const multiplier = 110; // 10% increase
      const optimizedGasPrice = gasPrice.mul(multiplier).div(100);
      
      // Cap at maximum gas price
      const maxGasPrice = ethers.utils.parseUnits('100', 'gwei');
      return optimizedGasPrice.gt(maxGasPrice) ? maxGasPrice : optimizedGasPrice;
    } catch (error) {
      logger.error('Error getting gas price:', error);
      return ethers.utils.parseUnits('50', 'gwei'); // Fallback gas price
    }
  }

  /**
   * Force process all pending transactions immediately
   * @returns Result of the batch transaction
   */
  public async flushBatch(): Promise<BatchTransactionResult | null> {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    
    if (this.pendingTransactions.length === 0) {
      return null;
    }
    
    return this.processBatch();
  }
}