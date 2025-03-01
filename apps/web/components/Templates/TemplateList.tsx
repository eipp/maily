import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useRouter } from 'next/router';
import { toast } from 'react-hot-toast';
import { FiPlus, FiSearch, FiFilter, FiEdit2, FiCopy, FiTrash2, FiEye } from 'react-icons/fi';

interface Template {
  id: number;
  name: string;
  description: string;
  thumbnail: string;
  category: string;
  tags: string[];
  is_public: boolean;
  is_featured: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

interface TemplateListProps {
  onSelect?: (template: Template) => void;
  showActions?: boolean;
  filterByCategory?: string;
  limit?: number;
}

export const TemplateList: React.FC<TemplateListProps> = ({
  onSelect,
  showActions = true,
  filterByCategory,
  limit
}) => {
  const { t } = useTranslation();
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState(filterByCategory || '');
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    fetchTemplates();
  }, [page, category, searchQuery, filterByCategory]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);

      let url = `/api/templates?page=${page}&size=${limit || 20}`;

      if (searchQuery) {
        url += `&search=${encodeURIComponent(searchQuery)}`;
      }

      if (category || filterByCategory) {
        url += `&category=${encodeURIComponent(category || filterByCategory || '')}`;
      }

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Failed to fetch templates');
      }

      const data = await response.json();
      setTemplates(data.items);
      setTotalCount(data.total);

      // Extract unique categories for the filter
      const uniqueCategories = Array.from(
        new Set(data.items.map((template: Template) => template.category).filter(Boolean))
      );
      setCategories(uniqueCategories as string[]);
    } catch (error) {
      console.error('Error fetching templates:', error);
      toast.error(t('templates.fetchError'));
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (templateId: number) => {
    router.push(`/templates/edit/${templateId}`);
  };

  const handleViewTemplate = (templateId: number) => {
    router.push(`/templates/${templateId}`);
  };

  const handleDuplicate = async (templateId: number) => {
    try {
      const response = await fetch(`/api/templates/${templateId}/duplicate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to duplicate template');
      }

      const duplicatedTemplate = await response.json();
      toast.success(t('templates.duplicateSuccess'));

      // Refresh the template list
      fetchTemplates();

      return duplicatedTemplate;
    } catch (error) {
      console.error('Error duplicating template:', error);
      toast.error(t('templates.duplicateError'));
      return null;
    }
  };

  const handleDelete = async (templateId: number) => {
    if (window.confirm(t('templates.confirmDelete'))) {
      try {
        const response = await fetch(`/api/templates/${templateId}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          throw new Error('Failed to delete template');
        }

        toast.success(t('templates.deleteSuccess'));

        // Refresh the template list
        fetchTemplates();
      } catch (error) {
        console.error('Error deleting template:', error);
        toast.error(t('templates.deleteError'));
      }
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setPage(1); // Reset to first page on search
  };

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setCategory(e.target.value);
    setPage(1); // Reset to first page on category change
  };

  const totalPages = Math.ceil(totalCount / (limit || 20));

  return (
    <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6">
      {/* Search and filter */}
      <div className="flex flex-col sm:flex-row justify-between mb-6">
        <div className="relative flex-1 mb-4 sm:mb-0 sm:mr-4">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <FiSearch className="text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder={t('templates.searchPlaceholder')}
            value={searchQuery}
            onChange={handleSearchChange}
          />
        </div>
        <div className="relative flex-1 sm:max-w-xs">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <FiFilter className="text-gray-400" />
          </div>
          <select
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            value={category}
            onChange={handleCategoryChange}
            disabled={!!filterByCategory}
          >
            <option value="">{t('templates.allCategories')}</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Create new template button */}
      {showActions && (
        <div className="mb-6">
          <button
            onClick={() => router.push('/templates/create')}
            className="flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <FiPlus className="mr-2" />
            {t('templates.createNew')}
          </button>
        </div>
      )}

      {/* Template grid */}
      {loading ? (
        <div className="flex justify-center my-12">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : templates.length > 0 ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <div
                key={template.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden hover:shadow-lg transition-shadow duration-200"
              >
                {/* Template thumbnail */}
                <div
                  className="h-40 bg-gray-100 dark:bg-gray-900 relative cursor-pointer"
                  onClick={() => onSelect ? onSelect(template) : handleViewTemplate(template.id)}
                >
                  {template.thumbnail ? (
                    <img
                      src={template.thumbnail}
                      alt={template.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      {t('templates.noThumbnail')}
                    </div>
                  )}
                  {template.is_featured && (
                    <div className="absolute top-2 right-2 bg-yellow-500 text-white text-xs px-2 py-1 rounded">
                      {t('templates.featured')}
                    </div>
                  )}
                </div>

                {/* Template info */}
                <div className="p-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {template.name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 line-clamp-2">
                    {template.description || t('templates.noDescription')}
                  </p>
                  <div className="flex items-center mt-3 text-xs text-gray-500 dark:text-gray-400">
                    <span>
                      {new Date(template.updated_at).toLocaleDateString()}
                    </span>
                    <span className="mx-2">•</span>
                    <span>v{template.version}</span>
                    {template.category && (
                      <>
                        <span className="mx-2">•</span>
                        <span>{template.category}</span>
                      </>
                    )}
                  </div>

                  {/* Action buttons */}
                  {showActions && (
                    <div className="flex mt-4 space-x-2">
                      <button
                        onClick={() => handleViewTemplate(template.id)}
                        className="p-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
                        title={t('templates.view')}
                      >
                        <FiEye size={18} />
                      </button>
                      <button
                        onClick={() => handleEdit(template.id)}
                        className="p-2 text-gray-600 dark:text-gray-300 hover:text-green-600 dark:hover:text-green-400"
                        title={t('templates.edit')}
                      >
                        <FiEdit2 size={18} />
                      </button>
                      <button
                        onClick={() => handleDuplicate(template.id)}
                        className="p-2 text-gray-600 dark:text-gray-300 hover:text-purple-600 dark:hover:text-purple-400"
                        title={t('templates.duplicate')}
                      >
                        <FiCopy size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(template.id)}
                        className="p-2 text-gray-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400"
                        title={t('templates.delete')}
                      >
                        <FiTrash2 size={18} />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center mt-8">
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white dark:bg-gray-800 dark:border-gray-600 text-sm font-medium ${
                    page === 1
                      ? 'text-gray-300 dark:text-gray-600'
                      : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  {t('common.previous')}
                </button>
                <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white dark:bg-gray-800 dark:border-gray-600 text-sm font-medium text-gray-700 dark:text-gray-300">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white dark:bg-gray-800 dark:border-gray-600 text-sm font-medium ${
                    page === totalPages
                      ? 'text-gray-300 dark:text-gray-600'
                      : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  {t('common.next')}
                </button>
              </nav>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            {t('templates.noTemplatesFound')}
          </p>
          {showActions && (
            <button
              onClick={() => router.push('/templates/create')}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <FiPlus className="mr-2" />
              {t('templates.createFirst')}
            </button>
          )}
        </div>
      )}
    </div>
  );
};
