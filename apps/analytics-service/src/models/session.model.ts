import mongoose, { Document, Schema } from 'mongoose';

/**
 * Session interface defining a user browsing session
 */
export interface Session {
  sessionId: string;
  userId?: string;
  startTime: Date;
  endTime?: Date;
  duration?: number; // in seconds
  ip?: string;
  userAgent?: string;
  device?: string;
  browser?: string;
  os?: string;
  country?: string;
  region?: string;
  city?: string;
  referrer?: string;
  entryPage?: string;
  exitPage?: string;
  pageViews: number;
  events: number;
  interactions?: number;
  bounced: boolean; // true if the session had only one page view
  metadata?: Record<string, any>;
}

/**
 * Document interface for sessions stored in MongoDB
 */
export interface SessionDocument extends Session, Document {
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Mongoose schema for sessions
 */
const sessionSchema = new Schema(
  {
    sessionId: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },
    userId: {
      type: String,
      sparse: true,
      index: true,
    },
    startTime: {
      type: Date,
      required: true,
      index: true,
    },
    endTime: {
      type: Date,
    },
    duration: {
      type: Number,
    },
    ip: {
      type: String,
    },
    userAgent: {
      type: String,
    },
    device: {
      type: String,
      index: true,
    },
    browser: {
      type: String,
      index: true,
    },
    os: {
      type: String,
      index: true,
    },
    country: {
      type: String,
      index: true,
    },
    region: {
      type: String,
    },
    city: {
      type: String,
    },
    referrer: {
      type: String,
    },
    entryPage: {
      type: String,
    },
    exitPage: {
      type: String,
    },
    pageViews: {
      type: Number,
      default: 0,
    },
    events: {
      type: Number,
      default: 0,
    },
    interactions: {
      type: Number,
      default: 0,
    },
    bounced: {
      type: Boolean,
      default: true,
    },
    metadata: {
      type: Schema.Types.Mixed,
    },
  },
  {
    timestamps: true,
    versionKey: false,
  }
);

// Create indexes for efficient querying
sessionSchema.index({ createdAt: 1 });
sessionSchema.index({ startTime: 1 });
sessionSchema.index({ userId: 1, startTime: 1 });
sessionSchema.index({ startTime: 1, bounced: 1 });
sessionSchema.index({ country: 1, startTime: 1 });
sessionSchema.index({ device: 1, browser: 1, os: 1 });

// Define model
const Session = mongoose.model<SessionDocument>('Session', sessionSchema);

export default Session;
