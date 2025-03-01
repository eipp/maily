import React, { useState } from 'react';
import { Button, Card, Input, Select, Spinner } from '../../ui';
import { useContactDiscovery } from '../../hooks/useContactDiscovery';

export const ContactDiscoveryForm: React.FC = () => {
  const [formState, setFormState] = useState({
    industry: '',
    role: '',
    company_size: '',
    location: '',
    keywords: '',
    discovery_depth: 'standard',
    enrichment_level: 'standard'
  });

  const {
    discoverContacts,
    isLoading,
    error
  } = useContactDiscovery();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormState(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Create target criteria from form state
    const targetCriteria = {
      industry: formState.industry,
      role: formState.role,
      company_size: formState.company_size,
      location: formState.location,
      keywords: formState.keywords ? formState.keywords.split(',').map(k => k.trim()) : []
    };

    // Remove empty values
    Object.keys(targetCriteria).forEach(key => {
      if (!targetCriteria[key] ||
          (Array.isArray(targetCriteria[key]) && targetCriteria[key].length === 0)) {
        delete targetCriteria[key];
      }
    });

    await discoverContacts({
      target_criteria: targetCriteria,
      discovery_depth: formState.discovery_depth,
      enrichment_level: formState.enrichment_level
    });
  };

  return (
    <Card className="p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Discover New Contacts</h2>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block mb-1 text-sm font-medium">Industry</label>
            <Input
              name="industry"
              value={formState.industry}
              onChange={handleChange}
              placeholder="e.g., SaaS, Fintech, Healthcare"
            />
          </div>

          <div>
            <label className="block mb-1 text-sm font-medium">Role</label>
            <Input
              name="role"
              value={formState.role}
              onChange={handleChange}
              placeholder="e.g., CTO, Marketing Director"
            />
          </div>

          <div>
            <label className="block mb-1 text-sm font-medium">Company Size</label>
            <Select
              name="company_size"
              value={formState.company_size}
              onChange={handleChange}
            >
              <option value="">Any size</option>
              <option value="1-10">1-10 employees</option>
              <option value="11-50">11-50 employees</option>
              <option value="51-200">51-200 employees</option>
              <option value="201-500">201-500 employees</option>
              <option value="501-1000">501-1000 employees</option>
              <option value="1001+">1001+ employees</option>
            </Select>
          </div>

          <div>
            <label className="block mb-1 text-sm font-medium">Location</label>
            <Input
              name="location"
              value={formState.location}
              onChange={handleChange}
              placeholder="e.g., San Francisco, New York"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block mb-1 text-sm font-medium">Keywords (comma separated)</label>
            <Input
              name="keywords"
              value={formState.keywords}
              onChange={handleChange}
              placeholder="e.g., machine learning, blockchain, remote work"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block mb-1 text-sm font-medium">Discovery Depth</label>
            <Select
              name="discovery_depth"
              value={formState.discovery_depth}
              onChange={handleChange}
            >
              <option value="basic">Basic - Faster but less thorough</option>
              <option value="standard">Standard - Balanced approach</option>
              <option value="deep">Deep - Most thorough but slower</option>
            </Select>
          </div>

          <div>
            <label className="block mb-1 text-sm font-medium">Enrichment Level</label>
            <Select
              name="enrichment_level"
              value={formState.enrichment_level}
              onChange={handleChange}
            >
              <option value="minimal">Minimal - Basic information only</option>
              <option value="standard">Standard - Balanced approach</option>
              <option value="comprehensive">Comprehensive - Maximum detail</option>
            </Select>
          </div>
        </div>

        <Button
          type="submit"
          className="w-full"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Spinner className="h-4 w-4 mr-2" />
              Discovering Contacts...
            </>
          ) : (
            'Discover Contacts'
          )}
        </Button>
      </form>
    </Card>
  );
};
