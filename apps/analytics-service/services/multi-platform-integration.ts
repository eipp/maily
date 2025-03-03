/**
 * Multi-platform Integration Service
 * 
 * This service provides data connectors for major platforms (Google, Facebook, LinkedIn),
 * data normalization across platforms, unified reporting, and cross-platform attribution.
 */

import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import { logger } from '../utils/logger';
import { prisma } from '../lib/prisma';
import { retry } from '../utils/retry';
import { Platform, PlatformConnection, PlatformData } from '../models/platform';
import { AttributionModel, AttributionResult } from '../models/attribution';
import { NormalizedData, DataSchema } from '../models/data-schema';
import { UnifiedReport, ReportType } from '../models/report';

// Environment variables
const GOOGLE_API_URL = process.env.GOOGLE_API_URL || 'https://analyticsdata.googleapis.com/v1beta';
const FACEBOOK_API_URL = process.env.FACEBOOK_API_URL || 'https://graph.facebook.com/v16.0';
const LINKEDIN_API_URL = process.env.LINKEDIN_API_URL || 'https://api.linkedin.com/v2';
const NANGO_API_URL = process.env.NANGO_API_URL || 'http://nango:3003';
const NANGO_SECRET_KEY = process.env.NANGO_SECRET_KEY || '';

/**
 * Multi-platform Integration Service
 */
export class MultiPlatformIntegrationService {
  private platformConnectors: Map<Platform, (connectionId: string) => Promise<any>>;
  private dataNormalizers: Map<Platform, (data: any) => Promise<NormalizedData>>;
  
  constructor() {
    // Initialize platform connectors
    this.platformConnectors = new Map();
    this.platformConnectors.set(Platform.GOOGLE, this.connectToGoogle.bind(this));
    this.platformConnectors.set(Platform.FACEBOOK, this.connectToFacebook.bind(this));
    this.platformConnectors.set(Platform.LINKEDIN, this.connectToLinkedIn.bind(this));
    
    // Initialize data normalizers
    this.dataNormalizers = new Map();
    this.dataNormalizers.set(Platform.GOOGLE, this.normalizeGoogleData.bind(this));
    this.dataNormalizers.set(Platform.FACEBOOK, this.normalizeFacebookData.bind(this));
    this.dataNormalizers.set(Platform.LINKEDIN, this.normalizeLinkedInData.bind(this));
    
    logger.info('Multi-platform Integration Service initialized');
  }
  
  /**
   * Get platform connections for a user
   * 
   * @param userId User ID
   * @returns Platform connections
   */
  async getPlatformConnections(userId: string): Promise<PlatformConnection[]> {
    try {
      const connections = await prisma.platformConnection.findMany({
        where: { userId },
      });
      
      return connections;
    } catch (error) {
      logger.error(`Error getting platform connections for user ${userId}:`, error);
      throw new Error('Failed to get platform connections');
    }
  }
  
  /**
   * Create platform connection
   * 
   * @param userId User ID
   * @param platform Platform
   * @param connectionDetails Connection details
   * @returns Platform connection
   */
  async createPlatformConnection(
    userId: string,
    platform: Platform,
    connectionDetails: Record<string, any>
  ): Promise<PlatformConnection> {
    try {
      logger.info(`Creating ${platform} connection for user ${userId}`);
      
      // Create connection in database
      const connection = await prisma.platformConnection.create({
        data: {
          id: uuidv4(),
          userId,
          platform,
          name: connectionDetails.name || `${platform} Connection`,
          status: 'pending',
          details: connectionDetails,
          createdAt: new Date(),
        },
      });
      
      // Test connection
      try {
        const connector = this.platformConnectors.get(platform);
        
        if (!connector) {
          throw new Error(`Connector not found for platform ${platform}`);
        }
        
        await connector(connection.id);
        
        // Update connection status
        await prisma.platformConnection.update({
          where: { id: connection.id },
          data: {
            status: 'connected',
            lastConnectedAt: new Date(),
          },
        });
        
        return {
          ...connection,
          status: 'connected',
          lastConnectedAt: new Date(),
        };
      } catch (error) {
        // Update connection status
        await prisma.platformConnection.update({
          where: { id: connection.id },
          data: {
            status: 'failed',
            error: error instanceof Error ? error.message : 'Unknown error',
          },
        });
        
        throw error;
      }
    } catch (error) {
      logger.error(`Error creating ${platform} connection for user ${userId}:`, error);
      throw new Error(`Failed to create ${platform} connection`);
    }
  }
  
