/**
 * Input Component Tests
 * Aureon by Rhematek Solutions
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/tests/test-utils';
import userEvent from '@testing-library/user-event';
import Input from '../Input';

describe('Input', () => {
  it('renders with label', () => {
    render(<Input label="Username" />);
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
  });

  it('renders with placeholder', () => {
    render(<Input placeholder="Enter your name" />);
    expect(screen.getByPlaceholderText(/enter your name/i)).toBeInTheDocument();
  });

  it('handles value changes', async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();

    render(<Input onChange={handleChange} />);
    const input = screen.getByRole('textbox');

    await user.type(input, 'Hello');

    expect(handleChange).toHaveBeenCalled();
    expect(input).toHaveValue('Hello');
  });

  it('shows error message', () => {
    render(<Input error="This field is required" />);
    expect(screen.getByText(/this field is required/i)).toBeInTheDocument();
  });

  it('applies error styles when error exists', () => {
    render(<Input error="Error message" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-red-500');
  });

  it('renders as disabled', () => {
    render(<Input disabled />);
    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
  });

  it('renders with left icon', () => {
    const LeftIcon = <svg data-testid="left-icon">Icon</svg>;
    render(<Input leftIcon={LeftIcon} />);
    expect(screen.getByTestId('left-icon')).toBeInTheDocument();
  });

  it('renders with right icon', () => {
    const RightIcon = <svg data-testid="right-icon">Icon</svg>;
    render(<Input rightIcon={RightIcon} />);
    expect(screen.getByTestId('right-icon')).toBeInTheDocument();
  });

  it('renders with helper text', () => {
    render(<Input helperText="Must be at least 8 characters" />);
    expect(screen.getByText(/must be at least 8 characters/i)).toBeInTheDocument();
  });

  it('supports different input types', () => {
    const { rerender } = render(<Input type="email" />);
    let input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('type', 'email');

    rerender(<Input type="password" />);
    input = screen.getByLabelText(/password/i) || document.querySelector('input[type="password"]')!;
    expect(input).toHaveAttribute('type', 'password');
  });

  it('applies required attribute', () => {
    render(<Input required label="Required Field" />);
    const input = screen.getByRole('textbox');
    expect(input).toBeRequired();
  });
});
