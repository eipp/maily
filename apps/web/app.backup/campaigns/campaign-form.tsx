'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@apollo/client';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Textarea } from '@/components/ui/textarea';
import { executeQuery } from '@/lib/apollo-server';
import { GET_CAMPAIGN } from '@/graphql/queries';
import { CREATE_CAMPAIGN, UPDATE_CAMPAIGN } from '@/graphql/mutations';
import { toast } from '@/components/ui/use-toast';
import { SubjectGenerator } from '@/components/ai/subject-generator';
import { ContentOptimizer } from '@/components/ai/content-optimizer';
import { TemplateRecommender } from '@/components/ai/template-recommender';
import { ContentAnalyzer } from '@/components/ai/content-analyzer';
import { Sparkles } from 'lucide-react';

interface CampaignFormProps {
  campaignId?: string;
}

interface CampaignData {
  campaign: {
    id: string;
    name: string;
    subject: string;
    previewText: string;
    template: {
      id: string;
      name: string;
    };
    segment: {
      id: string;
      name: string;
    };
    fromName: string;
    fromEmail: string;
    replyToEmail: string;
    trackOpens: boolean;
    trackClicks: boolean;
    emailContent?: string;
  };
}

const formSchema = z.object({
  name: z.string().min(1, 'Campaign name is required'),
  subject: z.string().min(1, 'Subject line is required'),
  previewText: z.string().optional(),
  templateId: z.string().min(1, 'Template is required'),
  segmentId: z.string().min(1, 'Audience segment is required'),
  fromName: z.string().min(1, 'Sender name is required'),
  fromEmail: z.string().email('Valid email is required'),
  replyToEmail: z.string().email('Valid email is required'),
  trackOpens: z.boolean().default(true),
  trackClicks: z.boolean().default(true),
  emailContent: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

export async function CampaignForm({ campaignId }: CampaignFormProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('details');
  const [isLoading, setIsLoading] = useState(false);
  const [templates, setTemplates] = useState([
    { id: '1', name: 'Welcome Email' },
    { id: '2', name: 'Newsletter' },
    { id: '3', name: 'Promotional' },
    { id: '4', name: 'Announcement' },
  ]);
  const [segments, setSegments] = useState([
    { id: '1', name: 'All Subscribers' },
    { id: '2', name: 'Active Users' },
    { id: '3', name: 'Inactive Users' },
    { id: '4', name: 'New Subscribers' },
  ]);

  // Default form values
  const defaultValues: FormValues = {
    name: '',
    subject: '',
    previewText: '',
    templateId: '',
    segmentId: '',
    fromName: 'Maily Team',
    fromEmail: 'noreply@mailyapp.com',
    replyToEmail: 'support@mailyapp.com',
    trackOpens: true,
    trackClicks: true,
    emailContent: '',
  };

  // Create form instance
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues,
  });

  // If editing, fetch campaign data
  if (campaignId) {
    const loadCampaignData = async () => {
      try {
        const data = await executeQuery<CampaignData>(GET_CAMPAIGN, { id: campaignId });
        if (data.campaign) {
          form.reset({
            name: data.campaign.name,
            subject: data.campaign.subject,
            previewText: data.campaign.previewText,
            templateId: data.campaign.template.id,
            segmentId: data.campaign.segment.id,
            fromName: data.campaign.fromName,
            fromEmail: data.campaign.fromEmail,
            replyToEmail: data.campaign.replyToEmail,
            trackOpens: data.campaign.trackOpens,
            trackClicks: data.campaign.trackClicks,
            emailContent: data.campaign.emailContent || '',
          });
        }
      } catch (error) {
        console.error('Error loading campaign data:', error);
        toast({
          title: 'Error',
          description: 'Failed to load campaign data. Please try again.',
          variant: 'destructive',
        });
      }
    };

    loadCampaignData();
  }

  // Form submission handler
  const onSubmit = async (values: FormValues) => {
    setIsLoading(true);
    try {
      if (campaignId) {
        // Update existing campaign
        await useMutation(UPDATE_CAMPAIGN, {
          variables: {
            id: campaignId,
            ...values,
          },
        });
        toast({
          title: 'Success',
          description: 'Campaign updated successfully',
        });
        router.push(`/campaigns/${campaignId}`);
      } else {
        // Create new campaign
        const { data } = await useMutation(CREATE_CAMPAIGN, {
          variables: values,
        });
        toast({
          title: 'Success',
          description: 'Campaign created successfully',
        });
        router.push(`/campaigns/${data.createCampaign.id}`);
      }
    } catch (error) {
      console.error('Error saving campaign:', error);
      toast({
        title: 'Error',
        description: 'Failed to save campaign. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle tab change
  const handleTabChange = (value: string) => {
    setActiveTab(value);
  };

  const nextTab = () => {
    if (activeTab === 'details') setActiveTab('content');
    else if (activeTab === 'content') setActiveTab('audience');
    else if (activeTab === 'audience') setActiveTab('settings');
  };

  const prevTab = () => {
    if (activeTab === 'settings') setActiveTab('audience');
    else if (activeTab === 'audience') setActiveTab('content');
    else if (activeTab === 'content') setActiveTab('details');
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="details">Campaign Details</TabsTrigger>
            <TabsTrigger value="content">Content</TabsTrigger>
            <TabsTrigger value="audience">Audience</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="details" className="space-y-6">
            <div className="grid grid-cols-1 gap-6">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Campaign Name</FormLabel>
                    <FormControl>
                      <Input placeholder="E.g. Monthly Newsletter - February 2025" {...field} />
                    </FormControl>
                    <FormDescription>
                      Internal name to identify your campaign
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="subject"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="flex items-center gap-2">
                      Subject Line
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
                        <Sparkles className="h-3 w-3 mr-1" />
                        AI-assisted
                      </span>
                    </FormLabel>
                    <FormControl>
                      <Input placeholder="E.g. Don't miss our February specials!" {...field} />
                    </FormControl>
                    <FormDescription>
                      The subject line recipients will see in their inbox
                    </FormDescription>
                    <FormMessage />
                    <div className="mt-3">
                      <SubjectGenerator
                        campaignName={form.watch('name')}
                        campaignType="marketing"
                        onSelectSubject={(subject) => form.setValue('subject', subject)}
                      />
                    </div>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="previewText"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Preview Text</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Brief preview text that appears in the inbox"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Short text displayed after the subject line in some email clients
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </TabsContent>

          <TabsContent value="content" className="space-y-6">
            <div className="grid grid-cols-1 gap-6">
              <FormField
                control={form.control}
                name="templateId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email Template</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a template" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {templates.map((template) => (
                          <SelectItem key={template.id} value={template.id}>
                            {template.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Choose a template for your campaign
                    </FormDescription>
                    <FormMessage />
                    <div className="mt-2 flex justify-end">
                      <TemplateRecommender
                        campaignName={form.watch('name')}
                        campaignSubject={form.watch('subject')}
                        campaignContent={form.watch('emailContent')}
                        campaignGoals={['engagement', 'conversion']}
                        onSelectTemplate={(templateId) => form.setValue('templateId', templateId)}
                      />
                    </div>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="emailContent"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="flex items-center gap-2">
                      Email Content
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
                        <Sparkles className="h-3 w-3 mr-1" />
                        AI-optimized
                      </span>
                    </FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Enter your email content here..."
                        className="h-[300px] font-mono"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Content will be merged with your selected template
                    </FormDescription>
                    <FormMessage />
                    <div className="mt-3 flex justify-end">
                      <ContentOptimizer
                        content={field.value || ''}
                        onApplySuggestion={(newContent) => field.onChange(newContent)}
                      />
                    </div>
                    <div className="mt-2 flex justify-end">
                      <ContentAnalyzer
                        content={field.value || ''}
                        subject={form.watch('subject')}
                      />
                    </div>
                  </FormItem>
                )}
              />
            </div>

            <div className="flex justify-between pt-6">
              <Button type="button" variant="outline" onClick={prevTab}>
                Back
              </Button>
              <Button type="button" onClick={nextTab}>
                Next
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="audience" className="space-y-6">
            <FormField
              control={form.control}
              name="segmentId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Audience Segment</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a segment" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {segments.map((segment) => (
                        <SelectItem key={segment.id} value={segment.id}>
                          {segment.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    Choose which subscribers will receive this campaign
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="p-4 bg-muted rounded-md">
              <h3 className="text-sm font-medium mb-2">Segment Details</h3>
              <p className="text-sm text-muted-foreground mb-2">Total recipients: 1,245</p>
              <div className="text-xs text-muted-foreground">
                <p>• Subscribed to newsletter</p>
                <p>• Opened an email in the last 30 days</p>
                <p>• Not marked as VIP</p>
              </div>
            </div>

            <div className="flex justify-end mt-6">
              <Button
                type="button"
                variant="outline"
                onClick={() => window.open('/segments', '_blank')}
              >
                Manage Segments
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FormField
                control={form.control}
                name="fromName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>From Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Sender name" {...field} />
                    </FormControl>
                    <FormDescription>
                      Name that will appear as the sender
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="fromEmail"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>From Email</FormLabel>
                    <FormControl>
                      <Input placeholder="sender@example.com" {...field} />
                    </FormControl>
                    <FormDescription>
                      Email address that will appear as the sender
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="replyToEmail"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Reply-To Email</FormLabel>
                    <FormControl>
                      <Input placeholder="reply@example.com" {...field} />
                    </FormControl>
                    <FormDescription>
                      Email address for replies
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="flex flex-col gap-4 mt-6">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="trackOpens"
                  checked={form.watch('trackOpens')}
                  onChange={(e) => form.setValue('trackOpens', e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <div className="grid gap-1.5 leading-none">
                  <Label htmlFor="trackOpens">Track Opens</Label>
                  <p className="text-sm text-muted-foreground">
                    Monitor when recipients open your email
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="trackClicks"
                  checked={form.watch('trackClicks')}
                  onChange={(e) => form.setValue('trackClicks', e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <div className="grid gap-1.5 leading-none">
                  <Label htmlFor="trackClicks">Track Clicks</Label>
                  <p className="text-sm text-muted-foreground">
                    Monitor when recipients click links in your email
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <div className="flex justify-between pt-6 border-t">
          <Button
            type="button"
            variant="outline"
            onClick={prevTab}
            disabled={activeTab === 'details'}
          >
            Previous
          </Button>

          {activeTab === 'settings' ? (
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push('/campaigns')}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Saving...' : campaignId ? 'Update Campaign' : 'Create Campaign'}
              </Button>
            </div>
          ) : (
            <Button
              type="button"
              onClick={nextTab}
            >
              Next
            </Button>
          )}
        </div>
      </form>
    </Form>
  );
}
