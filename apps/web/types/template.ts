export interface TemplateCreateInput {
  name: string;
  description?: string;
  content: string;
  thumbnail?: string;
  category?: string;
  tags?: string[];
  is_public?: boolean;
}

export interface TemplateUpdateInput {
  name?: string;
  description?: string;
  content?: string;
  thumbnail?: string;
  category?: string;
  tags?: string[];
  is_public?: boolean;
}

export class TemplateException extends Error {
  statusCode: number;

  constructor(message: string, statusCode: number = 500) {
    super(message);
    this.name = 'TemplateException';
    this.statusCode = statusCode;
  }
}

export interface Template {
  id: number;
  name: string;
  description: string;
  content: string;
  thumbnail: string | null;
  category: string | null;
  tags: string[];
  is_public: boolean;
  userId: string;
  createdAt: Date;
  updatedAt: Date;
  user?: {
    name: string | null;
    email: string | null;
  };
}

export interface TemplateListResponse {
  templates: Template[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    pages: number;
  };
}
