import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '../../../lib/prisma';
import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';
import { TemplateCreateInput, TemplateException } from '../../../types/template';

export async function GET(request: NextRequest) {
  const session = await getServerSession(authOptions);
  const userId = session?.user?.id;

  if (!userId) {
    return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
  }

  try {
    // Get URL parameters
    const searchParams = request.nextUrl.searchParams;
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '12');
    const search = searchParams.get('search') || '';
    const category = searchParams.get('category') || '';
    const sort = searchParams.get('sort') || 'updatedAt';
    const order = searchParams.get('order') || 'desc';
    const includePublic = searchParams.get('includePublic') !== 'false';

    const skip = (page - 1) * limit;

    // Build filter conditions
    const searchFilter = search
      ? {
          OR: [
            { name: { contains: search, mode: 'insensitive' } },
            { description: { contains: search, mode: 'insensitive' } },
            { category: { contains: search, mode: 'insensitive' } },
          ],
        }
      : {};

    const categoryFilter = category
      ? { category: { equals: category } }
      : {};

    // Determine ownership filter
    const ownershipFilter = includePublic
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
        [sort]: order,
      },
      skip,
      take: limit,
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

    return NextResponse.json({
      templates,
      pagination: {
        total: totalTemplates,
        page,
        limit,
        pages: Math.ceil(totalTemplates / limit),
      },
    });
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

export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);
  const userId = session?.user?.id;

  if (!userId) {
    return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
  }

  try {
    const templateData: TemplateCreateInput = await request.json();

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

    return NextResponse.json(newTemplate, { status: 201 });
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
