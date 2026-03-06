/**
 * Document Vault Page
 * Aureon by Rhematek Solutions
 *
 * Full-featured document management with folder navigation,
 * grid/list views, drag-and-drop upload, and file preview.
 */

import React, { useState, useRef, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentService } from '@/services/documentService';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Badge from '@/components/common/Badge';
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/common/Modal';
import Select from '@/components/common/Select';
import { useToast } from '@/components/common';

// ============================================
// TYPES
// ============================================

interface FolderItem {
  id: string;
  name: string;
  type: 'folder';
  itemCount: number;
  createdAt: string;
}

interface FileItem {
  id: string;
  title: string;
  name: string;
  type: 'file';
  file_type: string;
  file_size: number;
  category: string;
  created_at: string;
  updated_at: string;
  uploaded_by?: string;
  is_shared?: boolean;
  tags?: string[];
}

interface BreadcrumbItem {
  id: string;
  name: string;
}

// ============================================
// HELPERS
// ============================================

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

const getFileIcon = (fileType: string): { color: string; label: string } => {
  const type = fileType?.toLowerCase() || '';
  if (type.includes('pdf')) return { color: 'text-red-500', label: 'PDF' };
  if (type.includes('doc') || type.includes('word')) return { color: 'text-blue-600', label: 'DOC' };
  if (type.includes('xls') || type.includes('sheet') || type.includes('csv'))
    return { color: 'text-green-600', label: 'XLS' };
  if (type.includes('ppt') || type.includes('presentation'))
    return { color: 'text-orange-500', label: 'PPT' };
  if (type.includes('png') || type.includes('jpg') || type.includes('jpeg') || type.includes('gif') || type.includes('svg') || type.includes('webp') || type.includes('image'))
    return { color: 'text-purple-500', label: 'IMG' };
  if (type.includes('zip') || type.includes('rar') || type.includes('tar') || type.includes('gz'))
    return { color: 'text-yellow-600', label: 'ZIP' };
  if (type.includes('txt') || type.includes('text'))
    return { color: 'text-gray-500', label: 'TXT' };
  return { color: 'text-gray-400', label: 'FILE' };
};

const getCategoryBadgeVariant = (category: string): 'primary' | 'warning' | 'success' | 'default' | 'info' => {
  switch (category) {
    case 'contract': return 'primary';
    case 'invoice': return 'warning';
    case 'receipt': return 'success';
    case 'proposal': return 'info';
    default: return 'default';
  }
};

// ============================================
// FILE ICON COMPONENT
// ============================================

const FileTypeIcon: React.FC<{ fileType: string; size?: 'sm' | 'md' | 'lg' }> = ({ fileType, size = 'md' }) => {
  const { color, label } = getFileIcon(fileType);
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-12 h-12 text-sm',
    lg: 'w-16 h-16 text-base',
  };

  return (
    <div className={`${sizeClasses[size]} rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center`}>
      <span className={`${color} font-bold`}>{label}</span>
    </div>
  );
};

// ============================================
// FOLDER ICON COMPONENT
// ============================================

