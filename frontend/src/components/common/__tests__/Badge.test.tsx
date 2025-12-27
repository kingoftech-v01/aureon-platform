/**
 * Badge Component Tests
 * Aureon by Rhematek Solutions
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@/tests/test-utils';
import Badge from '../Badge';

describe('Badge', () => {
  it('renders children correctly', () => {
    render(<Badge>Test Badge</Badge>);
    expect(screen.getByText(/test badge/i)).toBeInTheDocument();
  });

  it('applies variant styles correctly', () => {
    const { rerender } = render(<Badge variant="primary">Primary</Badge>);
    let badge = screen.getByText(/primary/i);
    expect(badge).toHaveClass('bg-primary-100', 'text-primary-800');

    rerender(<Badge variant="success">Success</Badge>);
    badge = screen.getByText(/success/i);
    expect(badge).toHaveClass('bg-green-100', 'text-green-800');

    rerender(<Badge variant="danger">Danger</Badge>);
    badge = screen.getByText(/danger/i);
    expect(badge).toHaveClass('bg-red-100', 'text-red-800');

    rerender(<Badge variant="warning">Warning</Badge>);
    badge = screen.getByText(/warning/i);
    expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800');
  });

  it('applies size styles correctly', () => {
    const { rerender } = render(<Badge size="sm">Small</Badge>);
    let badge = screen.getByText(/small/i);
    expect(badge).toHaveClass('text-xs', 'px-2', 'py-0.5');

    rerender(<Badge size="lg">Large</Badge>);
    badge = screen.getByText(/large/i);
    expect(badge).toHaveClass('text-base', 'px-4', 'py-1.5');
  });

  it('accepts custom className', () => {
    render(<Badge className="custom-class">Custom</Badge>);
    const badge = screen.getByText(/custom/i);
    expect(badge).toHaveClass('custom-class');
  });

  it('renders with icon', () => {
    const Icon = () => <svg data-testid="badge-icon">Icon</svg>;
    render(
      <Badge>
        <Icon />
        With Icon
      </Badge>
    );
    expect(screen.getByTestId('badge-icon')).toBeInTheDocument();
    expect(screen.getByText(/with icon/i)).toBeInTheDocument();
  });

  it('renders with default variant', () => {
    render(<Badge>Default</Badge>);
    const badge = screen.getByText(/default/i);
    expect(badge).toHaveClass('bg-gray-100', 'text-gray-800');
  });
});
