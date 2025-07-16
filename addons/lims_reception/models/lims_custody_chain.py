#lims_custody_chain.py 
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
from datetime import datetime

class LimsCustodyChain(models.Model):
    _name = 'lims.custody_chain'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'Cadena de Custodia'
    _rec_name = 'custody_chain_code'

    # Campos de la Cadena de Custodia
    contact_ids = fields.Many2many('lims.contact', string='Contactos Relacionados', domain="[('department_id', '=', departamento_id)]")
    custody_chain_code = fields.Char(string="Código de Cadena de Custodia", copy=False, default='/', help="Se genera automaticamente al crear la cadena de custodia")
    cliente_id = fields.Many2one('res.partner', string="Cliente", domain=[('is_lims_customer', '=', True)])
    client_code = fields.Char(string="Código de Cliente", related='cliente_id.client_code', readonly=True, store=False,)
    sucursal_id = fields.Many2one('lims.branch', string="Sucursal", domain="[('customer_id', '=', cliente_id)]")
    departamento_id = fields.Many2one('lims.department', string="Departamento", domain="[('branch_id', '=', sucursal_id)]")
    date_created = fields.Datetime(string="Fecha de Creación", default=fields.Datetime.now)
    sample_ids = fields.One2many('lims.sample', 'custody_chain_id', string='Muestra')
    chain_of_custody_state = fields.Selection([('draft', 'Borrador'), ('in_progress', 'En Proceso'), ('done', 'Finalizado')], string="Estado de CC", default='draft',)
    quotation_id = fields.Many2one('sale.order', string ="Referencia de cotización")
    sampling_plan = fields.Text(string="Plan de muestreo")

    # Recolección
    collection_datetime = fields.Datetime(string="Fecha y Hora de Recolección")
    collected_by = fields.Char(string="Recolectado por", help="Nombre del personal que realizó la recolección")
      # Campo original para temperatura de recolección
    collection_temperature = fields.Float(string="Temperatura de Recolección", help="Temperatura en grados Celsius al momento de la recolección")
      # Campo de display 
    collection_temperature_display = fields.Char(string="Temperatura de Recolección", compute='_compute_display_collection_temperature', store=False)

    # Observaciones
    sampling_observations = fields.Text(string="Observaciones de Muestreo")
    internal_notes = fields.Text(string="Observaciones internas")

    @api.depends('collection_temperature')
    def _compute_display_collection_temperature(self):
        for record in self:
            field_config = {
                'collection_temperature': ('°C', 'N/A'),
                #Agregar mas campos si es necesario
            }

            for field_name, (suffix, default) in field_config.items():
                value = getattr(record, field_name)
                display_field = f"{field_name}_display"

                if value:
                    setattr(record, display_field, f"{value}{suffix}")
                else:
                    setattr(record, display_field, default)

    @api.model_create_multi
    def create(self, vals_list):
        year = str(datetime.today().year)

        for vals in vals_list:
            if not vals.get('custody_chain_code') or vals.get('custody_chain_code') == '/':
                # Buscar todas las cadenas de custodia del año actual
                existing = self.search([
                    ('custody_chain_code', 'like', f'%/{year}'),
                    ('custody_chain_code', '!=', '/')
                ])

                # Obtener el mayor consecutivo existente
                def extract_number(code):
                    try:
                        return int(code.split('/')[0])
                    except Exception:
                        return 0

                max_num = max([extract_number(rec.custody_chain_code) for rec in existing], default=0)
                next_num = str(max_num + 1).zfill(3)
                vals['custody_chain_code'] = f'{next_num}/{year}'

            text_fields_na = ['sampling_plan', 'sampling_observations', 'internal_notes']
            for field in text_fields_na: 
                if not vals.get (field) or (vals.get(field) and vals.get(field).strip() == ''):
                   vals[field] = 'N/A'

        return super(LimsCustodyChain, self).create(vals_list)
    
    def write(self, vals):
        text_fields_na = ['sampling_plan', 'sampling_observations', 'internal_notes']

        for field in text_fields_na:
            if field in vals: 
                if not vals.get(field) or vals.get(field).strip() == '':
                    vals[field] = 'N/A'

        return super(LimsCustodyChain, self).write(vals)

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
            'default_res_ids': [self.id],
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
