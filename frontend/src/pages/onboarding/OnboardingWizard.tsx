/**
 * Onboarding Wizard Page
 * Aureon by Rhematek Solutions
 *
 * Multi-step onboarding wizard for new users to set up their account,
 * branding, billing preferences, and optionally import data.
 */

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import apiClient from '@/services/api';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Card, { CardContent } from '@/components/common/Card';

interface OnboardingData {
  // Step 1
  company_name: string;
  industry: string;
  // Step 2
  logo: File | null;
  primary_color: string;
  business_address: string;
  business_city: string;
  business_state: string;
  business_country: string;
  business_postal_code: string;
  // Step 3
  currency: string;
  tax_rate: string;
  default_payment_terms: string;
  invoice_prefix: string;
  // Step 4
  import_file: File | null;
  skip_import: boolean;
}

const STEPS = [
  { number: 1, title: 'Welcome', description: 'Tell us about your business' },
  { number: 2, title: 'Branding', description: 'Customize your appearance' },
  { number: 3, title: 'Billing', description: 'Set billing preferences' },
  { number: 4, title: 'Import', description: 'Bring your data' },
  { number: 5, title: 'Complete', description: 'You are all set' },
];

const INDUSTRIES = [
  'Consulting',
  'Marketing & Advertising',
  'Software Development',
  'Design & Creative',
  'Accounting & Finance',
  'Legal Services',
  'Healthcare',
  'Education',
  'Real Estate',
  'E-Commerce',
  'Construction',
  'Manufacturing',
  'Freelance / Solopreneur',
  'Other',
];

const CURRENCIES = [
  { value: 'USD', label: 'US Dollar (USD)' },
  { value: 'EUR', label: 'Euro (EUR)' },
  { value: 'GBP', label: 'British Pound (GBP)' },
  { value: 'CAD', label: 'Canadian Dollar (CAD)' },
  { value: 'AUD', label: 'Australian Dollar (AUD)' },
  { value: 'JPY', label: 'Japanese Yen (JPY)' },
  { value: 'CHF', label: 'Swiss Franc (CHF)' },
  { value: 'NGN', label: 'Nigerian Naira (NGN)' },
  { value: 'ZAR', label: 'South African Rand (ZAR)' },
  { value: 'INR', label: 'Indian Rupee (INR)' },
];

const PAYMENT_TERMS = [
  { value: 'due_on_receipt', label: 'Due on Receipt' },
  { value: 'net_7', label: 'Net 7 (7 days)' },
  { value: 'net_15', label: 'Net 15 (15 days)' },
  { value: 'net_30', label: 'Net 30 (30 days)' },
  { value: 'net_45', label: 'Net 45 (45 days)' },
  { value: 'net_60', label: 'Net 60 (60 days)' },
  { value: 'net_90', label: 'Net 90 (90 days)' },
];

