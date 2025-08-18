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
            self.sample_lines = [(0, 0, {'sample_id': self.sample_id.id})]
        elif self.reception_mode == 'mass' and self.sample_ids:
            self.sample_lines = [(5, 0, 0)]  # Limpiar líneas existentes
            lines = []
            for sample in self.sample_ids:
                lines.append((0, 0, {'sample_id': sample.id}))
            self.sample_lines = lines

    @api.onchange('sample_lines')
    def _onchange_sample_lines(self):
        """Recalcular códigos cuando se modifican las líneas"""
        if self.sample_lines:
            # Reagrupar por cliente
            client_groups = {}
            for line in self.sample_lines:
                if line.sample_id and line.sample_id.cliente_id:
                    client_code = line.sample_id.cliente_id.client_code or 'XXX'
                    if client_code not in client_groups:
                        client_groups[client_code] = []
                    client_groups[client_code].append(line)
            
            # Recalcular códigos para cada grupo de cliente
            for client_code, client_lines in client_groups.items():
                # Buscar el máximo número existente en la base de datos
                existing = self.env['lims.sample.reception'].search([
                    ('sample_code', 'like', f'{client_code}/%'),
                    ('sample_code', '!=', '/')
                ])
                
                max_num = 0
                for rec in existing:
                    try:
                        parts = rec.sample_code.split('/')
                        if len(parts) == 2:
                            num = int(parts[1])
                            if num > max_num:
                                max_num = num
                    except:
                        pass
                
                # Asignar códigos secuenciales
                for i, line in enumerate(client_lines):
                    next_num = str(max_num + 1 + i).zfill(4)
                    new_code = f'{client_code}/{next_num}'
                    line.suggested_code = new_code
                    if not line.sample_code or line.sample_code == line.suggested_code:
                        line.sample_code = new_code

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
        for line in self.sample_lines:
            if not line.sample_code:
                raise UserError(_(f'La muestra "{line.sample_identifier}" no tiene código asignado.'))
            
            # Verificar si ya existe recepción
            existing_reception = self.env['lims.sample.reception'].search([
                ('sample_id', '=', line.sample_id.id)
            ], limit=1)
            
            # Preparar datos de recepción
            reception_data = {
                'sample_code': line.sample_code,
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
                existing_reception.write(reception_data)
                created_receptions.append(existing_reception)
            else:
                reception_data['sample_id'] = line.sample_id.id
                new_reception = self.env['lims.sample.reception'].create(reception_data)
                created_receptions.append(new_reception)
        
        # Preparar mensaje de éxito
        if self.reception_state == 'recibida':
            message = f"Se han marcado como RECIBIDAS {len(created_receptions)} muestra(s) exitosamente."
            notification_type = 'success'
        elif self.reception_state == 'rechazada':
            message = f"Se han marcado como RECHAZADAS {len(created_receptions)} muestra(s)."
            notification_type = 'warning'
        else:  # no_recibida
            message = f"Se han marcado como NO RECIBIDAS {len(created_receptions)} muestra(s). Estado restaurado."
            notification_type = 'success'
        
        # Mostrar notificación usando el bus
        self.env['bus.bus']._sendone(
            self.env.user.partner_id, 
            'simple_notification', 
            {
                'title': 'Procesamiento Completado',
                'message': message,
                'type': notification_type
            }
        )
        
        # Cerrar el wizard
        return {'type': 'ir.actions.act_window_close'}