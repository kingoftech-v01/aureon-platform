# Contributing to Aureon

First off, thank you for considering contributing to Aureon! It's people like you that make Aureon such a great tool for automating financial workflows.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

---

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, screenshots, etc.)
- **Describe the behavior you observed** and what you expected
- **Include environment details** (OS, Python version, Django version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **List any alternative solutions** you've considered

### Your First Code Contribution

Unsure where to begin? Look for issues tagged with:
- `good-first-issue` - Simple issues perfect for beginners
- `help-wanted` - Issues that need attention

### Pull Requests

- Fill in the required template
- Follow the coding standards
- Include tests for new functionality
- Update documentation as needed
- Ensure all tests pass

---

## Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+
- Docker and Docker Compose

### Local Setup

1. **Fork and clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/aureon.git
cd aureon
```

2. **Create a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
cd frontend && npm install
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your local configuration
```

5. **Run database migrations**
```bash
python manage.py migrate
```

6. **Create a superuser**
```bash
python manage.py createsuperuser
```

7. **Run the development server**
```bash
python manage.py runserver
```

8. **Run Celery worker (in another terminal)**
```bash
celery -A config worker -l info
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest apps/contracts/tests/test_models.py
```

---

## Pull Request Process

1. **Create a feature branch** from `develop`
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes** following our coding standards

3. **Write or update tests** for your changes

4. **Run the test suite** and ensure all tests pass
```bash
pytest
```

5. **Run linters and formatters**
```bash
black .
isort .
flake8 .
mypy .
```

6. **Commit your changes** with clear, descriptive messages
```bash
git commit -m "Add feature: description of your feature"
```

7. **Push to your fork**
```bash
git push origin feature/your-feature-name
```

8. **Create a Pull Request** on GitHub

### Pull Request Guidelines

- **Title**: Use a clear, descriptive title
- **Description**: Explain what changes you made and why
- **Link related issues**: Use "Fixes #123" or "Relates to #456"
- **Screenshots**: Include screenshots for UI changes
- **Tests**: Ensure all tests pass and add new tests for new features
- **Documentation**: Update relevant documentation

### Code Review Process

- At least one maintainer must approve the PR
- All CI checks must pass
- No merge conflicts
- Code meets our quality standards

---

## Coding Standards

### Python (Backend)

- Follow **PEP 8** style guide
- Use **Black** for code formatting (line length: 100)
- Use **isort** for import ordering
- Use **type hints** for all function signatures
- Write **docstrings** for all classes and functions (Google style)

Example:
```python
from typing import List, Optional

def create_invoice(
    client_id: int,
    amount: float,
    due_date: Optional[str] = None
) -> Invoice:
    """
    Create a new invoice for a client.

    Args:
        client_id: The ID of the client
        amount: The invoice amount
        due_date: Optional due date (ISO format)

    Returns:
        The created Invoice instance

    Raises:
        ValueError: If amount is negative
    """
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    # Implementation
```

### TypeScript/React (Frontend)

- Follow **Airbnb React/TypeScript** style guide
- Use **Prettier** for code formatting
- Use **ESLint** for linting
- Use **functional components** with hooks
- Write **TypeScript interfaces** for all props

Example:
```typescript
interface InvoiceProps {
  invoiceId: number;
  clientName: string;
  amount: number;
  onPay: (invoiceId: number) => void;
}

export const Invoice: React.FC<InvoiceProps> = ({
  invoiceId,
  clientName,
  amount,
  onPay
}) => {
  return (
    <div className="invoice">
      <h2>{clientName}</h2>
      <p>${amount.toFixed(2)}</p>
      <button onClick={() => onPay(invoiceId)}>Pay Now</button>
    </div>
  );
};
```

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests

Format:
```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```
feat: Add automated invoice generation

- Implement invoice generation from contract milestones
- Add Celery task for scheduled invoice creation
- Include PDF generation with WeasyPrint

Fixes #123
```

---

## Testing Guidelines

### Backend Tests

- Write tests using **pytest**
- Aim for **>80% code coverage**
- Use **factories** for test data (factory_boy)
- Mock external services (Stripe, email, etc.)

Test structure:
```python
# apps/invoicing/tests/test_models.py
import pytest
from apps.invoicing.models import Invoice

@pytest.mark.django_db
class TestInvoiceModel:
    def test_invoice_creation(self, invoice_factory):
        """Test that an invoice can be created."""
        invoice = invoice_factory()
        assert invoice.pk is not None
        assert invoice.status == "draft"

    def test_invoice_total_calculation(self, invoice_factory):
        """Test that invoice total is calculated correctly."""
        invoice = invoice_factory(subtotal=100.00, tax_rate=0.2)
        assert invoice.total == 120.00
```

### Frontend Tests

- Write tests using **Jest** and **React Testing Library**
- Test user interactions and component behavior
- Mock API calls

Example:
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Invoice } from './Invoice';

describe('Invoice Component', () => {
  it('renders invoice details', () => {
    render(<Invoice invoiceId={1} clientName="Acme Corp" amount={100} onPay={jest.fn()} />);
    expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    expect(screen.getByText('$100.00')).toBeInTheDocument();
  });

  it('calls onPay when button clicked', () => {
    const onPay = jest.fn();
    render(<Invoice invoiceId={1} clientName="Acme Corp" amount={100} onPay={onPay} />);
    fireEvent.click(screen.getByText('Pay Now'));
    expect(onPay).toHaveBeenCalledWith(1);
  });
});
```

---

## Documentation

### Code Documentation

- All public functions and classes must have docstrings
- Use Google-style docstrings for Python
- Use JSDoc comments for TypeScript
- Include examples where helpful

### Project Documentation

- Update README.md for significant features
- Add or update docs in the `/docs` directory
- Include API endpoint documentation
- Document environment variables and configuration

---

## Questions?

Feel free to contact us:
- Open an issue on GitHub
- Email: stephane@rhematek-solutions.com
- Community Forum: https://community.aureon.rhematek-solutions.com

Thank you for contributing to Aureon!

---

**Aureon** - From Signature to Cash, Everything Runs Automatically.
© 2025 Rhematek Solutions
