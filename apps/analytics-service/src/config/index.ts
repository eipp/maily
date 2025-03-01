import dotenv from 'dotenv';
import path from 'path';
import Joi from 'joi';

// Load environment variables from .env file
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

/**
 * Environment variable validation schema
 */
const envSchema = Joi.object()
  .keys({
    NODE_ENV: Joi.string()
      .valid('development', 'production', 'test', 'staging')
      .default('development'),
    PORT: Joi.number().default(4000),
    API_PREFIX: Joi.string().default('/api/v1'),

    // MongoDB
    MONGODB_URI: Joi.string().required().description('MongoDB connection URI'),

    // Redis
    REDIS_HOST: Joi.string().default('localhost'),
    REDIS_PORT: Joi.number().default(6379),
    REDIS_PASSWORD: Joi.string().allow('').default(''),
    REDIS_TTL: Joi.number().default(3600),

    // JWT
    JWT_SECRET: Joi.string().required(),
    JWT_EXPIRATION: Joi.string().default('1d'),

    // RabbitMQ
    RABBITMQ_URL: Joi.string().default('amqp://localhost:5672'),
    RABBITMQ_EXCHANGE: Joi.string().default('maily-events'),
    RABBITMQ_QUEUE: Joi.string().default('analytics-events'),

    // Kafka
    KAFKA_BROKERS: Joi.string().default('localhost:9092'),
    KAFKA_CLIENT_ID: Joi.string().default('analytics-service'),
    KAFKA_GROUP_ID: Joi.string().default('analytics-consumers'),

    // Logging
    LOG_LEVEL: Joi.string()
      .valid('error', 'warn', 'info', 'debug')
      .default('info'),
    LOG_FILE_PATH: Joi.string().default('logs/analytics-service.log'),

    // Monitoring
    ENABLE_METRICS: Joi.boolean().default(true),
    METRICS_PORT: Joi.number().default(9090),

    // Tracing
    ENABLE_TRACING: Joi.boolean().default(false),
    TRACING_EXPORTER: Joi.string().valid('jaeger', 'zipkin').default('jaeger'),
    JAEGER_ENDPOINT: Joi.string().default('http://localhost:14268/api/traces'),
  })
  .unknown();

/**
 * Validate environment variables against the schema
 */
const { value: validatedEnv, error } = envSchema
  .prefs({ errors: { label: 'key' } })
  .validate(process.env);

if (error) {
  throw new Error(`Environment variable validation error: ${error.message}`);
}

/**
 * Application configuration object
 */
export default {
  env: validatedEnv.NODE_ENV,
  isProduction: validatedEnv.NODE_ENV === 'production',
  isTest: validatedEnv.NODE_ENV === 'test',
  isDevelopment: validatedEnv.NODE_ENV === 'development',

  server: {
    port: validatedEnv.PORT,
    apiPrefix: validatedEnv.API_PREFIX,
  },

  mongodb: {
    uri: validatedEnv.MONGODB_URI,
    options: {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    },
  },

  redis: {
    host: validatedEnv.REDIS_HOST,
    port: validatedEnv.REDIS_PORT,
    password: validatedEnv.REDIS_PASSWORD,
    ttl: validatedEnv.REDIS_TTL,
  },

  jwt: {
    secret: validatedEnv.JWT_SECRET,
    expiration: validatedEnv.JWT_EXPIRATION,
  },

  rabbitmq: {
    url: validatedEnv.RABBITMQ_URL,
    exchange: validatedEnv.RABBITMQ_EXCHANGE,
    queue: validatedEnv.RABBITMQ_QUEUE,
  },

  kafka: {
    brokers: validatedEnv.KAFKA_BROKERS.split(','),
    clientId: validatedEnv.KAFKA_CLIENT_ID,
    groupId: validatedEnv.KAFKA_GROUP_ID,
  },

  logging: {
    level: validatedEnv.LOG_LEVEL,
    filePath: validatedEnv.LOG_FILE_PATH,
  },

  metrics: {
    enabled: validatedEnv.ENABLE_METRICS,
    port: validatedEnv.METRICS_PORT,
  },

  tracing: {
    enabled: validatedEnv.ENABLE_TRACING,
    exporter: validatedEnv.TRACING_EXPORTER,
    jaegerEndpoint: validatedEnv.JAEGER_ENDPOINT,
  },
};
