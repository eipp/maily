import { Command, CommandHandler, CommandResult } from './command';
import { ID } from '../../domain/value-objects/id';
import { EmailAddress } from '../../domain/value-objects/email-address';
import { Campaign } from '../../domain/entities/campaign';
import { CampaignRepository } from '../../domain/repositories/campaign-repository';

/**
 * Command to create a new campaign
 */
export class CreateCampaignCommand implements Command {
  readonly type = 'campaign.create';

  constructor(
    public readonly name: string,
    public readonly subject: string,
    public readonly content: string,
    public readonly fromName: string,
    public readonly fromEmail: string,
    public readonly options?: {
      description?: string;
      contentType?: 'html' | 'text';
      replyToEmail?: string;
      segmentId?: string;
      templateId?: string;
      metadata?: Record<string, any>;
    }
  ) {}
}

/**
 * Handler for CreateCampaignCommand
 */
export class CreateCampaignCommandHandler implements CommandHandler<CreateCampaignCommand, string> {
  constructor(private campaignRepository: CampaignRepository) {}

  async execute(command: CreateCampaignCommand): Promise<CommandResult<string>> {
    try {
      const fromEmail = EmailAddress.create(command.fromEmail);

      let replyToEmail: EmailAddress | undefined;
      if (command.options?.replyToEmail) {
        replyToEmail = EmailAddress.create(command.options.replyToEmail);
      }

      let segmentId: ID | undefined;
      if (command.options?.segmentId) {
        segmentId = ID.from(command.options.segmentId);
      }

      let templateId: ID | undefined;
      if (command.options?.templateId) {
        templateId = ID.from(command.options.templateId);
      }

      const campaign = Campaign.create(
        command.name,
        command.subject,
        command.content,
        command.fromName,
        fromEmail,
        {
          description: command.options?.description,
          contentType: command.options?.contentType,
          replyToEmail,
          segmentId,
          templateId,
          metadata: command.options?.metadata,
        }
      );

      await this.campaignRepository.save(campaign);

      return {
        success: true,
        data: campaign.id.getValue(),
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to create campaign: ${error.message}`,
        errorCode: 'CREATE_CAMPAIGN_ERROR',
      };
    }
  }
}

/**
 * Command to update an existing campaign
 */
export class UpdateCampaignCommand implements Command {
  readonly type = 'campaign.update';

  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly subject: string,
    public readonly content: string,
    public readonly fromName: string,
    public readonly fromEmail: string,
    public readonly options?: {
      description?: string;
      contentType?: 'html' | 'text';
      replyToEmail?: string;
      segmentId?: string;
      templateId?: string;
      metadata?: Record<string, any>;
    }
  ) {}
}

/**
 * Handler for UpdateCampaignCommand
 */
export class UpdateCampaignCommandHandler implements CommandHandler<UpdateCampaignCommand> {
  constructor(private campaignRepository: CampaignRepository) {}

  async execute(command: UpdateCampaignCommand): Promise<CommandResult> {
    try {
      const campaignId = ID.from(command.id);
      const campaign = await this.campaignRepository.findById(campaignId);

      if (!campaign) {
        return {
          success: false,
          error: `Campaign not found: ${command.id}`,
          errorCode: 'CAMPAIGN_NOT_FOUND',
        };
      }

      const fromEmail = EmailAddress.create(command.fromEmail);

      let replyToEmail: EmailAddress | undefined;
      if (command.options?.replyToEmail) {
        replyToEmail = EmailAddress.create(command.options.replyToEmail);
      }

      let segmentId: ID | undefined;
      if (command.options?.segmentId) {
        segmentId = ID.from(command.options.segmentId);
      }

      let templateId: ID | undefined;
      if (command.options?.templateId) {
        templateId = ID.from(command.options.templateId);
      }

      campaign.update(
        command.name,
        command.subject,
        command.content,
        command.fromName,
        fromEmail,
        {
          description: command.options?.description,
          contentType: command.options?.contentType,
          replyToEmail,
          segmentId,
          templateId,
          metadata: command.options?.metadata,
        }
      );

      await this.campaignRepository.save(campaign);

      return {
        success: true,
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to update campaign: ${error.message}`,
        errorCode: 'UPDATE_CAMPAIGN_ERROR',
      };
    }
  }
}

/**
 * Command to schedule a campaign
 */
export class ScheduleCampaignCommand implements Command {
  readonly type = 'campaign.schedule';

  constructor(
    public readonly id: string,
    public readonly scheduledAt: Date
  ) {}
}

/**
 * Handler for ScheduleCampaignCommand
 */
export class ScheduleCampaignCommandHandler implements CommandHandler<ScheduleCampaignCommand> {
  constructor(private campaignRepository: CampaignRepository) {}

