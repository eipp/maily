import mongoose, { Document, Schema } from 'mongoose';

/**
 * Base event interface with common properties for all events
 */
export interface BaseEvent {
  eventId: string;
  eventType: string;
  timestamp: Date;
  source: string;
  userId?: string;
  sessionId?: string;
  ip?: string;
  userAgent?: string;
  properties: Record<string, any>;
  metadata?: Record<string, any>;
}

/**
 * Document interface for events stored in MongoDB
 */
export interface EventDocument extends BaseEvent, Document {
  createdAt: Date;
  processingTime?: number;
}

/**
 * Mongoose schema for events
 */
const eventSchema = new Schema(
  {
    eventId: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },
    eventType: {
      type: String,
      required: true,
      index: true,
    },
    timestamp: {
      type: Date,
      required: true,
      index: true,
    },
    source: {
      type: String,
      required: true,
      index: true,
    },
    userId: {
      type: String,
      sparse: true,
      index: true,
    },
    sessionId: {
      type: String,
      sparse: true,
      index: true,
    },
    ip: {
      type: String,
    },
    userAgent: {
      type: String,
    },
    properties: {
      type: Schema.Types.Mixed,
      required: true,
    },
    metadata: {
      type: Schema.Types.Mixed,
    },
    processingTime: {
      type: Number,
    },
  },
  {
    timestamps: true,
    versionKey: false,
  }
);

// Create indexes for efficient querying
eventSchema.index({ createdAt: 1 });
eventSchema.index({ timestamp: 1, eventType: 1 });
eventSchema.index({ userId: 1, eventType: 1, timestamp: 1 });
eventSchema.index({ sessionId: 1, timestamp: 1 });

// Define model
const Event = mongoose.model<EventDocument>('Event', eventSchema);

export default Event;
