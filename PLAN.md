# Aureon Platform - Comprehensive Feature & Frontend Plan

## Overview

This plan covers 4 phases:
1. **Phase 1**: New feature APIs (models, serializers, views, URLs) + tests
2. **Phase 2**: URL restructuring (api/ vs frontend/ patterns) + views_api.py / views_frontend.py split
3. **Phase 3**: Frontend views (Django template views with context, no HTML templates)
4. **Phase 4**: Tests for frontend views + ensure 99%+ coverage

---

## Phase 1: New Feature Backend APIs

### 1A. New Django App: `apps/workflows/` — Automated Workflows & Triggers

**Models:**
- **Workflow**
  - id (UUID), name, description, is_active (bool)
  - trigger_type: choices (CONTRACT_SIGNED, INVOICE_CREATED, INVOICE_OVERDUE, INVOICE_PAID, PAYMENT_RECEIVED, PAYMENT_FAILED, CLIENT_CREATED, CLIENT_UPDATED, MILESTONE_COMPLETED, SUBSCRIPTION_CANCELLED, MANUAL)
  - trigger_config (JSONField) — e.g., `{"days_overdue": 7}` for delayed triggers
  - owner (FK→User)
  - created_at, updated_at

- **WorkflowAction**
  - id (UUID), workflow (FK→Workflow)
  - action_type: choices (SEND_EMAIL, SEND_NOTIFICATION, UPDATE_CLIENT_STAGE, CREATE_TASK, CREATE_INVOICE, WEBHOOK_CALL)
  - action_config (JSONField) — e.g., `{"template_id": "...", "to": "client"}` or `{"url": "...", "method": "POST"}`
  - order (IntegerField)
  - delay_minutes (IntegerField, default=0) — delay before executing
  - is_active (bool)
  - created_at, updated_at

