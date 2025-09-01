from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
from datetime import datetime

class LimsSampleReception(models.Model):
    _name = 'lims.sample.reception'
    _description = 'Recepción de Muestras'
    _rec_name = 'sample_code'
    _order = 'reception_date desc, create_date desc'

    # ==================== CAMPOS ACTIVOS ====================
    
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
    
    # CÓDIGO DE MUESTRA GENERADO
    sample_code = fields.Char(
        string='Código de Muestra',
        copy=False,
        default='/',
        help='Se genera automáticamente: ABC-000/XXXX'
    )
    
    sample_code_barcode = fields.Char(
        string='Código para Código de Barras',
        compute='_compute_sample_code_barcode'
    )

    # FECHA Y HORA DE RECEPCIÓN
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
    
    # ESTADOS DE RECEPCIÓN (MANTENER RECHAZADA)
    reception_state = fields.Selection([
        ('sin_procesar', 'Sin Procesar'),
        ('no_recibida', 'No Recibida'),
        ('rechazada', 'Rechazada'),
        ('recibida', 'Recibida')
    ], string='Estado de Recepción', default='sin_procesar')
    
 ########### DEPRECADO - Mantener por compatibilidad ###########

    # CAMPOS NUEVOS SIMPLIFICADOS
    received_by_initials = fields.Char(
        string='DEPRECADO - Iniciales de quien recibe',
        size=5,
        help='DEPRECADO - Iniciales del técnico que recibe la muestra'
    )

 ########### DEPRECADO - Mantener por compatibilidad ###########

    # Analista responsable de la recepción
    analyst_id = fields.Many2one(
        'lims.analyst',
        string='Responsable de Recepción',
        help='Analista que procesó la recepción de la muestra'
    )

    # Observaciones (ACTIVAS)
    reception_notes = fields.Text(
        string='Observaciones de Recepción'
    )
    internal_reception_notes = fields.Text(
        string='Observaciones Internas de Recepción',
        help='Notas internas del laboratorio sobre la recepción'
    )

    # Técnico que recibe (mantener por compatibilidad)
    received_by = fields.Many2one(
        'res.users',
        string='Recibido por',
        default=lambda self: self.env.user
    )
    
    # Relación con parámetros (IMPORTANTE - MANTENER)
    parameter_ids = fields.One2many(
        related='sample_id.parameter_ids',
        string='Parámetros de la Muestra',
        readonly=False
    )

    # ==================== CAMPOS DEPRECADOS ====================
    # NOTA: Estos campos están deprecados y solo se mantienen por 
    # compatibilidad con registros existentes. NO USAR EN NUEVAS FUNCIONALIDADES.
    
    # Checklist deprecado
    check_conditions = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿La muestra está en buenas condiciones? [DEPRECADO]')
    
    check_temperature = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿La temperatura de recepción es adecuada? [DEPRECADO]')
    
    check_container = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿El recipiente está íntegro? [DEPRECADO]')
    
    check_volume = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿El volumen/cantidad es suficiente? [DEPRECADO]')
    
    check_preservation = fields.Selection([
        ('si', 'Sí'),
        ('no', 'No'),
        ('na', 'N/A')
    ], string='¿Las condiciones de preservación son correctas? [DEPRECADO]')
    
    # Campos de observaciones deprecados
    conditions_notes = fields.Text(string='Observaciones - Condiciones [DEPRECADO]', invisible=True)
    can_process_conditions = fields.Boolean(string='¿Se puede procesar? [DEPRECADO]', invisible=True)
    temperature_notes = fields.Text(string='Observaciones - Temperatura [DEPRECADO]', invisible=True)
    can_process_temperature = fields.Boolean(string='¿Se puede procesar? [DEPRECADO]', invisible=True)
    container_notes = fields.Text(string='Observaciones - Recipiente [DEPRECADO]', invisible=True)
    can_process_container = fields.Boolean(string='¿Se puede procesar? [DEPRECADO]', invisible=True)
    volume_notes = fields.Text(string='Observaciones - Volumen [DEPRECADO]', invisible=True)
    can_process_volume = fields.Boolean(string='¿Se puede procesar? [DEPRECADO]', invisible=True)
    preservation_notes = fields.Text(string='Observaciones - Preservación [DEPRECADO]', invisible=True)
    can_process_preservation = fields.Boolean(string='¿Se puede procesar? [DEPRECADO]', invisible=True)
    
    # Campo computado deprecado
    can_change_state = fields.Boolean(
        string='Puede cambiar estado [DEPRECADO]',
        compute='_compute_can_change_state_deprecated',
        store=True
    )
    
    # ==================== MÉTODOS ACTIVOS ====================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generar código de muestra automáticamente o continuar secuencia"""
        for vals in vals_list:
            if (not vals.get('sample_code') or vals.get('sample_code') == '/') and vals.get('reception_state') == 'recibida':
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
        
        # Crear los registros
        result = super().create(vals_list)
        
        # NUEVO: Crear análisis automáticamente para recepciones marcadas como recibidas
        for record in result:
            if record.reception_state == 'recibida':
                try:
                    existing_analysis = self.env['lims.analysis.v2'].search([
                        ('sample_reception_id', '=', record.id)
                    ])
                    
                    if not existing_analysis:
                        # Crear análisis automáticamente
                        analysis = self.env['lims.analysis.v2'].create({
                            'sample_reception_id': record.id,
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
                except Exception:
                    # Si el modelo de análisis no existe, continuar sin error
                    pass
        
        return result
    
    @api.constrains('sample_code')
    def _check_unique_sample_code(self):
        """Validar que el código de muestra sea único - PROVISIONAL: Advertencia en lugar de error"""
        for record in self:
            if record.sample_code and record.sample_code != '/':
                duplicate = self.search([
                    ('sample_code', '=', record.sample_code),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    # PROVISIONAL: Solo mostrar advertencia en lugar de error
                    self.env['bus.bus']._sendone(
                        self.env.user.partner_id, 
                        'simple_notification', 
                        {
                            'title': 'Advertencia: Código Duplicado',
                            'message': f'El código "{record.sample_code}" ya existe en otra muestra.',
                            'type': 'warning'
                        }
                    )

    def write(self, vals):
        """Override write para crear análisis automáticamente cuando se marca como recibida"""
        
        # NUEVO: Generar código solo cuando se marca como recibida por primera vez
        if vals.get('reception_state') == 'recibida':
            for record in self:
                if not record.sample_code or record.sample_code == '/':
                    # Generar código (misma lógica que en create)
                    sample = record.sample_id
                    if sample and sample.cliente_id:
                        client_code = sample.cliente_id.client_code or 'XXX'
                        
                        existing = self.search([
                            ('sample_code', 'like', f'{client_code}/%'),
                            ('sample_code', '!=', '/')
                        ])
                        
                        def extract_number(code):
                            try:
                                parts = code.split('/')
                                if len(parts) == 2:
                                    return int(parts[1])
                                return 0
                            except (ValueError, IndexError):
                                return 0
                        
                        all_numbers = [extract_number(rec.sample_code) for rec in existing]
                        max_num = max(all_numbers) if all_numbers else 0
                        next_num = str(max_num + 1).zfill(4)
                        vals['sample_code'] = f'{client_code}/{next_num}'
        
        result = super().write(vals)
        
        # Si se cambió el estado a 'recibida', crear análisis automáticamente
        if vals.get('reception_state') == 'recibida':
            for record in self:
                # Verificar que no exista ya un análisis para esta recepción
                try:
                    existing_analysis = self.env['lims.analysis.v2'].search([
                        ('sample_reception_id', '=', record.id)
                    ])
                    
                    if not existing_analysis:
                        # Crear análisis automáticamente (SIN analyst_id)
                        analysis = self.env['lims.analysis.v2'].create({
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
                except Exception:
                    # Si el modelo de análisis no existe, continuar sin error
                    pass
        
        return result

    def action_print_label(self):
        """Imprimir etiqueta individual de muestra"""
        self.ensure_one()
        
        if not self.sample_code or self.sample_code == '/':
            raise UserError(_('La muestra debe tener un código asignado para imprimir la etiqueta.'))
        
        return self.env.ref('lims_sample_reception.action_report_sample_label').report_action(self)

    @api.depends('sample_code')
    def _compute_sample_code_barcode(self):
        """Usar código completo sin modificaciones"""
        for record in self:
            # Usar el código COMPLETO tal como está: PFI-068/0001
            record.sample_code_barcode = record.sample_code or ''

    @api.depends('analyst_id')
    def _compute_received_by_initials(self):
        """Obtener iniciales automáticamente del analista responsable"""
        for record in self:
            if record.analyst_id and record.analyst_id.initials:
                record.received_by_initials = record.analyst_id.initials
            else:
                record.received_by_initials = ''

    # ==================== MÉTODOS DEPRECADOS ====================
    # NOTA: Estos métodos están deprecados y solo se mantienen por compatibilidad

    @api.depends('check_conditions', 'check_temperature', 
                'check_container', 'check_volume', 'check_preservation')
    def _compute_can_change_state_deprecated(self):
        """MÉTODO DEPRECADO - Mantener solo por compatibilidad"""
        for record in self:
            record.can_change_state = True  # Siempre True para evitar errores
    
    @api.onchange('check_conditions')
    def _onchange_check_conditions(self):
        """MÉTODO DEPRECADO - No hacer nada"""
        if self.check_conditions != 'no':
            self.conditions_notes = False
            self.can_process_conditions = False

    @api.onchange('check_temperature')
    def _onchange_check_temperature(self):
        """MÉTODO DEPRECADO - No hacer nada"""
        if self.check_temperature != 'no':
            self.temperature_notes = False
            self.can_process_temperature = False

    @api.onchange('check_container')
    def _onchange_check_container(self):
        """MÉTODO DEPRECADO - No hacer nada"""
        if self.check_container != 'no':
            self.container_notes = False
            self.can_process_container = False

    @api.onchange('check_volume')
    def _onchange_check_volume(self):
        """MÉTODO DEPRECADO - No hacer nada"""
        if self.check_volume != 'no':
            self.volume_notes = False
            self.can_process_volume = False

    @api.onchange('check_preservation')
    def _onchange_check_preservation(self):
        """MÉTODO DEPRECADO - No hacer nada"""
        if self.check_preservation != 'no':
            self.preservation_notes = False
            self.can_process_preservation = False

    @api.onchange('template_id')
    def _onchange_template_id(self):
        """MÉTODO DEPRECADO - No hacer nada"""
        if self.template_id:
            template = self.template_id
            # SOLO campos esenciales para recepción
            self.name = template.name
            self.method = template.method
            self.category = template.category
            self.microorganism = template.microorganism
            self.unit = template.unit

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

    sample_code = fields.Char(
        string="Código de Muestra",
        compute='_compute_sample_code',
        help="Código generado en la recepción"
    )

    date_chainofcustody = fields.Date(
        string='Fecha de CC',
        related='custody_chain_id.date_chainofcustody',
        readonly=True,
        store=False
    )

    def action_mass_reception_selected(self):
        """Abrir wizard para recepción masiva de muestras seleccionadas"""
        selected_samples = self.browse(self.env.context.get('active_ids', []))
        
        if not selected_samples:
            raise UserError(_('Debe seleccionar al menos una muestra.'))
        
        # Verificar que no hay muestras ya recibidas
        already_received = []
        for sample in selected_samples:
            reception = self.env['lims.sample.reception'].search([
                ('sample_id', '=', sample.id)
            ], limit=1)
            if reception and reception.reception_state == 'recibida':
                already_received.append(sample.sample_identifier)
        
        if already_received:
            samples_list = ', '.join(already_received[:3])
            if len(already_received) > 3:
                samples_list += f' y {len(already_received) - 3} más'
            raise UserError(_(
                f'No se puede procesar la recepción masiva porque las siguientes muestras ya están recibidas:\n\n'
                f'{samples_list}\n\n'
                f'Para modificar muestras ya recibidas, use la opción "Editar" individual.'
            ))
        
        return {
            'name': _('Recepción Masiva de Muestras'),
            'type': 'ir.actions.act_window',
            'res_model': 'lims.sample.reception.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reception_mode': 'mass',
                'default_sample_ids': [(6, 0, selected_samples.ids)],
            }
        }

    def _compute_sample_code(self):
        """Obtener código desde la recepción asociada"""
        for record in self:
            reception = self.env['lims.sample.reception'].search([
                ('sample_id', '=', record.id)
            ], limit=1)
            
            if reception and reception.sample_code and reception.sample_code != '/':
                record.sample_code = reception.sample_code
            else:
                record.sample_code = 'Pendiente'

    def _compute_sample_reception_state(self):
        """Mostrar estado de recepción de la muestra"""
        for record in self:
            reception = self.env['lims.sample.reception'].search([
                ('sample_id', '=', record.id)
            ], limit=1)
            
            if reception:
                states = {
                    'sin_procesar': 'Sin Procesar',
                    'no_recibida': 'No Recibida',
                    'rechazada': 'Rechazada', 
                    'recibida': 'Recibida'
                }
                record.sample_reception_state = states.get(reception.reception_state, 'Sin estado')
            else:
                record.sample_reception_state = 'Sin Procesar'

    def has_sample_code(self):
        """Método simple para verificar si tiene código de muestra"""
        reception = self.env['lims.sample.reception'].search([
            ('sample_id', '=', self.id)
        ], limit=1)
        
        return bool(
            reception and 
            reception.sample_code and 
            reception.sample_code != '/'
        )

    # NUEVO MÉTODO PARA WIZARD INDIVIDUAL
    def action_individual_reception_wizard(self):
        """Abrir wizard para recepción individual"""
        self.ensure_one()
        
        return {
            'name': _('Recepción Individual de Muestra'),
            'type': 'ir.actions.act_window',
            'res_model': 'lims.sample.reception.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reception_mode': 'individual',
                'default_sample_id': self.id,
            }
        }

    def action_edit_reception_wizard(self):
        """Abrir wizard para editar recepción existente"""
        self.ensure_one()
        
        # Buscar la recepción existente
        reception = self.env['lims.sample.reception'].search([
            ('sample_id', '=', self.id)
        ], limit=1)
        
        if not reception:
            raise UserError(_('No se encontró recepción para esta muestra.'))
        
        return {
            'name': _('Editar Recepción de Muestra'),
            'type': 'ir.actions.act_window',
            'res_model': 'lims.sample.reception.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reception_mode': 'individual',
                'default_sample_id': self.id,
                'edit_mode': True,
                'reception_id': reception.id,
            }
        }

    def action_print_sample_label(self):
        """Imprimir etiqueta desde muestra"""
        self.ensure_one()
        
        # Buscar la recepción de esta muestra
        reception = self.env['lims.sample.reception'].search([
            ('sample_id', '=', self.id)
        ], limit=1)
        
        if not reception:
            raise UserError(_('Debe crear primero la recepción de esta muestra.'))
        
        return reception.action_print_label()

# CLASE 3: Herencia de LimsCustodyChain  
class LimsCustodyChain(models.Model):
    _inherit = 'lims.custody_chain'
    
    samples_total = fields.Integer(
        string='Total Muestras',
        compute='_compute_reception_stats'
    )
    samples_received = fields.Integer(
        string='Recibidas',
        compute='_compute_reception_stats'
    )
    samples_rejected = fields.Integer(
        string='Rechazadas', 
        compute='_compute_reception_stats'
    )
    samples_pending = fields.Integer(
        string='Pendientes',
        compute='_compute_reception_stats'
    )

    reception_status_display = fields.Char(
        string='Estado General',
        compute='_compute_reception_stats'
    )

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
    
    @api.depends('sample_ids')
    def _compute_reception_stats(self):
        """Calcular estadísticas de recepción"""
        for record in self:
            total = len(record.sample_ids)
            received = rejected = pending = 0
            
            for sample in record.sample_ids:
                reception = self.env['lims.sample.reception'].search([
                    ('sample_id', '=', sample.id)
                ], limit=1)
                
                if reception:
                    if reception.reception_state == 'recibida':
                        received += 1
                    elif reception.reception_state == 'rechazada':
                        rejected += 1
                    else:
                        pending += 1
                else:
                    pending += 1
            
            record.samples_total = total
            record.samples_received = received
            record.samples_rejected = rejected
            record.samples_pending = pending
            
            # Determinar estado general
            if total == 0:
                record.reception_status_display = 'Sin Muestras'
            elif pending == total:
                record.reception_status_display = 'Sin Procesar'
            elif pending == 0:
                record.reception_status_display = 'Completo'
            else:
                record.reception_status_display = 'En Proceso'

    def action_mass_reception_wizard(self):
        """Abrir wizard para recepción masiva"""
        self.ensure_one()
        
        # Si se llama desde la vista de lista con selecciones
        selected_ids = self.env.context.get('active_ids', [])
        if selected_ids and self.env.context.get('active_model') == 'lims.sample':
            samples = self.env['lims.sample'].browse(selected_ids)
        else:
            # Si se llama desde el formulario de cadena de custodia
            samples = self.sample_ids
        
        if not samples:
            raise UserError(_('No hay muestras en esta cadena de custodia.'))
        
        return {
            'name': _('Recepción Masiva de Muestras'),
            'type': 'ir.actions.act_window',
            'res_model': 'lims.sample.reception.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reception_mode': 'mass',
                'default_sample_ids': [(6, 0, samples.ids)],
            }
        }
    
    def action_samples_reception_multiselect(self):
        """Abrir vista de muestras para selección múltiple"""
        self.ensure_one()
        
        return {
            'name': _('Muestras - Selección Múltiple'),
            'type': 'ir.actions.act_window',
            'res_model': 'lims.sample',
            'view_mode': 'list',
            'view_id': self.env.ref('lims_sample_reception.view_samples_reception_list').id,
            'domain': [('custody_chain_id', '=', self.id)],
            'context': {
                'default_custody_chain_id': self.id,
            },
            'target': 'current',
        }
    
    def action_print_all_labels(self):
        """Imprimir etiquetas de todas las muestras"""
        self.ensure_one()
        
        if not self.sample_ids:
            raise UserError(_('No hay muestras en esta cadena de custodia.'))
        
        # Verificar que las muestras tengan recepciones con códigos
        samples_without_reception = []
        for sample in self.sample_ids:
            reception = self.env['lims.sample.reception'].search([
                ('sample_id', '=', sample.id)
            ], limit=1)
            if not reception or not reception.sample_code or reception.sample_code == '/':
                samples_without_reception.append(sample.sample_identifier)
        
        if samples_without_reception:
            raise UserError(_(
                'Las siguientes muestras no tienen código asignado y no se pueden imprimir etiquetas:\n' +
                '\n'.join(samples_without_reception) +
                '\n\nPrimero debe crear las recepciones para estas muestras.'
            ))
        
        return self.env.ref('lims_sample_reception.action_report_sample_labels_mass').report_action(self)
    
    def action_assign_change_analyst(self):
        """Abrir wizard universal para asignar/cambiar analista responsable"""
        self.ensure_one()
        
        action_description = "Cambiar responsable de recepción" if self.analyst_id else "Asignar responsable de recepción"
        
        return self.env['lims.analyst'].open_assignment_wizard(
            source_model='lims.sample.reception',
            source_record_id=self.id,
            source_field='analyst_id',
            action_description=f'{action_description} - Muestra {self.sample_code}'
        )