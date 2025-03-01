import { NextApiRequest, NextApiResponse } from 'next';
import { withApiAuth } from '../../../../utils/withApiAuth';
import { prisma } from '../../../../lib/prisma';
import { TemplateException } from '../../../../types/template';

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
    if (method !== 'POST') {
      res.setHeader('Allow', ['POST']);
      return res.status(405).json({ message: `Method ${method} Not Allowed` });
    }

    // Find the template to duplicate
    const templateToDuplicate = await prisma.emailTemplate.findUnique({
      where: { id: templateId },
    });

    if (!templateToDuplicate) {
      return res.status(404).json({ message: 'Template not found' });
    }

    // Check if the user has access to duplicate the template
    if (templateToDuplicate.userId !== userId && !templateToDuplicate.is_public) {
      return res.status(403).json({ message: 'You do not have permission to duplicate this template' });
    }

    // Create a new template based on the original
    const duplicatedTemplate = await prisma.emailTemplate.create({
      data: {
        name: `${templateToDuplicate.name} (Copy)`,
        description: templateToDuplicate.description,
        content: templateToDuplicate.content,
        thumbnail: templateToDuplicate.thumbnail,
        category: templateToDuplicate.category,
        tags: templateToDuplicate.tags,
        is_public: false, // Always set duplicated templates to private
        user: {
          connect: {
            id: userId,
          },
        },
      },
    });

    return res.status(201).json(duplicatedTemplate);
  } catch (error) {
    console.error('Template duplication error:', error);

    if (error instanceof TemplateException) {
      return res.status(error.statusCode).json({ message: error.message });
    }

    return res.status(500).json({ message: 'Internal Server Error' });
  }
};

export default withApiAuth(handler);
