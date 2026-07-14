from odoo import _, api, fields, models


class SocialReport(models.Model):
    _name = "cs.social.report"
    _description = "Informe social"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "report_date desc, id desc"

    name = fields.Char(string="Referencia", required=True, copy=False, default=lambda self: _("Nuevo informe"))
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
    report_date = fields.Date(
        string="Fecha",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    report_type = fields.Selection(
        [
            ("valoracion_inicial", "Valoración social inicial"),
            ("seguimiento", "Informe de seguimiento"),
            ("derivacion", "Informe de derivación"),
            ("organismo", "Informe para organismo oficial"),
            ("otro", "Otro"),
        ],
        string="Tipo de informe",
        default="valoracion_inicial",
        required=True,
        tracking=True,
    )
    recipient_entity = fields.Char(
        string="Organismo / entidad destinataria",
        help="Organismo o entidad a la que va dirigido el informe (si aplica).",
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("done", "Cerrado"),
        ],
        string="Estado",
        default="draft",
        tracking=True,
    )
    reason = fields.Text(string="Motivo del informe / demanda")
    family_situation = fields.Text(string="Situación socio-familiar")
    economic_situation = fields.Text(string="Situación económica y laboral")
    housing_situation = fields.Text(string="Vivienda y entorno")
    support_network = fields.Text(string="Red de apoyo y recursos")
    social_assessment = fields.Text(string="Valoración / diagnóstico social")
    intervention_plan = fields.Text(string="Plan de intervención social")

    assessment_template_id = fields.Many2one(
        "cs.followup.template",
        string="Plantilla",
        domain=[("state", "=", "published")],
    )
    assessment_id = fields.Many2one(
        "cs.followup.assessment",
        string="Evaluación (formulario)",
        domain="[('patient_id', '=', partner_id)]",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Documentos e imágenes",
        help="PDF, informes, capturas u otros archivos vinculados al informe.",
    )

    def action_mark_done(self):
        self.write({"state": "done"})

    def action_set_draft(self):
        self.write({"state": "draft"})

    @api.onchange('assessment_template_id')
    def _onchange_assessment_template_id(self):
        if self.assessment_template_id and not self.assessment_id:
            assessment = self.env['cs.followup.assessment'].create({
                'template_id': self.assessment_template_id.id,
                'patient_id': self.partner_id.id,
                'clinician_id': self.env.user.id,
                'assessment_date': self.report_date or fields.Date.context_today(self),
            })
            self.assessment_id = assessment.id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("Nuevo informe"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("cs.social.report") or _("Nuevo informe")
                )
        return super().create(vals_list)
