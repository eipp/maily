'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Canvas } from '@/components/Canvas';
import { CognitiveCanvas } from '@/components/CognitiveCanvas';
import { Button } from '@/components/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/Tabs';
import { Input } from '@/components/Input';
import { Textarea } from '@/components/Textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/Select';
import {
  FileText,
  PresentationIcon,
  FileSpreadsheet,
  FileIcon,
  PlusCircle,
  MinusCircle,
  FileCode,
  ChartPieIcon,
  TableIcon
} from 'lucide-react';

interface MailyDocsCanvasProps {
  initialDocumentType?: string;
  recipientData?: Record<string, any>;
  onSave?: (documentData: Record<string, any>) => Promise<void>;
  templates?: Array<{ id: string; name: string; type: string }>;
}

interface DocumentSection {
  id: string;
  type: 'text' | 'chart' | 'table' | 'image' | 'interactive';
  title: string;
  content: string | Record<string, any>;
}

export function MailyDocsCanvas({
  initialDocumentType = 'smart_pdf',
  recipientData,
  onSave,
  templates = []
}: MailyDocsCanvasProps) {
  // Document state
  const [documentType, setDocumentType] = useState(initialDocumentType);
  const [documentTitle, setDocumentTitle] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [sections, setSections] = useState<DocumentSection[]>([
    { id: '1', type: 'text', title: 'Introduction', content: '' }
  ]);
  const [personalizationEnabled, setPersonalizationEnabled] = useState(!!recipientData);
  const [blockchainVerify, setBlockchainVerify] = useState(false);
  const [activeTab, setActiveTab] = useState('design');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedPreview, setGeneratedPreview] = useState<string | null>(null);
  const [certificateData, setCertificateData] = useState<any>(null);
  const [verificationBadge, setVerificationBadge] = useState<string | null>(null);

  // Filtered templates based on document type
  const filteredTemplates = templates.filter(template => template.type === documentType);

  // Document type options with icons
  const documentTypes = [
    { id: 'smart_pdf', name: 'Smart PDF', icon: <FileText className="h-4 w-4" /> },
    { id: 'dynamic_presentation', name: 'Dynamic Presentation', icon: <PresentationIcon className="h-4 w-4" /> },
    { id: 'live_spreadsheet', name: 'Live Spreadsheet', icon: <FileSpreadsheet className="h-4 w-4" /> },
    { id: 'custom_report', name: 'Custom Report', icon: <FileIcon className="h-4 w-4" /> }
  ];

  // Section type options with icons
  const sectionTypes = [
    { id: 'text', name: 'Text', icon: <FileText className="h-4 w-4" /> },
    { id: 'chart', name: 'Chart', icon: <ChartPieIcon className="h-4 w-4" /> },
    { id: 'table', name: 'Table', icon: <TableIcon className="h-4 w-4" /> },
    { id: 'image', name: 'Image', icon: <FileIcon className="h-4 w-4" /> },
    { id: 'interactive', name: 'Interactive Element', icon: <FileCode className="h-4 w-4" /> }
  ];

  // Add a new section
  const addSection = () => {
    const newSection: DocumentSection = {
      id: Date.now().toString(),
      type: 'text',
      title: `Section ${sections.length + 1}`,
      content: ''
    };
    setSections([...sections, newSection]);
  };

  // Remove a section
  const removeSection = (id: string) => {
    setSections(sections.filter(section => section.id !== id));
  };

  // Update a section
  const updateSection = (id: string, field: string, value: any) => {
    setSections(sections.map(section =>
      section.id === id ? { ...section, [field]: value } : section
    ));
  };

  // Handle document type change
  const handleDocumentTypeChange = (type: string) => {
    setDocumentType(type);
    setSelectedTemplate(''); // Reset template when type changes
  };

  // Generate document preview
  const generatePreview = async () => {
    setIsGenerating(true);

    try {
      // Simulating API call for document preview generation
      await new Promise(resolve => setTimeout(resolve, 1500));

      // In a real implementation, this would call your API
      setGeneratedPreview(`https://example.com/preview/${documentType}_${Date.now()}.png`);
    } catch (error) {
      console.error('Error generating preview:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  // Handle document save
  const handleSave = async () => {
    if (!documentTitle) {
      alert('Please enter a document title');
      return;
    }

    const documentData = {
      type: documentType,
      title: documentTitle,
      template: selectedTemplate || null,
      sections: sections,
      personalization: personalizationEnabled,
      blockchainVerify: blockchainVerify,
      recipientData: recipientData || null
    };

    if (onSave) {
      try {
        // Save the document
        const savedDocument = await onSave(documentData);
        
        // If blockchain verification is enabled, generate a certificate
        if (blockchainVerify && savedDocument && savedDocument.id) {
          try {
            // Call the API to verify the document and generate a certificate
            const verifyResponse = await fetch(`/api/v1/mailydocs/documents/${savedDocument.id}/verify`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
            });
            
            if (verifyResponse.ok) {
              const verificationData = await verifyResponse.json();
              console.log('Document verified with certificate:', verificationData);
              
              // Store certificate data
              setCertificateData(verificationData);
              
              // Fetch verification badge if available
              if (verificationData.data && verificationData.data.verification_info && verificationData.data.verification_info.qr_code) {
                setVerificationBadge(verificationData.data.verification_info.qr_code);
              } else {
                // Try to fetch badge from the API
                try {
                  const badgeResponse = await fetch(`/api/v1/blockchain/canvas/${savedDocument.id}/badge`, {
                    method: 'GET',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                  });
                  
                  if (badgeResponse.ok) {
                    const badgeData = await badgeResponse.json();
                    if (badgeData.data && badgeData.data.qr_code) {
                      setVerificationBadge(badgeData.data.qr_code);
                    }
                  }
                } catch (badgeError) {
                  console.error('Error fetching verification badge:', badgeError);
                }
              }
              
              // Switch to certificate tab
              setActiveTab('certificate');
              
              // Show success message to user
              alert('Document saved with blockchain verification certificate');
            } else {
              console.error('Failed to verify document:', await verifyResponse.text());
              alert('Document saved, but blockchain verification failed');
            }
          } catch (verifyError) {
            console.error('Error verifying document:', verifyError);
            alert('Document saved, but an error occurred during blockchain verification');
          }
        } else {
          // Regular save without verification
          alert('Document saved successfully');
        }
      } catch (error) {
        console.error('Error saving document:', error);
        alert('Error saving document');
      }
    }
  };

  return (
    <div className="flex flex-col space-y-4">
      <h2 className="text-2xl font-bold">MailyDocs Editor</h2>

      <Tabs defaultValue={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="design">Design</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="preview">Preview</TabsTrigger>
          <TabsTrigger value="certificate" disabled={!certificateData}>Verification</TabsTrigger>
        </TabsList>

        {/* Design Tab */}
        <TabsContent value="design" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Document Type</label>
              <Select value={documentType} onValueChange={handleDocumentTypeChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select document type" />
                </SelectTrigger>
                <SelectContent>
                  {documentTypes.map(type => (
                    <SelectItem key={type.id} value={type.id}>
                      <div className="flex items-center space-x-2">
                        {type.icon}
                        <span>{type.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Template (Optional)</label>
              <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
                <SelectTrigger>
                  <SelectValue placeholder="Select template" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">No Template</SelectItem>
                  {filteredTemplates.map(template => (
                    <SelectItem key={template.id} value={template.id}>
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex flex-col space-y-2">
            <label className="block text-sm font-medium">Document Title</label>
            <Input
              value={documentTitle}
              onChange={e => setDocumentTitle(e.target.value)}
              placeholder="Enter document title"
            />
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="personalization"
                checked={personalizationEnabled}
                onChange={e => setPersonalizationEnabled(e.target.checked)}
              />
              <label htmlFor="personalization">Enable Personalization</label>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="blockchain"
                checked={blockchainVerify}
                onChange={e => setBlockchainVerify(e.target.checked)}
              />
              <label htmlFor="blockchain">Blockchain Verification</label>
            </div>
          </div>

          {/* Canvas integration */}
          <div className="border rounded-md p-4">
            <h3 className="text-lg font-medium mb-2">Visual Editor</h3>
            <CognitiveCanvas 
              documentId={documentTitle ? `${documentType}-${documentTitle.replace(/\s+/g, '-').toLowerCase()}` : undefined}
              userId={`editor-${Date.now()}`}
            />
          </div>
        </TabsContent>

        {/* Content Tab */}
        <TabsContent value="content" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium">Document Sections</h3>
            <Button onClick={addSection} size="sm">
              <PlusCircle className="h-4 w-4 mr-2" />
              Add Section
            </Button>
          </div>

          <div className="space-y-4">
            {sections.map(section => (
              <div key={section.id} className="border rounded-md p-4">
                <div className="flex justify-between items-center mb-2">
                  <div className="grid grid-cols-3 gap-2 w-full">
                    <Input
                      value={section.title}
                      onChange={e => updateSection(section.id, 'title', e.target.value)}
                      placeholder="Section title"
                    />

                    <Select
                      value={section.type}
                      onValueChange={value => updateSection(section.id, 'type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Section type" />
                      </SelectTrigger>
                      <SelectContent>
                        {sectionTypes.map(type => (
                          <SelectItem key={type.id} value={type.id}>
                            <div className="flex items-center space-x-2">
                              {type.icon}
                              <span>{type.name}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => removeSection(section.id)}
                    >
                      <MinusCircle className="h-4 w-4 mr-2" />
                      Remove
                    </Button>
                  </div>
                </div>

                {section.type === 'text' && (
                  <Textarea
                    value={section.content as string}
                    onChange={e => updateSection(section.id, 'content', e.target.value)}
                    placeholder="Enter text content"
                    className="w-full h-32"
                  />
                )}

                {section.type === 'chart' && (
                  <div className="border border-dashed rounded-md p-4 text-center">
                    <p>Chart Configuration (Visual editor in future version)</p>
                    <Textarea
                      value={typeof section.content === 'string' ? section.content : JSON.stringify(section.content, null, 2)}
                      onChange={e => {
                        try {
                          updateSection(section.id, 'content', JSON.parse(e.target.value));
                        } catch {
                          updateSection(section.id, 'content', e.target.value);
                        }
                      }}
                      placeholder="Enter chart configuration as JSON"
                      className="w-full h-32 mt-2"
                    />
                  </div>
                )}

                {section.type === 'table' && (
                  <div className="border border-dashed rounded-md p-4 text-center">
                    <p>Table Configuration (Visual editor in future version)</p>
                    <Textarea
                      value={typeof section.content === 'string' ? section.content : JSON.stringify(section.content, null, 2)}
                      onChange={e => {
                        try {
                          updateSection(section.id, 'content', JSON.parse(e.target.value));
                        } catch {
                          updateSection(section.id, 'content', e.target.value);
                        }
                      }}
                      placeholder="Enter table data as JSON"
                      className="w-full h-32 mt-2"
                    />
                  </div>
                )}

                {section.type === 'image' && (
                  <div className="border border-dashed rounded-md p-4 text-center">
                    <p>Image Placeholder (Upload functionality in future version)</p>
                    <Input
                      type="text"
                      value={section.content as string}
                      onChange={e => updateSection(section.id, 'content', e.target.value)}
                      placeholder="Enter image URL"
                      className="mt-2"
                    />
                  </div>
                )}

                {section.type === 'interactive' && (
                  <div className="border border-dashed rounded-md p-4 text-center">
                    <p>Interactive Element Configuration</p>
                    <Select
                      value={typeof section.content === 'object' && section.content ?
                        (section.content as any).type || '' : ''}
                      onValueChange={value => {
                        updateSection(section.id, 'content', { type: value });
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select element type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="form">Form</SelectItem>
                        <SelectItem value="calculator">Calculator</SelectItem>
                        <SelectItem value="navigation">Navigation</SelectItem>
                        <SelectItem value="survey">Survey</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>
            ))}
          </div>
        </TabsContent>

        {/* Preview Tab */}
        <TabsContent value="preview" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium">Document Preview</h3>
            <Button
              onClick={generatePreview}
              disabled={isGenerating}
            >
              {isGenerating ? 'Generating...' : 'Generate Preview'}
            </Button>
          </div>

          {generatedPreview ? (
            <div className="border rounded-md p-4">
              {/* In a real implementation, this would display an actual preview */}
              <div className="text-center p-8 bg-gray-100 rounded">
                <p className="text-lg font-medium">{documentTitle || 'Untitled Document'}</p>
                <p className="text-sm text-gray-500">{documentType}</p>
                <div className="my-4">
                  {/* Placeholder for preview image */}
                  <div className="h-64 bg-white border rounded flex items-center justify-center">
                    <p>Document Preview</p>
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  Preview generated at {new Date().toLocaleTimeString()}
                </p>
              </div>
            </div>
          ) : (
            <div className="border border-dashed rounded-md p-8 text-center">
              <p>Click 'Generate Preview' to see a preview of your document</p>
            </div>
          )}
        </TabsContent>
        
        {/* Certificate Tab */}
        <TabsContent value="certificate" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium">Document Verification</h3>
          </div>
          
          {certificateData ? (
            <div className="border rounded-md p-4">
              <div className="p-6 bg-gray-50 rounded">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-xl font-bold mb-2">Blockchain Certificate</h4>
                    <p className="text-sm text-gray-600 mb-1">Document: <span className="font-medium">{documentTitle}</span></p>
                    {certificateData.data?.verification_info?.certificate_id && (
                      <p className="text-sm text-gray-600 mb-1">Certificate ID: <span className="font-mono">{certificateData.data.verification_info.certificate_id}</span></p>
                    )}
                    {certificateData.data?.verification_info?.document_hash && (
                      <p className="text-sm text-gray-600 mb-1">Content Hash: <span className="font-mono">{certificateData.data.verification_info.document_hash.substring(0, 16)}...</span></p>
                    )}
                    {certificateData.data?.verification_info?.timestamp && (
                      <p className="text-sm text-gray-600 mb-1">Issued: <span className="font-medium">{new Date(certificateData.data.verification_info.timestamp).toLocaleString()}</span></p>
                    )}
                    
                    <div className="mt-4">
                      <p className="text-sm text-gray-800 font-medium">Blockchain Verification:</p>
                      {certificateData.data?.verification_info?.blockchain_transaction?.transaction_id ? (
                        <div className="mt-2">
                          <p className="text-sm text-gray-600">Transaction ID:</p>
                          <p className="text-xs font-mono bg-gray-100 p-2 rounded">{certificateData.data.verification_info.blockchain_transaction.transaction_id}</p>
                          <p className="text-sm text-gray-600 mt-2">Block Number:</p>
                          <p className="text-xs font-mono bg-gray-100 p-2 rounded">{certificateData.data.verification_info.blockchain_transaction.block_number}</p>
                          <p className="text-sm text-gray-600 mt-2">Network:</p>
                          <p className="text-xs font-mono bg-gray-100 p-2 rounded">{certificateData.data.verification_info.blockchain_transaction.network}</p>
                        </div>
                      ) : (
                        <p className="text-sm text-yellow-600">Verification in progress...</p>
                      )}
                    </div>
                  </div>
                  
                  {verificationBadge && (
                    <div className="ml-4 p-4 bg-white border rounded-md">
                      <p className="text-sm text-center mb-2">Verification QR Code</p>
                      <img 
                        src={verificationBadge} 
                        alt="Verification QR Code" 
                        className="w-40 h-40"
                      />
                      <p className="text-xs text-center mt-2 text-gray-500">Scan to verify authenticity</p>
                    </div>
                  )}
                </div>
                
                {certificateData.data?.verification_info?.verification_url && (
                  <div className="mt-6 flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Verification URL:</p>
                      <p className="text-xs font-mono bg-gray-100 p-2 rounded mt-1">
                        {certificateData.data.verification_info.verification_url}
                      </p>
                    </div>
                    <Button
                      onClick={() => window.open(certificateData.data.verification_info.verification_url, '_blank')}
                      variant="outline"
                      size="sm"
                    >
                      Verify Externally
                    </Button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="border border-dashed rounded-md p-8 text-center">
              <p>No verification certificate available. Save document with blockchain verification enabled.</p>
            </div>
          )}
        </TabsContent>
      </Tabs>

      <div className="flex justify-end space-x-4">
        <Button variant="outline">Cancel</Button>
        <Button onClick={handleSave}>Save Document</Button>
      </div>
    </div>
  );
}
