"""foodinfo admin

The public-facing website CMS (FAQs, policies, etc.) is managed under the
`Website` app (see `Website.admin_brita`).

This `foodinfo` app contains legacy/account models that are still used for
authentication, but we intentionally keep them out of the Django admin UI to
avoid exposing deprecated application surfaces.
"""

# Intentionally no Django admin registrations for this app.
