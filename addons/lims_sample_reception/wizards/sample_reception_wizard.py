from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class SampleReceptionWizard(models.TransientModel):
    _name = 'lims.sample.reception.wizard'
    _description = 'Wizard para Recepción de Muestras'

    # Modo: individual o masivo
    reception_mode = fields.Selection([
        ('individual', 'Recepción Individual'),
        ('mass', 'Recepción Masiva')
    ], string='Modo de Recepción', default='individual')
    
    # Para recepción individual
    sample_id = fields.Many2one(
        'lims.sample',
        string='Muestra',
        required=False
    )
    
    # Para recepción masiva
    sample_ids = fields.Many2many(
        'lims.sample',
        string='Muestras Seleccionadas'
    )
    
    # NUEVO: Líneas de muestras con códigos editables
    sample_lines = fields.One2many(
        'lims.sample.reception.line',
        'wizard_id',
        string='Muestras con Códigos'
    )
    
    # Estado de recepción
    reception_state = fields.Selection([
        ('no_recibida', 'No Recibida'),
        ('recibida', 'Recibida'),
        ('rechazada', 'Rechazada'),
    ], string='Estado Final', default='recibida', required=True)
    
    # Información de recepción
    reception_date = fields.Date(
        string='Fecha de Recepción',
        default=fields.Date.context_today,
        required=True
    )
    
    reception_time = fields.Char(
        string='Hora de Recepción',
        default=lambda self: datetime.now().strftime('%H:%M'),
        required=True
    )
    
    received_by_initials = fields.Char(
        string='Iniciales de quien procesó',
        required=True,
        size=5,
        help='Máximo 5 caracteres'
    )
    
    reception_notes = fields.Text(
        string='Observaciones de la Muestra'
    )
    
    # Motivo de rechazo
    rejection_reason = fields.Text(
        string='Motivo de Rechazo',
        help='Especifique el motivo por el cual se rechaza la muestra'
    )
    
    # Texto de confirmación
    confirmation_text = fields.Html(
        string='Texto de Confirmación',
        compute='_compute_confirmation_text'
    )
    
    # Campos para modo edición
    edit_mode = fields.Boolean(
        string='Modo Edición',
        default=False
    )

    reception_id = fields.Many2one(
        'lims.sample.reception',
        string='Recepción a Editar'
    )

    @api.depends('reception_state')
    def _compute_confirmation_text(self):
        for record in self:
            if record.reception_state == 'recibida':
                record.confirmation_text = '''
                    <div style="background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 15px 0; color: #155724;">
                        <p><strong>✅ Al marcar como RECIBIDA, usted acepta que las muestras:</strong></p>
                        <ul style="margin: 10px 0; color: #155724;">
                            <li>• Se encuentran en <strong>buenas condiciones</strong></li>
                            <li>• Tienen <strong>temperatura adecuada</strong></li>
                            <li>• El <strong>recipiente está íntegro</strong> y es adecuado</li>
                            <li>• El <strong>volumen/cantidad es suficiente</strong></li>
                            <li>• Las <strong>condiciones de preservación son correctas</strong></li>
                        </ul>
                    </div>
                '''
            elif record.reception_state == 'rechazada':
                record.confirmation_text = '''
                    <div style="background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 15px 0; color: #721c24;">
                        <p><strong>❌ Al marcar como RECHAZADA, usted confirma que las muestras:</strong></p>
                        <ul style="margin: 10px 0; color: #721c24;">
                            <li>• <strong>NO cumplen</strong> con las condiciones requeridas</li>
                            <li>• <strong>NO pueden ser procesadas</strong> para análisis</li>
                            <li>• Requieren <strong>nueva toma de muestra</strong></li>
                        </ul>
                        <p style="font-weight: bold; color: #721c24;">⚠️ Es OBLIGATORIO especificar el motivo de rechazo</p>
                    </div>
                '''
            elif record.reception_state == 'no_recibida':
                record.confirmation_text = '''
                    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #856404; margin: 15px 0; color: #856404;">
                        <p><strong>⏳ Al marcar como NO RECIBIDA, las muestras:</strong></p>
                        <ul style="margin: 10px 0; color: #856404;">
                            <li>• Volverán a su <strong>estado original</strong></li>
                            <li>• Estarán <strong>pendientes de procesamiento</strong></li>
                            <li>• Podrán ser procesadas <strong>nuevamente</strong></li>
                        </ul>
                        <p style="color: #856404;">💡 Use esta opción para corregir recepciones accidentales</p>
                    </div>
                '''
            else:
                record.confirmation_text = ''
    
    @api.onchange('sample_id', 'sample_ids', 'reception_mode')
    def _onchange_samples(self):
        """Crear líneas automáticamente cuando cambian las muestras"""
        if self.reception_mode == 'individual' and self.sample_id:
            self.sample_lines = [(5, 0, 0)]  # Limpiar líneas existentes
            
            # En modo edición, usar el código existente
            sample_code = False
            if self.edit_mode and self.reception_id:
                sample_code = self.reception_id.sample_code
                
            self.sample_lines = [(0, 0, {
                'sample_id': self.sample_id.id,
                'sample_code': sample_code  # Usar código existente o generar nuevo
            })]
        elif self.reception_mode == 'mass' and self.sample_ids:
            self.sample_lines = [(5, 0, 0)]  # Limpiar líneas existentes
            lines = []
            for sample in self.sample_ids:
                lines.append((0, 0, {'sample_id': sample.id}))
            self.sample_lines = lines

    @api.onchange('reception_state')
    def _onchange_reception_state(self):
        """Limpiar campos según el estado seleccionado"""
        if self.reception_state == 'recibida':
            self.rejection_reason = False
        elif self.reception_state == 'rechazada':
            # Al rechazar, mantener los otros campos pero dar prioridad al motivo
            pass

    def action_confirm_reception(self):
        """Confirmar procesamiento de muestras"""
        self.ensure_one()
        
        # Validar motivo de rechazo
        if self.reception_state == 'rechazada' and not self.rejection_reason:
            raise UserError(_('Debe especificar el motivo de rechazo.'))
        
        if not self.sample_lines:
            raise UserError(_('No hay muestras para procesar.'))
        
        created_receptions = []
        updated_codes = []
        
        for line in self.sample_lines:
            if not line.sample_code:
                raise UserError(_(f'La muestra "{line.sample_identifier}" no tiene código asignado.'))
            
            # Buscar recepción existente
            existing_reception = self.env['lims.sample.reception'].search([
                ('sample_id', '=', line.sample_id.id)
            ], limit=1)
            
            # Preparar datos de recepción
            reception_data = {
                'sample_code': line.sample_code,  # Usar EXACTAMENTE el código del wizard
                'reception_state': self.reception_state,
                'reception_date': self.reception_date,
                'reception_time': self.reception_time,
                'received_by_initials': self.received_by_initials,
            }
            
            # Agregar observaciones según el estado
            if self.reception_state == 'rechazada':
                reception_data['reception_notes'] = self.rejection_reason
            elif self.reception_state == 'no_recibida':
                reception_data['reception_notes'] = 'Estado restaurado a no recibida'
            else:
                reception_data['reception_notes'] = self.reception_notes or ''
            
            if existing_reception:
                # Verificar si el código cambió para mostrar en el mensaje
                old_code = existing_reception.sample_code
                existing_reception.write(reception_data)
                
                if old_code != line.sample_code:
                    updated_codes.append(f'{old_code} → {line.sample_code}')
                else:
                    updated_codes.append(line.sample_code)
                
                created_receptions.append(existing_reception)
            else:
                # Crear nueva recepción
                reception_data['sample_id'] = line.sample_id.id
                new_reception = self.env['lims.sample.reception'].create(reception_data)
                created_receptions.append(new_reception)
                updated_codes.append(f'Nuevo: {line.sample_code}')
        
        # Preparar mensaje de éxito
        if self.reception_state == 'recibida':
            message = f"✅ Se han marcado como RECIBIDAS {len(created_receptions)} muestra(s) exitosamente."
            notification_type = 'success'
        elif self.reception_state == 'rechazada':
            message = f"❌ Se han marcado como RECHAZADAS {len(created_receptions)} muestra(s)."
            notification_type = 'warning'
        else:  # no_recibida
            message = f"⏳ Se han marcado como NO RECIBIDAS {len(created_receptions)} muestra(s). Estado restaurado."
            notification_type = 'success'
        
        # Mostrar códigos procesados
        if updated_codes:
            codes_summary = ', '.join(updated_codes[:3])
            if len(updated_codes) > 3:
                codes_summary += f' y {len(updated_codes) - 3} más...'
            message += f'\n\n📝 Códigos procesados: {codes_summary}'
        
        # Mostrar notificación
        self.env['bus.bus']._sendone(
            self.env.user.partner_id, 
            'simple_notification', 
            {
                'title': 'Procesamiento Completado',
                'message': message,
                'type': notification_type
            }
        )
        
        return {'type': 'ir.actions.act_window_close'}