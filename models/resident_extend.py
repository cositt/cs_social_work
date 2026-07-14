# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ResidentSocialWorkExtend(models.Model):
    _inherit = 'cs.resident'

    social_session_count = fields.Integer(
        compute='_compute_social_work_counts',
        string='Atenciones Área Social',
    )
    social_report_count = fields.Integer(
        compute='_compute_social_work_counts',
        string='Informes sociales',
    )
    social_procedure_count = fields.Integer(
        compute='_compute_social_work_counts',
        string='Gestiones Área Social',
    )

    def _compute_social_work_counts(self):
        def counts_for(model):
            groups = self.env[model]._read_group(
                domain=[('resident_id', 'in', self.ids)],
                groupby=['resident_id'],
                aggregates=['__count'],
            )
            return {resident.id: count for resident, count in groups}

        session_counts = counts_for('cs.social.session')
        report_counts = counts_for('cs.social.report')
        procedure_counts = counts_for('cs.social.procedure')
        for rec in self:
            rec.social_session_count = session_counts.get(rec.id, 0)
            rec.social_report_count = report_counts.get(rec.id, 0)
            rec.social_procedure_count = procedure_counts.get(rec.id, 0)

    def action_open_social_sessions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Atenciones de Área Social — %s') % self.name,
            'res_model': 'cs.social.session',
            'view_mode': 'list,form',
            'domain': [('resident_id', '=', self.id)],
            'context': {'default_resident_id': self.id},
        }

    def action_open_social_reports(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Informes sociales — %s') % self.name,
            'res_model': 'cs.social.report',
            'view_mode': 'list,form',
            'domain': [('resident_id', '=', self.id)],
            'context': {'default_resident_id': self.id},
        }

    def action_open_social_procedures(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Gestiones de Área Social — %s') % self.name,
            'res_model': 'cs.social.procedure',
            'view_mode': 'list,form',
            'domain': [('resident_id', '=', self.id)],
            'context': {'default_resident_id': self.id},
        }
