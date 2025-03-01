import { Query, QueryHandler, QueryResult } from './query';
import { ID } from '../../domain/value-objects/id';
import { ProjectionRepository } from '../../event-sourcing/projections/projection';
import { CampaignReadModel } from '../../event-sourcing/projections/campaign-projection';

/**
 * DTO for campaign results
 */
export interface CampaignDto {
  id: string;
  name: string;
  description: string;
  subject: string;
  contentType: 'html' | 'text';
  fromName: string;
  fromEmail: string;
  replyToEmail: string | null;
  status: string;
  createdAt: string;
  updatedAt: string;
  scheduledAt: string | null;
  sentAt: string | null;
  completedAt: string | null;
  segmentId: string | null;
  templateId: string | null;
  metadata: Record<string, any>;
  stats?: {
    recipients: number;
    sent: number;
    delivered: number;
    opened: number;
    clicked: number;
    bounced: number;
    complaints: number;
    unsubscribed: number;
  };
  version: number;
}

/**
 * Pagination information for campaign list results
 */
export interface PaginationInfo {
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/**
 * Convert a campaign read model to a DTO
 */
function campaignToDto(campaign: CampaignReadModel): CampaignDto {
  return {
    id: campaign.id,
    name: campaign.name,
    description: campaign.description,
    subject: campaign.subject,
    contentType: campaign.contentType,
    fromName: campaign.fromName,
    fromEmail: campaign.fromEmail,
    replyToEmail: campaign.replyToEmail,
    status: campaign.status,
    createdAt: campaign.createdAt.toISOString(),
    updatedAt: campaign.updatedAt.toISOString(),
    scheduledAt: campaign.scheduledAt ? campaign.scheduledAt.toISOString() : null,
    sentAt: campaign.sentAt ? campaign.sentAt.toISOString() : null,
    completedAt: campaign.completedAt ? campaign.completedAt.toISOString() : null,
    segmentId: campaign.segmentId,
    templateId: campaign.templateId,
    metadata: campaign.metadata,
    stats: campaign.stats,
    version: campaign.version,
  };
}

/**
 * Query to get a campaign by ID
 */
export class GetCampaignByIdQuery implements Query {
  readonly type = 'campaign.getById';

  constructor(public readonly id: string) {}
}

/**
 * Handler for GetCampaignByIdQuery
 */
export class GetCampaignByIdQueryHandler implements QueryHandler<GetCampaignByIdQuery, CampaignDto> {
  constructor(private campaignRepository: ProjectionRepository<CampaignReadModel>) {}

  async execute(query: GetCampaignByIdQuery): Promise<QueryResult<CampaignDto>> {
    try {
      const campaign = await this.campaignRepository.get(query.id);

      if (!campaign) {
        return {
          success: false,
          error: `Campaign not found: ${query.id}`,
          errorCode: 'CAMPAIGN_NOT_FOUND',
        };
      }

      return {
        success: true,
        data: campaignToDto(campaign),
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to get campaign: ${error.message}`,
        errorCode: 'GET_CAMPAIGN_ERROR',
      };
    }
  }
}

/**
 * Query to list campaigns with filters and pagination
 */
export class ListCampaignsQuery implements Query {
  readonly type = 'campaign.list';

  constructor(
    public readonly filters: {
      status?: string | string[];
      search?: string;
      fromDate?: Date;
      toDate?: Date;
      segmentId?: string;
    } = {},
    public readonly pagination: {
      page?: number;
      pageSize?: number;
      sortBy?: string;
      sortDirection?: 'asc' | 'desc';
    } = {}
  ) {}
}

/**
 * Handler for ListCampaignsQuery
 */
export class ListCampaignsQueryHandler
  implements QueryHandler<ListCampaignsQuery, { campaigns: CampaignDto[]; pagination: PaginationInfo }>
{
  constructor(private campaignRepository: ProjectionRepository<CampaignReadModel>) {}

  async execute(
    query: ListCampaignsQuery
  ): Promise<QueryResult<{ campaigns: CampaignDto[]; pagination: PaginationInfo }>> {
    try {
      const page = query.pagination.page || 1;
      const pageSize = query.pagination.pageSize || 10;
      const skip = (page - 1) * pageSize;

      // Build query object based on filters
      const queryObject: Record<string, any> = {};

      if (query.filters.status) {
        if (Array.isArray(query.filters.status)) {
          queryObject.status = { $in: query.filters.status };
        } else {
          queryObject.status = query.filters.status;
        }
      }

      if (query.filters.search) {
        queryObject.$or = [
          { name: { $regex: query.filters.search, $options: 'i' } },
          { description: { $regex: query.filters.search, $options: 'i' } },
          { subject: { $regex: query.filters.search, $options: 'i' } },
        ];
      }

      if (query.filters.fromDate || query.filters.toDate) {
        queryObject.createdAt = {};

        if (query.filters.fromDate) {
          queryObject.createdAt.$gte = query.filters.fromDate;
        }

        if (query.filters.toDate) {
          queryObject.createdAt.$lte = query.filters.toDate;
        }
      }

      if (query.filters.segmentId) {
        queryObject.segmentId = query.filters.segmentId;
      }

      // Sort options
      const sortBy = query.pagination.sortBy || 'createdAt';
      const sortDirection = query.pagination.sortDirection || 'desc';

      // Get paginated results
      const campaigns = await this.campaignRepository.find({
        ...queryObject,
        $sort: { [sortBy]: sortDirection === 'asc' ? 1 : -1 },
        $skip: skip,
        $limit: pageSize,
      });

      // Get total count
      const total = await this.campaignRepository.count(queryObject);

      // Convert to DTOs
      const campaignDtos = campaigns.map(campaignToDto);

      return {
        success: true,
        data: {
          campaigns: campaignDtos,
          pagination: {
            total,
            page,
            pageSize,
            totalPages: Math.ceil(total / pageSize),
          },
        },
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to list campaigns: ${error.message}`,
        errorCode: 'LIST_CAMPAIGNS_ERROR',
      };
    }
  }
}

/**
 * Query to get campaign statistics
 */
export class GetCampaignStatsQuery implements Query {
  readonly type = 'campaign.getStats';

