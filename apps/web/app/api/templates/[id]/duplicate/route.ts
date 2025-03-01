import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '../../../../../lib/prisma';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../../auth/[...nextauth]/route';
import { TemplateException } from '../../../../../types/template';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getServerSession(authOptions);
  const userId = session?.user?.id;

  if (!userId) {
    return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
  }

  // Convert ID to a number
  const templateId = parseInt(params.id);

  if (isNaN(templateId)) {
    return NextResponse.json({ message: 'Invalid template ID' }, { status: 400 });
  }

  try {
    // Find the template to duplicate
    const templateToDuplicate = await prisma.emailTemplate.findUnique({
      where: { id: templateId },
    });

    if (!templateToDuplicate) {
      return NextResponse.json({ message: 'Template not found' }, { status: 404 });
    }

    // Check if the user has access to duplicate the template
    if (templateToDuplicate.userId !== userId && !templateToDuplicate.is_public) {
      return NextResponse.json(
        { message: 'You do not have permission to duplicate this template' },
        { status: 403 }
      );
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

    return NextResponse.json(duplicatedTemplate, { status: 201 });
  } catch (error) {
    console.error('Template duplication error:', error);

    if (error instanceof TemplateException) {
      return NextResponse.json(
        { message: error.message },
        { status: error.statusCode }
      );
    }

    return NextResponse.json(
      { message: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
