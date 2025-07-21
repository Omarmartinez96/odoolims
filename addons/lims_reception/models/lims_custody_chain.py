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
    internal_notes = fields.Text(string="Notas Internas", help="Notas internas relacionadas con la cadena de custodia")

    # 🆕 CAMPOS PARA FIRMA DIGITAL
    customer_signature = fields.Binary(
        string='Firma del Cliente',
        help='Firma digital del cliente'
    )
    signature_date = fields.Datetime(
        string='Fecha de Firma',
        help='Fecha y hora cuando se firmó el documento'
    )
    signature_name = fields.Char(
        string='Nombre del Firmante',
        help='Nombre de la persona que firmó'
    )
    signature_position = fields.Char(
        string='Cargo del Firmante',
        help='Cargo o posición de la persona que firmó'
    )
    is_signed = fields.Boolean(
        string='Documento Firmado',
        compute='_compute_is_signed',
        store=True
    )
    
    # ========== MÉTODOS EXISTENTES ==========
    
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
                        parts = code.split('/')
                        if len(parts) >= 1:
                            return int(parts[0])
                        return 0
                    except (ValueError, IndexError):
                        return 0

                max_num = max([extract_number(rec.custody_chain_code) for rec in existing], default=0)
                next_num = str(max_num + 1).zfill(3)
                vals['custody_chain_code'] = f'{next_num}/{year}'

            text_fields_na = ['internal_notes']
            for field in text_fields_na: 
                if not vals.get(field) or (isinstance(vals.get(field), str) and vals.get(field).strip() == ''):
                   vals[field] = 'N/A'

        return super(LimsCustodyChain, self).create(vals_list)
    
    def write(self, vals):
        text_fields_na = ['internal_notes']

        for field in text_fields_na:
            if field in vals: 
                if not vals.get(field) or (isinstance(vals.get(field), str) and vals.get(field).strip() == ''):
                    vals[field] = 'N/A'

        return super(LimsCustodyChain, self).write(vals)

    # ========== MÉTODOS DE FIRMA DIGITAL ==========
    
    @api.depends('customer_signature')
    def _compute_is_signed(self):
        """Calcula si el documento está firmado basándose en la existencia de la firma"""
        for record in self:
            record.is_signed = bool(record.customer_signature)

    def action_preview_and_sign(self):
        """Acción para vista previa del PDF y solicitar firma"""
        self.ensure_one()
        
        if self.chain_of_custody_state != 'done':
            raise UserError(_('La cadena de custodia debe estar finalizada para firmar.'))
        
        return {
            'name': _('Vista Previa y Firma'),
            'type': 'ir.actions.act_window',
            'res_model': 'lims.custody_chain',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('lims_reception.view_custody_chain_signature_form').id,
            'target': 'new',
            'context': {
                'form_view_initial_mode': 'edit',
                'signature_mode': True,
            }
        }

    def action_save_signature(self):
        """Guardar la firma y actualizar fechas"""
        self.ensure_one()
        
        if not self.customer_signature:
            raise UserError(_('Debe proporcionar una firma antes de guardar.'))
        
        self.signature_date = fields.Datetime.now()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Firma Guardada'),
                'message': _('La firma se ha guardado correctamente.'),
                'type': 'success',
            }
        }

    # ========== MÉTODO EXISTENTE DE EMAIL ==========
    
    def action_send_comprobante_email(self):
        self.ensure_one()
        
        if self.chain_of_custody_state != 'done':
            raise UserError(_('La cadena de custodia debe estar finalizada para enviar el comprobante.'))

        template = self.env.ref('lims_reception.email_template_comprobante', raise_if_not_found=False)
        if not template:
            raise UserError(_('No se encontró la plantilla de correo electrónico.'))

        report = self.env.ref('lims_reception.action_report_custody_chain', raise_if_not_found=False)
        if not report:
            raise UserError(_('No se encontró el reporte de comprobante.'))

        record = self.env['lims.custody_chain'].browse(self.id)
        if not record.exists():
            raise UserError(_("No se encontró la cadena de custodia con ID: %s") % self.id)

        try:
            # 🆕 EL PDF AHORA INCLUIRÁ LA FIRMA AUTOMÁTICAMENTE
            pdf_content, content_type = report._render_qweb_pdf(
                report_ref='lims_reception.action_report_custody_chain',
                res_ids=[self.id]
            )
        except Exception as e:
            raise UserError(_("Error al generar el PDF: %s") % str(e))
        
        safe_code = self.custody_chain_code.replace('/', '_') if self.custody_chain_code else 'comprobante'
        filename = f'{safe_code}.pdf'

        try:
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'lims.custody_chain',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
        except Exception as e:
            raise UserError(_("Error al crear el archivo adjunto: %s") % str(e))

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