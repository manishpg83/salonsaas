def assert_no_cross_tenant_access(client, detail_url):
    """
    Reusable cross-tenant isolation check (CLAUDE.md §4.2, §8). Every scoped
    module's tests should call this against a same-shaped object that
    belongs to a *different* salon than the one `client` is authenticated
    into.

    Expects 404, not 403: a wrong-tenant object must look like it doesn't
    exist at all — never leak its presence via a permission-denied response.
    """
    assert client.get(detail_url).status_code == 404
    assert client.patch(detail_url, {}, format="json").status_code == 404
    assert client.delete(detail_url).status_code == 404
