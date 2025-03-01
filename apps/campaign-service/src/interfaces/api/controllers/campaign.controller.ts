import { Request, Response } from 'express';
import { CommandBus } from '../../../application/commands/command';
import { QueryBus } from '../../../application/queries/query';
import {
  CreateCampaignCommand,
  UpdateCampaignCommand,
  ScheduleCampaignCommand,
  SendCampaignCommand,
  PauseCampaignCommand,
  CancelCampaignCommand,
  CompleteCampaignCommand,
  FailCampaignCommand,
} from '../../../application/commands/campaign-commands';
import {
  GetCampaignByIdQuery,
  ListCampaignsQuery,
  GetCampaignStatsQuery,
  GetCampaignCountsByStatusQuery,
} from '../../../application/queries/campaign-queries';
import logger from '../../../infrastructure/logging/logger';

/**
 * Controller for Campaign API endpoints
 */
export class CampaignController {
  constructor(
    private readonly commandBus: CommandBus,
    private readonly queryBus: QueryBus
  ) {}

  /**
   * Create a new campaign
   * @route POST /api/campaigns
   */
  async createCampaign(req: Request, res: Response): Promise<void> {
    try {
      const { name, subject, content, fromName, fromEmail, ...options } = req.body;

      const command = new CreateCampaignCommand(
        name,
        subject,
        content,
        fromName,
        fromEmail,
        options
      );

      const result = await this.commandBus.execute(command);

      if (result.success) {
        res.status(201).json({
          id: result.data,
          message: 'Campaign created successfully',
        });
      } else {
        res.status(400).json({
          error: result.error,
          code: result.errorCode,
        });
      }
    } catch (error: any) {
      logger.error('Error creating campaign', { error: error.message });
      res.status(500).json({
        error: 'Internal server error',
      });
    }
  }

