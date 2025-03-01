import mongoose from 'mongoose';
import config from '../config';
import logger from './logger';

/**
 * Connect to MongoDB
 */
export const connectDatabase = async (): Promise<void> => {
  try {
    // Set mongoose options
    mongoose.set('strictQuery', true);

    // Connect to MongoDB
    await mongoose.connect(config.mongodb.uri);

    logger.info('Connected to MongoDB successfully');

    // Log when disconnected
    mongoose.connection.on('disconnected', () => {
      logger.warn('MongoDB connection disconnected');
    });

    // Log when reconnected
    mongoose.connection.on('reconnected', () => {
      logger.info('MongoDB connection reestablished');
    });

    // Log connection errors
    mongoose.connection.on('error', (error) => {
      logger.error('MongoDB connection error', { error: error.message });
    });

  } catch (error: any) {
    logger.error('Failed to connect to MongoDB', { error: error.message });
    throw error;
  }
};

/**
 * Close the MongoDB connection
 */
export const closeDatabase = async (): Promise<void> => {
  try {
    await mongoose.disconnect();
    logger.info('MongoDB connection closed');
  } catch (error: any) {
    logger.error('Error while closing MongoDB connection', { error: error.message });
    throw error;
  }
};

/**
 * Check if the database connection is established
 */
export const isDatabaseConnected = (): boolean => {
  return mongoose.connection.readyState === 1;
};

/**
 * Get database connection statistics
 */
export const getDatabaseStats = async (): Promise<Record<string, any>> => {
  if (!isDatabaseConnected()) {
    throw new Error('Database connection not established');
  }

  const stats = await mongoose.connection.db.stats();
  return stats;
};

/**
 * Database health check function
 */
export const checkDatabaseHealth = async (): Promise<{ status: string; details?: Record<string, any> }> => {
  try {
    // Simple ping to check database connection
    await mongoose.connection.db.admin().ping();

    // Get basic stats
    const stats = await getDatabaseStats();

    return {
      status: 'healthy',
      details: {
        databaseName: stats.db,
        collections: stats.collections,
        documents: stats.objects,
        dataSize: `${(stats.dataSize / (1024 * 1024)).toFixed(2)} MB`,
        storageSize: `${(stats.storageSize / (1024 * 1024)).toFixed(2)} MB`,
        indexes: stats.indexes,
        indexSize: `${(stats.indexSize / (1024 * 1024)).toFixed(2)} MB`,
      },
    };
  } catch (error: any) {
    logger.error('Database health check failed', { error: error.message });

    return {
      status: 'unhealthy',
      details: {
        error: error.message,
        connectionState: mongoose.connection.readyState,
      },
    };
  }
};