const OnboardingWizard: React.FC = () => {
  const navigate = useNavigate();
  const { success: showSuccessToast, error: showErrorToast } = useToast();
  const [currentStep, setCurrentStep] = useState(1);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);

  const [formData, setFormData] = useState<OnboardingData>({
    company_name: '',
    industry: '',
    logo: null,
    primary_color: '#3b82f6',
    business_address: '',
    business_city: '',
    business_state: '',
    business_country: '',
    business_postal_code: '',
    currency: 'USD',
    tax_rate: '0',
    default_payment_terms: 'net_30',
    invoice_prefix: 'INV-',
    import_file: null,
    skip_import: false,
  });

  // Save onboarding data
  const saveMutation = useMutation({
    mutationFn: async (data: Partial<OnboardingData>) => {
      const payload: Record<string, any> = { ...data };
      delete payload.logo;
      delete payload.import_file;
      const response = await apiClient.post('/auth/onboarding/', payload);
      return response.data;
    },
    onError: (err: any) => {
      showErrorToast(err.response?.data?.message || 'Failed to save progress');
    },
  });

  // Update form data
  const updateField = useCallback((field: keyof OnboardingData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }, []);

  // Handle logo upload
  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      updateField('logo', file);
      const reader = new FileReader();
      reader.onload = () => setLogoPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  // Handle CSV import
  const handleImportFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      updateField('import_file', file);
      updateField('skip_import', false);
    }
  };

  // Navigation
  const goNext = () => {
    if (currentStep < 5) {
      // Save progress on step change
      saveMutation.mutate(formData);
      setCurrentStep(currentStep + 1);
    }
  };

  const goBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    if (currentStep === 4) {
      updateField('skip_import', true);
    }
    goNext();
  };

  const handleComplete = () => {
    saveMutation.mutate(formData);
    showSuccessToast('Onboarding complete! Welcome to Aureon.');
    navigate('/dashboard');
  };

  // Progress percentage
  const progress = ((currentStep - 1) / (STEPS.length - 1)) * 100;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Progress Bar */}
      <div className="w-full bg-gray-200 dark:bg-gray-700 h-1.5">
        <div
          className="bg-gradient-to-r from-primary-400 to-primary-600 h-1.5 transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Step Indicator */}
      <div className="max-w-3xl mx-auto w-full px-4 pt-8 pb-4">
        <div className="flex items-center justify-between">
          {STEPS.map((step, index) => (
            <React.Fragment key={step.number}>
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300 ${
                    step.number < currentStep
                      ? 'bg-green-500 text-white'
                      : step.number === currentStep
                      ? 'bg-primary-500 text-white ring-4 ring-primary-200 dark:ring-primary-900'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                  }`}
                >
                  {step.number < currentStep ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.number
                  )}
                </div>
                <span className={`mt-2 text-xs font-medium hidden sm:block ${
                  step.number <= currentStep
                    ? 'text-gray-900 dark:text-white'
                    : 'text-gray-400 dark:text-gray-500'
                }`}>
                  {step.title}
                </span>
              </div>
              {index < STEPS.length - 1 && (
                <div className={`flex-1 h-0.5 mx-2 ${
                  step.number < currentStep
                    ? 'bg-green-500'
                    : 'bg-gray-200 dark:bg-gray-700'
                }`} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="flex-1 flex items-start justify-center px-4 pb-8">
        <div className="max-w-2xl w-full">
          <Card shadow="lg">
            <CardContent className="p-8">

              {/* Step 1: Welcome */}
              {currentStep === 1 && (
                <div className="space-y-6">
                  <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-gradient-to-br from-primary-400 to-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <svg className="w-9 h-9 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                      Welcome to Aureon
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                      Let us set up your account in just a few steps. Tell us about your business.
                    </p>
                  </div>

                  <div>
                    <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Company / Business Name *
                    </label>
                    <input
                      id="company_name"
                      type="text"
                      value={formData.company_name}
                      onChange={(e) => updateField('company_name', e.target.value)}
                      placeholder="Acme Corp"
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>

                  <div>
                    <label htmlFor="industry" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Industry *
                    </label>
                    <select
                      id="industry"
                      value={formData.industry}
                      onChange={(e) => updateField('industry', e.target.value)}
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">Select your industry</option>
                      {INDUSTRIES.map((ind) => (
                        <option key={ind} value={ind}>{ind}</option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {/* Step 2: Brand Setup */}
              {currentStep === 2 && (
                <div className="space-y-6">
                  <div className="text-center mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Customize Your Brand</h2>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                      Make invoices and contracts match your brand identity.
                    </p>
                  </div>

                  {/* Logo Upload */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Company Logo
                    </label>
                    <div className="flex items-center space-x-6">
                      <div className="w-20 h-20 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center overflow-hidden bg-gray-50 dark:bg-gray-800">
                        {logoPreview ? (
                          <img src={logoPreview} alt="Logo preview" className="w-full h-full object-cover" />
                        ) : (
                          <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        )}
                      </div>
                      <div>
                        <label
                          htmlFor="logo-upload"
                          className="cursor-pointer inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                        >
                          <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                          Upload Logo
                        </label>
                        <input
                          id="logo-upload"
                          type="file"
                          accept="image/*"
                          onChange={handleLogoChange}
                          className="hidden"
                        />
                        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">PNG, JPG, SVG up to 2MB</p>
                      </div>
                    </div>
                  </div>

                  {/* Primary Color */}
                  <div>
                    <label htmlFor="primary_color" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Primary Brand Color
                    </label>
                    <div className="flex items-center space-x-3">
                      <input
                        id="primary_color"
                        type="color"
                        value={formData.primary_color}
                        onChange={(e) => updateField('primary_color', e.target.value)}
                        className="w-12 h-12 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer"
                      />
                      <input
                        type="text"
                        value={formData.primary_color}
                        onChange={(e) => updateField('primary_color', e.target.value)}
                        className="w-32 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                  </div>

                  {/* Business Address */}
                  <div>
                    <label htmlFor="business_address" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Business Address
                    </label>
                    <input
                      id="business_address"
                      type="text"
                      value={formData.business_address}
                      onChange={(e) => updateField('business_address', e.target.value)}
                      placeholder="123 Main Street"
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="business_city" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">City</label>
                      <input
                        id="business_city"
                        type="text"
                        value={formData.business_city}
                        onChange={(e) => updateField('business_city', e.target.value)}
                        placeholder="New York"
                        className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div>
                      <label htmlFor="business_state" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">State / Region</label>
                      <input
                        id="business_state"
                        type="text"
                        value={formData.business_state}
                        onChange={(e) => updateField('business_state', e.target.value)}
                        placeholder="NY"
                        className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="business_country" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Country</label>
                      <input
                        id="business_country"
                        type="text"
                        value={formData.business_country}
                        onChange={(e) => updateField('business_country', e.target.value)}
                        placeholder="United States"
                        className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div>
                      <label htmlFor="business_postal_code" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Postal Code</label>
                      <input
                        id="business_postal_code"
                        type="text"
                        value={formData.business_postal_code}
                        onChange={(e) => updateField('business_postal_code', e.target.value)}
                        placeholder="10001"
                        className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Step 3: Billing Preferences */}
              {currentStep === 3 && (
                <div className="space-y-6">
                  <div className="text-center mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Billing Preferences</h2>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                      Configure your default billing and invoicing settings.
                    </p>
                  </div>

                  <div>
                    <label htmlFor="currency" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Default Currency
                    </label>
                    <select
                      id="currency"
                      value={formData.currency}
                      onChange={(e) => updateField('currency', e.target.value)}
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      {CURRENCIES.map((c) => (
                        <option key={c.value} value={c.value}>{c.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="tax_rate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Default Tax Rate (%)
                    </label>
                    <div className="relative">
                      <input
                        id="tax_rate"
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        value={formData.tax_rate}
                        onChange={(e) => updateField('tax_rate', e.target.value)}
                        placeholder="0.00"
                        className="w-full px-4 py-3 pr-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                      <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">%</span>
                    </div>
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      This will be the default tax applied to new invoices. You can override per invoice.
                    </p>
                  </div>

                  <div>
                    <label htmlFor="default_payment_terms" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Default Payment Terms
                    </label>
                    <select
                      id="default_payment_terms"
                      value={formData.default_payment_terms}
                      onChange={(e) => updateField('default_payment_terms', e.target.value)}
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      {PAYMENT_TERMS.map((t) => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="invoice_prefix" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Invoice Number Prefix
                    </label>
                    <input
                      id="invoice_prefix"
                      type="text"
                      value={formData.invoice_prefix}
                      onChange={(e) => updateField('invoice_prefix', e.target.value)}
                      placeholder="INV-"
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      Example: {formData.invoice_prefix}0001
                    </p>
                  </div>
                </div>
              )}

              {/* Step 4: Import Data */}
              {currentStep === 4 && (
                <div className="space-y-6">
                  <div className="text-center mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Import Your Data</h2>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                      Bring your existing clients into Aureon via CSV, or skip to start fresh.
                    </p>
                  </div>

                  <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-8 text-center hover:border-primary-400 dark:hover:border-primary-500 transition-colors">
                    <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <label htmlFor="csv-upload" className="cursor-pointer">
                      <span className="text-primary-600 dark:text-primary-400 font-medium hover:underline">
                        Choose a CSV file
                      </span>
                      <span className="text-gray-500 dark:text-gray-400"> or drag and drop</span>
                    </label>
                    <input
                      id="csv-upload"
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={handleImportFile}
                      className="hidden"
                    />
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                      CSV, XLSX up to 10MB
                    </p>
                    {formData.import_file && (
                      <div className="mt-4 inline-flex items-center space-x-2 px-4 py-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
                        <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-sm text-green-700 dark:text-green-300 font-medium">
                          {formData.import_file.name}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="bg-blue-50 dark:bg-blue-900/10 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-2">
                      CSV Format Guide
                    </h4>
                    <p className="text-xs text-blue-700 dark:text-blue-400">
                      Your CSV should include columns for: Name, Email, Phone, Company, Address, City, State, Country.
                      Download a{' '}
                      <button className="underline font-medium hover:no-underline">
                        sample template
                      </button>{' '}
                      for reference.
                    </p>
                  </div>
                </div>
              )}

              {/* Step 5: Complete */}
              {currentStep === 5 && (
                <div className="text-center py-4">
                  {/* Success Animation */}
                  <div className="relative w-24 h-24 mx-auto mb-6">
                    <div className="absolute inset-0 bg-green-100 dark:bg-green-900/20 rounded-full animate-ping opacity-25" />
                    <div className="relative w-24 h-24 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center">
                      <svg className="w-14 h-14 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  </div>

                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                    You are all set!
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto">
                    Your Aureon workspace is ready. Start managing your finances with automation and confidence.
                  </p>

                  {/* Quick Action Buttons */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-lg mx-auto">
                    <button
                      onClick={() => navigate('/clients/create')}
                      className="flex flex-col items-center p-4 rounded-xl border-2 border-gray-200 dark:border-gray-700 hover:border-primary-400 dark:hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/10 transition-all group"
                    >
                      <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center mb-2 group-hover:bg-blue-200 dark:group-hover:bg-blue-900/30 transition-colors">
                        <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                        </svg>
                      </div>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">Create Client</span>
                    </button>

                    <button
                      onClick={() => navigate('/invoices/create')}
                      className="flex flex-col items-center p-4 rounded-xl border-2 border-gray-200 dark:border-gray-700 hover:border-primary-400 dark:hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/10 transition-all group"
                    >
                      <div className="w-10 h-10 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center mb-2 group-hover:bg-green-200 dark:group-hover:bg-green-900/30 transition-colors">
                        <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">Create Invoice</span>
                    </button>

                    <button
                      onClick={() => navigate('/dashboard')}
                      className="flex flex-col items-center p-4 rounded-xl border-2 border-gray-200 dark:border-gray-700 hover:border-primary-400 dark:hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/10 transition-all group"
                    >
                      <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center mb-2 group-hover:bg-purple-200 dark:group-hover:bg-purple-900/30 transition-colors">
                        <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                        </svg>
                      </div>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">Explore Dashboard</span>
                    </button>
                  </div>
                </div>
              )}

            </CardContent>
          </Card>

          {/* Navigation Buttons */}
          <div className="flex items-center justify-between mt-6">
            <div>
              {currentStep > 1 && currentStep < 5 && (
                <Button variant="ghost" onClick={goBack}>
                  <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Back
                </Button>
              )}
            </div>
            <div className="flex items-center space-x-3">
              {currentStep < 5 && currentStep !== 1 && (
                <Button variant="ghost" onClick={handleSkip}>
                  Skip
                </Button>
              )}
              {currentStep < 5 && (
                <Button
                  variant="primary"
                  onClick={goNext}
                  disabled={currentStep === 1 && !formData.company_name}
                  isLoading={saveMutation.isPending}
                >
                  {currentStep === 4 ? 'Finish Setup' : 'Next'}
                  <svg className="w-5 h-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </Button>
              )}
              {currentStep === 5 && (
                <Button variant="primary" onClick={handleComplete} isLoading={saveMutation.isPending}>
                  Go to Dashboard
                  <svg className="w-5 h-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingWizard;
