from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
from datetime import datetime

class LimsSampleReception(models.Model):
    _name = 'lims.sample.reception'
    _description = 'Recepción de Muestras'
    _rec_name = 'sample_code'
    _order = 'reception_date desc, create_date desc'

    # Relación con la muestra original
    sample_id = fields.Many2one(
        'lims.sample',
        string='Muestra',
        required=True,
        ondelete='cascade'
    )
    
    # Información heredada de la muestra
    sample_identifier = fields.Char(
        string='Identificación Original',
        related='sample_id.sample_identifier',
        readonly=True
    )
    custody_chain_id = fields.Many2one(
        'lims.custody_chain',
        string='Cadena de Custodia',
        related='sample_id.custody_chain_id',
        readonly=True
    )
    cliente_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='sample_id.cliente_id',
        readonly=True
    )
    
    # 🆕 CÓDIGO DE MUESTRA GENERADO
    sample_code = fields.Char(
        string='Código de Muestra',
        copy=False,
        default='/',
        help='Se genera automáticamente: ABC-000/XXXX'
    )
    
    # 🆕 FECHA Y HORA DE RECEPCIÓN
    reception_date = fields.Date(
        string='Fecha de Recepción',
        default=fields.Date.context_today,
        required=True
    )
    reception_time = fields.Char(
        string='Hora de Recepción',
        placeholder='HH:MM',
        help='Formato: HH:MM (ej: 14:30)'
    )
    
    # 🆕 CHECKLIST DE RECEPCIÓN
    check_conditions = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿La muestra está en buenas condiciones?')
    
    check_temperature = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿La temperatura de recepción es adecuada?')
    
    check_container = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿El recipiente está íntegro y es el adecuado para el tipo de muestra?')
    
    check_volume = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿El volumen/cantidad es suficiente?')
    
    check_preservation = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿Las condiciones de preservación son correctas?')
        
    # Campos de observaciones cuando la respuesta es NO
    conditions_notes = fields.Text(
        string='Observaciones - Condiciones',
        invisible=True
    )
    can_process_conditions = fields.Boolean(
        string='¿Se puede procesar?',
        invisible=True
    )

    temperature_notes = fields.Text(
        string='Observaciones - Temperatura',
        invisible=True
    )
    can_process_temperature = fields.Boolean(
        string='¿Se puede procesar?',
        invisible=True
    )

    container_notes = fields.Text(
        string='Observaciones - Recipiente',
        invisible=True
    )
    can_process_container = fields.Boolean(
        string='¿Se puede procesar?',
        invisible=True
    )

    volume_notes = fields.Text(
        string='Observaciones - Volumen',
        invisible=True
    )
    can_process_volume = fields.Boolean(
        string='¿Se puede procesar?',
        invisible=True
    )

    preservation_notes = fields.Text(
        string='Observaciones - Preservación',
        invisible=True
    )
    can_process_preservation = fields.Boolean(
        string='¿Se puede procesar?',
        invisible=True
    )

    # 🆕 ESTADOS DE RECEPCIÓN
    reception_state = fields.Selection([
        ('no_recibida', 'No Recibida'),
        ('rechazada', 'Rechazada'),
        ('recibida', 'Recibida')
    ], string='Estado de Recepción', default='no_recibida')
    
    # Campo computado para habilitar cambio de estado
    can_change_state = fields.Boolean(
        string='Puede cambiar estado',
        compute='_compute_can_change_state',
        store=True
    )
    
    # Observaciones
    reception_notes = fields.Text(
        string='Observaciones de Recepción'
    )
    # Observaciones internas de recepción
    internal_reception_notes = fields.Text(
        string='Observaciones Internas de Recepción',
        help='Notas internas del laboratorio sobre la recepción'
    )

    # Técnico que recibe
    received_by = fields.Many2one(
        'res.users',
        string='Recibido por',
        default=lambda self: self.env.user
    )
    
    # Relación con parámetros (MOVIDO AQUÍ)
    parameter_ids = fields.One2many(
        related='sample_id.parameter_ids',
        string='Parámetros de la Muestra',
        readonly=False
    )
    
    # MÉTODOS DE LimsSampleReception
    @api.depends('check_conditions', 'check_temperature', 
                'check_container', 'check_volume', 'check_preservation')
    def _compute_can_change_state(self):
        """Permite cambiar estado solo si TODOS los checks están completados"""
        for record in self:
            checks = [
                record.check_conditions,
                record.check_temperature,
                record.check_container,
                record.check_volume,
                record.check_preservation
            ]
            # Todos los checks deben tener una respuesta (no estar vacíos)
            all_answered = all(check for check in checks)
            record.can_change_state = all_answered
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generar código de muestra automáticamente o continuar secuencia"""
        for vals in vals_list:
            if not vals.get('sample_code') or vals.get('sample_code') == '/':
                sample = self.env['lims.sample'].browse(vals.get('sample_id'))
                if sample and sample.cliente_id:
                    client_code = sample.cliente_id.client_code or 'XXX'
                    
                    # Buscar TODOS los códigos existentes para este cliente
                    existing = self.search([
                        ('sample_code', 'like', f'{client_code}/%'),
                        ('sample_code', '!=', '/')
                    ])
                    
                    # Extraer el mayor número consecutivo existente
                    def extract_number(code):
                        try:
                            # Formato: ABC/0001
                            parts = code.split('/')
                            if len(parts) == 2:
                                return int(parts[1])
                            return 0
                        except (ValueError, IndexError):
                            return 0
                    
                    # Encontrar el número más alto
                    all_numbers = [extract_number(rec.sample_code) for rec in existing]
                    max_num = max(all_numbers) if all_numbers else 0
                    
                    # El siguiente consecutivo con 4 dígitos
                    next_num = str(max_num + 1).zfill(4)
                    vals['sample_code'] = f'{client_code}/{next_num}'
        
        return super().create(vals_list)
    
    @api.constrains('sample_code')
    def _check_unique_sample_code(self):
        """Validar que el código de muestra sea único"""
        for record in self:
            if record.sample_code and record.sample_code != '/':
                duplicate = self.search([
                    ('sample_code', '=', record.sample_code),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise UserError(f'El código de muestra "{record.sample_code}" ya existe. Debe ser único.')
                
    @api.onchange('check_conditions')
    def _onchange_check_conditions(self):
        if self.check_conditions != 'no':
            self.conditions_notes = False
            self.can_process_conditions = False

    @api.onchange('check_temperature')
    def _onchange_check_temperature(self):
        if self.check_temperature != 'no':
            self.temperature_notes = False
            self.can_process_temperature = False

    @api.onchange('check_container')
    def _onchange_check_container(self):
        if self.check_container != 'no':
            self.container_notes = False
            self.can_process_container = False

    @api.onchange('check_volume')
    def _onchange_check_volume(self):
        if self.check_volume != 'no':
            self.volume_notes = False
            self.can_process_volume = False

    @api.onchange('check_preservation')
    def _onchange_check_preservation(self):
        if self.check_preservation != 'no':
            self.preservation_notes = False
            self.can_process_preservation = False

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            template = self.template_id
            # SOLO campos esenciales para recepción
            self.name = template.name
            self.method = template.method
            self.category = template.category
            self.microorganism = template.microorganism
            self.unit = template.unit

    def write(self, vals):
        """Override write para crear análisis automáticamente cuando se marca como recibida"""
        result = super().write(vals)
        
        # Si se cambió el estado a 'recibida', crear análisis automáticamente
        if vals.get('reception_state') == 'recibida':
            for record in self:
                # Verificar que no exista ya un análisis para esta recepción
                existing_analysis = self.env['lims.analysis'].search([
                    ('sample_reception_id', '=', record.id)
                ])
                
                if not existing_analysis:
                    # Crear análisis automáticamente (SIN analyst_id)
                    analysis = self.env['lims.analysis'].create({
                        'sample_reception_id': record.id,
                        # Removido: 'analyst_id': self.env.user.id,
                    })
                    
                    # Mostrar notificación de éxito
                    self.env['bus.bus']._sendone(
                        self.env.user.partner_id, 
                        'simple_notification', 
                        {
                            'title': 'Análisis Creado',
                            'message': f'Se creó automáticamente el análisis para la muestra {record.sample_code}',
                            'type': 'success'
                        }
                    )
        
        return result


# CLASE 2: Herencia de LimsSample
class LimsSample(models.Model):
    _inherit = 'lims.sample'
    
    def action_create_reception(self):
        """Crear o abrir recepción para esta muestra"""
        # Buscar si ya existe una recepción para esta muestra
        reception = self.env['lims.sample.reception'].search([
            ('sample_id', '=', self.id)
        ], limit=1)
        
        if reception:
            # Si ya existe, abrir la existente
            return {
                'type': 'ir.actions.act_window',
                'name': 'Recepción de Muestra',
                'res_model': 'lims.sample.reception',
                'res_id': reception.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            # Crear nueva recepción
            new_reception = self.env['lims.sample.reception'].create({
                'sample_id': self.id,
            })
            return {
                'type': 'ir.actions.act_window',
                'name': 'Recepción de Muestra',
                'res_model': 'lims.sample.reception',
                'res_id': new_reception.id,
                'view_mode': 'form',
                'target': 'current',
            }

    sample_reception_state = fields.Char(
        string='Estado Recepción',
        compute='_compute_sample_reception_state'
    )

    def _compute_sample_reception_state(self):
        """Mostrar estado de recepción de la muestra"""
        for record in self:
            reception = self.env['lims.sample.reception'].search([
                ('sample_id', '=', record.id)
            ], limit=1)
            
            if reception:
                states = {
                    'no_recibida': 'No Recibida',
                    'rechazada': 'Rechazada', 
                    'recibida': 'Recibida'
                }
                record.sample_reception_state = states.get(reception.reception_state, 'Sin estado')
            else:
                record.sample_reception_state = 'No recibida'


# CLASE 3: Herencia de LimsCustodyChain  
class LimsCustodyChain(models.Model):
    _inherit = 'lims.custody_chain'
    
    def action_send_reception_report_email(self):
        """Enviar informe de recepción por correo electrónico"""
        self.ensure_one()
        
        # Verificar que hay muestras procesadas
        if not self.sample_ids:
            raise UserError(_('No hay muestras para enviar en el informe.'))
        
        # Obtener direcciones de email (similar al método de cadena de custodia)
        email_list = []
        partner_list = []
        
        # Agregar email del cliente principal
        if self.cliente_id and self.cliente_id.email:
            email_list.append(self.cliente_id.email)
            partner_list.append(self.cliente_id.id)
        
        # Agregar contactos del cliente
        if self.cliente_id:
            client_contacts = self.env['lims.contact'].search([
                ('department_id.branch_id.customer_id', '=', self.cliente_id.id)
            ])
            
            for contact in client_contacts:
                if contact.email and contact.email not in email_list:
                    email_list.append(contact.email)
                    if contact.partner_id:
                        partner_list.append(contact.partner_id.id)
        
        # Fallback: contactos seleccionados
        elif self.contact_ids:
            for contact in self.contact_ids:
                if contact.email and contact.email not in email_list:
                    email_list.append(contact.email)
                    if contact.partner_id:
                        partner_list.append(contact.partner_id.id)
        
        if not email_list:
            raise UserError(_('No se encontraron direcciones de email válidas para enviar el informe.'))

        # Generar el reporte PDF
        report = self.env.ref('lims_sample_reception.action_report_sample_reception', raise_if_not_found=False)
        if not report:
            raise UserError(_('No se encontró el reporte de recepción de muestras.'))

        try:
            pdf_content, content_type = report._render_qweb_pdf(
                report_ref='lims_sample_reception.action_report_sample_reception',
                res_ids=[self.id]
            )
        except Exception as e:
            raise UserError(_("Error al generar el PDF: %s") % str(e))
        
        # Crear nombre del archivo
        safe_code = self.custody_chain_code.replace('/', '_') if self.custody_chain_code else 'recepcion'
        filename = f'Informe de Recepción - {safe_code}.pdf'

        # Crear attachment
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

        # Preparar valores del email
        email_values = {
            'subject': f'Informe de Recepción de Muestras - {self.custody_chain_code}',
            'body_html': f'''
                <p>Estimado/a Cliente,</p>
                <p>Adjunto el informe de recepción de muestras correspondiente a:</p>
                <p><strong>Cadena de Custodia:</strong> {self.custody_chain_code}</p>
                <p><strong>Cliente:</strong> {self.cliente_id.name}</p>
                <p>Este informe detalla el estado de recepción de cada una de las muestras procesadas.</p>
                <br/>
                <p>Atentamente,<br/>El equipo de {self.env.company.name}</p>
            ''',
            'email_from': self.env.user.email,
            'email_to': ','.join(email_list),
            'attachment_ids': [(6, 0, [attachment.id])],
        }

        # Abrir wizard de envío
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')

        ctx = {
            'default_model': 'lims.custody_chain',
            'default_res_ids': [self.id],
            'default_composition_mode': 'comment',
            'default_subject': email_values['subject'],
            'default_body': email_values['body_html'],
            'default_email_from': email_values['email_from'],
            'default_attachment_ids': [(6, 0, [attachment.id])],
            'default_email_to': email_values['email_to'],
            'default_partner_ids': [(6, 0, partner_list)],
        }

        return {
            'name': _('Enviar Informe de Recepción'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'views': [(compose_form.id, 'form')],
            'target': 'new',
            'context': ctx,
        }