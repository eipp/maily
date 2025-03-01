import mongoose, { Document, Schema } from 'mongoose';

/**
 * Types of metrics that can be aggregated
 */
export enum MetricType {
  COUNT = 'count',
  SUM = 'sum',
  AVERAGE = 'average',
  MIN = 'min',
  MAX = 'max',
  UNIQUE = 'unique',
  PERCENTILE = 'percentile',
  HISTOGRAM = 'histogram',
}

/**
 * Time granularity for aggregated metrics
 */
export enum TimeGranularity {
  MINUTE = 'minute',
  HOUR = 'hour',
  DAY = 'day',
  WEEK = 'week',
  MONTH = 'month',
  QUARTER = 'quarter',
  YEAR = 'year',
}

/**
 * Interface defining an aggregated metric
 */
export interface Metric {
  name: string;
  type: MetricType;
  value: number | Record<string, number>;
  dimensions?: Record<string, string | number>;
  timestamp: Date;
  timeGranularity: TimeGranularity;
  startPeriod: Date;
  endPeriod: Date;
  metadata?: Record<string, any>;
}

/**
 * Document interface for metrics stored in MongoDB
 */
export interface MetricDocument extends Metric, Document {
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Mongoose schema for metrics
 */
const metricSchema = new Schema(
  {
    name: {
      type: String,
      required: true,
      index: true,
    },
    type: {
      type: String,
      enum: Object.values(MetricType),
      required: true,
      index: true,
    },
    value: {
      type: Schema.Types.Mixed,
      required: true,
    },
    dimensions: {
      type: Schema.Types.Mixed,
      default: {},
    },
    timestamp: {
      type: Date,
      required: true,
      index: true,
    },
    timeGranularity: {
      type: String,
      enum: Object.values(TimeGranularity),
      required: true,
      index: true,
    },
    startPeriod: {
      type: Date,
      required: true,
      index: true,
    },
    endPeriod: {
      type: Date,
      required: true,
      index: true,
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

// Create compound indexes for efficient querying
metricSchema.index({ name: 1, timestamp: 1 });
metricSchema.index({ name: 1, type: 1, timeGranularity: 1 });
metricSchema.index({ name: 1, startPeriod: 1, endPeriod: 1 });
metricSchema.index({
  name: 1,
  type: 1,
  timeGranularity: 1,
  startPeriod: 1
});

// Create a text index for the metric name to enable text search
metricSchema.index({ name: 'text' });

// Define model
const Metric = mongoose.model<MetricDocument>('Metric', metricSchema);

export default Metric;
