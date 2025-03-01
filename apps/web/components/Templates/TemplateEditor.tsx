import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useRouter } from 'next/router';
import { toast } from 'react-hot-toast';
import { FiSave, FiChevronLeft, FiTag, FiGlobe, FiFolder } from 'react-icons/fi';
import { EmailEditor } from '../Canvas/EmailEditor';

interface TemplateEditorProps {
  templateId?: number;
  isNew?: boolean;
  onBack?: () => void;
}

interface TemplateData {
  name: string;
  description: string;
  content: any;
  thumbnail?: string;
  category?: string;
  tags?: string[];
  is_public: boolean;
}

export const TemplateEditor: React.FC<TemplateEditorProps> = ({
  templateId,
  isNew = false,
  onBack
}) => {
  const { t } = useTranslation();
  const router = useRouter();

  const [templateData, setTemplateData] = useState<TemplateData>({
    name: '',
    description: '',
    content: {},
    is_public: false
  });

  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [editorContent, setEditorContent] = useState('');
  const [thumbnailPreview, setThumbnailPreview] = useState<string | null>(null);

  // Available categories (could be fetched from API)
  const categories = [
    'Newsletter',
    'Promotional',
    'Announcement',
    'Transactional',
    'Welcome',
    'Holiday',
    'Event',
    'Other'
  ];

  useEffect(() => {
    if (!isNew && templateId) {
      fetchTemplate();
    }
  }, [templateId, isNew]);

  const fetchTemplate = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/templates/${templateId}`);

      if (!response.ok) {
        throw new Error('Failed to fetch template');
      }

      const data = await response.json();
      setTemplateData({
        name: data.name,
        description: data.description || '',
        content: data.content,
        thumbnail: data.thumbnail,
        category: data.category || '',
        tags: data.tags || [],
        is_public: data.is_public
      });

      // Set the editor content
      setEditorContent(JSON.stringify(data.content));

      // Set thumbnail preview if available
      if (data.thumbnail) {
        setThumbnailPreview(data.thumbnail);
      }
    } catch (error) {
      console.error('Error fetching template:', error);
      toast.error(t('templates.fetchError'));
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setTemplateData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setTemplateData(prev => ({
      ...prev,
      [name]: checked
    }));
  };

  const handleTagChange = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && e.currentTarget.value) {
      e.preventDefault();
      const newTag = e.currentTarget.value.trim();
      if (newTag && !templateData.tags?.includes(newTag)) {
        setTemplateData(prev => ({
          ...prev,
          tags: [...(prev.tags || []), newTag]
        }));
        e.currentTarget.value = '';
      }
    }
  };

  const removeTag = (tagToRemove: string) => {
    setTemplateData(prev => ({
      ...prev,
      tags: prev.tags?.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleThumbnailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();

      reader.onload = (event) => {
        const dataUrl = event.target?.result as string;
        setThumbnailPreview(dataUrl);
        setTemplateData(prev => ({
          ...prev,
          thumbnail: dataUrl
        }));
      };

      reader.readAsDataURL(file);
    }
  };

  const handleEditorChange = (content: string) => {
    setEditorContent(content);
  };

  const handleSave = async () => {
    // Validate form
    if (!templateData.name.trim()) {
      toast.error(t('templates.nameRequired'));
      return;
    }

    if (!editorContent) {
      toast.error(t('templates.contentRequired'));
      return;
    }

    try {
      setSaving(true);

      // Parse the editor content
      const contentObj = JSON.parse(editorContent);

      const payload = {
        ...templateData,
        content: contentObj
      };

      const url = isNew
        ? '/api/templates'
        : `/api/templates/${templateId}`;

      const method = isNew ? 'POST' : 'PUT';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error('Failed to save template');
      }

      const savedTemplate = await response.json();

      toast.success(
        isNew
          ? t('templates.createSuccess')
          : t('templates.updateSuccess')
      );

      // Redirect to the template list or detail page
      if (isNew) {
        router.push(`/templates/${savedTemplate.id}`);
      } else if (onBack) {
        onBack();
      }
    } catch (error) {
      console.error('Error saving template:', error);
      toast.error(
        isNew
          ? t('templates.createError')
          : t('templates.updateError')
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center my-12">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6">
      {/* Header with back button */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={onBack || (() => router.push('/templates'))}
          className="flex items-center text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
        >
          <FiChevronLeft className="mr-2" />
          {t('common.back')}
        </button>

        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? (
            <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></span>
          ) : (
            <FiSave className="mr-2" />
          )}
          {t('common.save')}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Template Editor */}
        <div className="lg:col-span-2">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
              {isNew ? t('templates.createNew') : t('templates.editTemplate')}
            </h2>

            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <EmailEditor
                initialContent={editorContent}
                onChange={handleEditorChange}
                readOnly={false}
              />
            </div>
          </div>
        </div>

        {/* Template Details Form */}
        <div className="lg:col-span-1">
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              {t('templates.details')}
            </h3>

            <div className="space-y-4">
              {/* Template Name */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('templates.name')} *
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={templateData.name}
                  onChange={handleInputChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                  required
                />
              </div>

              {/* Template Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('templates.description')}
                </label>
                <textarea
                  id="description"
                  name="description"
                  value={templateData.description}
                  onChange={handleInputChange}
                  rows={3}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                />
              </div>

              {/* Category */}
              <div>
                <label htmlFor="category" className="flex items-center text-sm font-medium text-gray-700 dark:text-gray-300">
                  <FiFolder className="mr-2" />
                  {t('templates.category')}
                </label>
                <select
                  id="category"
                  name="category"
                  value={templateData.category || ''}
                  onChange={handleInputChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                >
                  <option value="">{t('templates.selectCategory')}</option>
                  {categories.map(category => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>

              {/* Tags */}
              <div>
                <label htmlFor="tags" className="flex items-center text-sm font-medium text-gray-700 dark:text-gray-300">
                  <FiTag className="mr-2" />
                  {t('templates.tags')}
                </label>
                <div className="mt-1">
                  <input
                    type="text"
                    id="tags"
                    placeholder={t('templates.addTag')}
                    onKeyDown={handleTagChange}
                    className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                  />
                </div>

                {/* Tag list */}
                <div className="flex flex-wrap gap-2 mt-2">
                  {templateData.tags?.map(tag => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
                        className="ml-1.5 inline-flex items-center justify-center w-4 h-4 rounded-full text-blue-400 hover:text-blue-600 dark:text-blue-300 dark:hover:text-blue-100"
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Thumbnail */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('templates.thumbnail')}
                </label>

                <div className="mt-1 flex items-center">
                  {thumbnailPreview ? (
                    <div className="relative w-full h-32 border-2 border-gray-300 border-dashed rounded-md overflow-hidden">
                      <img
                        src={thumbnailPreview}
                        alt="Template thumbnail"
                        className="w-full h-full object-cover"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          setThumbnailPreview(null);
                          setTemplateData(prev => ({ ...prev, thumbnail: undefined }));
                        }}
                        className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
                      >
                        &times;
                      </button>
                    </div>
                  ) : (
                    <div className="w-full">
                      <label
                        htmlFor="thumbnail-upload"
                        className="w-full flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md cursor-pointer hover:border-gray-400 dark:border-gray-600 dark:hover:border-gray-500"
                      >
                        <div className="space-y-1 text-center">
                          <svg
                            className="mx-auto h-12 w-12 text-gray-400"
                            stroke="currentColor"
                            fill="none"
                            viewBox="0 0 48 48"
                          >
                            <path
                              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4h-12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                              strokeWidth={2}
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          </svg>
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            {t('templates.uploadThumbnail')}
                          </div>
                        </div>
                      </label>
                      <input
                        id="thumbnail-upload"
                        type="file"
                        accept="image/*"
                        onChange={handleThumbnailChange}
                        className="sr-only"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Public/Private setting */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_public"
                  name="is_public"
                  checked={templateData.is_public}
                  onChange={handleCheckboxChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="is_public" className="ml-2 flex items-center text-sm text-gray-700 dark:text-gray-300">
                  <FiGlobe className="mr-2" />
                  {t('templates.makePublic')}
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
