/**
 * ClientCreate Page Tests
 * Aureon by Rhematek Solutions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/tests/test-utils';
import userEvent from '@testing-library/user-event';
import ClientCreate from '../ClientCreate';
import { mockClient } from '@/tests/mocks/data';
import * as clientService from '@/services/clientService';

// Mock clientService
vi.mock('@/services/clientService', () => ({
  clientService: {
    createClient: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    Link: ({ children, to }: any) => <a href={to}>{children}</a>,
  };
});

describe('ClientCreate', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders create client form', () => {
    render(<ClientCreate />);

    expect(screen.getByRole('heading', { name: /create new client/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/client type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/last name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it('shows validation errors for required fields', async () => {
    const user = userEvent.setup();

    render(<ClientCreate />);

    const submitButton = screen.getByRole('button', { name: /create client/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/first name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/last name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    });
  });

  it('shows validation error for invalid email', async () => {
    const user = userEvent.setup();

    render(<ClientCreate />);

    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, 'invalid-email');

    const submitButton = screen.getByRole('button', { name: /create client/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/invalid email address/i)).toBeInTheDocument();
    });
  });

  it('creates individual client successfully', async () => {
    const user = userEvent.setup();

    vi.mocked(clientService.clientService.createClient).mockResolvedValue(mockClient);

    render(<ClientCreate />);

    // Fill in the form
    await user.type(screen.getByLabelText(/first name/i), 'Jane');
    await user.type(screen.getByLabelText(/last name/i), 'Smith');
    await user.type(screen.getByLabelText(/email/i), 'jane@example.com');
    await user.type(screen.getByLabelText(/phone/i), '+1234567890');

    const submitButton = screen.getByRole('button', { name: /create client/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(clientService.clientService.createClient).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'individual',
          first_name: 'Jane',
          last_name: 'Smith',
          email: 'jane@example.com',
          phone: '+1234567890',
        })
      );
    });

    expect(mockNavigate).toHaveBeenCalledWith(`/clients/${mockClient.id}`);
  });

  it('creates business client successfully', async () => {
    const user = userEvent.setup();

    const businessClient = {
      ...mockClient,
      type: 'business' as const,
      company_name: 'Acme Corp',
      tax_id: '12-3456789',
    };

    vi.mocked(clientService.clientService.createClient).mockResolvedValue(businessClient);

    render(<ClientCreate />);

    // Select business type
    const typeSelect = screen.getByLabelText(/client type/i);
    await user.selectOptions(typeSelect, 'business');

    // Fill in business fields
    await user.type(screen.getByLabelText(/company name/i), 'Acme Corp');
    await user.type(screen.getByLabelText(/first name/i), 'John');
    await user.type(screen.getByLabelText(/last name/i), 'Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@acme.com');
    await user.type(screen.getByLabelText(/tax id/i), '12-3456789');

    const submitButton = screen.getByRole('button', { name: /create client/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(clientService.clientService.createClient).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'business',
          company_name: 'Acme Corp',
          tax_id: '12-3456789',
        })
      );
    });
  });

  it('shows error message on creation failure', async () => {
    const user = userEvent.setup();

    vi.mocked(clientService.clientService.createClient).mockRejectedValue(
      new Error('Failed to create client')
    );

    render(<ClientCreate />);

    await user.type(screen.getByLabelText(/first name/i), 'Jane');
    await user.type(screen.getByLabelText(/last name/i), 'Smith');
    await user.type(screen.getByLabelText(/email/i), 'jane@example.com');

    const submitButton = screen.getByRole('button', { name: /create client/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/failed to create client/i)).toBeInTheDocument();
    });
  });

  it('fills in address fields', async () => {
    const user = userEvent.setup();

    vi.mocked(clientService.clientService.createClient).mockResolvedValue(mockClient);

    render(<ClientCreate />);

    await user.type(screen.getByLabelText(/first name/i), 'Jane');
    await user.type(screen.getByLabelText(/last name/i), 'Smith');
    await user.type(screen.getByLabelText(/email/i), 'jane@example.com');
    await user.type(screen.getByLabelText(/address line 1/i), '123 Main St');
    await user.type(screen.getByLabelText(/city/i), 'New York');
    await user.type(screen.getByLabelText(/state/i), 'NY');
    await user.type(screen.getByLabelText(/postal code/i), '10001');
    await user.type(screen.getByLabelText(/country/i), 'USA');

    const submitButton = screen.getByRole('button', { name: /create client/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(clientService.clientService.createClient).toHaveBeenCalledWith(
        expect.objectContaining({
          address_line1: '123 Main St',
          city: 'New York',
          state: 'NY',
          postal_code: '10001',
          country: 'USA',
        })
      );
    });
  });

  it('sets lifecycle stage', async () => {
    const user = userEvent.setup();

    vi.mocked(clientService.clientService.createClient).mockResolvedValue(mockClient);

    render(<ClientCreate />);

    await user.type(screen.getByLabelText(/first name/i), 'Jane');
    await user.type(screen.getByLabelText(/last name/i), 'Smith');
    await user.type(screen.getByLabelText(/email/i), 'jane@example.com');

    const stageSelect = screen.getByLabelText(/lifecycle stage/i);
    await user.selectOptions(stageSelect, 'customer');

    const submitButton = screen.getByRole('button', { name: /create client/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(clientService.clientService.createClient).toHaveBeenCalledWith(
        expect.objectContaining({
          lifecycle_stage: 'customer',
        })
      );
    });
  });

  it('has cancel button that navigates back', async () => {
    const user = userEvent.setup();

    render(<ClientCreate />);

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    expect(mockNavigate).toHaveBeenCalledWith('/clients');
  });

  it('disables submit button while loading', async () => {
    const user = userEvent.setup();

    vi.mocked(clientService.clientService.createClient).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000))
    );

    render(<ClientCreate />);

    await user.type(screen.getByLabelText(/first name/i), 'Jane');
    await user.type(screen.getByLabelText(/last name/i), 'Smith');
    await user.type(screen.getByLabelText(/email/i), 'jane@example.com');

    const submitButton = screen.getByRole('button', { name: /create client/i });
    await user.click(submitButton);

    expect(submitButton).toBeDisabled();
  });
});
