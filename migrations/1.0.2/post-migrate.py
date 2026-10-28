from odoo import SUPERUSER_ID, api

SEQUENCE_CODES = ("cs.social.session", "cs.social.report", "cs.social.procedure")


def migrate(cr, version):
    """Secuencias compartidas: con compañía, next_by_code no las encuentra en otras compañías."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["ir.sequence"].search([("code", "in", SEQUENCE_CODES)]).write({"company_id": False})
