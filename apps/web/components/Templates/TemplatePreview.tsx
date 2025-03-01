import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useRouter } from 'next/router';
import { toast } from 'react-hot-toast';
import { FiChevronLeft, FiEdit, FiCopy, FiTrash2, FiUser, FiCalendar, FiTag } from 'react-icons/fi';
import { EmailEditor } from '../Canvas/EmailEditor';
import { Template } from '../../types/template';
import { formatDate } from '../../utils/dateUtils';

interface TemplatePreviewProps {
  templateId: number;
  onBack?: () => void;
  onEdit?: (id: number) => void;
  onDuplicate?: (id: number) => void;
  onDelete?: (id: number) => void;
}

export const TemplatePreview: React.FC<TemplatePreviewProps> = ({
  templateId,
  onBack,
  onEdit,
  onDuplicate,
  onDelete
}) => {
  const { t } = useTranslation();
  const router = useRouter();

  const [template, setTemplate] = useState<Template | null>(null);
  const [loading, setLoading] = useState(true);
  const [editorContent, setEditorContent] = useState('');

  useEffect(() => {
    if (templateId) {
      fetchTemplate();
    }
  }, [templateId]);

  const fetchTemplate = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/templates/${templateId}`);

      if (!response.ok) {
        throw new Error('Failed to fetch template');
      }

      const data = await response.json();
      setTemplate(data);

      // Set the editor content
      setEditorContent(JSON.stringify(data.content));
    } catch (error) {
      console.error('Error fetching template:', error);
      toast.error(t('templates.fetchError'));
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    if (onEdit) {
      onEdit(templateId);
    } else {
      router.push(`/templates/${templateId}?mode=edit`);
    }
  };

  const handleDuplicate = async () => {
    try {
      const response = await fetch(`/api/templates/${templateId}/duplicate`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to duplicate template');
      }

      const duplicatedTemplate = await response.json();
      toast.success(t('templates.duplicateSuccess'));

      if (onDuplicate) {
        onDuplicate(duplicatedTemplate.id);
      } else {
        router.push(`/templates/${duplicatedTemplate.id}`);
      }
    } catch (error) {
      console.error('Error duplicating template:', error);
      toast.error(t('templates.duplicateError'));
    }
  };

  const handleDelete = async () => {
    if (confirm(t('templates.deleteConfirm'))) {
      try {
        const response = await fetch(`/api/templates/${templateId}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          throw new Error('Failed to delete template');
        }

        toast.success(t('templates.deleteSuccess'));

        if (onDelete) {
          onDelete(templateId);
        } else {
          router.push('/templates');
        }
      } catch (error) {
        console.error('Error deleting template:', error);
        toast.error(t('templates.deleteError'));
      }
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center my-12">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">{t('templates.notFound')}</p>
        <button
          onClick={onBack || (() => router.push('/templates'))}
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          {t('common.back')}
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6">
      {/* Header with back button and actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 space-y-4 sm:space-y-0">
        <button
          onClick={onBack || (() => router.push('/templates'))}
          className="flex items-center text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
        >
          <FiChevronLeft className="mr-2" />
          {t('common.back')}
        </button>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleEdit}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600"
          >
            <FiEdit className="mr-2" />
            {t('templates.editTemplate')}
          </button>

          <button
            onClick={handleDuplicate}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600"
          >
            <FiCopy className="mr-2" />
            {t('templates.duplicateTemplate')}
          </button>

          <button
            onClick={handleDelete}
            className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:bg-gray-700 dark:text-red-400 dark:border-red-800 dark:hover:bg-red-900"
          >
            <FiTrash2 className="mr-2" />
            {t('templates.deleteTemplate')}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Template Preview */}
        <div className="lg:col-span-2">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              {template.name}
            </h2>

            {template.description && (
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                {template.description}
              </p>
            )}

            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <EmailEditor
                initialContent={editorContent}
                readOnly={true}
              />
            </div>
          </div>
        </div>

        {/* Template Details */}
        <div className="lg:col-span-1">
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              {t('templates.details')}
            </h3>

            <div className="space-y-4">
              {/* Creator */}
              <div className="flex items-start">
                <FiUser className="mt-1 mr-2 text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    {t('templates.by')}
                  </p>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {template.user?.name || 'Unknown'}
                  </p>
                </div>
              </div>

              {/* Dates */}
              <div className="flex items-start">
                <FiCalendar className="mt-1 mr-2 text-gray-400" />
                <div>
                  <div className="mb-2">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      {t('templates.createdAt')}
                    </p>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {formatDate(new Date(template.createdAt))}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      {t('templates.updatedAt')}
                    </p>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {formatDate(new Date(template.updatedAt))}
                    </p>
                  </div>
                </div>
              </div>

              {/* Category */}
              {template.category && (
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    {t('templates.category')}
                  </p>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-sm font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                    {template.category}
                  </span>
                </div>
              )}

              {/* Tags */}
              {template.tags && template.tags.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1 flex items-center">
                    <FiTag className="mr-1" />
                    {t('templates.tags')}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {template.tags.map(tag => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Public/Private status */}
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  {t('common.status')}
                </p>
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-sm font-medium ${
                    template.is_public
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                  }`}
                >
                  {template.is_public ? t('templates.public') : t('templates.private')}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
