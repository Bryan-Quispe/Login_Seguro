"""
Tests dinámicos de seguridad: XSS y CSRF (ejemplos)

Estos tests son plantillas prácticas que puedes adaptar a los endpoints
reales de la aplicación. Usan `httpx.AsyncClient` con `ASGITransport`
igual que las otras pruebas de integración.

Notas:
- Ajusta los endpoints y campos según tu API real.
- Para CSRF, si usas autenticación por cookies/CSRF tokens, adapta el test
  que contiene el flujo de login por cookie y envío sin token.
"""
import pytest
import pytest_asyncio
import re
import httpx
from app.main import app


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as test_client:
        yield test_client


class TestDynamicXSS:
    """Pruebas dinámicas para XSS (reflejado y almacenado)"""

    @pytest.mark.asyncio
    async def test_reflected_xss_payload_is_escaped(self, client):
        """Enviar payload XSS a un endpoint que podría reflejar input.

        Este test verifica que la respuesta no contiene el payload sin escapar.
        Ajusta el endpoint y el parámetro según tu API.
        """
        payload = '<script>alert("xss")</script>'

        # Ejemplo: endpoint de registro que podría reflejar el username
        response = await client.post("/api/auth/register", json={
            "username": payload,
            "password": "Test@12345",
            "email": "xss@example.test"
        })

        assert response.status_code in (200, 400, 422)

        # Asegurarse que la respuesta no contiene el script sin escapar
        text = response.text or ""
        assert payload not in text

        # Detectar presencia de etiquetas <script> sin ser entidades HTML
        assert not re.search(r"<script[\s>].*?</script>", text, flags=re.I | re.S)

    @pytest.mark.asyncio
    async def test_persistent_xss_check(self, client):
        """Prueba básica de XSS persistente: crear recurso con payload y leerlo."""
        payload = '<img src=x onerror=alert(1) />'

        # Crear recurso (ajusta a tu endpoint real que almacene datos del usuario)
        create_resp = await client.post("/api/admin/users", json={
            "username": "xss_test_user",
            "password": "Test@12345",
            "bio": payload
        })

        # Aceptamos varios códigos porque puede requerir auth
        assert create_resp.status_code in (200, 201, 401, 403, 422)

        # Intentar leer recurso que hipotéticamente contiene la bio
        read_resp = await client.get("/api/admin/users/username/xss_test_user")
        assert read_resp.status_code in (200, 401, 403, 404)

        if read_resp.status_code == 200:
            body = read_resp.text or ""
            assert payload not in body
            assert not re.search(r"onerror=|<script[\s>]", body, flags=re.I)


class TestDynamicCSRF:
    """Pruebas dinámicas para CSRF.

    - Si tu app usa JWT en Authorization header: CSRF normalmente no aplica.
    - Si usas sesiones por cookie, implementa protección CSRF y prueba
      que acciones POST/PUT/DELETE sin token son rechazadas.
    """

    @pytest.mark.asyncio
    async def test_csrf_missing_token_rejected_template(self, client):
        """Plantilla que simula un POST protegido por CSRF.

        Ajusta el flujo de login si tu app usa cookies de sesión.
        """
        # 1) Simular login que establece cookie de sesión (si aplica)
        login_resp = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "Test@12345"
        })

        # Si el login devuelve cookie, httpx la manejará automáticamente
        assert login_resp.status_code in (200, 401, 422)

        # 2) Enviar POST a endpoint que requiere CSRF sin token
        post_resp = await client.post("/api/admin/disable/1", json={})

        # Si la app implementa CSRF por cookies, debería rechazar (403)
        assert post_resp.status_code in (401, 403, 422)

    @pytest.mark.asyncio
    async def test_csrf_with_token_example(self, client):
        """Ejemplo de cómo incluir token CSRF si el sistema lo exige.

        - Obtener token (por ejemplo /csrf-token o en la cookie). Adaptar.
        - Incluir en header `X-CSRF-Token` o campo del formulario.
        """
        # Obtener token (endpoint hipotético)
        token_resp = await client.get("/csrf-token")
        if token_resp.status_code == 200:
            token = token_resp.json().get("csrf_token")
            headers = {"X-CSRF-Token": token}
            resp = await client.post("/api/admin/disable/1", headers=headers, json={})
            assert resp.status_code in (200, 204, 401, 403)
        else:
            pytest.skip("No hay endpoint /csrf-token en esta app; adapta el test")


# Fin de archivo
