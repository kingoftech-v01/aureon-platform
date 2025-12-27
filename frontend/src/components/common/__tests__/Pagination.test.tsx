/**
 * Pagination Component Tests
 * Aureon by Rhematek Solutions
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/tests/test-utils';
import userEvent from '@testing-library/user-event';
import Pagination from '../Pagination';

describe('Pagination', () => {
  const defaultProps = {
    currentPage: 1,
    totalPages: 5,
    onPageChange: vi.fn(),
    totalItems: 50,
    pageSize: 10,
    onPageSizeChange: vi.fn(),
  };

  it('renders pagination controls', () => {
    render(<Pagination {...defaultProps} />);
    expect(screen.getByText(/page 1 of 5/i)).toBeInTheDocument();
  });

  it('shows total items count', () => {
    render(<Pagination {...defaultProps} />);
    expect(screen.getByText(/showing 1-10 of 50/i)).toBeInTheDocument();
  });

  it('disables previous button on first page', () => {
    render(<Pagination {...defaultProps} currentPage={1} />);
    const prevButton = screen.getByRole('button', { name: /previous/i });
    expect(prevButton).toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(<Pagination {...defaultProps} currentPage={5} />);
    const nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).toBeDisabled();
  });

  it('calls onPageChange when next is clicked', async () => {
    const onPageChange = vi.fn();
    const user = userEvent.setup();

    render(<Pagination {...defaultProps} onPageChange={onPageChange} />);
    const nextButton = screen.getByRole('button', { name: /next/i });

    await user.click(nextButton);

    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('calls onPageChange when previous is clicked', async () => {
    const onPageChange = vi.fn();
    const user = userEvent.setup();

    render(<Pagination {...defaultProps} currentPage={3} onPageChange={onPageChange} />);
    const prevButton = screen.getByRole('button', { name: /previous/i });

    await user.click(prevButton);

    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('renders page size selector', () => {
    render(<Pagination {...defaultProps} />);
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('calls onPageSizeChange when page size changes', async () => {
    const onPageSizeChange = vi.fn();
    const user = userEvent.setup();

    render(<Pagination {...defaultProps} onPageSizeChange={onPageSizeChange} />);
    const select = screen.getByRole('combobox');

    await user.selectOptions(select, '25');

    expect(onPageSizeChange).toHaveBeenCalledWith(25);
  });

  it('calculates correct item range for middle page', () => {
    render(<Pagination {...defaultProps} currentPage={3} />);
    expect(screen.getByText(/showing 21-30 of 50/i)).toBeInTheDocument();
  });

  it('calculates correct item range for last page', () => {
    render(<Pagination {...defaultProps} currentPage={5} totalItems={47} />);
    expect(screen.getByText(/showing 41-47 of 47/i)).toBeInTheDocument();
  });
});
