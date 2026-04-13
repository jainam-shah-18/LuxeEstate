"""
SMTP email backend: uses Certifi's CA bundle for TLS (fixes many Windows / Python SSL issues).

Corporate SSL inspection often presents a local CA whose cert fails OpenSSL 3 checks, e.g.
"CERTIFICATE_VERIFY_FAILED: Basic Constraints of CA cert not marked critical".
For local development only, set EMAIL_SMTP_INSECURE_SKIP_VERIFY=True in .env.

Optional: EMAIL_SMTP_CA_BUNDLE=/path/to/extra.pem appends custom roots (e.g. corporate CA)
before falling back to insecure skip.
"""

import logging
import ssl

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend
from django.utils.functional import cached_property

logger = logging.getLogger(__name__)


class EmailBackend(DjangoSMTPBackend):
    @cached_property
    def ssl_context(self):
        if getattr(settings, "EMAIL_SMTP_INSECURE_SKIP_VERIFY", False):
            return ssl._create_unverified_context()
        if self.ssl_certfile or self.ssl_keyfile:
            return super().ssl_context

        extra_bundle = (getattr(settings, "EMAIL_SMTP_CA_BUNDLE", None) or "").strip()
        if extra_bundle:
            try:
                import certifi

                ctx = ssl.create_default_context(cafile=certifi.where())
            except ImportError:
                ctx = ssl.create_default_context()
            try:
                ctx.load_verify_locations(cafile=extra_bundle)
            except OSError as e:
                logger.error("Could not load EMAIL_SMTP_CA_BUNDLE %s: %s", extra_bundle, e)
                raise
            return ctx

        try:
            import certifi

            return ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            return ssl.create_default_context()