  async execute(command: ScheduleCampaignCommand): Promise<CommandResult> {
    try {
      const campaignId = ID.from(command.id);
      const campaign = await this.campaignRepository.findById(campaignId);

      if (!campaign) {
        return {
          success: false,
          error: `Campaign not found: ${command.id}`,
          errorCode: 'CAMPAIGN_NOT_FOUND',
        };
      }

      campaign.schedule(command.scheduledAt);

      await this.campaignRepository.save(campaign);

      return {
        success: true,
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to schedule campaign: ${error.message}`,
        errorCode: 'SCHEDULE_CAMPAIGN_ERROR',
      };
    }
  }
}

/**
 * Command to start sending a campaign
 */
export class SendCampaignCommand implements Command {
  readonly type = 'campaign.send';

  constructor(
    public readonly id: string
  ) {}
}

/**
 * Handler for SendCampaignCommand
 */
export class SendCampaignCommandHandler implements CommandHandler<SendCampaignCommand> {
  constructor(private campaignRepository: CampaignRepository) {}

  async execute(command: SendCampaignCommand): Promise<CommandResult> {
    try {
      const campaignId = ID.from(command.id);
      const campaign = await this.campaignRepository.findById(campaignId);

      if (!campaign) {
        return {
          success: false,
          error: `Campaign not found: ${command.id}`,
          errorCode: 'CAMPAIGN_NOT_FOUND',
        };
      }

      campaign.send();

      await this.campaignRepository.save(campaign);

      return {
        success: true,
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to send campaign: ${error.message}`,
        errorCode: 'SEND_CAMPAIGN_ERROR',
      };
    }
  }
}

/**
 * Command to pause a campaign
 */
export class PauseCampaignCommand implements Command {
  readonly type = 'campaign.pause';

  constructor(
    public readonly id: string
  ) {}
}

/**
 * Handler for PauseCampaignCommand
 */
export class PauseCampaignCommandHandler implements CommandHandler<PauseCampaignCommand> {
  constructor(private campaignRepository: CampaignRepository) {}

  async execute(command: PauseCampaignCommand): Promise<CommandResult> {
    try {
      const campaignId = ID.from(command.id);
      const campaign = await this.campaignRepository.findById(campaignId);

      if (!campaign) {
        return {
          success: false,
          error: `Campaign not found: ${command.id}`,
          errorCode: 'CAMPAIGN_NOT_FOUND',
        };
      }

      campaign.pause();

      await this.campaignRepository.save(campaign);

      return {
        success: true,
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to pause campaign: ${error.message}`,
        errorCode: 'PAUSE_CAMPAIGN_ERROR',
      };
    }
  }
}

/**
 * Command to cancel a campaign
 */
export class CancelCampaignCommand implements Command {
  readonly type = 'campaign.cancel';

  constructor(
    public readonly id: string
  ) {}
}

/**
 * Handler for CancelCampaignCommand
 */
export class CancelCampaignCommandHandler implements CommandHandler<CancelCampaignCommand> {
  constructor(private campaignRepository: CampaignRepository) {}

  async execute(command: CancelCampaignCommand): Promise<CommandResult> {
    try {
      const campaignId = ID.from(command.id);
      const campaign = await this.campaignRepository.findById(campaignId);

      if (!campaign) {
        return {
          success: false,
          error: `Campaign not found: ${command.id}`,
          errorCode: 'CAMPAIGN_NOT_FOUND',
        };
      }

      campaign.cancel();

      await this.campaignRepository.save(campaign);

      return {
        success: true,
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to cancel campaign: ${error.message}`,
        errorCode: 'CANCEL_CAMPAIGN_ERROR',
      };
    }
  }
}

/**
 * Command to mark a campaign as completed
 */
export class CompleteCampaignCommand implements Command {
  readonly type = 'campaign.complete';

  constructor(
    public readonly id: string
  ) {}
}

/**
 * Handler for CompleteCampaignCommand
 */
export class CompleteCampaignCommandHandler implements CommandHandler<CompleteCampaignCommand> {
  constructor(private campaignRepository: CampaignRepository) {}

  async execute(command: CompleteCampaignCommand): Promise<CommandResult> {
    try {
      const campaignId = ID.from(command.id);
      const campaign = await this.campaignRepository.findById(campaignId);

      if (!campaign) {
        return {
          success: false,
          error: `Campaign not found: ${command.id}`,
          errorCode: 'CAMPAIGN_NOT_FOUND',
        };
      }

      campaign.complete();

      await this.campaignRepository.save(campaign);

      return {
        success: true,
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to complete campaign: ${error.message}`,
        errorCode: 'COMPLETE_CAMPAIGN_ERROR',
      };
    }
  }
}

/**
 * Command to mark a campaign as failed
 */
export class FailCampaignCommand implements Command {
  readonly type = 'campaign.fail';

  constructor(
    public readonly id: string,
    public readonly reason: string
  ) {}
}

/**
 * Handler for FailCampaignCommand
 */
export class FailCampaignCommandHandler implements CommandHandler<FailCampaignCommand> {
  constructor(private campaignRepository: CampaignRepository) {}

  async execute(command: FailCampaignCommand): Promise<CommandResult> {
    try {
      const campaignId = ID.from(command.id);
      const campaign = await this.campaignRepository.findById(campaignId);

      if (!campaign) {
        return {
          success: false,
          error: `Campaign not found: ${command.id}`,
          errorCode: 'CAMPAIGN_NOT_FOUND',
        };
      }

      campaign.fail(command.reason);

      await this.campaignRepository.save(campaign);

      return {
        success: true,
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to mark campaign as failed: ${error.message}`,
        errorCode: 'FAIL_CAMPAIGN_ERROR',
      };
    }
  }
}
