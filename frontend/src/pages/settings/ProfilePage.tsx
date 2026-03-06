/**
 * Profile Page
 * Aureon by Rhematek Solutions
 *
 * Dedicated user profile management with avatar, personal info,
 * password change, 2FA, preferences, and account danger zone.
 */

import React, { useState, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useAuth } from '@/contexts';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/common/Modal';
import apiClient from '@/services/api';

const ProfilePage: React.FC = () => {
  const { user, updateUser } = useAuth();
  const { success: showSuccess, error: showError } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Personal info state
  const [profileData, setProfileData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    phone: (user as any)?.phone || '',
  });

  // Password state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  // Preferences state
  const [timezone, setTimezone] = useState((user as any)?.timezone || 'UTC');
  const [language, setLanguage] = useState((user as any)?.language || 'en');

  // 2FA state
  const [twoFactorEnabled, setTwoFactorEnabled] = useState((user as any)?.two_factor_enabled || false);

  // Danger zone modal
  const [showDeactivateModal, setShowDeactivateModal] = useState(false);
  const [deactivateConfirm, setDeactivateConfirm] = useState('');

  // Avatar upload state
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

  // Profile update mutation
  const profileMutation = useMutation({
    mutationFn: async (data: typeof profileData) => {
      const response = await apiClient.put('/auth/user/', data);
      return response.data;
    },
    onSuccess: (data) => {
      updateUser(data);
      showSuccess('Profile updated successfully');
    },
    onError: () => {
      showError('Failed to update profile');
    },
  });

  // Password change mutation
  const passwordMutation = useMutation({
    mutationFn: async (data: { current_password: string; new_password: string }) => {
      await apiClient.post('/auth/change-password/', data);
    },
    onSuccess: () => {
      showSuccess('Password changed successfully');
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
    },
    onError: () => {
      showError('Failed to change password. Please check your current password.');
    },
  });

  // 2FA toggle mutation
  const twoFactorMutation = useMutation({
    mutationFn: async (enable: boolean) => {
      if (enable) {
        const response = await apiClient.post(`/users/${user?.id}/enable-2fa/`);
        return response.data;
      } else {
        await apiClient.post(`/users/${user?.id}/disable-2fa/`);
        return null;
      }
    },
    onSuccess: (_, enable) => {
      setTwoFactorEnabled(enable);
      showSuccess(enable ? 'Two-factor authentication enabled' : 'Two-factor authentication disabled');
    },
    onError: () => {
      showError('Failed to update two-factor authentication');
    },
  });

  // Preferences mutation
  const preferencesMutation = useMutation({
    mutationFn: async (data: { timezone: string; language: string }) => {
      const response = await apiClient.patch('/auth/user/', data);
      return response.data;
    },
    onSuccess: () => {
      showSuccess('Preferences updated successfully');
    },
    onError: () => {
      showError('Failed to update preferences');
    },
  });

  // Avatar upload mutation
  const avatarMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('avatar', file);
      const response = await apiClient.post('/auth/user/avatar/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
    onSuccess: () => {
      showSuccess('Avatar updated successfully');
    },
    onError: () => {
      showError('Failed to upload avatar');
    },
  });

  // Deactivate account mutation
  const deactivateMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post('/auth/user/deactivate/');
    },
    onSuccess: () => {
      showSuccess('Account deactivated');
      window.location.href = '/login';
    },
    onError: () => {
      showError('Failed to deactivate account');
    },
  });

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    profileMutation.mutate(profileData);
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      showError('Passwords do not match');
      return;
    }
    if (passwordData.new_password.length < 8) {
      showError('Password must be at least 8 characters');
      return;
    }
    passwordMutation.mutate({
      current_password: passwordData.current_password,
      new_password: passwordData.new_password,
    });
  };

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        showError('File size must be less than 5MB');
        return;
      }
      const reader = new FileReader();
      reader.onload = () => setAvatarPreview(reader.result as string);
      reader.readAsDataURL(file);
      avatarMutation.mutate(file);
    }
  };

  const handleDeactivate = () => {
    if (deactivateConfirm === 'DEACTIVATE') {
      deactivateMutation.mutate();
    }
  };

  const initials = `${user?.first_name?.[0] || ''}${user?.last_name?.[0] || ''}`;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl p-8 text-white">
        <h1 className="text-3xl font-bold">My Profile</h1>
        <p className="mt-2 text-primary-100">Manage your personal information and account settings</p>
      </div>

      {/* Avatar Section */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center space-x-6">
            <div className="relative">
              {avatarPreview ? (
                <img
                  src={avatarPreview}
                  alt="Avatar"
                  className="w-24 h-24 rounded-2xl object-cover shadow-lg"
                />
              ) : (
                <div className="w-24 h-24 bg-gradient-to-br from-primary-400 via-primary-500 to-primary-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-lg">
                  {initials}
                </div>
              )}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="absolute -bottom-2 -right-2 w-8 h-8 bg-white dark:bg-gray-700 rounded-full shadow-md flex items-center justify-center hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                title="Upload avatar"
              >
                <svg className="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleAvatarChange}
                className="hidden"
              />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {user?.first_name} {user?.last_name}
              </h2>
              <p className="text-gray-500 dark:text-gray-400">{user?.email}</p>
              <Badge variant="success" size="sm" className="mt-2">Active Account</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Personal Information */}
      <Card>
        <CardHeader>
          <CardTitle>Personal Information</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="First Name"
                value={profileData.first_name}
                onChange={(e) => setProfileData({ ...profileData, first_name: e.target.value })}
                fullWidth
                required
              />
              <Input
                label="Last Name"
                value={profileData.last_name}
                onChange={(e) => setProfileData({ ...profileData, last_name: e.target.value })}
                fullWidth
                required
              />
            </div>
            <Input
              label="Email Address"
              type="email"
              value={profileData.email}
              onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
              fullWidth
              required
            />
            <Input
              label="Phone Number"
              type="tel"
              value={profileData.phone}
              onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
              fullWidth
              placeholder="+1 (555) 000-0000"
            />
            <div className="flex justify-end pt-2">
              <Button
                type="submit"
                variant="primary"
                isLoading={profileMutation.isPending}
              >
                Save Changes
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Password Change */}
      <Card>
        <CardHeader>
          <CardTitle>Change Password</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <Input
              label="Current Password"
              type="password"
              value={passwordData.current_password}
              onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
              fullWidth
              required
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="New Password"
                type="password"
                value={passwordData.new_password}
                onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                fullWidth
                required
              />
              <Input
                label="Confirm New Password"
                type="password"
                value={passwordData.confirm_password}
                onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                fullWidth
                required
              />
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Password must be at least 8 characters long and include a mix of letters, numbers, and symbols.
            </p>
            <div className="flex justify-end pt-2">
              <Button
                type="submit"
                variant="primary"
                isLoading={passwordMutation.isPending}
              >
                Change Password
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Two-Factor Authentication */}
      <Card>
        <CardHeader>
          <CardTitle>Two-Factor Authentication</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">
                {twoFactorEnabled ? 'Two-factor authentication is enabled' : 'Two-factor authentication is disabled'}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Add an extra layer of security to your account by requiring a verification code in addition to your password.
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Badge variant={twoFactorEnabled ? 'success' : 'default'} size="sm">
                {twoFactorEnabled ? 'Enabled' : 'Disabled'}
              </Badge>
              <Button
                variant={twoFactorEnabled ? 'danger' : 'primary'}
                size="sm"
                onClick={() => twoFactorMutation.mutate(!twoFactorEnabled)}
                isLoading={twoFactorMutation.isPending}
              >
                {twoFactorEnabled ? 'Disable' : 'Enable'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Timezone and Language Preferences */}
      <Card>
        <CardHeader>
          <CardTitle>Preferences</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Timezone
                </label>
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-900 dark:text-white focus:border-primary-500 focus:ring-2 focus:ring-primary-500 transition-colors"
                >
                  <option value="UTC">UTC (GMT +0:00)</option>
                  <option value="America/New_York">Eastern Time (GMT -5:00)</option>
                  <option value="America/Chicago">Central Time (GMT -6:00)</option>
                  <option value="America/Denver">Mountain Time (GMT -7:00)</option>
                  <option value="America/Los_Angeles">Pacific Time (GMT -8:00)</option>
                  <option value="Europe/London">London (GMT +0:00)</option>
                  <option value="Europe/Paris">Central European (GMT +1:00)</option>
                  <option value="Asia/Tokyo">Tokyo (GMT +9:00)</option>
                  <option value="Australia/Sydney">Sydney (GMT +11:00)</option>
                  <option value="Africa/Lagos">West Africa (GMT +1:00)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Language
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-900 dark:text-white focus:border-primary-500 focus:ring-2 focus:ring-primary-500 transition-colors"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="pt">Portuguese</option>
                  <option value="ja">Japanese</option>
                  <option value="zh">Chinese (Simplified)</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <Button
                variant="primary"
                onClick={() => preferencesMutation.mutate({ timezone, language })}
                isLoading={preferencesMutation.isPending}
              >
                Save Preferences
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card>
        <CardHeader>
          <CardTitle>
            <span className="text-red-600 dark:text-red-400">Danger Zone</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="border border-red-200 dark:border-red-800 rounded-lg p-4 bg-red-50 dark:bg-red-900/10">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-red-900 dark:text-red-300">Deactivate Account</p>
                <p className="text-sm text-red-700 dark:text-red-400 mt-1">
                  Once you deactivate your account, all your data will be retained but you will lose access. This action can be reversed by contacting support.
                </p>
              </div>
              <Button
                variant="danger"
                size="sm"
                onClick={() => setShowDeactivateModal(true)}
              >
                Deactivate
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Deactivate Confirmation Modal */}
      <Modal isOpen={showDeactivateModal} onClose={() => setShowDeactivateModal(false)} size="md">
        <ModalHeader>Deactivate Account</ModalHeader>
        <ModalBody>
          <div className="space-y-4">
            <p className="text-gray-600 dark:text-gray-400">
              Are you sure you want to deactivate your account? You will lose access to all your data, contracts, and invoices.
            </p>
            <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
              <p className="text-sm text-red-800 dark:text-red-300 font-medium">
                This will immediately log you out and disable your account.
              </p>
            </div>
            <Input
              label='Type "DEACTIVATE" to confirm'
              value={deactivateConfirm}
              onChange={(e) => setDeactivateConfirm(e.target.value)}
              fullWidth
              placeholder="DEACTIVATE"
            />
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" onClick={() => setShowDeactivateModal(false)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleDeactivate}
            disabled={deactivateConfirm !== 'DEACTIVATE'}
            isLoading={deactivateMutation.isPending}
          >
            Deactivate Account
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default ProfilePage;
