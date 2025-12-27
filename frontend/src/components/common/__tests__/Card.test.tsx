/**
 * Card Component Tests
 * Aureon by Rhematek Solutions
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@/tests/test-utils';
import Card, { CardHeader, CardTitle, CardContent, CardFooter } from '../Card';

describe('Card', () => {
  it('renders children correctly', () => {
    render(<Card>Card Content</Card>);
    expect(screen.getByText(/card content/i)).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<Card className="custom-class">Content</Card>);
    const card = screen.getByText(/content/i).parentElement;
    expect(card).toHaveClass('custom-class');
  });

  it('renders with padding by default', () => {
    render(<Card>Content</Card>);
    const card = screen.getByText(/content/i).parentElement;
    expect(card).toHaveClass('p-6');
  });

  it('renders without padding when noPadding is true', () => {
    render(<Card noPadding>Content</Card>);
    const card = screen.getByText(/content/i).parentElement;
    expect(card).not.toHaveClass('p-6');
  });
});

describe('CardHeader', () => {
  it('renders children correctly', () => {
    render(<CardHeader>Header Content</CardHeader>);
    expect(screen.getByText(/header content/i)).toBeInTheDocument();
  });

  it('applies header styles', () => {
    render(<CardHeader>Header</CardHeader>);
    const header = screen.getByText(/header/i);
    expect(header).toHaveClass('border-b');
  });
});

describe('CardTitle', () => {
  it('renders title correctly', () => {
    render(<CardTitle>Card Title</CardTitle>);
    expect(screen.getByText(/card title/i)).toBeInTheDocument();
  });

  it('applies title styles', () => {
    render(<CardTitle>Title</CardTitle>);
    const title = screen.getByText(/title/i);
    expect(title).toHaveClass('text-xl', 'font-semibold');
  });
});

describe('CardContent', () => {
  it('renders content correctly', () => {
    render(<CardContent>Content Area</CardContent>);
    expect(screen.getByText(/content area/i)).toBeInTheDocument();
  });

  it('applies content styles', () => {
    render(<CardContent>Content</CardContent>);
    const content = screen.getByText(/content/i);
    expect(content).toHaveClass('p-6');
  });
});

describe('CardFooter', () => {
  it('renders footer correctly', () => {
    render(<CardFooter>Footer Content</CardFooter>);
    expect(screen.getByText(/footer content/i)).toBeInTheDocument();
  });

  it('applies footer styles', () => {
    render(<CardFooter>Footer</CardFooter>);
    const footer = screen.getByText(/footer/i);
    expect(footer).toHaveClass('border-t');
  });
});

describe('Card Composition', () => {
  it('renders complete card with all parts', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Test Card</CardTitle>
        </CardHeader>
        <CardContent>Card body content</CardContent>
        <CardFooter>Card footer</CardFooter>
      </Card>
    );

    expect(screen.getByText(/test card/i)).toBeInTheDocument();
    expect(screen.getByText(/card body content/i)).toBeInTheDocument();
    expect(screen.getByText(/card footer/i)).toBeInTheDocument();
  });
});
