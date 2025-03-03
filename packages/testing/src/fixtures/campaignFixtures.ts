import { Campaign, CampaignId, CampaignStatus } from '@maily/domain';

/**
 * Creates a draft campaign fixture for testing.
 * 
 * @param overrides - Optional properties to override default values
 * @returns A Campaign entity in DRAFT status
 */
export function createDraftCampaignFixture(overrides?: Partial<{
  id: string;
  name: string;
  subject: string;
  content: string;
  contactListIds: string[];
  userId: string;
  templateId: string;
  tags: string[];
}>) {
  const id = overrides?.id || 'campaign-123';
  const name = overrides?.name || 'Test Campaign';
  const subject = overrides?.subject || 'Test Subject';
  const content = overrides?.content || '<p>Test content</p>';
  const contactListIds = overrides?.contactListIds || ['list-123'];
  const userId = overrides?.userId || 'user-123';
  const templateId = overrides?.templateId;
  const tags = overrides?.tags || ['test', 'campaign'];

  const campaignResult = Campaign.create(
    CampaignId.create(id),
    {
      name,
      subject,
      content,
      contactListIds,
      userId,
      templateId,
      tags
    }
  );

  if (campaignResult.isFailure()) {
    throw new Error(`Failed to create campaign fixture: ${campaignResult.getError().message}`);
  }

  return campaignResult.getValue();
}

/**
 * Creates a scheduled campaign fixture for testing.
 * 
 * @param overrides - Optional properties to override default values
 * @returns A Campaign entity in SCHEDULED status
 */
export function createScheduledCampaignFixture(overrides?: Partial<{
  id: string;
  name: string;
  subject: string;
  content: string;
  contactListIds: string[];
  userId: string;
  templateId: string;
  tags: string[];
  sendAt: Date;
}>) {
  const campaign = createDraftCampaignFixture(overrides);
  
  const sendAt = overrides?.sendAt || new Date(Date.now() + 24 * 60 * 60 * 1000); // Tomorrow
  const scheduleResult = campaign.schedule(sendAt);
  
  if (scheduleResult.isFailure()) {
    throw new Error(`Failed to schedule campaign fixture: ${scheduleResult.getError().message}`);
  }
  
  return campaign;
}

/**
 * Creates a sent campaign fixture for testing.
 * 
 * @param overrides - Optional properties to override default values
 * @returns A Campaign entity in SENT status
 */
export function createSentCampaignFixture(overrides?: Partial<{
  id: string;
  name: string;
  subject: string;
  content: string;
  contactListIds: string[];
  userId: string;
  templateId: string;
  tags: string[];
  sendAt: Date;
}>) {
  const campaign = createScheduledCampaignFixture(overrides);
  
  const startResult = campaign.startSending();
  if (startResult.isFailure()) {
    throw new Error(`Failed to start sending campaign fixture: ${startResult.getError().message}`);
  }
  
  const sentResult = campaign.markAsSent();
  if (sentResult.isFailure()) {
    throw new Error(`Failed to mark campaign as sent: ${sentResult.getError().message}`);
  }
  
  return campaign;
}