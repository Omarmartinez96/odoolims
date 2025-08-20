#lims_custody_chain.py 
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class LimsCustodyChain(models.Model):
    _name = 'lims.custody_chain'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'Cadena de Custodia'
    _rec_name = 'custody_chain_code'
    _order = 'custody_chain_sequence desc, date_chainofcustody desc'

    # Campos de la Cadena de Custodia
    contact_ids = fields.Many2many(
        'lims.contact', 
        string='Contactos Relacionados', 
        domain="[('department_id', '=', departamento_id)]"
    )
    custody_chain_code = fields.Char(
        string="Código de Cadena de Custodia", 
        copy=False, 
        store=True,
        help='Número consecutivo extraído del código para ordenamiento correcto'
    )

    custody_chain_sequence = fields.Integer(
        string='Secuencia Numérica',
        compute='_compute_custody_chain_sequence',
        store=True,
        help='Número consecutivo extraído del código para ordenamiento correcto'
    )

    cliente_id = fields.Many2one(
        'res.partner', 
        string="Cliente", 
        domain=[('is_lims_customer', '=', True)]
    )
    client_code = fields.Char(
        string="Código de Cliente", 
        related='cliente_id.client_code', 
        readonly=True, store=False,
    )
    sucursal_id = fields.Many2one(
        'lims.branch', 
        string="Sucursal", 
        domain="[('customer_id', '=', cliente_id)]"
    )
    departamento_id = fields.Many2one(
        'lims.department', 
        string="Departamento", 
        domain="[('branch_id', '=', sucursal_id)]"
    )

# ============ INHABILITADO =================

    date_created = fields.Datetime(
        string="Fecha de Creación", 
        default=fields.Datetime.now
    )