  /**
   * Delete platform connection
   * 
   * @param connectionId Connection ID
   */
  async deletePlatformConnection(connectionId: string): Promise<void> {
    try {
      await prisma.platformConnection.delete({
        where: { id: connectionId },
      });
      
      logger.info(`Deleted platform connection ${connectionId}`);
    } catch (error) {
      logger.error(`Error deleting platform connection ${connectionId}:`, error);
      throw new Error('Failed to delete platform connection');
    }
  }
  
  /**
   * Fetch data from all connected platforms for a user
   * 
   * @param userId User ID
   * @param startDate Start date
   * @param endDate End date
   * @param metrics Metrics to fetch
   * @returns Platform data
   */
  async fetchAllPlatformData(
    userId: string,
    startDate: Date,
    endDate: Date,
    metrics: string[] = []
  ): Promise<PlatformData[]> {
    try {
      logger.info(`Fetching data from all platforms for user ${userId}`);
      
      // Get user's platform connections
      const connections = await this.getPlatformConnections(userId);
      
      if (connections.length === 0) {
        logger.warn(`No platform connections found for user ${userId}`);
        return [];
      }
      
      // Fetch data from each platform
      const platformDataPromises = connections.map(connection =>
        this.fetchPlatformData(connection.id, startDate, endDate, metrics)
      );
      
      const platformDataResults = await Promise.allSettled(platformDataPromises);
      
      // Filter successful results
      const platformData: PlatformData[] = [];
      
      for (let i = 0; i < platformDataResults.length; i++) {
        const result = platformDataResults[i];
        
        if (result.status === 'fulfilled') {
          platformData.push(result.value);
        } else {
          logger.error(
            `Error fetching data from platform ${connections[i].platform}:`,
            result.reason
          );
        }
      }
      
      return platformData;
    } catch (error) {
      logger.error(`Error fetching all platform data for user ${userId}:`, error);
      throw new Error('Failed to fetch platform data');
    }
  }
  
  /**
   * Fetch data from a specific platform
   * 
   * @param connectionId Connection ID
   * @param startDate Start date
   * @param endDate End date
   * @param metrics Metrics to fetch
   * @returns Platform data
   */
  async fetchPlatformData(
    connectionId: string,
    startDate: Date,
    endDate: Date,
    metrics: string[] = []
  ): Promise<PlatformData> {
    try {
      // Get connection
      const connection = await prisma.platformConnection.findUnique({
        where: { id: connectionId },
      });
      
      if (!connection) {
        throw new Error(`Platform connection ${connectionId} not found`);
      }
      
      logger.info(`Fetching data from ${connection.platform} for connection ${connectionId}`);
      
      // Get platform connector
      const connector = this.platformConnectors.get(connection.platform as Platform);
      
      if (!connector) {
        throw new Error(`Connector not found for platform ${connection.platform}`);
      }
      
      // Connect to platform
      const client = await connector(connectionId);
      
      // Fetch data based on platform
      let rawData: any;
      
      switch (connection.platform) {
        case Platform.GOOGLE:
          rawData = await this.fetchGoogleData(client, startDate, endDate, metrics);
          break;
        
        case Platform.FACEBOOK:
          rawData = await this.fetchFacebookData(client, startDate, endDate, metrics);
          break;
        
        case Platform.LINKEDIN:
          rawData = await this.fetchLinkedInData(client, startDate, endDate, metrics);
          break;
        
        default:
          throw new Error(`Unsupported platform: ${connection.platform}`);
      }
      
      // Normalize data
      const normalizer = this.dataNormalizers.get(connection.platform as Platform);
      
      if (!normalizer) {
        throw new Error(`Normalizer not found for platform ${connection.platform}`);
      }
      
      const normalizedData = await normalizer(rawData);
      
      // Create platform data record
      const platformData: PlatformData = {
        id: uuidv4(),
        connectionId,
        platform: connection.platform as Platform,
        startDate,
        endDate,
        metrics,
        rawData,
        normalizedData,
        fetchedAt: new Date(),
      };
      
      // Store platform data
      await prisma.platformData.create({
        data: {
          id: platformData.id,
          connectionId,
          platform: connection.platform,
          startDate,
          endDate,
          metrics,
          rawData,
          normalizedData,
          fetchedAt: platformData.fetchedAt,
        },
      });
      
      return platformData;
    } catch (error) {
      logger.error(`Error fetching platform data for connection ${connectionId}:`, error);
      throw new Error('Failed to fetch platform data');
    }
  }
  
