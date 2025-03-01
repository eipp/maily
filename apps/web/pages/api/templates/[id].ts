import { NextApiRequest, NextApiResponse } from 'next';
import { withApiAuth } from '../../../utils/withApiAuth';
import { prisma } from '../../../lib/prisma';
import { TemplateException } from '../../../types/template';

const handler = async (req: NextApiRequest, res: NextApiResponse) => {
  const { method } = req;
  const userId = req.user?.id;
  const { id } = req.query;

  if (!userId) {
    return res.status(401).json({ message: 'Unauthorized' });
  }

  // Convert ID to a number
  const templateId = parseInt(id as string);

  if (isNaN(templateId)) {
    return res.status(400).json({ message: 'Invalid template ID' });
  }

  try {
    // Check template existence and permissions
    const template = await prisma.emailTemplate.findUnique({
      where: { id: templateId },
    });

    if (!template) {
      return res.status(404).json({ message: 'Template not found' });
    }

    // For non-GET methods, ensure the user owns the template
    if (method !== 'GET' && template.userId !== userId) {
      return res.status(403).json({ message: 'You do not have permission to modify this template' });
    }

    // For GET method, ensure the user has access to the template (is owner or template is public)
    if (method === 'GET' && template.userId !== userId && !template.is_public) {
      return res.status(403).json({ message: 'You do not have permission to view this template' });
    }

    switch (method) {
      case 'GET':
        // Get template details
        const templateDetail = await prisma.emailTemplate.findUnique({
          where: { id: templateId },
          include: {
            user: {
              select: {
                name: true,
                email: true,
              },
            },
          },
        });

        return res.status(200).json(templateDetail);

      case 'PUT':
        // Update template
        const updateData = req.body;

        if (Object.keys(updateData).length === 0) {
          throw new TemplateException('No update data provided', 400);
        }

        const updatedTemplate = await prisma.emailTemplate.update({
          where: { id: templateId },
          data: {
            name: updateData.name !== undefined ? updateData.name : undefined,
            description: updateData.description !== undefined ? updateData.description : undefined,
            content: updateData.content !== undefined ? updateData.content : undefined,
            thumbnail: updateData.thumbnail !== undefined ? updateData.thumbnail : undefined,
            category: updateData.category !== undefined ? updateData.category : undefined,
            tags: updateData.tags !== undefined ? updateData.tags : undefined,
            is_public: updateData.is_public !== undefined ? updateData.is_public : undefined,
            updatedAt: new Date(),
          },
        });

        return res.status(200).json(updatedTemplate);

      case 'DELETE':
        // Delete template
        await prisma.emailTemplate.delete({
          where: { id: templateId },
        });

        return res.status(200).json({ message: 'Template deleted successfully' });

      default:
        res.setHeader('Allow', ['GET', 'PUT', 'DELETE']);
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
