import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { ValidationSchema } from 'joi';
import logger from '../../../infrastructure/logging/logger';
import config from '../../../config';

/**
 * Middleware to validate request data against a schema
 * @param schema The Joi validation schema
 */
export function validation(schema: ValidationSchema) {
  return (req: Request, res: Response, next: NextFunction) => {
    const { error } = schema.validate(req.body);

    if (error) {
      logger.debug('Validation error', { error: error.message });
      return res.status(400).json({
        error: error.message,
        code: 'VALIDATION_ERROR',
      });
    }

    next();
  };
}

/**
 * Middleware to check JWT authorization
 * @param permissions Required permissions
 */
export function authorization(permissions: string[] = []) {
  return (req: Request, res: Response, next: NextFunction) => {
    const authHeader = req.headers.authorization;

    if (!authHeader) {
      return res.status(401).json({
        error: 'Authentication token is required',
        code: 'MISSING_TOKEN',
      });
    }

    const [bearer, token] = authHeader.split(' ');

    if (bearer !== 'Bearer' || !token) {
      return res.status(401).json({
        error: 'Invalid authentication token format',
        code: 'INVALID_TOKEN_FORMAT',
      });
    }

    try {
      const decoded = jwt.verify(token, config.jwt.secret) as {
        userId: string;
        permissions: string[];
      };

      // Skip permission check if no specific permissions are required
      if (permissions.length === 0) {
        req.user = decoded;
        return next();
      }

      // Check if user has any of the required permissions
      const hasPermission = permissions.some(permission =>
        decoded.permissions?.includes(permission)
      );

      if (!hasPermission) {
        return res.status(403).json({
          error: 'You do not have permission to access this resource',
          code: 'INSUFFICIENT_PERMISSIONS',
        });
      }

      req.user = decoded;
      next();
    } catch (error: any) {
      logger.debug('Authorization error', { error: error.message });
      return res.status(401).json({
        error: 'Invalid or expired authentication token',
        code: 'INVALID_TOKEN',
      });
    }
  };
}

// Add user property to Express Request interface
declare global {
  namespace Express {
    interface Request {
      user?: {
        userId: string;
        permissions: string[];
      };
    }
  }
}
