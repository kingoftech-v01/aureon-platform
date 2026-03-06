/**
 * Settings Page
 * Aureon by Rhematek Solutions
 *
 * Application settings and user preferences
 */

import React, { useState } from 'react';
import { useAuth, useTheme } from '@/contexts';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import api from '../../services/api';

const Settings: React.FC = () => {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const { success: showSuccessToast, error: showErrorToast } = useToast();
  const [selectedTab, setSelectedTab] = useState<'profile' | 'company' | 'preferences' | 'billing'>('profile');

  const [profileData, setProfileData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    phone: '',
    job_title: '',
  });

  const [companyData, setCompanyData] = useState({
    name: 'Rhematek Solutions',
    address: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    tax_id: '',
  });

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [smsNotifications, setSmsNotifications] = useState(false);

  const [timezone, setTimezone] = useState(user?.timezone || 'UTC');
  const [currency, setCurrency] = useState('USD');
  const [savingPreferences, setSavingPreferences] = useState(false);

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.put('/api/accounts/profile/', {
        first_name: profileData.first_name,
        last_name: profileData.last_name,
        email: profileData.email,
        phone: profileData.phone,
      });
      showSuccessToast('Profile updated successfully');
    } catch (error) {
      showErrorToast('Failed to update profile');
    }
  };

  const handleCompanySave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.put('/api/tenants/settings/', {
        company_name: companyData.name,
      });
      showSuccessToast('Company settings updated');
    } catch (error) {
      showErrorToast('Failed to update company settings');
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      showErrorToast('Passwords do not match');
      return;
    }
    try {
      await api.post('/api/accounts/change-password/', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      showSuccessToast('Password changed successfully');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      showErrorToast('Failed to change password');
    }
  };

  const handlePreferencesSave = async () => {
    setSavingPreferences(true);
    try {
      await api.patch('/auth/api/users/me/', { timezone, language: currency });
      showSuccessToast('Preferences saved successfully');
    } catch (error) {
      showErrorToast('Failed to save preferences');
    } finally {
      setSavingPreferences(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Manage your account and application preferences
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setSelectedTab('profile')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'profile'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            Profile
          </button>
          <button
            onClick={() => setSelectedTab('company')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'company'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            Company
          </button>
          <button
            onClick={() => setSelectedTab('preferences')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'preferences'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            Preferences
          </button>
          <button
            onClick={() => setSelectedTab('billing')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'billing'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            Billing
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {selectedTab === 'profile' && (
        <>
        <form onSubmit={handleProfileSave} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="First Name"
                  value={profileData.first_name}
                  onChange={(e) => setProfileData({ ...profileData, first_name: e.target.value })}
                  fullWidth
                />
                <Input
                  label="Last Name"
                  value={profileData.last_name}
                  onChange={(e) => setProfileData({ ...profileData, last_name: e.target.value })}
                  fullWidth
                />
              </div>

              <Input
                label="Email Address"
                type="email"
                value={profileData.email}
                onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                fullWidth
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Phone Number"
                  type="tel"
                  value={profileData.phone}
                  onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                  fullWidth
                />
                <Input
                  label="Job Title"
                  value={profileData.job_title}
                  onChange={(e) => setProfileData({ ...profileData, job_title: e.target.value })}
                  fullWidth
                />
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button type="submit" variant="primary">
              Save Changes
            </Button>
          </div>
        </form>

        <form onSubmit={handlePasswordChange} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="Current Password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                fullWidth
              />
              <Input
                label="New Password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                fullWidth
              />
              <Input
                label="Confirm New Password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                fullWidth
              />
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button type="submit" variant="primary">
              Change Password
            </Button>
          </div>
        </form>
        </>
      )}

      {selectedTab === 'company' && (
        <form onSubmit={handleCompanySave} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Company Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="Company Name"
                value={companyData.name}
                onChange={(e) => setCompanyData({ ...companyData, name: e.target.value })}
                fullWidth
              />

              <Input
                label="Street Address"
                value={companyData.address}
                onChange={(e) => setCompanyData({ ...companyData, address: e.target.value })}
                fullWidth
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="City"
                  value={companyData.city}
                  onChange={(e) => setCompanyData({ ...companyData, city: e.target.value })}
                  fullWidth
                />
                <Input
                  label="State/Province"
                  value={companyData.state}
                  onChange={(e) => setCompanyData({ ...companyData, state: e.target.value })}
                  fullWidth
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Postal Code"
                  value={companyData.postal_code}
                  onChange={(e) => setCompanyData({ ...companyData, postal_code: e.target.value })}
                  fullWidth
                />
                <Input
                  label="Country"
                  value={companyData.country}
                  onChange={(e) => setCompanyData({ ...companyData, country: e.target.value })}
                  fullWidth
                />
              </div>

              <Input
                label="Tax ID"
                value={companyData.tax_id}
                onChange={(e) => setCompanyData({ ...companyData, tax_id: e.target.value })}
                fullWidth
              />
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button type="submit" variant="primary">
              Save Changes
            </Button>
          </div>
        </form>
      )}

      {selectedTab === 'preferences' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Theme
                </label>
                <div className="grid grid-cols-3 gap-4">
                  <button
                    type="button"
                    onClick={() => setTheme('light')}
                    className={`p-4 border-2 rounded-lg transition-colors ${
                      theme === 'light'
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <svg className="w-6 h-6 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    <p className="font-medium text-gray-900 dark:text-white">Light</p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setTheme('dark')}
                    className={`p-4 border-2 rounded-lg transition-colors ${
                      theme === 'dark'
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <svg className="w-6 h-6 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                    </svg>
                    <p className="font-medium text-gray-900 dark:text-white">Dark</p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setTheme('system')}
                    className={`p-4 border-2 rounded-lg transition-colors ${
                      theme === 'system'
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <svg className="w-6 h-6 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    <p className="font-medium text-gray-900 dark:text-white">System</p>
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Notifications</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Email Notifications</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Receive email updates about your account</p>
                </div>
                <input type="checkbox" className="w-4 h-4" checked={emailNotifications} onChange={(e) => setEmailNotifications(e.target.checked)} />
              </div>
              <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Payment Reminders</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Get notified about upcoming payments</p>
                </div>
                <input type="checkbox" className="w-4 h-4" checked={pushNotifications} onChange={(e) => setPushNotifications(e.target.checked)} />
              </div>
              <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">Invoice Updates</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Notifications when invoices are paid</p>
                </div>
                <input type="checkbox" className="w-4 h-4" checked={smsNotifications} onChange={(e) => setSmsNotifications(e.target.checked)} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Regional Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Timezone
                  </label>
                  <select
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-900 dark:text-white"
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
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Currency
                  </label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-900 dark:text-white"
                  >
                    <option value="USD">USD - US Dollar</option>
                    <option value="EUR">EUR - Euro</option>
                    <option value="GBP">GBP - British Pound</option>
                    <option value="CAD">CAD - Canadian Dollar</option>
                    <option value="AUD">AUD - Australian Dollar</option>
                    <option value="JPY">JPY - Japanese Yen</option>
                    <option value="NGN">NGN - Nigerian Naira</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button
              variant="primary"
              onClick={handlePreferencesSave}
              disabled={savingPreferences}
            >
              {savingPreferences ? 'Saving...' : 'Save Preferences'}
            </Button>
          </div>
        </div>
      )}

      {selectedTab === 'billing' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Current Plan</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">Professional Plan</p>
                  <p className="text-gray-600 dark:text-gray-400 mt-1">$49/month</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                    Next billing date: January 1, 2025
                  </p>
                </div>
                <Button variant="outline">Upgrade Plan</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Payment Method</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">•••• •••• •••• 4242</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Expires 12/2025</p>
                  </div>
                </div>
                <Button variant="outline" size="sm">Update</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Billing History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">December 2024</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Professional Plan</p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="font-semibold text-gray-900 dark:text-white">$49.00</span>
                    <Button variant="ghost" size="sm">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </Button>
                  </div>
                </div>
                <div className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">November 2024</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Professional Plan</p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="font-semibold text-gray-900 dark:text-white">$49.00</span>
                    <Button variant="ghost" size="sm">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Settings;
