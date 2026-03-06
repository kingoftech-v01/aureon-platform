"""
Tests for integrations URL configuration.

Covers:
- DefaultRouter-generated URLs for IntegrationViewSet
- app_name namespace
- Router registration
"""

from django.urls import URLResolver


class TestIntegrationURLs:

    def test_app_name(self):
        from apps.integrations import urls
        assert urls.app_name == 'integrations'

    def test_router_registered(self):
        from apps.integrations.urls import router
        assert len(router.registry) == 1
        assert router.registry[0][0] == ''
        assert router.registry[0][2] == 'integration'

    def test_router_generates_list_url(self):
        from apps.integrations.urls import router
        urls = router.get_urls()
        url_names = [u.name for u in urls if hasattr(u, 'name')]
        assert 'integration-list' in url_names

    def test_router_generates_detail_url(self):
        from apps.integrations.urls import router
        urls = router.get_urls()
        url_names = [u.name for u in urls if hasattr(u, 'name')]
        assert 'integration-detail' in url_names

    def test_viewset_class(self):
        from apps.integrations.urls import router
        viewset_cls = router.registry[0][1]
        assert viewset_cls.__name__ == 'IntegrationViewSet'

    def test_urlpatterns_not_empty(self):
        from apps.integrations.urls import urlpatterns
        assert len(urlpatterns) > 0

    def test_router_has_expected_actions(self):
        from apps.integrations.urls import router
        urls = router.get_urls()
        url_names = [u.name for u in urls if hasattr(u, 'name') and u.name]
        assert any('integration' in name for name in url_names)
