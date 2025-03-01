import { NextApiRequest, NextApiResponse } from 'next';
import { withApiAuth } from '../../../utils/withApiAuth';
import { prisma } from '../../../lib/prisma';
import { TemplateCreateInput, TemplateException } from '../../../types/template';

const handler = async (req: NextApiRequest, res: NextApiResponse) => {
  const { method } = req;
  const userId = req.user?.id;

  if (!userId) {
    return res.status(401).json({ message: 'Unauthorized' });
  }

  try {
    switch (method) {
      case 'GET':
        // Get templates with pagination, filtering and sorting
        const {
          page = '1',
          limit = '12',
          search = '',
          category = '',
          sort = 'updatedAt',
          order = 'desc',
          includePublic = 'true'
        } = req.query;

        const pageNum = parseInt(page as string);
        const limitNum = parseInt(limit as string);
        const skip = (pageNum - 1) * limitNum;
        const includePublicBool = (includePublic as string) === 'true';

        // Build filter conditions
        const searchFilter = search
          ? {
              OR: [
                { name: { contains: search as string, mode: 'insensitive' } },
                { description: { contains: search as string, mode: 'insensitive' } },
                { category: { contains: search as string, mode: 'insensitive' } },
              ],
            }
          : {};

        const categoryFilter = category
          ? { category: { equals: category as string } }
          : {};

        // Determine ownership filter
        const ownershipFilter = includePublicBool
          ? {
              OR: [
                { userId: userId },
                { is_public: true },
              ],
            }
          : { userId: userId };

        // Combine all filters
        const where = {
          ...searchFilter,
          ...categoryFilter,
          ...ownershipFilter,
        };

        // Get total count for pagination
        const totalTemplates = await prisma.emailTemplate.count({
          where,
        });

        // Get templates
        const templates = await prisma.emailTemplate.findMany({
          where,
          orderBy: {
            [sort as string]: order,
          },
          skip,
          take: limitNum,
          select: {
            id: true,
            name: true,
            description: true,
            thumbnail: true,
            category: true,
            tags: true,
            is_public: true,
            userId: true,
            createdAt: true,
            updatedAt: true,
            user: {
              select: {
                name: true,
                email: true,
              },
            },
          },
        });

        return res.status(200).json({
          templates,
          pagination: {
            total: totalTemplates,
            page: pageNum,
            limit: limitNum,
            pages: Math.ceil(totalTemplates / limitNum),
          },
        });

      case 'POST':
        // Create a new template
        const templateData: TemplateCreateInput = req.body;

        if (!templateData.name) {
          throw new TemplateException('Template name is required', 400);
        }

        if (!templateData.content) {
          throw new TemplateException('Template content is required', 400);
        }

        const newTemplate = await prisma.emailTemplate.create({
          data: {
            name: templateData.name,
            description: templateData.description || '',
            content: templateData.content,
            thumbnail: templateData.thumbnail,
            category: templateData.category,
            tags: templateData.tags || [],
            is_public: templateData.is_public || false,
            user: {
              connect: {
                id: userId,
              },
            },
          },
        });

        return res.status(201).json(newTemplate);

      default:
        res.setHeader('Allow', ['GET', 'POST']);
        return res.status(405).json({ message: `Method ${method} Not Allowed` });
    }
  } catch (error) {
    console.error('Template API error:', error);

    if (error instanceof TemplateException) {
      return res.status(error.statusCode).json({ message: error.message });
    }

    return res.status(500).json({ message: 'Internal Server Error' });
  }
};

export default withApiAuth(handler);
