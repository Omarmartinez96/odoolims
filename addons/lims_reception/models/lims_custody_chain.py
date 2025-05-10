#lims_custody_chain.py 
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64

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
        self.ensure_one()
        
        if self.chain_of_custody_state != 'done':
            raise UserError(_('La cadena de custodia debe estar finalizada para enviar el comprobante.'))

        template = self.env.ref('lims_reception.email_template_comprobante', raise_if_not_found=False)
        if not template:
            raise UserError(_('No se encontró la plantilla de correo electrónico.'))

        # Get and verify report
        report = self.env.ref('lims_reception.action_report_custody_chain', raise_if_not_found=False)
        if not report:
            raise UserError(_('No se encontró el reporte de comprobante.'))

        # Optional but helpful: confirm the record exists
        record = self.env['lims.custody_chain'].browse(self.id)
        if not record.exists():
            raise UserError(_("No se encontró la cadena de custodia con ID: %s") % self.id)

        # Render the PDF (pass list of IDs)
        pdf_content, content_type = report._render_qweb_pdf(
            'lims_reception.action_report_custody_chain',
            res_ids=[self.id]
        )
        
        filename = '%s.pdf' % (self.custody_chain_code.replace('/', '_') if self.custody_chain_code else 'comprobante')

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'lims.custody_chain',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        compose_form = self.env.ref('mail.email_compose_message_wizard_form')

        ctx = {
            'default_model': 'lims.custody_chain',
            'default_res_id': self.id,
            'default_use_template': True,
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'default_attachment_ids': [(6, 0, [attachment.id])],
        }

        return {
            'name': _('Enviar Comprobante'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'views': [(compose_form.id, 'form')],
            'target': 'new',
            'context': ctx,
        }
