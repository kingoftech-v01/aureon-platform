/**
 * Select Component Tests
 * Aureon by Rhematek Solutions
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/tests/test-utils';
import userEvent from '@testing-library/user-event';
import Select from '../Select';

describe('Select', () => {
  const options = [
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
    { value: 'option3', label: 'Option 3' },
  ];

  it('renders with label', () => {
    render(<Select label="Choose an option" options={options} />);
    expect(screen.getByLabelText(/choose an option/i)).toBeInTheDocument();
  });

  it('renders all options', () => {
    render(<Select options={options} />);
    const select = screen.getByRole('combobox');

    expect(select).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /option 1/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /option 2/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /option 3/i })).toBeInTheDocument();
  });

  it('handles value changes', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();

    render(<Select options={options} onChange={onChange} />);
    const select = screen.getByRole('combobox');

    await user.selectOptions(select, 'option2');

    expect(onChange).toHaveBeenCalled();
    expect(select).toHaveValue('option2');
  });

  it('shows error message', () => {
    render(<Select options={options} error="This field is required" />);
    expect(screen.getByText(/this field is required/i)).toBeInTheDocument();
  });

  it('applies error styles when error exists', () => {
    render(<Select options={options} error="Error message" />);
    const select = screen.getByRole('combobox');
    expect(select).toHaveClass('border-red-500');
  });

  it('renders as disabled', () => {
    render(<Select options={options} disabled />);
    const select = screen.getByRole('combobox');
    expect(select).toBeDisabled();
  });

  it('sets default value', () => {
    render(<Select options={options} value="option2" />);
    const select = screen.getByRole('combobox');
    expect(select).toHaveValue('option2');
  });

  it('renders with placeholder', () => {
    const optionsWithPlaceholder = [
      { value: '', label: 'Select an option...' },
      ...options,
    ];
    render(<Select options={optionsWithPlaceholder} value="" />);
    expect(screen.getByRole('option', { name: /select an option/i })).toBeInTheDocument();
  });

  it('applies required attribute', () => {
    render(<Select options={options} required label="Required Field" />);
    const select = screen.getByRole('combobox');
    expect(select).toBeRequired();
  });

  it('accepts custom className', () => {
    render(<Select options={options} className="custom-class" />);
    const select = screen.getByRole('combobox');
    expect(select).toHaveClass('custom-class');
  });
});
