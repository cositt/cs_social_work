from odoo import _, api, fields, models


class SocialProcedure(models.Model):
    _name = "cs.social.procedure"
    _description = "Gestión / trámite de trabajo social"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, id desc"

    name = fields.Char(string="Referencia", required=True, copy=False, default=lambda self: _("Nueva gestión"))
    resident_id = fields.Many2one(
        "cs.resident",
        string="Residente",
        required=True,
        index=True,
        tracking=True,
    )
    partner_id = fields.Many2one(
        related="resident_id.partner_id",
        comodel_name="res.partner",
        string="Paciente (contacto)",
        store=True,
        readonly=True,
    )
    social_worker_id = fields.Many2one(
        "cs.worker",
        string="Trabajador/a o Educador/a Social",
        tracking=True,
        domain=[("job_title", "in", ["trabajador_social", "educador_social"])],
    )
    procedure_type = fields.Selection(
        [
            ("ayuda_economica", "Ayuda económica"),
            ("pension", "Pensión / prestación"),
            ("dependencia", "Ley de Dependencia"),
            ("discapacidad", "Certificado de discapacidad"),
            ("documentacion", "Documentación (DNI, tarjeta sanitaria...)"),
            ("cita_externa", "Cita externa / acompañamiento"),
            ("recurso_social", "Recurso social / derivación"),
            ("judicial", "Judicial (tutela, incapacitación...)"),
            ("otro", "Otro"),
        ],
        string="Tipo de gestión",
        required=True,
        default="otro",
        tracking=True,
    )
    organism = fields.Char(
        string="Organismo / entidad",
        help="Organismo o entidad ante la que se realiza la gestión.",
    )
    state = fields.Selection(
        [
            ("pending", "Pendiente"),
            ("in_progress", "En trámite"),
            ("waiting", "Esperando respuesta"),
            ("done", "Completada"),
            ("cancelled", "Cancelada"),
        ],
        string="Estado",
        default="pending",
        tracking=True,
    )
    request_date = fields.Date(
        string="Fecha de inicio",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    due_date = fields.Date(string="Fecha límite", tracking=True)
    completion_date = fields.Date(string="Fecha de finalización", readonly=True, copy=False)
    description = fields.Text(string="Descripción de la gestión")
    notes = fields.Text(string="Notas / seguimiento")

    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Documentos e imágenes",
        help="Solicitudes, resoluciones, justificantes u otros archivos de la gestión.",
    )

    def action_start(self):
        self.write({"state": "in_progress"})

    def action_wait(self):
        self.write({"state": "waiting"})

    def action_mark_done(self):
        self.write({"state": "done", "completion_date": fields.Date.context_today(self)})

    def action_mark_cancelled(self):
        self.write({"state": "cancelled"})

    def action_set_pending(self):
        self.write({"state": "pending", "completion_date": False})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("Nueva gestión"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("cs.social.procedure") or _("Nueva gestión")
                )
        return super().create(vals_list)
