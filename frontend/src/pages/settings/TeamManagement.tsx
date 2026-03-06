/**
 * Team Management Page
 * Aureon by Rhematek Solutions
 *
 * Manage team members, roles, and invitations
 */

import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/services/api';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Table, { TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@/components/common/Table';
import Badge from '@/components/common/Badge';
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/common/Modal';
import LoadingSpinner from '@/components/common/LoadingSpinner';

// ============================================
// TYPES
// ============================================

type TeamRole = 'admin' | 'manager' | 'contributor';
type MemberStatus = 'active' | 'pending' | 'deactivated';

interface TeamMember {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: TeamRole;
  status: MemberStatus;
  last_login: string | null;
  date_joined: string;
  avatar_url?: string;
}

interface Invitation {
  id: string;
  email: string;
  role: TeamRole;
  invited_by: string;
  created_at: string;
  expires_at: string;
  status: 'pending' | 'accepted' | 'expired' | 'cancelled';
}

interface TeamListResponse {
  count: number;
  results: TeamMember[];
}

interface InvitationListResponse {
  count: number;
  results: Invitation[];
}

interface InviteFormData {
  email: string;
  role: TeamRole;
  message: string;
}

// ============================================
// CONSTANTS
// ============================================

const ROLE_OPTIONS = [
  { value: 'admin', label: 'Admin' },
  { value: 'manager', label: 'Manager' },
  { value: 'contributor', label: 'Contributor' },
];

// ============================================
// COMPONENT
// ============================================

const TeamManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const { success: showSuccessToast, error: showErrorToast } = useToast();

  // State
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [editingMember, setEditingMember] = useState<TeamMember | null>(null);
  const [editRole, setEditRole] = useState<TeamRole>('contributor');
  const [inviteForm, setInviteForm] = useState<InviteFormData>({
    email: '',
    role: 'contributor',
    message: '',
  });

  // ============================================
  // DATA FETCHING
  // ============================================

  const {
    data: teamData,
    isLoading: isLoadingTeam,
    error: teamError,
  } = useQuery<TeamListResponse>({
    queryKey: ['team-members'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/api/users/');
      return response.data;
    },
  });

  const {
    data: invitationData,
    isLoading: isLoadingInvitations,
    error: invitationError,
  } = useQuery<InvitationListResponse>({
    queryKey: ['invitations'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/api/invitations/');
      return response.data;
    },
  });

  // Handle errors
  React.useEffect(() => {
    if (teamError) {
      showErrorToast('Failed to load team members');
    }
  }, [teamError, showErrorToast]);

  React.useEffect(() => {
    if (invitationError) {
      showErrorToast('Failed to load invitations');
    }
  }, [invitationError, showErrorToast]);

  // ============================================
  // MUTATIONS
  // ============================================

  const inviteMutation = useMutation({
    mutationFn: async (data: InviteFormData) => {
      const response = await apiClient.post('/auth/api/invitations/', {
        email: data.email,
        role: data.role,
        message: data.message || undefined,
      });
      return response.data;
    },
    onSuccess: () => {
      showSuccessToast('Invitation sent successfully');
      setIsInviteModalOpen(false);
      setInviteForm({ email: '', role: 'contributor', message: '' });
      queryClient.invalidateQueries({ queryKey: ['invitations'] });
    },
    onError: () => {
      showErrorToast('Failed to send invitation');
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: async ({ memberId, role }: { memberId: string; role: TeamRole }) => {
      const response = await apiClient.patch(`/auth/api/users/${memberId}/`, { role });
      return response.data;
    },
    onSuccess: () => {
      showSuccessToast('Role updated successfully');
      setEditingMember(null);
      queryClient.invalidateQueries({ queryKey: ['team-members'] });
    },
    onError: () => {
      showErrorToast('Failed to update role');
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: async (memberId: string) => {
      const response = await apiClient.patch(`/auth/api/users/${memberId}/`, {
        status: 'deactivated',
      });
      return response.data;
    },
    onSuccess: () => {
      showSuccessToast('Member deactivated');
      queryClient.invalidateQueries({ queryKey: ['team-members'] });
    },
    onError: () => {
      showErrorToast('Failed to deactivate member');
    },
  });

  const resendInvitationMutation = useMutation({
    mutationFn: async (invitationId: string) => {
      const response = await apiClient.post(`/auth/api/invitations/${invitationId}/resend/`);
      return response.data;
    },
    onSuccess: () => {
      showSuccessToast('Invitation resent');
      queryClient.invalidateQueries({ queryKey: ['invitations'] });
    },
    onError: () => {
      showErrorToast('Failed to resend invitation');
    },
  });

  const cancelInvitationMutation = useMutation({
    mutationFn: async (invitationId: string) => {
      const response = await apiClient.delete(`/auth/api/invitations/${invitationId}/`);
      return response.data;
    },
    onSuccess: () => {
      showSuccessToast('Invitation cancelled');
      queryClient.invalidateQueries({ queryKey: ['invitations'] });
    },
    onError: () => {
      showErrorToast('Failed to cancel invitation');
    },
  });

  // ============================================
  // HANDLERS
  // ============================================

  const handleInviteSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!inviteForm.email.trim()) {
        showErrorToast('Email is required');
        return;
      }
      inviteMutation.mutate(inviteForm);
    },
    [inviteForm, inviteMutation, showErrorToast]
  );

  const handleEditRole = useCallback(
    (member: TeamMember) => {
      setEditingMember(member);
      setEditRole(member.role);
    },
    []
  );

  const handleSaveRole = useCallback(() => {
    if (editingMember) {
      updateRoleMutation.mutate({ memberId: editingMember.id, role: editRole });
    }
  }, [editingMember, editRole, updateRoleMutation]);

  const handleDeactivate = useCallback(
    (memberId: string) => {
      if (window.confirm('Are you sure you want to deactivate this team member?')) {
        deactivateMutation.mutate(memberId);
      }
    },
    [deactivateMutation]
  );

  // ============================================
  // HELPERS
  // ============================================

  const getRoleBadgeVariant = (role: TeamRole): 'primary' | 'info' | 'default' => {
    const variants: Record<TeamRole, 'primary' | 'info' | 'default'> = {
      admin: 'primary',
      manager: 'info',
      contributor: 'default',
    };
    return variants[role];
  };

  const getStatusBadge = (status: MemberStatus) => {
    const config: Record<MemberStatus, { variant: 'success' | 'warning' | 'danger'; label: string }> = {
      active: { variant: 'success', label: 'Active' },
      pending: { variant: 'warning', label: 'Pending' },
      deactivated: { variant: 'danger', label: 'Deactivated' },
    };
    const { variant, label } = config[status];
    return <Badge variant={variant} dot>{label}</Badge>;
  };

  const formatDate = (date: string | null): string => {
    if (!date) return 'Never';
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatDateTime = (date: string): string => {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const isInvitationExpired = (expiresAt: string): boolean => {
    return new Date(expiresAt) < new Date();
  };

  // Filter to only pending invitations
  const pendingInvitations = invitationData?.results.filter(
    (inv) => inv.status === 'pending' && !isInvitationExpired(inv.expires_at)
  ) || [];

  // ============================================
  // RENDER
  // ============================================

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Team Management</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage team members, roles, and invitations
          </p>
        </div>
        <Button
          variant="primary"
          size="lg"
          onClick={() => setIsInviteModalOpen(true)}
          leftIcon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
              />
            </svg>
          }
        >
          Invite Member
        </Button>
      </div>

      {/* Team Members Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {teamData
              ? `${teamData.count} Team Member${teamData.count !== 1 ? 's' : ''}`
              : 'Team Members'}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoadingTeam ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner size="lg" text="Loading team members..." />
            </div>
          ) : teamData && teamData.results.length > 0 ? (
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Name</TableHeaderCell>
                  <TableHeaderCell>Email</TableHeaderCell>
                  <TableHeaderCell>Role</TableHeaderCell>
                  <TableHeaderCell>Last Login</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell align="right">Actions</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {teamData.results.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell>
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-sm font-medium text-primary-700 dark:text-primary-300">
                          {member.first_name?.[0]?.toUpperCase() || ''}
                          {member.last_name?.[0]?.toUpperCase() || ''}
                        </div>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {member.first_name} {member.last_name}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-gray-600 dark:text-gray-400">{member.email}</span>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getRoleBadgeVariant(member.role)}>
                        {member.role.charAt(0).toUpperCase() + member.role.slice(1)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(member.last_login)}
                      </span>
                    </TableCell>
                    <TableCell>{getStatusBadge(member.status)}</TableCell>
                    <TableCell align="right">
                      <div className="flex items-center justify-end space-x-2">
                        {/* Edit Role */}
                        <button
                          onClick={() => handleEditRole(member)}
                          className="p-1.5 text-gray-400 hover:text-primary-500 transition-colors rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                          title="Edit role"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                            />
                          </svg>
                        </button>

                        {/* Deactivate */}
                        {member.status === 'active' && (
                          <button
                            onClick={() => handleDeactivate(member.id)}
                            className="p-1.5 text-gray-400 hover:text-red-500 transition-colors rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                            title="Deactivate member"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
                              />
                            </svg>
                          </button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No team members found
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Get started by inviting your first team member
              </p>
              <Button variant="primary" onClick={() => setIsInviteModalOpen(true)}>
                Invite Member
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pending Invitations */}
      <Card>
        <CardHeader>
          <CardTitle>
            Pending Invitations
            {pendingInvitations.length > 0 && (
              <Badge variant="warning" size="sm" className="ml-2">
                {pendingInvitations.length}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoadingInvitations ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner size="md" text="Loading invitations..." />
            </div>
          ) : pendingInvitations.length > 0 ? (
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Email</TableHeaderCell>
                  <TableHeaderCell>Role</TableHeaderCell>
                  <TableHeaderCell>Invited By</TableHeaderCell>
                  <TableHeaderCell>Expires</TableHeaderCell>
                  <TableHeaderCell align="right">Actions</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {pendingInvitations.map((invitation) => (
                  <TableRow key={invitation.id}>
                    <TableCell>
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
                          <svg className="w-4 h-4 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                            />
                          </svg>
                        </div>
                        <span className="text-gray-900 dark:text-white">{invitation.email}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getRoleBadgeVariant(invitation.role)}>
                        {invitation.role.charAt(0).toUpperCase() + invitation.role.slice(1)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {invitation.invited_by}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDateTime(invitation.expires_at)}
                      </span>
                    </TableCell>
                    <TableCell align="right">
                      <div className="flex items-center justify-end space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => resendInvitationMutation.mutate(invitation.id)}
                          isLoading={resendInvitationMutation.isPending}
                        >
                          Resend
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            if (window.confirm('Cancel this invitation?')) {
                              cancelInvitationMutation.mutate(invitation.id);
                            }
                          }}
                          isLoading={cancelInvitationMutation.isPending}
                          className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                        >
                          Cancel
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500 dark:text-gray-400">
                No pending invitations
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Invite Member Modal */}
      <Modal
        isOpen={isInviteModalOpen}
        onClose={() => {
          setIsInviteModalOpen(false);
          setInviteForm({ email: '', role: 'contributor', message: '' });
        }}
        size="md"
      >
        <form onSubmit={handleInviteSubmit}>
          <ModalHeader>Invite Team Member</ModalHeader>
          <ModalBody className="space-y-4">
            <Input
              label="Email Address"
              type="email"
              placeholder="colleague@company.com"
              value={inviteForm.email}
              onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
              fullWidth
              required
            />

            <Select
              label="Role"
              options={ROLE_OPTIONS}
              value={inviteForm.role}
              onChange={(e) =>
                setInviteForm({ ...inviteForm, role: e.target.value as TeamRole })
              }
              fullWidth
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Message (optional)
              </label>
              <textarea
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 px-4 py-2 text-base transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                rows={3}
                placeholder="Add a personal message to the invitation..."
                value={inviteForm.message}
                onChange={(e) => setInviteForm({ ...inviteForm, message: e.target.value })}
              />
            </div>

            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                <strong className="text-gray-900 dark:text-white">Role permissions:</strong>
              </p>
              <ul className="mt-2 space-y-1 text-sm text-gray-600 dark:text-gray-400">
                {inviteForm.role === 'admin' && (
                  <>
                    <li>-- Full access to all features and settings</li>
                    <li>-- Can manage team members and billing</li>
                    <li>-- Can create, edit, and delete all resources</li>
                  </>
                )}
                {inviteForm.role === 'manager' && (
                  <>
                    <li>-- Can manage clients, contracts, and invoices</li>
                    <li>-- Can view reports and analytics</li>
                    <li>-- Cannot manage team members or billing</li>
                  </>
                )}
                {inviteForm.role === 'contributor' && (
                  <>
                    <li>-- Can view and edit assigned resources</li>
                    <li>-- Can create invoices and contracts</li>
                    <li>-- Limited access to settings and reports</li>
                  </>
                )}
              </ul>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button
              variant="ghost"
              type="button"
              onClick={() => {
                setIsInviteModalOpen(false);
                setInviteForm({ email: '', role: 'contributor', message: '' });
              }}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              type="submit"
              isLoading={inviteMutation.isPending}
            >
              Send Invitation
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Edit Role Modal */}
      <Modal
        isOpen={!!editingMember}
        onClose={() => setEditingMember(null)}
        size="sm"
      >
        <ModalHeader>Edit Role</ModalHeader>
        <ModalBody className="space-y-4">
          {editingMember && (
            <>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Changing role for{' '}
                <span className="font-medium text-gray-900 dark:text-white">
                  {editingMember.first_name} {editingMember.last_name}
                </span>
              </p>
              <Select
                label="New Role"
                options={ROLE_OPTIONS}
                value={editRole}
                onChange={(e) => setEditRole(e.target.value as TeamRole)}
                fullWidth
              />
            </>
          )}
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" onClick={() => setEditingMember(null)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSaveRole}
            isLoading={updateRoleMutation.isPending}
          >
            Save Changes
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default TeamManagement;