const FolderIcon: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-14 h-14',
  };

  return (
    <svg className={`${sizeClasses[size]} text-amber-500`} fill="currentColor" viewBox="0 0 24 24">
      <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
    </svg>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================

const DocumentVault: React.FC = () => {
  const queryClient = useQueryClient();
  const { success: showSuccessToast, error: showErrorToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // State
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [page, setPage] = useState(1);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showCreateFolderModal, setShowCreateFolderModal] = useState(false);
  const [showFilePreviewModal, setShowFilePreviewModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [newFolderName, setNewFolderName] = useState('');
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([
    { id: 'root', name: 'Home' },
  ]);
  const [currentFolderId, setCurrentFolderId] = useState<string>('root');

  // Mock folder data (would come from API in production)
  const [folders] = useState<FolderItem[]>([
    { id: 'f1', name: 'Contracts', type: 'folder', itemCount: 12, createdAt: '2025-11-15T10:00:00Z' },
    { id: 'f2', name: 'Invoices', type: 'folder', itemCount: 34, createdAt: '2025-10-20T10:00:00Z' },
    { id: 'f3', name: 'Receipts', type: 'folder', itemCount: 28, createdAt: '2025-09-05T10:00:00Z' },
    { id: 'f4', name: 'Proposals', type: 'folder', itemCount: 8, createdAt: '2025-12-01T10:00:00Z' },
  ]);

  // Fetch documents
  const { data: documentsData, isLoading } = useQuery({
    queryKey: ['documents', page, search, categoryFilter, currentFolderId],
    queryFn: () =>
      documentService.getDocuments(
        { page, pageSize: 20 },
        {
          search: search || undefined,
          category: categoryFilter !== 'all' ? categoryFilter : undefined,
        }
      ),
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      return documentService.uploadDocument(file, {
        name: file.name,
        category: 'other',
      });
    },
    onSuccess: () => {
      showSuccessToast('Document uploaded successfully');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: () => {
      showErrorToast('Failed to upload document');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentService.deleteDocument(id),
    onSuccess: () => {
      showSuccessToast('Document deleted');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setShowFilePreviewModal(false);
      setSelectedFile(null);
    },
    onError: () => showErrorToast('Failed to delete document'),
  });

  // Drag and drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        files.forEach((file) => uploadMutation.mutate(file));
      }
    },
    [uploadMutation]
  );

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      Array.from(files).forEach((file) => uploadMutation.mutate(file));
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Folder navigation
  const handleFolderClick = (folder: FolderItem) => {
    setCurrentFolderId(folder.id);
    setBreadcrumbs((prev) => [...prev, { id: folder.id, name: folder.name }]);
    setPage(1);
  };

  const handleBreadcrumbClick = (index: number) => {
    const crumb = breadcrumbs[index];
    setCurrentFolderId(crumb.id);
    setBreadcrumbs((prev) => prev.slice(0, index + 1));
    setPage(1);
  };

  // File preview
  const handleFileClick = (file: any) => {
    setSelectedFile(file);
    setShowFilePreviewModal(true);
  };

  // Create folder
  const handleCreateFolder = () => {
    if (!newFolderName.trim()) return;
    showSuccessToast(`Folder "${newFolderName}" created`);
    setNewFolderName('');
    setShowCreateFolderModal(false);
  };

  // Download handler
  const handleDownload = (id: string) => {
    documentService.downloadDocument(id);
  };

  const documents = documentsData?.results || [];
  const totalCount = documentsData?.count || 0;
  const isAtRoot = breadcrumbs.length === 1;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">
            Document Vault
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage your contracts, invoices, receipts, and files
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={() => setShowCreateFolderModal(true)}>
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
            </svg>
            New Folder
          </Button>
          <label className="cursor-pointer">
            <Button>
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Upload Files
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={handleFileInputChange}
            />
          </label>
        </div>
      </div>

      {/* Breadcrumb Navigation */}
      <nav className="flex items-center space-x-2 text-sm">
        {breadcrumbs.map((crumb, index) => (
          <React.Fragment key={crumb.id}>
            {index > 0 && (
              <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            )}
            <button
              onClick={() => handleBreadcrumbClick(index)}
              className={`hover:text-primary-600 dark:hover:text-primary-400 transition-colors ${
                index === breadcrumbs.length - 1
                  ? 'text-gray-900 dark:text-white font-medium'
                  : 'text-gray-500 dark:text-gray-400'
              }`}
            >
              {index === 0 ? (
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  {crumb.name}
                </span>
              ) : (
                crumb.name
              )}
            </button>
          </React.Fragment>
        ))}
      </nav>

      {/* Drag and Drop Upload Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-xl transition-all duration-200 ${
          isDragOver
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
        }`}
      >
        <div className="flex flex-col items-center justify-center py-8 px-4">
          <svg
            className={`w-10 h-10 mb-3 transition-colors ${
              isDragOver ? 'text-primary-500' : 'text-gray-400 dark:text-gray-500'
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {isDragOver ? 'Drop files here to upload' : 'Drag and drop files here, or click "Upload Files"'}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Supports PDF, DOC, XLS, IMG, and more (max 50MB per file)
          </p>
          {uploadMutation.isPending && (
            <div className="mt-3 flex items-center gap-2 text-sm text-primary-600 dark:text-primary-400">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Uploading...
            </div>
          )}
        </div>
      </div>

      {/* Filters and View Toggle */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <Input
              placeholder="Search files..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9 w-64"
            />
          </div>
          <Select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(1);
            }}
            options={[
              { value: 'all', label: 'All Types' },
              { value: 'contract', label: 'Contracts' },
              { value: 'invoice', label: 'Invoices' },
              { value: 'receipt', label: 'Receipts' },
              { value: 'other', label: 'Other' },
            ]}
            className="w-40"
          />
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {totalCount} file{totalCount !== 1 ? 's' : ''}
          </span>
        </div>

        <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-md transition-colors ${
              viewMode === 'grid'
                ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
            aria-label="Grid view"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded-md transition-colors ${
              viewMode === 'list'
                ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
            aria-label="List view"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading ? (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500" />
        </div>
      ) : (
        <>
          {/* Folders Section (only at root or first level) */}
          {isAtRoot && categoryFilter === 'all' && !search && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                Folders
              </h2>
              {viewMode === 'grid' ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                  {folders.map((folder) => (
                    <Card
                      key={folder.id}
                      hover
                      className="cursor-pointer group"
                      padding="sm"
                    >
                      <button
                        onClick={() => handleFolderClick(folder)}
                        className="w-full flex flex-col items-center py-4 px-2"
                      >
                        <FolderIcon size="lg" />
                        <p className="mt-2 text-sm font-medium text-gray-900 dark:text-white truncate w-full text-center group-hover:text-primary-600 dark:group-hover:text-primary-400">
                          {folder.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                          {folder.itemCount} items
                        </p>
                      </button>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="space-y-1">
                  {folders.map((folder) => (
                    <button
                      key={folder.id}
                      onClick={() => handleFolderClick(folder)}
                      className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
                    >
                      <FolderIcon size="sm" />
                      <div className="flex-1 text-left">
                        <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">
                          {folder.name}
                        </p>
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {folder.itemCount} items
                      </span>
                      <span className="text-xs text-gray-400 dark:text-gray-500">
                        {new Date(folder.createdAt).toLocaleDateString()}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Files Section */}
          <div>
            <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
              Files
            </h2>

            {documents.length === 0 ? (
              <Card>
                <CardContent>
                  <div className="text-center py-16">
                    <svg className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">
                      No files found
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400 mb-4">
                      {search
                        ? `No results for "${search}". Try a different search term.`
                        : 'Upload your first document to get started.'}
                    </p>
                    <label className="cursor-pointer inline-block">
                      <Button variant="primary">Upload a File</Button>
                      <input type="file" className="hidden" onChange={handleFileInputChange} />
                    </label>
                  </div>
                </CardContent>
              </Card>
            ) : viewMode === 'grid' ? (
              /* Grid View */
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {documents.map((doc: any) => (
                  <Card
                    key={doc.id}
                    hover
                    className="cursor-pointer group"
                    padding="sm"
                  >
                    <button
                      onClick={() => handleFileClick(doc)}
                      className="w-full flex flex-col items-center py-4 px-2"
                    >
                      <div className="relative">
                        <FileTypeIcon fileType={doc.file_type} size="lg" />
                        {doc.is_shared && (
                          <div className="absolute -top-1 -right-1 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                            </svg>
                          </div>
                        )}
                      </div>
                      <p className="mt-2 text-sm font-medium text-gray-900 dark:text-white truncate w-full text-center group-hover:text-primary-600 dark:group-hover:text-primary-400">
                        {doc.title || doc.name}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        {formatFileSize(doc.file_size)}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                        {new Date(doc.updated_at || doc.created_at).toLocaleDateString()}
                      </p>
                    </button>
                  </Card>
                ))}
              </div>
            ) : (
              /* List View */
              <Card padding="none">
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {documents.map((doc: any) => (
                    <button
                      key={doc.id}
                      onClick={() => handleFileClick(doc)}
                      className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors group"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <FileTypeIcon fileType={doc.file_type} size="sm" />
                        <div className="min-w-0 text-left">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate group-hover:text-primary-600 dark:group-hover:text-primary-400">
                            {doc.title || doc.name}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {doc.file_type?.toUpperCase()} &middot; {formatFileSize(doc.file_size)} &middot;{' '}
                            {new Date(doc.updated_at || doc.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                        {doc.is_shared && (
                          <Badge variant="info" size="sm">
                            Shared
                          </Badge>
                        )}
                        <Badge variant={getCategoryBadgeVariant(doc.category)} size="sm">
                          {doc.category}
                        </Badge>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDownload(doc.id);
                          }}
                          className="p-1.5 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                          aria-label="Download"
                        >
                          <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteMutation.mutate(doc.id);
                          }}
                          className="p-1.5 rounded-md hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                          aria-label="Delete"
                        >
                          <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </button>
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* Pagination */}
          {totalCount > 20 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-gray-600 dark:text-gray-400 px-4">
                Page {page} of {Math.ceil(totalCount / 20)}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= Math.ceil(totalCount / 20)}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}

      {/* Create Folder Modal */}
      <Modal
        isOpen={showCreateFolderModal}
        onClose={() => {
          setShowCreateFolderModal(false);
          setNewFolderName('');
        }}
        size="sm"
      >
        <ModalHeader>Create New Folder</ModalHeader>
        <ModalBody>
          <Input
            label="Folder Name"
            placeholder="Enter folder name..."
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            fullWidth
            autoFocus
          />
        </ModalBody>
        <ModalFooter>
          <Button
            variant="ghost"
            onClick={() => {
              setShowCreateFolderModal(false);
              setNewFolderName('');
            }}
          >
            Cancel
          </Button>
          <Button onClick={handleCreateFolder} disabled={!newFolderName.trim()}>
            Create Folder
          </Button>
        </ModalFooter>
      </Modal>

      {/* File Preview Modal */}
      <Modal
        isOpen={showFilePreviewModal}
        onClose={() => {
          setShowFilePreviewModal(false);
          setSelectedFile(null);
        }}
        size="lg"
      >
        {selectedFile && (
          <>
            <ModalHeader>File Details</ModalHeader>
            <ModalBody>
              <div className="flex flex-col sm:flex-row gap-6">
                <div className="flex-shrink-0 flex justify-center">
                  <FileTypeIcon fileType={selectedFile.file_type} size="lg" />
                </div>
                <div className="flex-1 space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {selectedFile.title || selectedFile.name}
                    </h3>
                    <Badge variant={getCategoryBadgeVariant(selectedFile.category)} size="sm" className="mt-1">
                      {selectedFile.category}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Type</p>
                      <p className="text-sm text-gray-900 dark:text-white mt-0.5">
                        {selectedFile.file_type?.toUpperCase() || 'Unknown'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Size</p>
                      <p className="text-sm text-gray-900 dark:text-white mt-0.5">
                        {formatFileSize(selectedFile.file_size)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Uploaded</p>
                      <p className="text-sm text-gray-900 dark:text-white mt-0.5">
                        {new Date(selectedFile.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Uploaded By</p>
                      <p className="text-sm text-gray-900 dark:text-white mt-0.5">
                        {selectedFile.uploaded_by || 'You'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Last Modified</p>
                      <p className="text-sm text-gray-900 dark:text-white mt-0.5">
                        {new Date(selectedFile.updated_at || selectedFile.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Shared</p>
                      <p className="text-sm text-gray-900 dark:text-white mt-0.5">
                        {selectedFile.is_shared ? 'Yes' : 'No'}
                      </p>
                    </div>
                  </div>

                  {selectedFile.tags && selectedFile.tags.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-1">Tags</p>
                      <div className="flex flex-wrap gap-1">
                        {selectedFile.tags.map((tag) => (
                          <Badge key={tag} variant="default" size="sm">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </ModalBody>
            <ModalFooter>
              <Button
                variant="danger"
                size="sm"
                onClick={() => deleteMutation.mutate(selectedFile.id)}
              >
                <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowFilePreviewModal(false);
                  setSelectedFile(null);
                }}
              >
                Close
              </Button>
              <Button onClick={() => handleDownload(selectedFile.id)}>
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download
              </Button>
            </ModalFooter>
          </>
        )}
      </Modal>
    </div>
  );
};

export default DocumentVault;
