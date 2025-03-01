import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '../../../../lib/prisma';
import { getServerSession } from 'next-auth';
import { authOptions } from '../../auth/[...nextauth]/route';
import { TemplateException } from '../../../../types/template';

export async function GET(
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
    // Get template details
    const template = await prisma.emailTemplate.findUnique({
      where: { id: templateId },
    });

    if (!template) {
      return NextResponse.json({ message: 'Template not found' }, { status: 404 });
    }

    // Ensure the user has access to the template (is owner or template is public)
    if (template.userId !== userId && !template.is_public) {
      return NextResponse.json(
        { message: 'You do not have permission to view this template' },
        { status: 403 }
      );
    }

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

    return NextResponse.json(templateDetail);
  } catch (error) {
    console.error('Template API error:', error);

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

export async function PUT(
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
    // Check template existence and permissions
    const template = await prisma.emailTemplate.findUnique({
      where: { id: templateId },
    });

    if (!template) {
      return NextResponse.json({ message: 'Template not found' }, { status: 404 });
    }

    // Ensure the user owns the template
    if (template.userId !== userId) {
      return NextResponse.json(
        { message: 'You do not have permission to modify this template' },
        { status: 403 }
      );
    }

    // Update template
    const updateData = await request.json();

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

    return NextResponse.json(updatedTemplate);
  } catch (error) {
    console.error('Template API error:', error);

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

export async function DELETE(
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
    // Check template existence and permissions
    const template = await prisma.emailTemplate.findUnique({
      where: { id: templateId },
    });

    if (!template) {
      return NextResponse.json({ message: 'Template not found' }, { status: 404 });
    }

    // Ensure the user owns the template
    if (template.userId !== userId) {
      return NextResponse.json(
        { message: 'You do not have permission to delete this template' },
        { status: 403 }
      );
    }

    // Delete template
    await prisma.emailTemplate.delete({
      where: { id: templateId },
    });

    return NextResponse.json({ message: 'Template deleted successfully' });
  } catch (error) {
    console.error('Template API error:', error);

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
