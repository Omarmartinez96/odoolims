#lims_custody_chain.py 
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LimsCustodyChain(models.Model):
    _name = 'lims.custody_chain'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'Cadena de Custodia'
    _rec_name = 'custody_chain_code'

    contact_ids = fields.Many2many(
        'lims.contact',
        string='Contactos Relacionados',
        domain="[('department_id', '=', departamento_id)]"
    )
    custody_chain_code = fields.Char(
        string="Código de Cadena de Custodia", 
        #required=True, 
        copy=False
    )
    cliente_id = fields.Many2one(
        'res.partner', 
        string="Cliente", 
        #required=True, 
        domain=[('is_lims_customer', '=', True)]
    )
    sucursal_id = fields.Many2one(
        'lims.branch', 
        string="Sucursal", 
        #required=True, 
        domain="[('customer_id', '=', cliente_id)]"
    )
    departamento_id = fields.Many2one(
        'lims.department', 
        string="Departamento", 
        domain="[('branch_id', '=', sucursal_id)]"
    )
    date_created = fields.Datetime(
        string="Fecha de Creación", 
        default=fields.Datetime.now
    )
    sample_ids = fields.One2many(
        'lims.sample', 
        'custody_chain_id', 
        string='Muestra'
    )
    chain_of_custody_state = fields.Selection(
        [('draft', 'Borrador'), ('in_progress', 'En Proceso'), ('done', 'Finalizado')], 
        string="Estado de CdC",
        default='draft', 
        #required=True
    )
    quotation_id = fields.Many2one(
        'sale.order',
        string ="Referencia de cotización"
    )
    sampling_plan = fields.Text(
        string="Plan de muestreo"
    )
    collected_by = fields.Char(
        string="Recolectado por"
    )
    collection_datetime = fields.Datetime(
        string="Fecha y Hora de Recolección"
    )
    sampling_observations = fields.Text(
        string="Observaciones de Muestreo"
    )
    internal_notes = fields.Text(
        string="Observaciones internas"
    )

    def action_send_comprobante_email(self):
        """Abre el wizard de composición de correo con la plantilla y el PDF adjunto."""
        self.ensure_one()
        if self.chain_of_custody_state != 'done':
            raise UserError(_('La cadena de custodia debe estar finalizada para enviar el comprobante.'))

        template = self.env.ref('lims_reception.email_template_comprobante', raise_if_not_found=False)
        if not template:
            raise UserError(_('No se encontró la plantilla de correo electrónico.'))

        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        ctx = {
            'default_model': 'lims.custody_chain',
            'default_res_id': self.id,
            'default_use_template': True,
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
        }
        return {
            'name': _('Enviar Comprobante'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

