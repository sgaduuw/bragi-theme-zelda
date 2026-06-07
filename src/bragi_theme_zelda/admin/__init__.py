"""Admin-side Flask blueprint for the Zelda theme.

The blueprint mounts under ``/admin/sites/<site_slug>/zelda/rom/`` and
exposes upload, delete, and status views. Bragi's admin app picks it
up via the ``register_admin_blueprint`` hookimpl in
:mod:`bragi_theme_zelda.plugin`.
"""

from bragi_theme_zelda.admin.routes import build_admin_blueprint

__all__ = ["build_admin_blueprint"]
