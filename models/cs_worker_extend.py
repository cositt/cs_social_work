# -*- coding: utf-8 -*-
from odoo import api, fields, models


class WorkerSocialWorkExtend(models.Model):
    _inherit = 'cs.worker'

    job_title = fields.Selection(
        selection_add=[
            ('terapeuta',),
            ('trabajador_social', 'Trabajador/a Social'),
            ('educador_social', 'Educador/a Social'),
        ],
        ondelete={
            'trabajador_social': lambda recs: recs.write({'job_title': 'otro'}),
            'educador_social': lambda recs: recs.write({'job_title': 'otro'}),
        },
    )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        if self.partner_id and not self.job_title:
            for category in self.partner_id.category_id:
                category_name = category.name.lower()
                if 'educador' in category_name:
                    self.job_title = 'educador_social'
                    break
                if 'social' in category_name:
                    self.job_title = 'trabajador_social'
                    break
        return res
