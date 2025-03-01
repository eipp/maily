import Link from 'next/link';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  EyeIcon,
  PencilIcon,
  CopyIcon,
  TrashIcon,
  StarIcon
} from 'lucide-react';
import { formatDate } from '@/lib/utils';
import { getTemplates, Template } from '@/services/graphql-templates';

export async function TemplatesList() {
  try {
    // Use the service instead of direct executeQuery
    const templates = await getTemplates(1, 20);

    if (!templates || templates.length === 0) {
      return (
        <div className="text-center py-12 border rounded-lg bg-background">
          <h3 className="text-lg font-medium">No templates found</h3>
          <p className="text-muted-foreground mt-2">
            Create your first template or use one of our pre-built templates
          </p>
          <div className="mt-6 flex justify-center gap-4">
            <Button asChild>
              <Link href="/templates/new">Create Template</Link>
            </Button>
            <Button variant="outline">Browse Gallery</Button>
          </div>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map((template) => (
          <div
            key={template.id}
            className="group border rounded-lg overflow-hidden bg-background hover:shadow-md transition-shadow"
          >
            <div className="relative aspect-video bg-muted overflow-hidden">
              {template.thumbnail ? (
                <Image
                  src={template.thumbnail}
                  alt={template.name}
                  fill
                  className="object-cover"
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center bg-primary/10">
                  <span className="text-primary font-medium">No Preview</span>
                </div>
              )}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="secondary" size="icon" asChild>
                        <Link href={`/templates/${template.id}/preview`}>
                          <EyeIcon className="h-4 w-4" />
                        </Link>
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Preview</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="secondary" size="icon" asChild>
                        <Link href={`/templates/${template.id}/edit`}>
                          <PencilIcon className="h-4 w-4" />
                        </Link>
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Edit</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="secondary" size="icon">
                        <CopyIcon className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Duplicate</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              {template.isPopular && (
                <div className="absolute top-2 left-2">
                  <Badge className="bg-amber-500 hover:bg-amber-600 flex items-center gap-1">
                    <StarIcon className="h-3 w-3" />
                    Popular
                  </Badge>
                </div>
              )}
            </div>

            <div className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium">
                    <Link href={`/templates/${template.id}`} className="hover:underline">
                      {template.name}
                    </Link>
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                    {template.description || "No description provided"}
                  </p>
                </div>
                <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive">
                  <TrashIcon className="h-4 w-4" />
                  <span className="sr-only">Delete</span>
                </Button>
              </div>

              <div className="flex items-center justify-between mt-4">
                <Badge variant="outline">
                  {template.category || "Uncategorized"}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {formatDate(template.createdAt)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  } catch (error) {
    console.error('Failed to fetch templates:', error);
    return (
      <div className="text-center py-8 border rounded-lg bg-background">
        <p className="text-destructive">Error loading templates. Please try again later.</p>
        <Button variant="outline" className="mt-4">
          Retry
        </Button>
      </div>
    );
  }
}
