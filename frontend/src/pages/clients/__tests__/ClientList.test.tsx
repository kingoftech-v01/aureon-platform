/**
 * ClientList Page Tests
 * Aureon by Rhematek Solutions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/tests/test-utils';
import userEvent from '@testing-library/user-event';
import ClientList from '../ClientList';
import { mockClient, mockPaginatedResponse } from '@/tests/mocks/data';
import * as clientService from '@/services/clientService';

// Mock clientService
vi.mock('@/services/clientService', () => ({
  clientService: {
    getClients: vi.fn(),
    deleteClient: vi.fn(),
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

describe('ClientList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders client list page', async () => {
    vi.mocked(clientService.clientService.getClients).mockResolvedValue(
      mockPaginatedResponse([mockClient])
    );

    render(<ClientList />);

    expect(screen.getByRole('heading', { name: /clients/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });
  });

  it('displays loading skeleton while fetching', () => {
    vi.mocked(clientService.clientService.getClients).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<ClientList />);

    expect(screen.getByTestId('skeleton-table')).toBeInTheDocument();
  });

  it('displays empty state when no clients exist', async () => {
    vi.mocked(clientService.clientService.getClients).mockResolvedValue(
      mockPaginatedResponse([])
    );

    render(<ClientList />);

    await waitFor(() => {
      expect(screen.getByText(/no clients found/i)).toBeInTheDocument();
    });
  });

  it('filters clients by search query', async () => {
    const user = userEvent.setup();

    vi.mocked(clientService.clientService.getClients).mockResolvedValue(
      mockPaginatedResponse([mockClient])
    );

    render(<ClientList />);

    const searchInput = screen.getByPlaceholderText(/search clients/i);
    await user.type(searchInput, 'Jane');

    const searchButton = screen.getByRole('button', { name: /search/i });
    await user.click(searchButton);

    await waitFor(() => {
      expect(clientService.clientService.getClients).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
        }),
        expect.objectContaining({
          search: 'Jane',
        }),
        expect.any(Object)
      );
    });
  });

  it('filters clients by lifecycle stage', async () => {
    const user = userEvent.setup();

    vi.mocked(clientService.clientService.getClients).mockResolvedValue(
      mockPaginatedResponse([mockClient])
    );

    render(<ClientList />);

    const stageFilter = screen.getByRole('combobox', { name: /lifecycle stage/i });
    await user.selectOptions(stageFilter, 'customer');

    await waitFor(() => {
      expect(clientService.clientService.getClients).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          lifecycle_stage: 'customer',
        }),
        expect.any(Object)
      );
    });
  });

  it('filters clients by type', async () => {
    const user = userEvent.setup();

    vi.mocked(clientService.clientService.getClients).mockResolvedValue(
      mockPaginatedResponse([mockClient])
    );

    render(<ClientList />);

    const typeFilter = screen.getByRole('combobox', { name: /client type/i });
    await user.selectOptions(typeFilter, 'business');

    await waitFor(() => {
      expect(clientService.clientService.getClients).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          type: 'business',
        }),
        expect.any(Object)
      );
    });
  });

  it('navigates to client detail when row is clicked', async () => {
    const user = userEvent.setup();

    vi.mocked(clientService.clientService.getClients).mockResolvedValue(
      mockPaginatedResponse([mockClient])
    );

    render(<ClientList />);

    await waitFor(() => {
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });

    const row = screen.getByText('Jane Smith').closest('tr');
    await user.click(row!);

    expect(mockNavigate).toHaveBeenCalledWith(`/clients/${mockClient.id}`);
  });

  it('navigates to create client page when button is clicked', async () => {
    const user = userEvent.setup();

    vi.mocked(clientService.clientService.getClients).mockResolvedValue(
      mockPaginatedResponse([])
    );

    render(<ClientList />);

    const createButton = screen.getByRole('button', { name: /new client/i });
    expect(createButton).toBeInTheDocument();
  });

  it('handles pagination', async () => {
    const user = userEvent.setup();
    const clients = Array.from({ length: 20 }, (_, i) => ({
      ...mockClient,
      id: `${i + 1}`,
      first_name: `Client ${i + 1}`,
    }));

    vi.mocked(clientService.clientService.getClients).mockResolvedValue({
      count: 20,
      next: 'http://api/clients/?page=2',
      previous: null,
      results: clients.slice(0, 10),
    });

    render(<ClientList />);

    await waitFor(() => {
      expect(screen.getByText(/page 1 of 2/i)).toBeInTheDocument();
    });

    const nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    await waitFor(() => {
      expect(clientService.clientService.getClients).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2,
        }),
        expect.any(Object),
        expect.any(Object)
      );
    });
  });

  it('changes page size', async () => {
    const user = userEvent.setup();

    vi.mocked(clientService.clientService.getClients).mockResolvedValue(
      mockPaginatedResponse([mockClient])
    );

    render(<ClientList />);

    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: /page size/i })).toBeInTheDocument();
    });

    const pageSizeSelect = screen.getByRole('combobox', { name: /page size/i });
    await user.selectOptions(pageSizeSelect, '25');

    await waitFor(() => {
      expect(clientService.clientService.getClients).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          pageSize: 25,
        }),
        expect.any(Object),
        expect.any(Object)
      );
    });
  });

  it('sorts by column', async () => {
    const user = userEvent.setup();

    vi.mocked(clientService.clientService.getClients).mockResolvedValue(
      mockPaginatedResponse([mockClient])
    );

    render(<ClientList />);

    await waitFor(() => {
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });

    const nameHeader = screen.getByRole('columnheader', { name: /name/i });
    await user.click(nameHeader);

    await waitFor(() => {
      expect(clientService.clientService.getClients).toHaveBeenCalledWith(
        expect.any(Object),
        expect.any(Object),
        expect.objectContaining({
          field: 'first_name',
          direction: 'asc',
        })
      );
    });
  });
});
