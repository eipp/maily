import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export function CampaignsListSkeleton() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Subject</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Created</TableHead>
          <TableHead>Open Rate</TableHead>
          <TableHead>Click Rate</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {Array.from({ length: 5 }).map((_, index) => (
          <TableRow key={index}>
            <TableCell>
              <Skeleton className="h-5 w-[180px]" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-5 w-[250px]" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-6 w-[80px] rounded-full" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-5 w-[100px]" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-5 w-[40px]" />
            </TableCell>
            <TableCell>
              <Skeleton className="h-5 w-[40px]" />
            </TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-2">
                <Skeleton className="h-8 w-8 rounded-md" />
                <Skeleton className="h-8 w-8 rounded-md" />
                <Skeleton className="h-8 w-8 rounded-md" />
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
