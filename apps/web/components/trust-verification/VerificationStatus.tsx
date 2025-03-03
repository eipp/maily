/**
 * VerificationStatus Component
 * 
 * This component displays the blockchain verification status of emails and campaigns,
 * including certificate visualization, QR code generation, and verification history.
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Timeline, TimelineItem, TimelineConnector, TimelineContent, TimelineDot, TimelineOppositeContent, TimelineSeparator } from '@/components/ui/timeline';
import { QRCode } from '@/components/ui/qr-code';
import { Certificate } from '@/components/ui/certificate';
import { Shield, CheckCircle, XCircle, Clock, ExternalLink, Download, Copy, QrCode, History, Certificate as CertificateIcon } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
import { useVerification } from '@/hooks/use-verification';
import { VerificationStatus as VerificationStatusType, Certificate as CertificateType, VerificationEvent } from '@/types/verification';

// Define the props
export interface VerificationStatusProps {
  entityId: string;
  entityType: 'email' | 'campaign';
  className?: string;
  compact?: boolean;
}

/**
 * VerificationStatus component
 * 
 * @param props Component props
 * @returns VerificationStatus component
 */
export const VerificationStatus: React.FC<VerificationStatusProps> = ({
  entityId,
  entityType,
  className = '',
  compact = false,
}) => {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<string>('status');
  const [showQRCode, setShowQRCode] = useState<boolean>(false);
  const [showCertificate, setShowCertificate] = useState<boolean>(false);
  
  // Get verification data
  const {
    status,
    certificate,
    verificationEvents,
    verificationUrl,
    isLoading,
    error,
    refreshVerification,
  } = useVerification(entityId, entityType);
  
  // Copy verification URL to clipboard
  const copyVerificationUrl = () => {
    if (!verificationUrl) return;
    
    navigator.clipboard.writeText(verificationUrl)
      .then(() => {
        toast({
          title: 'URL copied to clipboard',
          description: 'Verification URL has been copied to your clipboard.',
        });
      })
      .catch((err) => {
        console.error('Failed to copy URL:', err);
        toast({
          title: 'Failed to copy URL',
          description: 'An error occurred while copying the URL.',
          variant: 'destructive',
        });
      });
  };
  
  // Download certificate
  const downloadCertificate = () => {
    if (!certificate) return;
    
    // Create a blob from the certificate data
    const certificateJson = JSON.stringify(certificate, null, 2);
    const blob = new Blob([certificateJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    // Create a temporary link and trigger download
    const a = document.createElement('a');
    a.href = url;
    a.download = `certificate-${entityId.substring(0, 8)}.json`;
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast({
      title: 'Certificate downloaded',
      description: 'The certificate has been downloaded as a JSON file.',
    });
  };
  
  // Get status color
  const getStatusColor = (status: VerificationStatusType): string => {
    switch (status) {
      case 'verified':
        return 'bg-green-500';
      case 'pending':
        return 'bg-yellow-500';
      case 'failed':
        return 'bg-red-500';
      case 'revoked':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };
  
  // Get status icon
  const getStatusIcon = (status: VerificationStatusType) => {
    switch (status) {
      case 'verified':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'revoked':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Shield className="h-5 w-5 text-gray-500" />;
    }
  };
  
  // Get status text
  const getStatusText = (status: VerificationStatusType): string => {
    switch (status) {
      case 'verified':
        return 'Verified';
      case 'pending':
        return 'Pending Verification';
      case 'failed':
        return 'Verification Failed';
      case 'revoked':
        return 'Certificate Revoked';
      default:
        return 'Unknown Status';
    }
  };
  
  // Get event icon
  const getEventIcon = (event: VerificationEvent) => {
    switch (event.type) {
      case 'created':
        return <CertificateIcon className="h-4 w-4 text-blue-500" />;
      case 'submitted':
        return <Shield className="h-4 w-4 text-blue-500" />;
      case 'verified':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'revoked':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };
  
  // Render compact view
  if (compact) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        {getStatusIcon(status)}
        <span className="text-sm font-medium">{getStatusText(status)}</span>
        
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={() => setShowCertificate(true)}
              >
                <CertificateIcon className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>View Certificate</TooltipContent>
          </Tooltip>
        </TooltipProvider>
        
        <Dialog open={showCertificate} onOpenChange={setShowCertificate}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Verification Certificate</DialogTitle>
              <DialogDescription>
                This certificate verifies the authenticity of this {entityType}.
              </DialogDescription>
            </DialogHeader>
            
            {certificate ? (
              <div className="mt-4">
                <Certificate
                  certificate={certificate}
                  verificationUrl={verificationUrl}
                />
              </div>
            ) : (
              <div className="flex items-center justify-center h-64">
                <p className="text-muted-foreground">
                  {isLoading ? 'Loading certificate...' : 'No certificate available'}
                </p>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    );
  }
  
  // Render full view
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Shield className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Trust Verification</CardTitle>
          </div>
          
          <Badge
            className={`${
              status === 'verified'
                ? 'bg-green-100 text-green-800'
                : status === 'pending'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {getStatusText(status)}
          </Badge>
        </div>
        <CardDescription>
          Blockchain verification for this {entityType}
        </CardDescription>
      </CardHeader>
      
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="w-full"
      >
        <div className="px-4">
          <TabsList className="w-full">
            <TabsTrigger value="status" className="flex-1">
              Status
            </TabsTrigger>
            <TabsTrigger value="certificate" className="flex-1">
              Certificate
            </TabsTrigger>
            <TabsTrigger value="history" className="flex-1">
              History
            </TabsTrigger>
          </TabsList>
        </div>
        
        {/* Status tab */}
        <TabsContent value="status" className="m-0">
          <CardContent className="pt-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(status)}
                  <span className="font-medium">{getStatusText(status)}</span>
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={refreshVerification}
                  disabled={isLoading}
                >
                  Refresh
                </Button>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Verification Progress</span>
                  <span className="font-medium">
                    {status === 'verified'
                      ? '100%'
                      : status === 'pending'
                      ? '50%'
                      : '0%'}
                  </span>
                </div>
                <Progress
                  value={
                    status === 'verified'
                      ? 100
                      : status === 'pending'
                      ? 50
                      : 0
                  }
                  className="h-2"
                  indicatorClassName={getStatusColor(status)}
                />
              </div>
              
              {verificationUrl && (
                <div className="pt-2">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-muted-foreground">Verification URL</span>
                    <div className="flex items-center space-x-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={copyVerificationUrl}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => setShowQRCode(true)}
                      >
                        <QrCode className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  <div className="bg-muted p-2 rounded-md text-xs break-all">
                    <a
                      href={verificationUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline flex items-center"
                    >
                      {verificationUrl}
                      <ExternalLink className="h-3 w-3 ml-1 flex-shrink-0" />
                    </a>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </TabsContent>
        
        {/* Certificate tab */}
        <TabsContent value="certificate" className="m-0">
          <CardContent className="pt-4">
            {certificate ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium">Certificate Details</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={downloadCertificate}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download
                  </Button>
                </div>
                
                <div className="bg-muted p-4 rounded-md">
                  <Certificate
                    certificate={certificate}
                    verificationUrl={verificationUrl}
                    compact
                  />
                </div>
                
                <div className="pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => setShowCertificate(true)}
                  >
                    View Full Certificate
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-48">
                <p className="text-muted-foreground">
                  {isLoading ? 'Loading certificate...' : 'No certificate available'}
                </p>
              </div>
            )}
          </CardContent>
        </TabsContent>
        
        {/* History tab */}
        <TabsContent value="history" className="m-0">
          <CardContent className="pt-4">
            {verificationEvents && verificationEvents.length > 0 ? (
              <ScrollArea className="h-48">
                <Timeline position="alternate">
                  {verificationEvents.map((event, index) => (
                    <TimelineItem key={index}>
                      <TimelineOppositeContent className="text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                      </TimelineOppositeContent>
                      <TimelineSeparator>
                        <TimelineDot className="bg-primary">
                          {getEventIcon(event)}
                        </TimelineDot>
                        {index < verificationEvents.length - 1 && <TimelineConnector />}
                      </TimelineSeparator>
                      <TimelineContent>
                        <div className="text-sm font-medium">
                          {event.type.charAt(0).toUpperCase() + event.type.slice(1)}
                        </div>
                        {event.details && (
                          <div className="text-xs text-muted-foreground">
                            {event.details}
                          </div>
                        )}
                      </TimelineContent>
                    </TimelineItem>
                  ))}
                </Timeline>
              </ScrollArea>
            ) : (
              <div className="flex items-center justify-center h-48">
                <p className="text-muted-foreground">
                  {isLoading ? 'Loading history...' : 'No verification history available'}
                </p>
              </div>
            )}
          </CardContent>
        </TabsContent>
      </Tabs>
      
      <CardFooter className="pt-2 pb-3">
        <div className="text-xs text-muted-foreground">
          {certificate && (
            <span>
              Certificate ID: <code className="bg-muted px-1 rounded">{certificate.id.substring(0, 8)}</code>
            </span>
          )}
        </div>
      </CardFooter>
      
      {/* QR Code Dialog */}
      <Dialog open={showQRCode} onOpenChange={setShowQRCode}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Verification QR Code</DialogTitle>
            <DialogDescription>
              Scan this QR code to verify the authenticity of this {entityType}.
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex items-center justify-center p-4">
            <QRCode
              value={verificationUrl || ''}
              size={256}
              level="H"
              includeMargin
            />
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Certificate Dialog */}
      <Dialog open={showCertificate} onOpenChange={setShowCertificate}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Verification Certificate</DialogTitle>
            <DialogDescription>
              This certificate verifies the authenticity of this {entityType}.
            </DialogDescription>
          </DialogHeader>
          
          {certificate ? (
            <div className="mt-4">
              <Certificate
                certificate={certificate}
                verificationUrl={verificationUrl}
              />
            </div>
          ) : (
            <div className="flex items-center justify-center h-64">
              <p className="text-muted-foreground">
                {isLoading ? 'Loading certificate...' : 'No certificate available'}
              </p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default VerificationStatus;
