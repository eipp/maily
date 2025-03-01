'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { z } from 'zod';

// Campaign schema for validation
const CampaignSchema = z.object({
  id: z.string(),
  name: z.string(),
  subject: z.string(),
  status: z.enum(['draft', 'scheduled', 'sending', 'sent', 'canceled']),
  scheduledAt: z.string().nullable().optional(),
  sentAt: z.string().nullable().optional(),
  totalSent: z.number().default(0),
  openRate: z.number().default(0),
  clickRate: z.number().default(0),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export type Campaign = z.infer<typeof CampaignSchema>;

// API response schemas
const CampaignsResponseSchema = z.object({
  campaigns: z.array(CampaignSchema),
  total: z.number(),
});

const CampaignResponseSchema = z.object({
  campaign: CampaignSchema,
});

// Query keys for caching
const campaignKeys = {
  all: ['campaigns'] as const,
  lists: () => [...campaignKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...campaignKeys.lists(), filters] as const,
  details: () => [...campaignKeys.all, 'detail'] as const,
  detail: (id: string) => [...campaignKeys.details(), id] as const,
};

// Function to fetch campaigns with filters
async function fetchCampaigns({
  status,
  page = 1,
  limit = 10,
  sort = 'createdAt',
  order = 'desc',
}: {
  status?: string;
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}) {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('page', page.toString());
  params.append('limit', limit.toString());
  params.append('sort', sort);
  params.append('order', order);

  const { data } = await axios.get(`/api/campaigns?${params.toString()}`);
  return CampaignsResponseSchema.parse(data);
}

// Function to fetch a single campaign
async function fetchCampaign(id: string) {
  const { data } = await axios.get(`/api/campaigns/${id}`);
  return CampaignResponseSchema.parse(data);
}

// Function to create a campaign
async function createCampaign(campaign: Omit<Campaign, 'id' | 'createdAt' | 'updatedAt'>) {
  const { data } = await axios.post('/api/campaigns', campaign);
  return CampaignResponseSchema.parse(data);
}

// Function to update a campaign
async function updateCampaign({
  id,
  ...campaign
}: Partial<Campaign> & { id: string }) {
  const { data } = await axios.put(`/api/campaigns/${id}`, campaign);
  return CampaignResponseSchema.parse(data);
}

// Function to delete a campaign
async function deleteCampaign(id: string) {
  await axios.delete(`/api/campaigns/${id}`);
  return { id };
}

// React Query hooks
export function useCampaigns(filters: {
  status?: string;
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
} = {}) {
  return useQuery({
    queryKey: campaignKeys.list(filters),
    queryFn: () => fetchCampaigns(filters),
  });
}

export function useCampaign(id: string) {
  return useQuery({
    queryKey: campaignKeys.detail(id),
    queryFn: () => fetchCampaign(id),
    enabled: !!id,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

export function useUpdateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateCampaign,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(data.campaign.id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

export function useDeleteCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteCampaign,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}
