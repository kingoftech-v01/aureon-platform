"""
Tests for documents URL configuration.

Covers:
- DefaultRouter-generated URLs for DocumentViewSet
- app_name namespace
- Router registration
"""

from django.urls import resolve, URLResolver


class TestDocumentURLs:

    def test_app_name(self):
        from apps.documents import urls
        assert urls.app_name == 'documents'

    def test_router_registered(self):
        from apps.documents.urls import router
        assert len(router.registry) == 1
        assert router.registry[0][0] == ''
        assert router.registry[0][2] == 'document'

    def test_router_generates_list_url(self):
        from apps.documents.urls import router
        urls = router.get_urls()
        url_names = [u.name for u in urls if hasattr(u, 'name')]
        assert 'document-list' in url_names

    def test_router_generates_detail_url(self):
        from apps.documents.urls import router
        urls = router.get_urls()
        url_names = [u.name for u in urls if hasattr(u, 'name')]
        assert 'document-detail' in url_names

    def test_viewset_class(self):
        from apps.documents.urls import router
        viewset_cls = router.registry[0][1]
        assert viewset_cls.__name__ == 'DocumentViewSet'

    def test_urlpatterns_not_empty(self):
        from apps.documents.urls import urlpatterns
        assert len(urlpatterns) > 0

    def test_router_has_expected_actions(self):
        from apps.documents.urls import router
        urls = router.get_urls()
        # Router should generate urls for standard CRUD and custom actions
        url_names = [u.name for u in urls if hasattr(u, 'name') and u.name]
        assert any('document' in name for name in url_names)
