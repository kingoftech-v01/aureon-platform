/**
 * Contract Versions Page
 * Aureon by Rhematek Solutions
 *
 * Contract version history with side-by-side diff comparison and revert capability
 */

import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contractService } from '@/services';
import apiClient from '@/services/api';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { SkeletonCard } from '@/components/common/Skeleton';

interface ContractVersion {
  id: string;
  version_number: number;
  content: string;
  change_summary?: string;
  author: {
    id: string;
    name: string;
    email?: string;
  };
  created_at: string;
  is_current: boolean;
}

const ContractVersions: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success: showSuccessToast, error: showErrorToast } = useToast();
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [compareVersionId, setCompareVersionId] = useState<string | null>(null);
  const [showRevertConfirm, setShowRevertConfirm] = useState(false);
  const [viewMode, setViewMode] = useState<'single' | 'diff'>('single');

  // Fetch contract details
  const { data: contract } = useQuery({
    queryKey: ['contract', id],
    queryFn: () => contractService.getContract(id!),
    enabled: !!id,
  });

  // Fetch versions
  const { data: versions, isLoading, error } = useQuery<ContractVersion[]>({
    queryKey: ['contract-versions', id],
    queryFn: async () => {
      const response = await apiClient.get(`/contracts/${id}/versions/`);
      return response.data;
    },
    enabled: !!id,
  });

  // Revert mutation
  const revertMutation = useMutation({
    mutationFn: async (versionId: string) => {
      const response = await apiClient.post(`/contracts/${id}/versions/${versionId}/revert/`);
      return response.data;
    },
    onSuccess: () => {
      showSuccessToast('Contract reverted to selected version successfully');
      queryClient.invalidateQueries({ queryKey: ['contract-versions', id] });
      queryClient.invalidateQueries({ queryKey: ['contract', id] });
      setShowRevertConfirm(false);
    },
    onError: (err: any) => {
      showErrorToast(err.response?.data?.message || 'Failed to revert contract version');
      setShowRevertConfirm(false);
    },
  });

  // Format date
  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatDateTime = (date: string) => {
    return new Date(date).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Get selected version
  const selectedVersion = useMemo(() => {
    if (!versions?.length) return null;
    if (selectedVersionId) return versions.find((v) => v.id === selectedVersionId) || versions[0];
    return versions[0];
  }, [versions, selectedVersionId]);

  // Get compare version
  const compareVersion = useMemo(() => {
    if (!versions?.length || !compareVersionId) return null;
    return versions.find((v) => v.id === compareVersionId) || null;
  }, [versions, compareVersionId]);

  // Simple diff computation
  const computeDiff = (oldText: string, newText: string): Array<{ type: 'same' | 'add' | 'remove'; text: string }> => {
    const oldLines = oldText.split('\n');
    const newLines = newText.split('\n');
    const result: Array<{ type: 'same' | 'add' | 'remove'; text: string }> = [];

    const maxLen = Math.max(oldLines.length, newLines.length);
    for (let i = 0; i < maxLen; i++) {
      const oldLine = oldLines[i];
      const newLine = newLines[i];

      if (oldLine === newLine) {
        result.push({ type: 'same', text: oldLine || '' });
      } else {
        if (oldLine !== undefined) {
          result.push({ type: 'remove', text: oldLine });
        }
        if (newLine !== undefined) {
          result.push({ type: 'add', text: newLine });
        }
      }
    }
    return result;
  };

  const diffLines = useMemo(() => {
    if (!compareVersion || !selectedVersion) return [];
    return computeDiff(compareVersion.content || '', selectedVersion.content || '');
  }, [selectedVersion, compareVersion]);

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <SkeletonCard />
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <SkeletonCard />
          <div className="lg:col-span-3"><SkeletonCard /></div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !versions) {
    return (
      <div className="max-w-7xl mx-auto text-center py-16">
        <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Could not load versions</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Failed to load version history for this contract.
        </p>
        <Button variant="primary" onClick={() => navigate(`/contracts/${id}`)}>Back to Contract</Button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate(`/contracts/${id}`)}
            className="p-2 -ml-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            title="Back to contract"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Version History
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {contract?.title || 'Contract'} -- {versions.length} version{versions.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => { setViewMode('single'); setCompareVersionId(null); }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                viewMode === 'single'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Single View
            </button>
            <button
              onClick={() => setViewMode('diff')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                viewMode === 'diff'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Compare
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Version List Sidebar */}
        <div className="lg:col-span-1">
          <Card padding="none">
            <CardHeader className="px-4 pt-4">
              <CardTitle className="text-base">Versions</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-gray-100 dark:divide-gray-700 max-h-[600px] overflow-y-auto">
                {versions.map((version) => {
                  const isSelected = selectedVersion?.id === version.id;
                  const isCompare = compareVersionId === version.id;
                  return (
                    <button
                      key={version.id}
                      onClick={() => {
                        if (viewMode === 'diff' && selectedVersionId && selectedVersionId !== version.id) {
                          setCompareVersionId(version.id);
                        } else {
                          setSelectedVersionId(version.id);
                          if (viewMode === 'diff') setCompareVersionId(null);
                        }
                      }}
                      className={`w-full text-left px-4 py-3 transition-colors ${
                        isSelected
                          ? 'bg-primary-50 dark:bg-primary-900/20 border-l-4 border-primary-500'
                          : isCompare
                          ? 'bg-amber-50 dark:bg-amber-900/10 border-l-4 border-amber-500'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-800/50 border-l-4 border-transparent'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">
                          v{version.version_number}
                        </span>
                        <div className="flex items-center space-x-1">
                          {version.is_current && (
                            <Badge variant="success" size="sm">Current</Badge>
                          )}
                          {isCompare && (
                            <Badge variant="warning" size="sm">Compare</Badge>
                          )}
                        </div>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {formatDate(version.created_at)}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        by {version.author?.name || 'Unknown'}
                      </p>
                      {version.change_summary && (
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                          {version.change_summary}
                        </p>
                      )}
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Content Area */}
        <div className="lg:col-span-3 space-y-4">
          {selectedVersion && (
            <>
              {/* Version Details Bar */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-6">
                      <div>
                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Version</p>
                        <p className="text-lg font-bold text-gray-900 dark:text-white">
                          v{selectedVersion.version_number}
                        </p>
                      </div>
                      <div className="h-10 border-l border-gray-200 dark:border-gray-700" />
                      <div>
                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Author</p>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {selectedVersion.author?.name || 'Unknown'}
                        </p>
                      </div>
                      <div className="h-10 border-l border-gray-200 dark:border-gray-700" />
                      <div>
                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Date</p>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {formatDateTime(selectedVersion.created_at)}
                        </p>
                      </div>
                      {selectedVersion.change_summary && (
                        <>
                          <div className="h-10 border-l border-gray-200 dark:border-gray-700" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Change Summary</p>
                            <p className="text-sm text-gray-900 dark:text-white truncate">
                              {selectedVersion.change_summary}
                            </p>
                          </div>
                        </>
                      )}
                    </div>
                    {!selectedVersion.is_current && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowRevertConfirm(true)}
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                        </svg>
                        Revert to This Version
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Content Display */}
              {viewMode === 'single' ? (
                <Card>
                  <CardHeader>
                    <CardTitle>
                      Version {selectedVersion.version_number} Content
                      {selectedVersion.is_current && (
                        <Badge variant="success" size="sm" className="ml-2">Current</Badge>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6 font-mono text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed max-h-[500px] overflow-y-auto">
                      {selectedVersion.content || 'No content available for this version.'}
                    </div>
                  </CardContent>
                </Card>
              ) : (
                /* Diff View */
                <Card>
                  <CardHeader>
                    <CardTitle>
                      <div className="flex items-center space-x-3">
                        <span>
                          Comparing v{compareVersion?.version_number || '?'} vs v{selectedVersion.version_number}
                        </span>
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {!compareVersionId ? (
                      <div className="text-center py-12">
                        <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                        </svg>
                        <p className="text-gray-600 dark:text-gray-400 mb-2">
                          Select another version from the sidebar to compare
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Click on a different version to see the differences
                        </p>
                      </div>
                    ) : (
                      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 font-mono text-sm max-h-[500px] overflow-y-auto">
                        <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200 dark:border-gray-700">
                          <div className="flex items-center space-x-4">
                            <div className="flex items-center space-x-2">
                              <span className="w-3 h-3 rounded-full bg-red-400" />
                              <span className="text-xs text-gray-600 dark:text-gray-400">
                                Removed (v{compareVersion?.version_number})
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="w-3 h-3 rounded-full bg-green-400" />
                              <span className="text-xs text-gray-600 dark:text-gray-400">
                                Added (v{selectedVersion.version_number})
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="space-y-0">
                          {diffLines.map((line, index) => (
                            <div
                              key={index}
                              className={`px-4 py-1 ${
                                line.type === 'add'
                                  ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border-l-4 border-green-500'
                                  : line.type === 'remove'
                                  ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-l-4 border-red-500'
                                  : 'text-gray-700 dark:text-gray-300 border-l-4 border-transparent'
                              }`}
                            >
                              <span className="select-none text-gray-400 dark:text-gray-600 mr-4 text-xs">
                                {line.type === 'add' ? '+' : line.type === 'remove' ? '-' : ' '}
                              </span>
                              {line.text || '\u00A0'}
                            </div>
                          ))}
                          {diffLines.length === 0 && (
                            <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                              No differences found between these versions.
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {!selectedVersion && versions.length === 0 && (
            <Card>
              <CardContent className="p-12 text-center">
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Versions Available</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  This contract has no version history yet. Versions are created automatically when the contract is edited.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Revert Confirmation Modal */}
      {showRevertConfirm && selectedVersion && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md m-4">
            <CardHeader>
              <CardTitle>Revert to Version {selectedVersion.version_number}?</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-gray-600 dark:text-gray-400">
                  This will restore the contract content to version {selectedVersion.version_number}
                  from {formatDateTime(selectedVersion.created_at)}.
                  A new version will be created with the reverted content.
                </p>
                <div className="bg-amber-50 dark:bg-amber-900/10 rounded-lg p-3 border border-amber-200 dark:border-amber-800">
                  <div className="flex items-start space-x-2">
                    <svg className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <p className="text-sm text-amber-800 dark:text-amber-300">
                      This action cannot be undone. The current version will be preserved in the history.
                    </p>
                  </div>
                </div>
                <div className="flex justify-end space-x-3 pt-2">
                  <Button variant="outline" onClick={() => setShowRevertConfirm(false)}>
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => revertMutation.mutate(selectedVersion.id)}
                    isLoading={revertMutation.isPending}
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                    </svg>
                    Revert
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ContractVersions;
