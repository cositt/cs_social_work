from odoo import api, fields, models

# Context keys evitan bucles de sincronización atención ↔ calendario
CTX_SKIP_SESSION_SYNC = "cs_social_calendar_skip_session_sync"
CTX_SKIP_CALENDAR_SYNC = "cs_social_calendar_skip_calendar_sync"


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    cs_is_social_work_visit = fields.Boolean(
        string="Visita de área social",
        default=False,
        index=True,
        help="Marca la cita para filtrarla en el gestor de área social y mostrar campos del centro.",
    )
    cs_social_worker_id = fields.Many2one(
        "cs.worker",
        string="Trabajador/a o Educador/a Social",
        domain=[("job_title", "in", ["trabajador_social", "educador_social"])],
        tracking=True,
    )
    cs_social_session_id = fields.Many2one(
        "cs.social.session",
        string="Atención de área social",
        ondelete="set null",
        copy=False,
        index=True,
    )
    cs_visit_mode = fields.Selection(
        selection_add=[("gestion", "Gestión externa")],
        ondelete={"gestion": "set default"},
    )

    @api.onchange("cs_social_worker_id")
    def _onchange_cs_social_worker_calendar(self):
        if self.cs_social_worker_id and self.cs_social_worker_id.partner_id:
            self.partner_ids |= self.cs_social_worker_id.partner_id

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get(CTX_SKIP_CALENDAR_SYNC):
            return res
        watch = {"start", "stop", "duration"}
        if not watch & vals.keys():
            return res
        for event in self:
            sess = event.cs_social_session_id
            if not sess:
                continue
            upd = {}
            if event.start:
                upd["session_date"] = event.start
            if event.stop and event.start:
                mins = int((event.stop - event.start).total_seconds() // 60)
                if mins > 0:
                    upd["duration_minutes"] = mins
            if upd:
                sess.with_context(**{CTX_SKIP_SESSION_SYNC: True}).write(upd)
        return res