  /**
   * Create unified report from platform data
   * 
   * @param userId User ID
   * @param reportType Report type
   * @param startDate Start date
   * @param endDate End date
   * @param options Report options
   * @returns Unified report
   */
  async createUnifiedReport(
    userId: string,
    reportType: ReportType,
    startDate: Date,
    endDate: Date,
    options: Record<string, any> = {}
  ): Promise<UnifiedReport> {
    try {
      logger.info(`Creating unified ${reportType} report for user ${userId}`);
      
      // Fetch platform data
      const platformData = await this.fetchAllPlatformData(
        userId,
        startDate,
        endDate,
        options.metrics || []
      );
      
      if (platformData.length === 0) {
        throw new Error('No platform data available');
      }
      
      // Create unified report based on report type
      let reportData: Record<string, any>;
      
      switch (reportType) {
        case ReportType.PERFORMANCE:
          reportData = this.createPerformanceReport(platformData, options);
          break;
        
        case ReportType.AUDIENCE:
          reportData = this.createAudienceReport(platformData, options);
          break;
        
        case ReportType.CONVERSION:
          reportData = this.createConversionReport(platformData, options);
          break;
        
        case ReportType.ATTRIBUTION:
          reportData = await this.createAttributionReport(platformData, options);
          break;
        
        default:
          throw new Error(`Unsupported report type: ${reportType}`);
      }
      
      // Create unified report
      const report: UnifiedReport = {
        id: uuidv4(),
        userId,
        reportType,
        startDate,
        endDate,
        options,
        data: reportData,
        createdAt: new Date(),
      };
      
      // Store report
      await prisma.unifiedReport.create({
        data: {
          id: report.id,
          userId,
          reportType,
          startDate,
          endDate,
          options,
          data: reportData,
          createdAt: report.createdAt,
        },
      });
      
      return report;
    } catch (error) {
      logger.error(`Error creating unified report for user ${userId}:`, error);
      throw new Error('Failed to create unified report');
    }
  }
  
  /**
   * Get unified report by ID
   * 
   * @param reportId Report ID
   * @returns Unified report
   */
  async getUnifiedReport(reportId: string): Promise<UnifiedReport> {
    try {
      const report = await prisma.unifiedReport.findUnique({
        where: { id: reportId },
      });
      
      if (!report) {
        throw new Error(`Unified report ${reportId} not found`);
      }
      
      return report as UnifiedReport;
    } catch (error) {
      logger.error(`Error getting unified report ${reportId}:`, error);
      throw new Error('Failed to get unified report');
    }
  }
  
  /**
   * Get unified reports for a user
   * 
   * @param userId User ID
   * @param reportType Report type (optional)
   * @param limit Limit (optional)
   * @param offset Offset (optional)
   * @returns Unified reports
   */
  async getUnifiedReports(
    userId: string,
    reportType?: ReportType,
    limit: number = 10,
    offset: number = 0
  ): Promise<UnifiedReport[]> {
    try {
      const reports = await prisma.unifiedReport.findMany({
        where: {
          userId,
          ...(reportType ? { reportType } : {}),
        },
        orderBy: {
          createdAt: 'desc',
        },
        take: limit,
        skip: offset,
      });
      
      return reports as UnifiedReport[];
    } catch (error) {
      logger.error(`Error getting unified reports for user ${userId}:`, error);
      throw new Error('Failed to get unified reports');
    }
  }
  