# ============ INHABILITADO =================

    date_chainofcustody = fields.Date(
        string="Fecha de Cadena de Custodia",
        default=fields.Date.context_today,
        help="Fecha en que se crea la cadena de custodia"   
    )

    time_chainofcustody = fields.Char(
        string="Hora de Cadena de Custodia",
        default=lambda self: datetime.now().strftime('%H:%M'),
        help="Hora en que se crea la cadena de custodia"
    )

    sample_ids = fields.One2many(
        'lims.sample', 
        'custody_chain_id', 
        string='Muestra'
    )
    chain_of_custody_state = fields.Selection(
        [('draft', 'Borrador'), ('in_progress', 'En Proceso'), 
         ('done', 'Finalizado')], 
        string="Estado de CC", 
        default='draft',
    )
    # Analista responsable
    analyst_id = fields.Many2one(
        'lims.analyst',
        string='Finalizado por',
        help='Persona que finalizó la cadena de custodia'
    )

    quotation_id = fields.Many2one(
        'sale.order', 
        string ="Referencia de cotización"
    )
    internal_notes = fields.Text(
        string="Notas Internas", 
        help="Notas internas relacionadas con la cadena de custodia"
    )

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

    @api.depends('custody_chain_code')
    def _compute_custody_chain_sequence(self):
        """Extraer número consecutivo del código para ordenamiento correcto"""
        for record in self:
            sequence = 0
            if record.custody_chain_code:
                try:
                    parts = str(record.custody_chain_code).split('/')
                    if parts and parts[0].isdigit():
                        sequence = int(parts[0])
                except (ValueError, IndexError):
                    sequence = 0
            record.custody_chain_sequence = sequence

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

        email_list = []
        partner_list = []  # Para filtrar contactos en el wizard
        
        # Agregar email del cliente principal
        if self.cliente_id and self.cliente_id.email:
            email_list.append(self.cliente_id.email)
            partner_list.append(self.cliente_id.id)
        
        # Filtrar todos los contactos del mismo cliente
        if self.cliente_id:
            client_contacts = self.env['lims.contact'].search([
                ('department_id.branch_id.customer_id', '=', self.cliente_id.id)
            ])
            
            for contact in client_contacts:
                if contact.email and contact.email not in email_list:
                    email_list.append(contact.email)
                    # Agregar partner_id si existe para filtrado en wizard
                    if contact.partner_id:
                        partner_list.append(contact.partner_id.id)
        
        # Fallback: Si no hay cliente definido, usar contactos seleccionados
        elif self.contact_ids:
            for contact in self.contact_ids:
                if contact.email and contact.email not in email_list:
                    email_list.append(contact.email)
                    if contact.partner_id:
                        partner_list.append(contact.partner_id.id)
        
        if not email_list:
            raise UserError(_('No se encontraron direcciones de email válidas para enviar el comprobante.'))

        template = self.env.ref('lims_reception.email_template_comprobante', raise_if_not_found=False)
        if not template:
            raise UserError(_('No se encontró la plantilla de correo electrónico.'))

        report = self.env.ref('lims_reception.action_report_custody_chain', raise_if_not_found=False)
        if not report:
            raise UserError(_('No se encontró el reporte de comprobante.'))

        try:
            pdf_content, content_type = report._render_qweb_pdf(
                report_ref='lims_reception.action_report_custody_chain',
                res_ids=[self.id]
            )
        except Exception as e:
            raise UserError(_("Error al generar el PDF: %s") % str(e))
        
        safe_code = self.custody_chain_code.replace('/', '_') if self.custody_chain_code else 'comprobante'
        filename = f'Cadena de custodia {safe_code}.pdf'

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

        # EMAIL SIMPLIFICADO DESDE PYTHON
        email_values = {
            'subject': f'Comprobante de Cadena de Custodia - {self.custody_chain_code}',
            'body_html': f'''
                <p>Estimado/a Cliente,</p>
                <p>Adjunto el comprobante correspondiente a la siguiente Cadena de Custodia:</p>
                <p><strong>Código:</strong> {self.custody_chain_code}</p>
                <p>Gracias por su confianza.</p>
                <br/>
                <p>Atentamente,<br/>El equipo de {self.env.company.name}</p>
            ''',
            'email_from': self.env.user.email,
            'email_to': ','.join(email_list),
            'attachment_ids': [(6, 0, [attachment.id])],
        }

        compose_form = self.env.ref('mail.email_compose_message_wizard_form')

        # Contexto con filtrado de partners
        ctx = {
            'default_model': 'lims.custody_chain',
            'default_res_ids': [self.id],
            'default_composition_mode': 'comment',
            'default_subject': email_values['subject'],
            'default_body': email_values['body_html'],
            'default_email_from': email_values['email_from'],
            'default_attachment_ids': [(6, 0, [attachment.id])],
            'default_email_to': email_values['email_to'],
            # Filtrar solo partners del cliente
            'default_partner_ids': [(6, 0, partner_list)],
            'active_domain': [('id', 'in', partner_list)] if partner_list else [],
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
    
    # REEMPLAZAR EL MÉTODO action_view_signed_document EN lims_custody_chain.py

    def action_view_signed_document(self):
        """Acción para ver/descargar el documento firmado"""
        self.ensure_one()
        
        try:
            # Obtener la referencia del reporte correctamente
            report = self.env.ref('lims_reception.action_report_custody_chain')
            
            # Generar el PDF con la sintaxis correcta
            pdf_content, content_type = report._render_qweb_pdf(
                report_ref='lims_reception.action_report_custody_chain',
                res_ids=[self.id]
            )
            
            # Crear attachment temporal
            safe_code = self.custody_chain_code.replace('/', '_') if self.custody_chain_code else 'comprobante'
            filename = f'{safe_code}.pdf'
            
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            
            # Retornar acción para abrir el PDF
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'new',
            }
            
        except Exception as e:
            raise UserError(_("Error al generar el documento: %s") % str(e))

    def action_assign_analyst(self):
        """Abrir wizard para asignar analista responsable"""
        self.ensure_one()
        
        return self.env['lims.analyst'].open_assignment_wizard(
            source_model='lims.custody_chain',
            source_record_id=self.id,
            source_field='analyst_id',
            action_description=f'Finalizar cadena de custodia {self.custody_chain_code}'
        )

    def action_change_analyst(self):
        """Cambiar analista responsable"""
        self.ensure_one()
        
        # NO limpiar analista actual - el wizard se encarga del cambio
        # self.analyst_id = False  # ELIMINAR ESTA LÍNEA
        
        # Abrir wizard para seleccionar nuevo analista
        return self.env['lims.analyst'].open_assignment_wizard(
            source_model='lims.custody_chain',
            source_record_id=self.id,
            source_field='analyst_id',
            action_description=f'Cambiar analista responsable de cadena {self.custody_chain_code}'
        )

    def unlink(self):
        """Override para mostrar información antes de eliminar"""
        for chain in self:
            samples_count = len(chain.sample_ids)
            if samples_count > 0:
                # Buscar recepciones relacionadas
                receptions = self.env['lims.sample.reception'].search([
                    ('sample_id', 'in', chain.sample_ids.ids)
                ])
                analyses = self.env['lims.analysis.v2'].search([
                    ('sample_reception_id', 'in', receptions.ids)
                ])
                
                message = f"Al eliminar la cadena '{chain.custody_chain_code}' también se eliminarán:\n"
                message += f"• {samples_count} muestras\n"
                message += f"• {len(receptions)} recepciones\n"
                message += f"• {len(analyses)} análisis"
                
                # Log para auditoría
                _logger.info(f"ELIMINACIÓN EN CASCADA: {message}")
        
        return super().unlink()
    
    def copy(self, default=None):
        """Personalizar duplicado de cadenas de custodia CON muestras"""
        if default is None:
            default = {}
        
        # Resetear campos específicos para la nueva cadena
        default.update({
            'custody_chain_code': '/',
            'chain_of_custody_state': 'draft',
            'customer_signature': False,
            'signature_date': False,
            'signature_name': False,
            'signature_position': False,
            'is_signed': False,
            'date_chainofcustody': fields.Date.context_today(self),
            'time_chainofcustody': datetime.now().strftime('%H:%M'),
        })
        
        # Crear la nueva cadena SIN las muestras primero
        new_chain = super().copy(default)
        
        # Ahora copiar manualmente cada muestra
        for sample in self.sample_ids:
            # Copiar la muestra con identificación vacía
            sample.copy({
                'custody_chain_id': new_chain.id,
                'sample_identifier': '',
                'sample_description': '',
            })
        
        return new_chain
    
    def action_duplicate_with_confirmation(self):
        """Mostrar wizard de confirmación antes de duplicar"""
        self.ensure_one()
        
        return {
            'name': _('Confirmar Duplicado'),
            'type': 'ir.actions.act_window',
            'res_model': 'lims.custody_chain.duplicate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_custody_chain_id': self.id,
            }
        }
