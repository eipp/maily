import { Router } from 'express';
import { CampaignController } from '../controllers/campaign.controller';
import { CommandBus, InMemoryCommandBus } from '../../../application/commands/command';
import { QueryBus, InMemoryQueryBus } from '../../../application/queries/query';
import { authorization, validation } from '../middlewares';
import { campaignValidation } from '../validations/campaign.validation';

/**
 * Campaign routes
 */
export function setupCampaignRoutes(
  router: Router,
  commandBus: CommandBus = new InMemoryCommandBus(),
  queryBus: QueryBus = new InMemoryQueryBus()
): Router {
  const campaignController = new CampaignController(commandBus, queryBus);

  // Command routes
  router.post(
    '/campaigns',
    authorization(['campaigns:create']),
    validation(campaignValidation.createCampaign),
    campaignController.createCampaign.bind(campaignController)
  );

  router.put(
    '/campaigns/:id',
    authorization(['campaigns:update']),
    validation(campaignValidation.updateCampaign),
    campaignController.updateCampaign.bind(campaignController)
  );

  router.post(
    '/campaigns/:id/schedule',
    authorization(['campaigns:schedule']),
    validation(campaignValidation.scheduleCampaign),
    campaignController.scheduleCampaign.bind(campaignController)
  );

  router.post(
    '/campaigns/:id/send',
    authorization(['campaigns:send']),
    campaignController.sendCampaign.bind(campaignController)
  );

  router.post(
    '/campaigns/:id/pause',
    authorization(['campaigns:pause']),
    campaignController.pauseCampaign.bind(campaignController)
  );

  router.post(
    '/campaigns/:id/cancel',
    authorization(['campaigns:cancel']),
    campaignController.cancelCampaign.bind(campaignController)
  );

  router.post(
    '/campaigns/:id/complete',
    authorization(['campaigns:complete']),
    campaignController.completeCampaign.bind(campaignController)
  );

  router.post(
    '/campaigns/:id/fail',
    authorization(['campaigns:fail']),
    validation(campaignValidation.failCampaign),
    campaignController.failCampaign.bind(campaignController)
  );

  // Query routes
  router.get(
    '/campaigns/:id',
    authorization(['campaigns:read']),
    campaignController.getCampaign.bind(campaignController)
  );

  router.get(
    '/campaigns',
    authorization(['campaigns:read']),
    campaignController.listCampaigns.bind(campaignController)
  );

  router.get(
    '/campaigns/:id/stats',
    authorization(['campaigns:read']),
    campaignController.getCampaignStats.bind(campaignController)
  );

  router.get(
    '/campaigns/counts',
    authorization(['campaigns:read']),
    campaignController.getCampaignCounts.bind(campaignController)
  );

  return router;
}