  /**
   * Calculate cross-platform attribution
   * 
   * @param userId User ID
   * @param conversionEvent Conversion event
   * @param lookbackWindow Lookback window in days
   * @param attributionModel Attribution model
   * @returns Attribution result
   */
  async calculateAttribution(
    userId: string,
    conversionEvent: string,
    lookbackWindow: number = 30,
    attributionModel: AttributionModel = AttributionModel.LAST_TOUCH
  ): Promise<AttributionResult> {
    try {
      logger.info(`Calculating attribution for user ${userId} using ${attributionModel} model`);
      
      // Calculate lookback period
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - lookbackWindow);
      
      // Fetch platform data
      const platformData = await this.fetchAllPlatformData(userId, startDate, endDate);
      
      if (platformData.length === 0) {
        throw new Error('No platform data available');
      }
      
      // Create attribution report
      const attributionReport = await this.createAttributionReport(
        platformData,
        {
          conversionEvent,
          attributionModel,
        }
      );
      
      return attributionReport.attribution;
    } catch (error) {
      logger.error(`Error calculating attribution for user ${userId}:`, error);
      throw new Error('Failed to calculate attribution');
    }
  }
  
  /**
   * Connect to Google
   * 
   * @param connectionId Connection ID
   * @returns Google client
   */
  private async connectToGoogle(connectionId: string): Promise<any> {
    try {
      // Get connection details
      const connection = await prisma.platformConnection.findUnique({
        where: { id: connectionId },
      });
      
      if (!connection) {
        throw new Error(`Platform connection ${connectionId} not found`);
      }
      
      // Get access token from Nango
      const response = await retry(
        () =>
          axios.get(`${NANGO_API_URL}/connection/${connection.details.nangoConnectionId}`, {
            headers: {
              Authorization: `Bearer ${NANGO_SECRET_KEY}`,
            },
          }),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
        }
      );
      
      const accessToken = response.data.credentials.access_token;
      
      // Create Google client
      return {
        accessToken,
        propertyId: connection.details.propertyId,
      };
    } catch (error) {
      logger.error(`Error connecting to Google for connection ${connectionId}:`, error);
      throw new Error('Failed to connect to Google');
    }
  }
  
  /**
   * Connect to Facebook
   * 
   * @param connectionId Connection ID
   * @returns Facebook client
   */
  private async connectToFacebook(connectionId: string): Promise<any> {
    try {
      // Get connection details
      const connection = await prisma.platformConnection.findUnique({
        where: { id: connectionId },
      });
      
      if (!connection) {
        throw new Error(`Platform connection ${connectionId} not found`);
      }
      
      // Get access token from Nango
      const response = await retry(
        () =>
          axios.get(`${NANGO_API_URL}/connection/${connection.details.nangoConnectionId}`, {
            headers: {
              Authorization: `Bearer ${NANGO_SECRET_KEY}`,
            },
          }),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
        }
      );
      
      const accessToken = response.data.credentials.access_token;
      
      // Create Facebook client
      return {
        accessToken,
        adAccountId: connection.details.adAccountId,
      };
    } catch (error) {
      logger.error(`Error connecting to Facebook for connection ${connectionId}:`, error);
      throw new Error('Failed to connect to Facebook');
    }
  }
  
  /**
   * Connect to LinkedIn
   * 
   * @param connectionId Connection ID
   * @returns LinkedIn client
   */
  private async connectToLinkedIn(connectionId: string): Promise<any> {
    try {
      // Get connection details
      const connection = await prisma.platformConnection.findUnique({
        where: { id: connectionId },
      });
      
      if (!connection) {
        throw new Error(`Platform connection ${connectionId} not found`);
      }
      
      // Get access token from Nango
      const response = await retry(
        () =>
          axios.get(`${NANGO_API_URL}/connection/${connection.details.nangoConnectionId}`, {
            headers: {
              Authorization: `Bearer ${NANGO_SECRET_KEY}`,
            },
          }),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
        }
      );
      
      const accessToken = response.data.credentials.access_token;
      
      // Create LinkedIn client
      return {
        accessToken,
        organizationId: connection.details.organizationId,
      };
    } catch (error) {
      logger.error(`Error connecting to LinkedIn for connection ${connectionId}:`, error);
      throw new Error('Failed to connect to LinkedIn');
    }
  }
  
  /**
   * Fetch data from Google
   * 
   * @param client Google client
   * @param startDate Start date
   * @param endDate End date
   * @param metrics Metrics to fetch
   * @returns Google data
   */
  private async fetchGoogleData(
    client: any,
    startDate: Date,
    endDate: Date,
    metrics: string[] = []
  ): Promise<any> {
    try {
      // Format dates
      const formattedStartDate = startDate.toISOString().split('T')[0];
      const formattedEndDate = endDate.toISOString().split('T')[0];
      
      // Default metrics if none provided
      const defaultMetrics = [
        'activeUsers',
        'sessions',
        'conversions',
        'engagementRate',
      ];
      
      const metricsToFetch = metrics.length > 0 ? metrics : defaultMetrics;
      
      // Fetch data from Google Analytics
      const response = await retry(
        () =>
          axios.post(
            `${GOOGLE_API_URL}/properties/${client.propertyId}:runReport`,
            {
              dateRanges: [
                {
                  startDate: formattedStartDate,
                  endDate: formattedEndDate,
                },
              ],
              metrics: metricsToFetch.map(metric => ({ name: metric })),
              dimensions: [{ name: 'date' }],
            },
            {
              headers: {
                Authorization: `Bearer ${client.accessToken}`,
                'Content-Type': 'application/json',
              },
            }
          ),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
        }
      );
      
      return response.data;
    } catch (error) {
      logger.error('Error fetching Google data:', error);
      throw new Error('Failed to fetch Google data');
    }
  }
  
  /**
   * Fetch data from Facebook
   * 
   * @param client Facebook client
   * @param startDate Start date
   * @param endDate End date
   * @param metrics Metrics to fetch
   * @returns Facebook data
   */
  private async fetchFacebookData(
    client: any,
    startDate: Date,
    endDate: Date,
    metrics: string[] = []
  ): Promise<any> {
    try {
      // Format dates
      const formattedStartDate = startDate.toISOString().split('T')[0];
      const formattedEndDate = endDate.toISOString().split('T')[0];
      
      // Default metrics if none provided
      const defaultMetrics = [
        'impressions',
        'clicks',
        'spend',
        'conversions',
      ];
      
      const metricsToFetch = metrics.length > 0 ? metrics : defaultMetrics;
      
      // Fetch data from Facebook Ads
      const response = await retry(
        () =>
          axios.get(
            `${FACEBOOK_API_URL}/act_${client.adAccountId}/insights`,
            {
              params: {
                time_range: JSON.stringify({
                  since: formattedStartDate,
                  until: formattedEndDate,
                }),
                fields: metricsToFetch.join(','),
                time_increment: 1,
                access_token: client.accessToken,
              },
            }
          ),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
        }
      );
      
      return response.data;
    } catch (error) {
      logger.error('Error fetching Facebook data:', error);
      throw new Error('Failed to fetch Facebook data');
    }
  }
  
  /**
   * Fetch data from LinkedIn
   * 
   * @param client LinkedIn client
   * @param startDate Start date
   * @param endDate End date
   * @param metrics Metrics to fetch
   * @returns LinkedIn data
   */
  private async fetchLinkedInData(
    client: any,
    startDate: Date,
    endDate: Date,
    metrics: string[] = []
  ): Promise<any> {
    try {
      // Format dates
      const formattedStartDate = startDate.toISOString().split('T')[0];
      const formattedEndDate = endDate.toISOString().split('T')[0];
      
      // Default metrics if none provided
      const defaultMetrics = [
        'impressions',
        'clicks',
        'likes',
        'comments',
        'shares',
      ];
      
      const metricsToFetch = metrics.length > 0 ? metrics : defaultMetrics;
      
      // Fetch data from LinkedIn
      const response = await retry(
        () =>
          axios.get(
            `${LINKEDIN_API_URL}/organizationalEntityShareStatistics`,
            {
              params: {
                q: 'organizationalEntity',
                organizationalEntity: `urn:li:organization:${client.organizationId}`,
                timeIntervals: `(timeRange:(start:${formattedStartDate},end:${formattedEndDate}),timeGranularity:DAY)`,
                fields: metricsToFetch.join(','),
              },
              headers: {
                Authorization: `Bearer ${client.accessToken}`,
                'X-Restli-Protocol-Version': '2.0.0',
              },
            }
          ),
        {
          retries: 3,
          minTimeout: 1000,
          factor: 2,
        }
      );
      
      return response.data;
    } catch (error) {
      logger.error('Error fetching LinkedIn data:', error);
      throw new Error('Failed to fetch LinkedIn data');
    }
  }
  
  /**
   * Normalize Google data
   * 
   * @param data Google data
   * @returns Normalized data
   */
  private async normalizeGoogleData(data: any): Promise<NormalizedData> {
    try {
      // Extract dimensions and metrics
      const dimensionHeaders = data.dimensionHeaders.map((header: any) => header.name);
      const metricHeaders = data.metricHeaders.map((header: any) => header.name);
      
      // Process rows
      const rows = data.rows.map((row: any) => {
        const dimensionValues = row.dimensionValues.map((value: any) => value.value);
        const metricValues = row.metricValues.map((value: any) => value.value);
        
        // Create row object
        const rowObject: Record<string, any> = {};
        
        // Add dimensions
        for (let i = 0; i < dimensionHeaders.length; i++) {
          rowObject[dimensionHeaders[i]] = dimensionValues[i];
        }
        
        // Add metrics
        for (let i = 0; i < metricHeaders.length; i++) {
          rowObject[metricHeaders[i]] = parseFloat(metricValues[i]);
        }
        
        return rowObject;
      });
      
      // Create normalized data
      const normalizedData: NormalizedData = {
        schema: {
          dimensions: dimensionHeaders,
          metrics: metricHeaders,
        },
        rows,
        totals: this.calculateTotals(rows, metricHeaders),
      };
      
      return normalizedData;
    } catch (error) {
      logger.error('Error normalizing Google data:', error);
      throw new Error('Failed to normalize Google data');
    }
  }
  
  /**
   * Normalize Facebook data
   * 
   * @param data Facebook data
   * @returns Normalized data
   */
  private async normalizeFacebookData(data: any): Promise<NormalizedData> {
    try {
      // Extract metrics
      const metrics = Object.keys(data.data[0]).filter(key => key !== 'date_start' && key !== 'date_stop');
      
      // Process rows
      const rows = data.data.map((item: any) => {
        const rowObject: Record<string, any> = {
          date: item.date_start,
        };
        
        // Add metrics
        for (const metric of metrics) {
          rowObject[metric] = parseFloat(item[metric]);
        }
        
        return rowObject;
      });
      
      // Create normalized data
      const normalizedData: NormalizedData = {
        schema: {
          dimensions: ['date'],
          metrics,
        },
        rows,
        totals: this.calculateTotals(rows, metrics),
      };
      
      return normalizedData;
    } catch (error) {
      logger.error('Error normalizing Facebook data:', error);
      throw new Error('Failed to normalize Facebook data');
    }
  }
  
  /**
   * Normalize LinkedIn data
   * 
   * @param data LinkedIn data
   * @returns Normalized data
   */
  private async normalizeLinkedInData(data: any): Promise<NormalizedData> {
    try {
      // Extract metrics
      const metrics = Object.keys(data.elements[0].totalShareStatistics).filter(
        key => key !== 'share'
      );
      
      // Process rows
      const rows = data.elements.map((element: any) => {
        const rowObject: Record<string, any> = {
          date: element.timeRange.start,
        };
        
        // Add metrics
        for (const metric of metrics) {
          rowObject[metric] = element.totalShareStatistics[metric];
        }
        
        return rowObject;
      });
      
      // Create normalized data
      const normalizedData: NormalizedData = {
        schema: {
          dimensions: ['date'],
          metrics,
        },
        rows,
        totals: this.calculateTotals(rows, metrics),
      };
      
      return normalizedData;
    } catch (error) {
      logger.error('Error normalizing LinkedIn data:', error);
      throw new Error('Failed to normalize LinkedIn data');
    }
  }
  
  /**
   * Calculate totals for metrics
   * 
   * @param rows Data rows
   * @param metrics Metrics
   * @returns Totals
   */
  private calculateTotals(rows: Record<string, any>[], metrics: string[]): Record<string, number> {
    const totals: Record<string, number> = {};
    
    for (const metric of metrics) {
      totals[metric] = rows.reduce((sum, row) => sum + (row[metric] || 0), 0);
    }
    
    return totals;
  }
  
  /**
   * Create performance report
   * 
   * @param platformData Platform data
   * @param options Report options
   * @returns Performance report
   */
  private createPerformanceReport(
    platformData: PlatformData[],
    options: Record<string, any> = {}
  ): Record<string, any> {
    // Extract normalized data from all platforms
    const allData = platformData.map(data => ({
      platform: data.platform,
      data: data.normalizedData,
    }));
    
    // Create unified metrics
    const unifiedMetrics: Record<string, any> = {
      byPlatform: {},
      byDate: {},
      totals: {},
    };
    
    // Process each platform's data
    for (const { platform, data } of allData) {
      unifiedMetrics.byPlatform[platform] = {
        metrics: data.totals,
        rows: data.rows,
      };
      
      // Aggregate by date
      for (const row of data.rows) {
        const date = row.date;
        
        if (!unifiedMetrics.byDate[date]) {
          unifiedMetrics.byDate[date] = {};
        }
        
        if (!unifiedMetrics.byDate[date][platform]) {
          unifiedMetrics.byDate[date][platform] = {};
        }
        
        // Add metrics for this date and platform
        for (const metric of data.schema.metrics) {
          unifiedMetrics.byDate[date][platform][metric] = row[metric];
        }
      }
    }
    
    //