  /**
   * Update an existing campaign
   * @route PUT /api/campaigns/:id
   */
  async updateCampaign(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { name, subject, content, fromName, fromEmail, ...options } = req.body;

      const command = new UpdateCampaignCommand(
        id,
        name,
        subject,
        content,
        fromName,
        fromEmail,
        options
      );

      const result = await this.commandBus.execute(command);

      if (result.success) {
        res.status(200).json({
          message: 'Campaign updated successfully',
        });
      } else {
        const status = result.errorCode === 'CAMPAIGN_NOT_FOUND' ? 404 : 400;
        res.status(status).json({
          error: result.error,
          code: result.errorCode,
        });
      }
    } catch (error: any) {
      logger.error('Error updating campaign', { error: error.message, campaignId: req.params.id });
      res.status(500).json({
        error: 'Internal server error',
      });
    }
  }

  /**
   * Schedule a campaign
   * @route POST /api/campaigns/:id/schedule
   */
  async scheduleCampaign(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { scheduledAt } = req.body;

      const command = new ScheduleCampaignCommand(id, new Date(scheduledAt));

      const result = await this.commandBus.execute(command);

      if (result.success) {
        res.status(200).json({
          message: 'Campaign scheduled successfully',
        });
      } else {
        const status = result.errorCode === 'CAMPAIGN_NOT_FOUND' ? 404 : 400;
        res.status(status).json({
          error: result.error,
          code: result.errorCode,
        });
      }
    } catch (error: any) {
      logger.error('Error scheduling campaign', { error: error.message, campaignId: req.params.id });
      res.status(500).json({
        error: 'Internal server error',
      });
    }
  }

  /**
   * Start sending a campaign
   * @route POST /api/campaigns/:id/send
   */
  async sendCampaign(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const command = new SendCampaignCommand(id);

      const result = await this.commandBus.execute(command);

      if (result.success) {
        res.status(200).json({
          message: 'Campaign sending started successfully',
        });
      } else {
        const status = result.errorCode === 'CAMPAIGN_NOT_FOUND' ? 404 : 400;
        res.status(status).json({
          error: result.error,
          code: result.errorCode,
        });
      }
    } catch (error: any) {
      logger.error('Error sending campaign', { error: error.message, campaignId: req.params.id });
      res.status(500).json({
        error: 'Internal server error',
      });
    }
  }

  /**
   * Pause a campaign
   * @route POST /api/campaigns/:id/pause
   */
  async pauseCampaign(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const command = new PauseCampaignCommand(id);

      const result = await this.commandBus.execute(command);

      if (result.success) {
        res.status(200).json({
          message: 'Campaign paused successfully',
        });
      } else {
        const status = result.errorCode === 'CAMPAIGN_NOT_FOUND' ? 404 : 400;
        res.status(status).json({
          error: result.error,
          code: result.errorCode,
        });
      }
    } catch (error: any) {
      logger.error('Error pausing campaign', { error: error.message, campaignId: req.params.id });
      res.status(500).json({
        error: 'Internal server error',
      });
    }
  }

  /**
   * Cancel a campaign
   * @route POST /api/campaigns/:id/cancel
   */
  async cancelCampaign(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const command = new CancelCampaignCommand(id);

      const result = await this.commandBus.execute(command);

      if (result.success) {
        res.status(200).json({
          message: 'Campaign canceled successfully',
        });
      } else {
        const status = result.errorCode === 'CAMPAIGN_NOT_FOUND' ? 404 : 400;
        res.status(status).json({
          error: result.error,
          code: result.errorCode,
        });
      }
    } catch (error: any) {
      logger.error('Error canceling campaign', { error: error.message, campaignId: req.params.id });
      res.status(500).json({
        error: 'Internal server error',
      });
    }
  }

  /**
   * Complete a campaign
   * @route POST /api/campaigns/:id/complete
   */
  async completeCampaign(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const command = new CompleteCampaignCommand(id);

      const result = await this.commandBus.execute(command);

      if (result.success) {
        res.status(200).json({
          message: 'Campaign completed successfully',
        });
      } else {
        const status = result.errorCode === 'CAMPAIGN_NOT_FOUND' ? 404 : 400;
        res.status(status).json({
          error: result.error,
          code: result.errorCode,
        });
      }
    } catch (error: any) {
      logger.error('Error completing campaign', { error: error.message, campaignId: req.params.id });
      res.status(500).json({
        error: 'Internal server error',
      });
    }
  }

  /**
   * Mark a campaign as failed
   * @route POST /api/campaigns/:id/fail
   */
  async failCampaign(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { reason } = req.body;

      if (!reason) {
        res.status(400).json({
          error: 'Failure reason is required',
          code: 'MISSING_REASON',
        });
        return;
      }

      const command = new FailCampaignCommand(id, reason);

      const result = await this.commandBus.execute(command);

      if (result.success) {
        res.status(200).json({
          message: 'Campaign marked as failed successfully',
        });
      } else {
        const status = result.errorCode === 'CAMPAIGN_NOT_FOUND' ? 404 : 400;
        res.status(status).json({
          error: result.error,
          code: result.errorCode,
        });
      }
    } catch (error: any) {
      logger.error('Error failing campaign', { error: error.message, campaignId: req.params.id });
      res.status(500).json({
        error: 'Internal server error',
      });
    }
  }

  /**
   * Get a campaign by ID
   * @route GET /api/campaigns/:id
   */
  async getCampaign(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const query = new GetCampaignByIdQuery(id);

      const result = await this.queryBus.execute(query);

      if (result.success) {
        res.status(200).json(result.data);
      } else {
        const status = result.errorCode === 'CAMPAIGN_NOT_FOUND' ? 404 : 400;
        res.status(status).json({
          error: result.error,
          code: result.errorCode,
        });
      }
    } catch (error: any) {
      logger.error('Error getting campaign', { error: error.message, campaignId: req.params.id });
      res.status(500).json({
        error: 'Internal server error',
      });
    }
  }

  /**
   * List campaigns with filters and pagination
   * @route GET /api/campaigns
   */
  async listCampaigns(req: Request, res: Response): Promise<void> {
    try {
      const {
        status,
        search,
        fromDate,
        toDate,
        segmentId,
        page,
        pageSize,
        sortBy,
        sortDirection,
      } = req.query;

      const filters: any = {};

      if (status) filters.status = status;
      if (search) filters.search = search;
      if (fromDate) filters.fromDate = new Date(fromDate as string);
      if (toDate) filters.toDate = new Date(toDate as string);
      if (segmentId) filters.segmentId = segmentId;

      const pagination: any = {};

      if (page) pagination.page = parseInt(page as string, 10);
      if (pageSize) pagination.pageSize = parseInt(pageSize as string, 10);
      if (sortBy) pagination.sortBy = sortBy;
      if (sortDirection) pagination.sortDirection = sortDirection as 'asc' | 'desc';

      const query = new ListCampaignsQuery(filters, pagination);

      const result = await this.queryBus.execute(query);

      if (result.success) {
        res.status(200).json(result.data);
      } else {
        res.status(400).json({
          error: result.error,
          code: result.errorCode,
        });
      }
    } catch (error: any) {
      logger.error('Error listing campaigns', { error: error.message });
      res.status(500).json({
        error: 'Internal server error',
      });
    }
  }

  /**
   * Get campaign statistics
   * @route GET /api/campaigns/:id/stats
   */
  async getCampaignStats(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const query = new GetCampaignStatsQuery(id);

      const result = await this.queryBus.execute(query);

      if (result.success) {
        res.status(200).json(result.data);
      } else {
        const status = result.errorCode === 'CAMPAIGN_NOT_FOUND' ? 404 : 400;
        res.status(status).json({
          error: result.error,
          code: result.errorCode,
        });
      }
    } catch (error: any) {
      logger.error('Error getting campaign stats', { error: error.message, campaignId: req.params.id });
      res.status(500).json({
        error: 'Internal server error',
      });
    }
  }

  /**
   * Get campaign counts by status
   * @route GET /api/campaigns/counts
   */
  async getCampaignCounts(req: Request, res: Response): Promise<void> {
    try {
      const { fromDate, toDate } = req.query;

      const filters: any = {};

      if (fromDate) filters.fromDate = new Date(fromDate as string);
      if (toDate) filters.toDate = new Date(toDate as string);

      const query = new GetCampaignCountsByStatusQuery(filters);

      const result = await this.queryBus.execute(query);

      if (result.success) {
        res.status(200).json(result.data);
      } else {
        res.status(400).json({
          error: result.error,
          code: result.errorCode,
        });
      }
    } catch (error: any) {
      logger.error('Error getting campaign counts', { error: error.message });
      res.status(500).json({
        error: 'Internal server error',
      });
    }
  }
}
