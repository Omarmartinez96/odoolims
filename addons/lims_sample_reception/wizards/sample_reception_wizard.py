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
    
    # *** NUEVO CAMPO: Estado de recepción ***
    reception_state = fields.Selection([
        ('recibida', 'Recibida'),
        ('rechazada', 'Rechazada'),
    ], string='Marcar como', default='recibida', required=True)
    
    # Información de recepción
    sample_code = fields.Char(
        string='Código de Muestra',
        readonly=True
    )
    
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
    
    # *** NUEVO CAMPO: Motivo de rechazo ***
    rejection_reason = fields.Text(
        string='Motivo de Rechazo',
        help='Especifique el motivo por el cual se rechaza la muestra'
    )
    
    # Campos computados para mostrar información
    samples_count = fields.Integer(
        string='Número de Muestras',
        compute='_compute_samples_info'
    )
    
    samples_info = fields.Text(
        string='Información de Muestras',
        compute='_compute_samples_info'
    )
    
    # *** NUEVO CAMPO COMPUTADO: Texto de confirmación ***
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
            else:
                record.confirmation_text = ''
    
    @api.depends('sample_id', 'sample_ids', 'reception_mode')
    def _compute_samples_info(self):
        for record in self:
            if record.reception_mode == 'individual' and record.sample_id:
                record.samples_count = 1
                record.samples_info = f"• {record.sample_id.sample_identifier}"
                # Generar código automático
                if record.sample_id.cliente_id:
                    client_code = record.sample_id.cliente_id.client_code or 'XXX'
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
                    next_num = str(max_num + 1).zfill(4)
                    record.sample_code = f'{client_code}/{next_num}'
            elif record.reception_mode == 'mass' and record.sample_ids:
                record.samples_count = len(record.sample_ids)
                info_lines = []
                for sample in record.sample_ids:
                    info_lines.append(f"• {sample.sample_identifier}")
                record.samples_info = "\n".join(info_lines)
                record.sample_code = f"Códigos automáticos ({len(record.sample_ids)} muestras)"
            else:
                record.samples_count = 0
                record.samples_info = ""
                record.sample_code = ""
    
    @api.onchange('reception_state')
    def _onchange_reception_state(self):
        """Limpiar campos según el estado seleccionado"""
        if self.reception_state == 'recibida':
            self.rejection_reason = False
        elif self.reception_state == 'rechazada':
            # Al rechazar, mantener los otros campos pero dar prioridad al motivo
            pass
    
    def action_confirm_reception(self):
        """Confirmar recepción de muestras"""
        self.ensure_one()
        
        # Validar motivo de rechazo
        if self.reception_state == 'rechazada' and not self.rejection_reason:
            raise UserError(_('Debe especificar el motivo de rechazo.'))
        
        samples_to_process = []
        if self.reception_mode == 'individual' and self.sample_id:
            samples_to_process = [self.sample_id]
        elif self.reception_mode == 'mass' and self.sample_ids:
            samples_to_process = self.sample_ids
        
        if not samples_to_process:
            raise UserError(_('No hay muestras para procesar.'))
        
        created_receptions = []
        for sample in samples_to_process:
            # Verificar si ya existe recepción
            existing_reception = self.env['lims.sample.reception'].search([
                ('sample_id', '=', sample.id)
            ], limit=1)
            
            # Preparar datos de recepción
            reception_data = {
                'reception_state': self.reception_state,
                'reception_date': self.reception_date,
                'reception_time': self.reception_time,
                'received_by_initials': self.received_by_initials,
            }
            
            # Agregar observaciones según el estado
            if self.reception_state == 'rechazada':
                reception_data['reception_notes'] = self.rejection_reason
            else:
                reception_data['reception_notes'] = self.reception_notes or ''
            
            if existing_reception:
                # Actualizar existente
                existing_reception.write(reception_data)
                created_receptions.append(existing_reception)
            else:
                # Crear nueva recepción
                reception_data['sample_id'] = sample.id
                new_reception = self.env['lims.sample.reception'].create(reception_data)
                created_receptions.append(new_reception)
        
        # Mensaje de éxito según el estado
        if self.reception_state == 'recibida':
            title = '¡Muestras Recibidas!'
            message = f"Se han marcado como RECIBIDAS {len(created_receptions)} muestra(s) exitosamente."
            msg_type = 'success'
        else:
            title = '¡Muestras Rechazadas!'
            message = f"Se han marcado como RECHAZADAS {len(created_receptions)} muestra(s)."
            msg_type = 'warning'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(title),
                'message': _(message),
                'type': msg_type,
            }
        }