- **WorkflowExecution**
  - id (UUID), workflow (FK→Workflow)
  - status: choices (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
  - triggered_by (FK→User, optional)
  - trigger_data (JSONField) — context that triggered the execution
  - started_at, completed_at, error_message
  - created_at

- **WorkflowActionExecution**
  - id (UUID), execution (FK→WorkflowExecution), action (FK→WorkflowAction)
  - status: choices (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED)
  - result_data (JSONField)
  - started_at, completed_at, error_message

**Serializers:**
- WorkflowListSerializer, WorkflowDetailSerializer, WorkflowCreateUpdateSerializer
- WorkflowActionSerializer
- WorkflowExecutionSerializer, WorkflowActionExecutionSerializer

**Views (API):**
- WorkflowViewSet (CRUD + custom actions: activate, deactivate, execute, executions)
- WorkflowActionViewSet (CRUD, nested under workflow)
- WorkflowExecutionViewSet (list, retrieve — read-only)

**URLs:**
- `api/workflows/` — Workflow CRUD
- `api/workflows/{id}/actions/` — Action CRUD
- `api/workflows/{id}/execute/` — Manual trigger
- `api/workflows/{id}/executions/` — Execution history
- `api/workflow-executions/` — All executions (filterable)

---

### 1B. New Django App: `apps/tasks/` — Task & Activity Management

**Models:**
- **Task**
  - id (UUID), title, description
  - status: choices (TODO, IN_PROGRESS, DONE, CANCELLED)
  - priority: choices (LOW, MEDIUM, HIGH, URGENT)
  - due_date (DateTimeField, optional)
  - assigned_to (FK→User, optional)
  - created_by (FK→User)
  - client (FK→Client, optional)
  - contract (FK→Contract, optional)
  - invoice (FK→Invoice, optional)
  - tags (JSONField, default=[])
  - completed_at (DateTimeField, optional)
  - created_at, updated_at

- **TaskComment**
  - id (UUID), task (FK→Task)
  - author (FK→User)
  - content (TextField)
  - created_at, updated_at

**Serializers:**
- TaskListSerializer, TaskDetailSerializer, TaskCreateUpdateSerializer
- TaskCommentSerializer
- TaskStatsSerializer

**Views (API):**
- TaskViewSet (CRUD + custom actions: complete, reopen, stats, comments)
- TaskCommentViewSet (CRUD)

**URLs:**
- `api/tasks/` — Task CRUD
- `api/tasks/{id}/complete/` — Mark complete
- `api/tasks/{id}/reopen/` — Reopen
- `api/tasks/{id}/comments/` — Comments
- `api/tasks/stats/` — Task statistics
- `api/task-comments/` — All comments (filterable)

---

### 1C. New Django App: `apps/emails/` — Built-in Email System

**Models:**
- **EmailAccount**
  - id (UUID), user (FK→User)
  - email_address, display_name
  - provider: choices (SMTP, GMAIL, OUTLOOK, SES)
  - config (JSONField) — SMTP settings, API keys
  - is_active (bool), is_default (bool)
  - created_at, updated_at

- **EmailMessage**
  - id (UUID), account (FK→EmailAccount)
  - direction: choices (INBOUND, OUTBOUND)
  - from_email, to_emails (JSONField — list of emails)
  - cc_emails (JSONField), bcc_emails (JSONField)
  - subject, body_text, body_html
  - status: choices (DRAFT, QUEUED, SENT, DELIVERED, FAILED, RECEIVED)
  - client (FK→Client, optional) — auto-linked
  - contract (FK→Contract, optional)
  - invoice (FK→Invoice, optional)
  - message_id (CharField, unique, optional) — email Message-ID header
  - in_reply_to (FK→self, optional) — threading
  - thread_id (CharField, optional)
  - is_read (bool, default=False)
  - opened_at (DateTimeField, optional)
  - opened_count (IntegerField, default=0)
  - sent_at, received_at
  - metadata (JSONField)
  - created_at, updated_at

- **EmailAttachment**
  - id (UUID), email (FK→EmailMessage)
  - file (FileField), file_name, file_size, file_type
  - created_at

- **EmailTemplate**
  - id (UUID), name, subject, body_text, body_html
  - category: choices (GENERAL, FOLLOW_UP, INVOICE, CONTRACT, REMINDER, WELCOME)
  - available_variables (JSONField)
  - is_active (bool)
  - owner (FK→User)
  - created_at, updated_at

**Serializers:**
- EmailAccountSerializer
- EmailMessageListSerializer, EmailMessageDetailSerializer, EmailMessageCreateSerializer
- EmailAttachmentSerializer
- EmailTemplateSerializer

**Views (API):**
- EmailAccountViewSet (CRUD + custom actions: set_default, test_connection)
- EmailMessageViewSet (CRUD + custom actions: send, mark_read, mark_unread, reply, forward, stats)
- EmailAttachmentViewSet (list, create, retrieve, delete)
- EmailTemplateViewSet (CRUD + custom actions: preview, render)

**URLs:**
- `api/email-accounts/` — Account CRUD
- `api/emails/` — Email message CRUD
- `api/emails/{id}/send/` — Send draft
- `api/emails/{id}/reply/` — Reply
- `api/emails/{id}/forward/` — Forward
- `api/emails/stats/` — Email statistics
- `api/email-attachments/` — Attachment management
- `api/email-templates/` — Template CRUD

---

### 1D. New Django App: `apps/calendar_app/` — Calendar & Scheduling

**Models:**
- **CalendarEvent**
  - id (UUID), title, description
  - event_type: choices (MEETING, DEADLINE, MILESTONE, FOLLOW_UP, OTHER)
  - start_time (DateTimeField), end_time (DateTimeField)
  - all_day (bool, default=False)
  - location (CharField, optional)
  - video_link (URLField, optional)
  - organizer (FK→User)
  - client (FK→Client, optional)
  - contract (FK→Contract, optional)
  - recurrence_rule (CharField, optional) — RRULE string
  - reminder_minutes (IntegerField, default=30)
  - status: choices (SCHEDULED, CANCELLED, COMPLETED)
  - external_id (CharField, optional) — Google/Outlook calendar event ID
  - color (CharField, optional) — hex color code
  - metadata (JSONField)
  - created_at, updated_at

- **EventAttendee**
  - id (UUID), event (FK→CalendarEvent)
  - user (FK→User, optional)
  - email (EmailField)
  - name (CharField, optional)
  - response_status: choices (PENDING, ACCEPTED, DECLINED, TENTATIVE)
  - created_at

- **BookingLink**
  - id (UUID), owner (FK→User)
  - slug (SlugField, unique)
  - title, description
  - duration_minutes (IntegerField)
  - available_days (JSONField) — e.g., [1,2,3,4,5] for weekdays
  - available_start_time (TimeField)
  - available_end_time (TimeField)
  - buffer_minutes (IntegerField, default=0) — gap between bookings
  - max_bookings_per_day (IntegerField, optional)
  - is_active (bool)
  - created_at, updated_at

- **Booking**
  - id (UUID), booking_link (FK→BookingLink)
  - event (OneToOne→CalendarEvent)
  - booker_name, booker_email
  - notes (TextField, optional)
  - status: choices (CONFIRMED, CANCELLED, COMPLETED, NO_SHOW)
  - confirmation_token (CharField, unique)
  - cancelled_at (DateTimeField, optional)
  - created_at

**Serializers:**
- CalendarEventListSerializer, CalendarEventDetailSerializer, CalendarEventCreateUpdateSerializer
- EventAttendeeSerializer
- BookingLinkSerializer, BookingLinkCreateUpdateSerializer
- BookingSerializer, BookingCreateSerializer

**Views (API):**
- CalendarEventViewSet (CRUD + custom actions: cancel, complete, attendees)
- EventAttendeeViewSet (CRUD)
- BookingLinkViewSet (CRUD + custom actions: availability)
- BookingViewSet (list, create, retrieve + custom actions: cancel, confirm)

**URLs:**
- `api/calendar/events/` — Event CRUD
- `api/calendar/events/{id}/cancel/` — Cancel event
- `api/calendar/events/{id}/attendees/` — Attendees
- `api/calendar/attendees/` — Attendee CRUD
- `api/calendar/booking-links/` — Booking link CRUD
- `api/calendar/booking-links/{slug}/availability/` — Available slots
- `api/calendar/bookings/` — Booking list/create
- `api/calendar/bookings/{id}/cancel/` — Cancel booking

---

### 1E. New Django App: `apps/proposals/` — Proposal Builder

**Models:**
- **Proposal**
  - id (UUID), proposal_number (auto-generated, PRP-00001)
  - client (FK→Client)
  - title, description (rich text)
  - status: choices (DRAFT, SENT, VIEWED, ACCEPTED, DECLINED, EXPIRED, CONVERTED)
  - valid_until (DateField)
  - total_value (DecimalField)
  - currency (CharField, default=USD)
  - owner (FK→User)
  - contract (FK→Contract, optional) — linked after conversion
  - sent_at, viewed_at, accepted_at, declined_at
  - client_message (TextField, optional) — client's response note
  - signature (TextField, optional) — client acceptance signature
  - pdf_file (FileField, optional)
  - metadata (JSONField)
  - created_at, updated_at

- **ProposalSection**
  - id (UUID), proposal (FK→Proposal)
  - title, content (rich text)
  - order (IntegerField)
  - section_type: choices (OVERVIEW, SCOPE, TIMELINE, PRICING, TERMS, CUSTOM)
  - created_at, updated_at

- **ProposalPricingOption**
  - id (UUID), proposal (FK→Proposal)
  - name (CharField) — e.g., "Basic", "Standard", "Premium"
  - description
  - price (DecimalField)
  - is_recommended (bool, default=False)
  - features (JSONField) — list of included features
  - order (IntegerField)
  - created_at, updated_at

- **ProposalActivity**
  - id (UUID), proposal (FK→Proposal)
  - activity_type: choices (CREATED, SENT, VIEWED, ACCEPTED, DECLINED, EDITED, CONVERTED)
  - description
  - user (FK→User, optional)
  - ip_address (GenericIPAddressField, optional)
  - metadata (JSONField)
  - created_at

**Serializers:**
- ProposalListSerializer, ProposalDetailSerializer, ProposalCreateUpdateSerializer
- ProposalSectionSerializer
- ProposalPricingOptionSerializer
- ProposalActivitySerializer
- ProposalStatsSerializer

**Views (API):**
- ProposalViewSet (CRUD + custom actions: send, accept, decline, convert_to_contract, duplicate, stats, activities)
- ProposalSectionViewSet (CRUD)
- ProposalPricingOptionViewSet (CRUD)

**URLs:**
- `api/proposals/` — Proposal CRUD
- `api/proposals/{id}/send/` — Send to client
- `api/proposals/{id}/accept/` — Client accepts
- `api/proposals/{id}/decline/` — Client declines
- `api/proposals/{id}/convert/` — Convert to contract
- `api/proposals/{id}/duplicate/` — Clone proposal
- `api/proposals/{id}/activities/` — Activity log
- `api/proposals/stats/` — Proposal statistics
- `api/proposal-sections/` — Section CRUD
- `api/proposal-pricing-options/` — Pricing option CRUD

---

### 1F. New Django App: `apps/expenses/` — Expense Tracking

**Models:**
- **ExpenseCategory**
  - id (UUID), name, description, color (hex)
  - is_active (bool, default=True)
  - created_at, updated_at

- **Expense**
  - id (UUID), description, amount (DecimalField), currency
  - category (FK→ExpenseCategory, optional)
  - expense_date (DateField)
  - client (FK→Client, optional) — billable expense
  - contract (FK→Contract, optional)
  - invoice (FK→Invoice, optional) — linked when invoiced
  - is_billable (bool, default=False)
  - is_invoiced (bool, default=False)
  - receipt_file (FileField, optional)
  - receipt_number (CharField, optional)
  - vendor (CharField, optional)
  - payment_method: choices (CARD, CASH, BANK_TRANSFER, OTHER)
  - status: choices (PENDING, APPROVED, REJECTED, INVOICED)
  - submitted_by (FK→User)
  - approved_by (FK→User, optional)
  - approved_at (DateTimeField, optional)
  - notes (TextField, optional)
  - tags (JSONField, default=[])
  - metadata (JSONField)
  - created_at, updated_at

**Serializers:**
- ExpenseCategorySerializer
- ExpenseListSerializer, ExpenseDetailSerializer, ExpenseCreateUpdateSerializer
- ExpenseStatsSerializer

**Views (API):**
- ExpenseCategoryViewSet (CRUD)
- ExpenseViewSet (CRUD + custom actions: approve, reject, mark_billable, mark_invoiced, stats)

**URLs:**
- `api/expense-categories/` — Category CRUD
- `api/expenses/` — Expense CRUD
- `api/expenses/{id}/approve/` — Approve expense
- `api/expenses/{id}/reject/` — Reject expense
- `api/expenses/stats/` — Expense statistics

---

### 1G. New Django App: `apps/ai_assistant/` — AI Assistant

**Models:**
- **AISuggestion**
  - id (UUID)
  - suggestion_type: choices (FOLLOW_UP, CONTRACT_DRAFT, INVOICE_REMINDER, CASH_FLOW, CLIENT_INSIGHT, PRICING)
  - title, description, detail (JSONField)
  - priority: choices (LOW, MEDIUM, HIGH)
  - status: choices (PENDING, ACCEPTED, DISMISSED, EXPIRED)
  - user (FK→User)
  - client (FK→Client, optional)
  - contract (FK→Contract, optional)
  - invoice (FK→Invoice, optional)
  - expires_at (DateTimeField, optional)
  - accepted_at, dismissed_at
  - metadata (JSONField)
  - created_at

- **CashFlowPrediction**
  - id (UUID)
  - prediction_date (DateField) — the date being predicted
  - predicted_income (DecimalField)
  - predicted_expenses (DecimalField)
  - predicted_net (DecimalField)
  - confidence_score (DecimalField) — 0 to 1
  - actual_income (DecimalField, optional) — filled after the fact
  - actual_expenses (DecimalField, optional)
  - factors (JSONField) — what drove the prediction
  - created_at

- **AIInsight**
  - id (UUID)
  - insight_type: choices (REVENUE_TREND, CLIENT_RISK, PAYMENT_PATTERN, SEASONAL, GROWTH)
  - title, description
  - data (JSONField) — charts, numbers, details
  - severity: choices (INFO, WARNING, CRITICAL)
  - user (FK→User)
  - is_read (bool, default=False)
  - read_at (DateTimeField, optional)
  - created_at

**Serializers:**
- AISuggestionSerializer
- CashFlowPredictionSerializer
- AIInsightSerializer

**Views (API):**
- AISuggestionViewSet (list, retrieve + custom actions: accept, dismiss, generate)
- CashFlowPredictionViewSet (list, retrieve + custom action: predict)
- AIInsightViewSet (list, retrieve + custom actions: mark_read, mark_all_read)

**URLs:**
- `api/ai/suggestions/` — List suggestions
- `api/ai/suggestions/{id}/accept/` — Accept
- `api/ai/suggestions/{id}/dismiss/` — Dismiss
- `api/ai/suggestions/generate/` — Generate new suggestions
- `api/ai/cash-flow/` — Cash flow predictions
- `api/ai/cash-flow/predict/` — Generate new prediction
- `api/ai/insights/` — AI insights

---

### 1H. Enhance Existing App: `apps/invoicing/` — Recurring Invoices + Late Payment Tools

**New Models (added to invoicing/models.py):**
- **RecurringInvoice**
  - id (UUID), client (FK→Client), contract (FK→Contract, optional)
  - template_name (CharField) — descriptive name
  - frequency: choices (WEEKLY, BIWEEKLY, MONTHLY, QUARTERLY, ANNUALLY)
  - start_date (DateField), end_date (DateField, optional)
  - next_run_date (DateField)
  - amount (DecimalField), currency
  - tax_rate (DecimalField), discount_amount (DecimalField)
  - items_template (JSONField) — template for line items
  - auto_send (bool, default=True)
  - status: choices (ACTIVE, PAUSED, CANCELLED, COMPLETED)
  - invoices_generated (IntegerField, default=0)
  - last_generated_at (DateTimeField, optional)
  - owner (FK→User)
  - notes, metadata (JSONField)
  - created_at, updated_at

- **LateFeePolicy**
  - id (UUID), name
  - fee_type: choices (FLAT, PERCENTAGE)
  - fee_amount (DecimalField) — flat amount or percentage
  - grace_period_days (IntegerField, default=0)
  - max_fee_amount (DecimalField, optional) — cap for percentage fees
  - is_compound (bool, default=False) — compound on previous fees
  - apply_frequency: choices (ONCE, DAILY, WEEKLY, MONTHLY)
  - is_active (bool)
  - created_at, updated_at

- **PaymentReminder**
  - id (UUID), invoice (FK→Invoice)
  - reminder_type: choices (BEFORE_DUE, ON_DUE, AFTER_DUE)
  - days_offset (IntegerField) — days before/after due date
  - status: choices (SCHEDULED, SENT, CANCELLED)
  - scheduled_date (DateField)
  - sent_at (DateTimeField, optional)
  - notification (FK→Notification, optional)
  - created_at

**New Serializers:**
- RecurringInvoiceSerializer, RecurringInvoiceCreateUpdateSerializer
- LateFeePolicySerializer
- PaymentReminderSerializer

**New Views:**
- RecurringInvoiceViewSet (CRUD + custom actions: pause, resume, generate_now)
- LateFeePolicyViewSet (CRUD)
- PaymentReminderViewSet (CRUD + custom actions: send_now, cancel)

**New URLs (added to invoicing/urls.py):**
- `api/recurring-invoices/` — Recurring invoice CRUD
- `api/recurring-invoices/{id}/pause/`
- `api/recurring-invoices/{id}/resume/`
- `api/recurring-invoices/{id}/generate-now/`
- `api/late-fee-policies/` — Late fee policy CRUD
- `api/payment-reminders/` — Payment reminder CRUD

---

### 1I. Enhance Existing App: `apps/accounts/` — Team Features

**New Models (added to accounts/models.py):**
- **Team**
  - id (UUID), name, description
  - owner (FK→User, related_name=owned_teams)
  - is_active (bool, default=True)
  - metadata (JSONField)
  - created_at, updated_at

- **TeamMember**
  - id (UUID), team (FK→Team)
  - user (FK→User)
  - role: choices (OWNER, ADMIN, MEMBER, VIEWER)
  - joined_at (DateTimeField, auto_now_add)
  - unique_together: [team, user]

- **TeamInvitation**
  - id (UUID), team (FK→Team)
  - email (EmailField)
  - role (CharField)
  - invited_by (FK→User)
  - invitation_token (CharField, unique)
  - status: choices (PENDING, ACCEPTED, EXPIRED, CANCELLED)
  - created_at, expires_at, accepted_at

**New Serializers:**
- TeamSerializer, TeamCreateUpdateSerializer
- TeamMemberSerializer
- TeamInvitationSerializer

**New Views:**
- TeamViewSet (CRUD + custom actions: members, invite, remove_member, stats)
- TeamMemberViewSet (list, retrieve, update, destroy)
- TeamInvitationViewSet (list, create, cancel, accept)

**New URLs (added to accounts/urls.py):**
- `api/teams/` — Team CRUD
- `api/teams/{id}/members/` — Team members
- `api/teams/{id}/invite/` — Invite to team
- `api/team-members/` — Team member management
- `api/team-invitations/` — Team invitation management

---

### 1J. Enhance Existing App: `apps/clients/` — Client Portal API

**New Models (added to clients/models.py):**
- **PortalMessage**
  - id (UUID), client (FK→Client)
  - sender (FK→User)
  - subject, content
  - is_from_client (bool, default=False)
  - is_read (bool, default=False)
  - read_at (DateTimeField, optional)
  - parent (FK→self, optional) — threaded messages
  - created_at, updated_at

**New Serializers:**
- PortalMessageSerializer

**New Views:**
- PortalMessageViewSet (CRUD + mark_read, unread_count)

**New URLs (added to clients/urls.py):**
- `api/portal-messages/` — Portal message CRUD

---

## Phase 2: URL Restructuring + View Splitting

### For EVERY app (existing 13 + new 7 = 20 apps):

**Step 1: Split views.py → views_api.py + views_frontend.py**
- `views_api.py` — Contains all DRF ViewSets and API function-based views (moved from current views.py)
- `views_frontend.py` — Contains Django TemplateView-based views (new)
- Keep `views.py` as a re-export file for backwards compatibility (imports from both)

**Step 2: Split urls.py → have api_urlpatterns + frontend_urlpatterns**
- Each app's `urls.py` will be restructured to contain:
  ```python
  api_urlpatterns = [...]  # DRF router + API paths
  frontend_urlpatterns = [...]  # Template-based views for HTML pages
  urlpatterns = api_urlpatterns + frontend_urlpatterns
  ```

**Step 3: Update config/urls.py**
- API routes under `api/` prefix
- Frontend routes under root or `app/` prefix
- Clear separation: `api/clients/` vs `clients/` (frontend)

---

## Phase 3: Frontend Views (No HTML)

For each app, create `views_frontend.py` with Django class-based views that:
- Inherit from `LoginRequiredMixin + TemplateView` (or `ListView`, `DetailView`, etc.)
- Set `template_name` to the expected HTML file path
- Pass all needed data in `get_context_data()`
- Do NOT create actual HTML template files

### Frontend Views Per App:

**accounts:**
- LoginView → `template: accounts/login.html`
- RegisterView → `template: accounts/register.html`
- ProfileView → `template: accounts/profile.html`
- SettingsView → `template: accounts/settings.html`
- TeamListView → `template: accounts/team_list.html`
- TeamDetailView → `template: accounts/team_detail.html`
- UserListView → `template: accounts/user_list.html`
- InvitationListView → `template: accounts/invitation_list.html`
- TwoFactorSetupView → `template: accounts/two_factor_setup.html`

**clients:**
- ClientListView → `template: clients/client_list.html`
- ClientDetailView → `template: clients/client_detail.html`
- ClientCreateView → `template: clients/client_form.html`
- ClientEditView → `template: clients/client_form.html`
- ClientPortalView → `template: clients/portal.html`
- PortalMessagesView → `template: clients/portal_messages.html`

**contracts:**
- ContractListView → `template: contracts/contract_list.html`
- ContractDetailView → `template: contracts/contract_detail.html`
- ContractCreateView → `template: contracts/contract_form.html`
- ContractEditView → `template: contracts/contract_form.html`
- ContractSignView → `template: contracts/contract_sign.html`
- MilestoneListView → `template: contracts/milestone_list.html`

**invoicing:**
- InvoiceListView → `template: invoicing/invoice_list.html`
- InvoiceDetailView → `template: invoicing/invoice_detail.html`
- InvoiceCreateView → `template: invoicing/invoice_form.html`
- InvoiceEditView → `template: invoicing/invoice_form.html`
- RecurringInvoiceListView → `template: invoicing/recurring_list.html`
- RecurringInvoiceDetailView → `template: invoicing/recurring_detail.html`
- LateFeePolicyListView → `template: invoicing/late_fee_list.html`
- PaymentReminderListView → `template: invoicing/reminder_list.html`

**payments:**
- PaymentListView → `template: payments/payment_list.html`
- PaymentDetailView → `template: payments/payment_detail.html`
- PaymentMethodListView → `template: payments/payment_method_list.html`

**documents:**
- DocumentListView → `template: documents/document_list.html`
- DocumentDetailView → `template: documents/document_detail.html`
- DocumentUploadView → `template: documents/document_upload.html`

**notifications:**
- NotificationListView → `template: notifications/notification_list.html`
- NotificationSettingsView → `template: notifications/settings.html`
- NotificationTemplateListView → `template: notifications/template_list.html`

**analytics:**
- DashboardView → `template: analytics/dashboard.html`
- RevenueView → `template: analytics/revenue.html`
- ClientMetricsView → `template: analytics/client_metrics.html`
- ActivityFeedView → `template: analytics/activity_feed.html`

**integrations:**
- IntegrationListView → `template: integrations/integration_list.html`
- IntegrationDetailView → `template: integrations/integration_detail.html`
- IntegrationConnectView → `template: integrations/connect.html`

**subscriptions:**
- SubscriptionPlanListView → `template: subscriptions/plan_list.html`
- SubscriptionDetailView → `template: subscriptions/subscription_detail.html`
- SubscriptionManageView → `template: subscriptions/manage.html`

**webhooks:**
- WebhookEventListView → `template: webhooks/event_list.html`
- WebhookEventDetailView → `template: webhooks/event_detail.html`
- WebhookEndpointListView → `template: webhooks/endpoint_list.html`

**workflows:**
- WorkflowListView → `template: workflows/workflow_list.html`
- WorkflowDetailView → `template: workflows/workflow_detail.html`
- WorkflowCreateView → `template: workflows/workflow_form.html`
- WorkflowEditView → `template: workflows/workflow_form.html`
- WorkflowExecutionListView → `template: workflows/execution_list.html`

**tasks:**
- TaskListView → `template: tasks/task_list.html`
- TaskDetailView → `template: tasks/task_detail.html`
- TaskCreateView → `template: tasks/task_form.html`
- TaskBoardView → `template: tasks/task_board.html` (Kanban style)

**emails:**
- EmailInboxView → `template: emails/inbox.html`
- EmailDetailView → `template: emails/email_detail.html`
- EmailComposeView → `template: emails/compose.html`
- EmailAccountSettingsView → `template: emails/account_settings.html`
- EmailTemplateListView → `template: emails/template_list.html`

**calendar_app:**
- CalendarView → `template: calendar_app/calendar.html`
- EventDetailView → `template: calendar_app/event_detail.html`
- EventCreateView → `template: calendar_app/event_form.html`
- BookingLinkListView → `template: calendar_app/booking_link_list.html`
- BookingLinkPublicView → `template: calendar_app/booking_public.html` (AllowAny)
- BookingConfirmView → `template: calendar_app/booking_confirm.html`

**proposals:**
- ProposalListView → `template: proposals/proposal_list.html`
- ProposalDetailView → `template: proposals/proposal_detail.html`
- ProposalCreateView → `template: proposals/proposal_form.html`
- ProposalEditView → `template: proposals/proposal_form.html`
- ProposalClientView → `template: proposals/proposal_client_view.html` (AllowAny — client-facing)

**expenses:**
- ExpenseListView → `template: expenses/expense_list.html`
- ExpenseDetailView → `template: expenses/expense_detail.html`
- ExpenseCreateView → `template: expenses/expense_form.html`
- ExpenseCategoryListView → `template: expenses/category_list.html`
- ExpenseReportView → `template: expenses/report.html`

**ai_assistant:**
- AIDashboardView → `template: ai_assistant/dashboard.html`
- AISuggestionsView → `template: ai_assistant/suggestions.html`
- CashFlowView → `template: ai_assistant/cash_flow.html`
- AIInsightsView → `template: ai_assistant/insights.html`

---

## Phase 4: Tests (99%+ Coverage)

### Test Structure Per App:
Each app will have the following test files:
- `tests/test_models.py` — Model creation, validation, methods, properties
- `tests/test_serializers.py` — Serialization, validation, nested operations
- `tests/test_views_api.py` — API endpoint tests (CRUD + custom actions)
- `tests/test_views_frontend.py` — Frontend view tests (template names, context, auth)
- `tests/test_urls.py` — URL resolution and reverse
- `tests/test_admin.py` — Admin registration and display (where applicable)

### Test Strategy:
- Use `pytest` + `pytest-django`
- Use `factory_boy` for test data factories
- Each factory in a `factories.py` file per app
- Test all CRUD operations, permissions, filters, search, ordering
- Test all custom actions (status transitions, business logic)
- Test edge cases: empty data, invalid data, permission denied
- Test frontend views: correct template, context data, login required
- Target: 99%+ line coverage

---

## Execution Order

1. Create 7 new Django apps (register in settings.py INSTALLED_APPS)
2. Write all new models + migrations
3. Write all serializers
4. Write all API views (views_api.py)
5. Write all URL configurations
6. Write tests for new features
7. Restructure existing apps: split views.py → views_api.py + views_frontend.py
8. Restructure existing apps: split urls.py with api_urlpatterns + frontend_urlpatterns
9. Write all frontend views (views_frontend.py)
10. Write tests for frontend views
11. Update config/urls.py for new routing
12. Run full test suite, fix any failures
13. Verify 99%+ coverage
14. Commit and push

---

## New App Registration (settings.py update)

```python
INSTALLED_APPS += [
    'apps.workflows',
    'apps.tasks',
    'apps.emails',
    'apps.calendar_app',
    'apps.proposals',
    'apps.expenses',
    'apps.ai_assistant',
]
```

## Summary

| Component | Count |
|-----------|-------|
| New Django apps | 7 |
| New models | ~25 |
| New serializers | ~35 |
| New API ViewSets | ~20 |
| New frontend views | ~65 |
| New URL patterns | ~80 |
| New test files | ~80+ |
| Enhanced existing apps | 3 (invoicing, accounts, clients) |
| Apps restructured | 20 (all) |
