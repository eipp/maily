import { Router } from 'express';
import eventsController from '../controllers/events.controller';

const router = Router();

/**
 * @route   POST /api/v1/events
 * @desc    Track a new event
 * @access  Public
 */
router.post('/', eventsController.trackEvent);

/**
 * @route   POST /api/v1/events/batch
 * @desc    Track multiple events in batch
 * @access  Public
 */
router.post('/batch', eventsController.trackBatchEvents);

/**
 * @route   GET /api/v1/events
 * @desc    Get events with filtering options
 * @access  Private
 */
router.get('/', eventsController.getEvents);

/**
 * @route   GET /api/v1/events/counts
 * @desc    Get event counts by type
 * @access  Private
 */
router.get('/counts', eventsController.getEventCounts);

/**
 * @route   GET /api/v1/events/:id
 * @desc    Get a specific event by ID
 * @access  Private
 */
router.get('/:id', eventsController.getEventById);

export default router;
