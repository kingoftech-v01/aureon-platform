"""
Tests for accounts URL configuration.

Covers:
- All URL patterns resolve correctly
- URL names map to the correct views
- URL reverse lookups produce correct paths
"""

import pytest
from django.urls import resolve, reverse


class TestAuthenticationURLs:
    """Tests for JWT authentication URL patterns."""

    def test_login_url_resolves(self):
        """Login URL resolves to CustomTokenObtainPairView."""
        url = reverse('accounts:token_obtain_pair')
        assert url == '/api/auth/login/'
        resolver = resolve('/api/auth/login/')
        assert resolver.url_name == 'token_obtain_pair'

    def test_register_url_resolves(self):
        """Register URL resolves to the register view."""
        url = reverse('accounts:register')
        assert url == '/api/auth/register/'
        resolver = resolve('/api/auth/register/')
        assert resolver.url_name == 'register'

    def test_token_refresh_url_resolves(self):
        """Token refresh URL resolves to TokenRefreshView."""
        url = reverse('accounts:token_refresh')
        assert url == '/api/auth/token/refresh/'
        resolver = resolve('/api/auth/token/refresh/')
        assert resolver.url_name == 'token_refresh'

    def test_logout_url_resolves(self):
        """Logout URL resolves to the logout view."""
        url = reverse('accounts:logout')
        assert url == '/api/auth/logout/'
        resolver = resolve('/api/auth/logout/')
        assert resolver.url_name == 'logout'

    def test_current_user_url_resolves(self):
        """Current user URL resolves to the get_current_user view."""
        url = reverse('accounts:current_user')
        assert url == '/api/auth/user/'
        resolver = resolve('/api/auth/user/')
        assert resolver.url_name == 'current_user'


class TestTwoFactorURLs:
    """Tests for 2FA URL patterns."""

    def test_2fa_enable_url_resolves(self):
        """2FA enable URL resolves correctly."""
        url = reverse('accounts:2fa_enable')
        assert url == '/api/auth/2fa/enable/'
        resolver = resolve('/api/auth/2fa/enable/')
        assert resolver.url_name == '2fa_enable'

    def test_2fa_verify_setup_url_resolves(self):
        """2FA verify-setup URL resolves correctly."""
        url = reverse('accounts:2fa_verify_setup')
        assert url == '/api/auth/2fa/verify-setup/'
        resolver = resolve('/api/auth/2fa/verify-setup/')
        assert resolver.url_name == '2fa_verify_setup'

    def test_2fa_disable_url_resolves(self):
        """2FA disable URL resolves correctly."""
        url = reverse('accounts:2fa_disable')
        assert url == '/api/auth/2fa/disable/'
        resolver = resolve('/api/auth/2fa/disable/')
        assert resolver.url_name == '2fa_disable'

    def test_2fa_verify_url_resolves(self):
        """2FA verify URL resolves correctly."""
        url = reverse('accounts:2fa_verify')
        assert url == '/api/auth/2fa/verify/'
        resolver = resolve('/api/auth/2fa/verify/')
        assert resolver.url_name == '2fa_verify'

    def test_2fa_backup_code_url_resolves(self):
        """2FA backup-code URL resolves correctly."""
        url = reverse('accounts:2fa_backup_code')
        assert url == '/api/auth/2fa/backup-code/'
        resolver = resolve('/api/auth/2fa/backup-code/')
        assert resolver.url_name == '2fa_backup_code'

    def test_2fa_regenerate_codes_url_resolves(self):
        """2FA regenerate-backup-codes URL resolves correctly."""
        url = reverse('accounts:2fa_regenerate_codes')
        assert url == '/api/auth/2fa/regenerate-backup-codes/'
        resolver = resolve('/api/auth/2fa/regenerate-backup-codes/')
        assert resolver.url_name == '2fa_regenerate_codes'

    def test_2fa_status_url_resolves(self):
        """2FA status URL resolves correctly."""
        url = reverse('accounts:2fa_status')
        assert url == '/api/auth/2fa/status/'
        resolver = resolve('/api/auth/2fa/status/')
        assert resolver.url_name == '2fa_status'


class TestRouterURLs:
    """Tests for DRF router URL patterns (users, invitations, api-keys)."""

    def test_users_list_url_resolves(self):
        """Users list URL resolves correctly."""
        url = reverse('accounts:user-list')
        assert url == '/api/auth/api/users/'
        resolver = resolve('/api/auth/api/users/')
        assert resolver.url_name == 'user-list'

    def test_invitations_list_url_resolves(self):
        """Invitations list URL resolves correctly."""
        url = reverse('accounts:invitation-list')
        assert url == '/api/auth/api/invitations/'
        resolver = resolve('/api/auth/api/invitations/')
        assert resolver.url_name == 'invitation-list'

    def test_apikeys_list_url_resolves(self):
        """API keys list URL resolves correctly."""
        url = reverse('accounts:apikey-list')
        assert url == '/api/auth/api/api-keys/'
        resolver = resolve('/api/auth/api/api-keys/')
        assert resolver.url_name == 'apikey-list'


class TestURLNamespace:
    """Tests for the accounts URL namespace."""

    def test_app_name_is_accounts(self):
        """The accounts app URL namespace is 'accounts'."""
        # Verify that reverse with the accounts namespace works
        url = reverse('accounts:register')
        assert '/api/auth/' in url

    def test_all_url_names_are_reversible(self):
        """All defined URL names in the accounts app can be reversed."""
        url_names = [
            'accounts:token_obtain_pair',
            'accounts:register',
            'accounts:token_refresh',
            'accounts:logout',
            'accounts:current_user',
            'accounts:2fa_enable',
            'accounts:2fa_verify_setup',
            'accounts:2fa_disable',
            'accounts:2fa_verify',
            'accounts:2fa_backup_code',
            'accounts:2fa_regenerate_codes',
            'accounts:2fa_status',
            'accounts:user-list',
            'accounts:invitation-list',
            'accounts:apikey-list',
        ]
        for url_name in url_names:
            url = reverse(url_name)
            assert url is not None, f"Failed to reverse URL name: {url_name}"
            assert url.startswith('/api/auth/'), f"URL {url_name} does not start with /api/auth/"