  constructor(public readonly id: string) {}
}

/**
 * Handler for GetCampaignStatsQuery
 */
export class GetCampaignStatsQueryHandler
  implements QueryHandler<GetCampaignStatsQuery, CampaignDto['stats']>
{
  constructor(private campaignRepository: ProjectionRepository<CampaignReadModel>) {}

  async execute(query: GetCampaignStatsQuery): Promise<QueryResult<CampaignDto['stats']>> {
    try {
      const campaign = await this.campaignRepository.get(query.id);

      if (!campaign) {
        return {
          success: false,
          error: `Campaign not found: ${query.id}`,
          errorCode: 'CAMPAIGN_NOT_FOUND',
        };
      }

      return {
        success: true,
        data: campaign.stats,
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to get campaign stats: ${error.message}`,
        errorCode: 'GET_CAMPAIGN_STATS_ERROR',
      };
    }
  }
}

/**
 * Query to get campaign counts by status
 */
export class GetCampaignCountsByStatusQuery implements Query {
  readonly type = 'campaign.getCountsByStatus';

  constructor(public readonly filters: {
    fromDate?: Date;
    toDate?: Date;
  } = {}) {}
}

/**
 * Handler for GetCampaignCountsByStatusQuery
 */
export class GetCampaignCountsByStatusQueryHandler
  implements QueryHandler<GetCampaignCountsByStatusQuery, Record<string, number>>
{
  constructor(private campaignRepository: ProjectionRepository<CampaignReadModel>) {}

  async execute(query: GetCampaignCountsByStatusQuery): Promise<QueryResult<Record<string, number>>> {
    try {
      // Base query
      const baseQuery: Record<string, any> = {};

      // Add date filters if provided
      if (query.filters.fromDate || query.filters.toDate) {
        baseQuery.createdAt = {};

        if (query.filters.fromDate) {
          baseQuery.createdAt.$gte = query.filters.fromDate;
        }

        if (query.filters.toDate) {
          baseQuery.createdAt.$lte = query.filters.toDate;
        }
      }

      // Get all statuses
      const statuses = [
        'DRAFT',
        'SCHEDULED',
        'SENDING',
        'PAUSED',
        'COMPLETED',
        'CANCELED',
        'FAILED',
      ];

      // Count campaigns for each status
      const counts: Record<string, number> = {};

      for (const status of statuses) {
        const count = await this.campaignRepository.count({
          ...baseQuery,
          status,
        });

        counts[status] = count;
      }

      // Get total count
      counts.TOTAL = Object.values(counts).reduce((sum, count) => sum + count, 0);

      return {
        success: true,
        data: counts,
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to get campaign counts by status: ${error.message}`,
        errorCode: 'GET_CAMPAIGN_COUNTS_ERROR',
      };
    }
  }
}
