/**
 * Document Management API Service
 * Aureon by Rhematek Solutions
 */

import apiClient, { uploadFile, downloadFile, buildQueryParams } from './api';
import type {
  Document,
  DocumentCategory,
  PaginatedResponse,
  PaginationConfig,
  FilterConfig,
  SortConfig,
} from '@/types';

export const documentService = {
  /**
   * Get documents with pagination, filtering, and sorting
   */
  getDocuments: async (
    pagination?: PaginationConfig,
    filters?: FilterConfig,
    sort?: SortConfig
  ): Promise<PaginatedResponse<Document>> => {
    const params = {
      page: pagination?.page,
      page_size: pagination?.pageSize,
      ordering: sort ? `${sort.direction === 'desc' ? '-' : ''}${sort.field}` : undefined,
      category: filters?.category,
      client: filters?.client,
      contract: filters?.contract,
      invoice: filters?.invoice,
      ...filters,
    };

    const queryString = buildQueryParams(params);
    const response = await apiClient.get(`/documents/${queryString}`);
    return response.data;
  },

  /**
   * Get single document by ID
   */
  getDocument: async (id: string): Promise<Document> => {
    const response = await apiClient.get(`/documents/${id}/`);
    return response.data;
  },

  /**
   * Upload document
   */
  uploadDocument: async (
    file: File,
    metadata: {
      name?: string;
      category: DocumentCategory;
      description?: string;
      client_id?: string;
      contract_id?: string;
      invoice_id?: string;
      tags?: string[];
      is_public?: boolean;
    },
    onProgress?: (progress: number) => void
  ): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata.name) formData.append('name', metadata.name);
    formData.append('category', metadata.category);
    if (metadata.description) formData.append('description', metadata.description);
    if (metadata.client_id) formData.append('client_id', metadata.client_id);
    if (metadata.contract_id) formData.append('contract_id', metadata.contract_id);
    if (metadata.invoice_id) formData.append('invoice_id', metadata.invoice_id);
    if (metadata.tags) formData.append('tags', JSON.stringify(metadata.tags));
    if (metadata.is_public !== undefined) {
      formData.append('is_public', metadata.is_public.toString());
    }

    return uploadFile('/documents/', formData, onProgress);
  },

  /**
   * Update document metadata
   */
  updateDocument: async (id: string, data: Partial<Document>): Promise<Document> => {
    const response = await apiClient.patch(`/documents/${id}/`, data);
    return response.data;
  },

  /**
   * Delete document
   */
  deleteDocument: async (id: string): Promise<void> => {
    await apiClient.delete(`/documents/${id}/`);
  },

  /**
   * Download document
   */
  downloadDocument: async (id: string): Promise<void> => {
    await downloadFile(`/documents/${id}/download/`);
  },

  /**
   * Get document download URL
   */
  getDownloadURL: async (id: string): Promise<{ url: string; expires_at: string }> => {
    const response = await apiClient.get(`/documents/${id}/download-url/`);
    return response.data;
  },

  /**
   * Get document preview URL
   */
  getPreviewURL: async (id: string): Promise<{ url: string }> => {
    const response = await apiClient.get(`/documents/${id}/preview-url/`);
    return response.data;
  },

  /**
   * Search documents
   */
  searchDocuments: async (query: string, filters?: FilterConfig): Promise<Document[]> => {
    const params = {
      q: query,
      ...filters,
    };
    const queryString = buildQueryParams(params);
    const response = await apiClient.get(`/documents/search/${queryString}`);
    return response.data;
  },

  /**
   * Get document categories
   */
  getCategories: async (): Promise<DocumentCategory[]> => {
    const response = await apiClient.get('/documents/categories/');
    return response.data;
  },

  /**
   * Share document
   */
  shareDocument: async (
    id: string,
    data: {
      recipient_emails: string[];
      message?: string;
      expires_at?: string;
      allow_download?: boolean;
    }
  ): Promise<{
    share_links: Array<{ email: string; link: string }>;
  }> => {
    const response = await apiClient.post(`/documents/${id}/share/`, data);
    return response.data;
  },

  /**
   * Generate public share link
   */
  generateShareLink: async (
    id: string,
    options?: {
      expires_in_days?: number;
      password_protected?: boolean;
      allow_download?: boolean;
    }
  ): Promise<{
    share_url: string;
    expires_at: string;
    password?: string;
  }> => {
    const response = await apiClient.post(`/documents/${id}/generate-link/`, options || {});
    return response.data;
  },

  /**
   * Revoke share link
   */
  revokeShareLink: async (id: string, linkId: string): Promise<void> => {
    await apiClient.post(`/documents/${id}/revoke-link/${linkId}/`);
  },

  /**
   * Add document version
   */
  addVersion: async (
    id: string,
    file: File,
    versionNote?: string,
    onProgress?: (progress: number) => void
  ): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    if (versionNote) formData.append('version_note', versionNote);

    return uploadFile(`/documents/${id}/versions/`, formData, onProgress);
  },

  /**
   * Get document versions
   */
  getVersions: async (id: string): Promise<
    Array<{
      id: string;
      version_number: number;
      file_url: string;
      file_size: number;
      uploaded_by: string;
      uploaded_at: string;
      version_note?: string;
    }>
  > => {
    const response = await apiClient.get(`/documents/${id}/versions/`);
    return response.data;
  },

  /**
   * Restore document version
   */
  restoreVersion: async (id: string, versionId: string): Promise<Document> => {
    const response = await apiClient.post(`/documents/${id}/restore-version/${versionId}/`);
    return response.data;
  },

  /**
   * Add tags to document
   */
  addTags: async (id: string, tags: string[]): Promise<Document> => {
    const response = await apiClient.post(`/documents/${id}/tags/`, { tags });
    return response.data;
  },

  /**
   * Remove tags from document
   */
  removeTags: async (id: string, tags: string[]): Promise<Document> => {
    const response = await apiClient.delete(`/documents/${id}/tags/`, {
      data: { tags },
    });
    return response.data;
  },

  /**
   * Get all tags
   */
  getAllTags: async (): Promise<string[]> => {
    const response = await apiClient.get('/documents/tags/');
    return response.data;
  },

  /**
   * Move document to folder
   */
  moveToFolder: async (id: string, folderId: string): Promise<Document> => {
    const response = await apiClient.post(`/documents/${id}/move/`, {
      folder_id: folderId,
    });
    return response.data;
  },

  /**
   * Get document permissions
   */
  getPermissions: async (id: string): Promise<
    Array<{
      user_id: string;
      user_name: string;
      permission: 'view' | 'edit' | 'admin';
    }>
  > => {
    const response = await apiClient.get(`/documents/${id}/permissions/`);
    return response.data;
  },

  /**
   * Update document permissions
   */
  updatePermissions: async (
    id: string,
    permissions: Array<{
      user_id: string;
      permission: 'view' | 'edit' | 'admin';
    }>
  ): Promise<void> => {
    await apiClient.post(`/documents/${id}/permissions/`, { permissions });
  },

  /**
   * Get storage statistics
   */
  getStorageStats: async (): Promise<{
    total_documents: number;
    total_size_bytes: number;
    total_size_mb: number;
    storage_limit_mb: number;
    storage_used_percentage: number;
    documents_by_category: Record<DocumentCategory, number>;
  }> => {
    const response = await apiClient.get('/documents/storage-stats/');
    return response.data;
  },

  /**
   * Bulk delete documents
   */
  bulkDelete: async (documentIds: string[]): Promise<{ deleted: number }> => {
    const response = await apiClient.post('/documents/bulk-delete/', {
      document_ids: documentIds,
    });
    return response.data;
  },

  /**
   * Archive document
   */
  archiveDocument: async (id: string): Promise<Document> => {
    const response = await apiClient.post(`/documents/${id}/archive/`);
    return response.data;
  },

  /**
   * Unarchive document
   */
  unarchiveDocument: async (id: string): Promise<Document> => {
    const response = await apiClient.post(`/documents/${id}/unarchive/`);
    return response.data;
  },

  /**
   * Get archived documents
   */
  getArchivedDocuments: async (
    pagination?: PaginationConfig
  ): Promise<PaginatedResponse<Document>> => {
    const params = {
      page: pagination?.page,
      page_size: pagination?.pageSize,
    };
    const queryString = buildQueryParams(params);
    const response = await apiClient.get(`/documents/archived/${queryString}`);
    return response.data;
  },

  /**
   * Extract text from document (OCR)
   */
  extractText: async (id: string): Promise<{ text: string }> => {
    const response = await apiClient.post(`/documents/${id}/extract-text/`);
    return response.data;
  },

  /**
   * Generate document thumbnail
   */
  generateThumbnail: async (id: string): Promise<{ thumbnail_url: string }> => {
    const response = await apiClient.post(`/documents/${id}/generate-thumbnail/`);
    return response.data;
  },
};

export default documentService;
