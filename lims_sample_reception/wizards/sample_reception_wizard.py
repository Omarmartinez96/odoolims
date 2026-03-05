from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import pytz

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
        ('sin_procesar', 'Sin Procesar'),
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
        default=lambda self: datetime.now(pytz.timezone('America/Tijuana')).strftime('%H:%M'),
        required=True
    )

    #### DEPRECADO: Iniciales de quien procesó ####
    received_by_initials = fields.Char(
        string='DEPRECADO: Iniciales de quien procesó',
        size=5,
        help='DEPRECADO: Iniciales de quien procesó la recepción'
    )
    #### DEPRECADO: Iniciales de quien procesó ####

    # Verificación temporal de analista (solo para esta sesión)
    analyst_id = fields.Many2one(
        'lims.analyst',
        string='Responsable de la Recepción',
        domain=[('active', '=', True), ('pin_hash', '!=', False)],
        help='Analista que procesa la recepción (solo con PIN configurado)'
    )

    pin_input = fields.Char(
        string='PIN de Verificación',
        help='Ingrese su PIN para confirmar el procesamiento'
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
                        <p><strong>⚠️ Al marcar como NO RECIBIDA, las muestras:</strong></p>
                        <ul style="margin: 10px 0; color: #856404;">
                            <li>• Se <strong>facturan normalmente</strong> al cliente</li>
                            <li>• <strong>NO tienen código asignado</strong></li>
                            <li>• <strong>NO se procesarán</strong> para análisis</li>
                            <li>• Quedan <strong>registradas en el sistema</strong></li>
                        </ul>
                        <p style="color: #856404;">📋 Use para puntos cerrados, sin agua, etc.</p>
                    </div>
                '''
            elif record.reception_state == 'sin_procesar':
                record.confirmation_text = '''
                    <div style="background-color: #e2e3e5; padding: 15px; border-left: 4px solid #6c757d; margin: 15px 0; color: #383d41;">
                        <p><strong>⚪ Al marcar como SIN PROCESAR, las muestras:</strong></p>
                        <ul style="margin: 10px 0; color: #383d41;">
                            <li>• Regresan a su <strong>estado inicial</strong></li>
                            <li>• <strong>NO tienen código asignado</strong></li>
                            <li>• Están <strong>pendientes de procesamiento</strong></li>
                            <li>• Pueden ser procesadas <strong>posteriormente</strong></li>
                        </ul>
                        <p style="color: #383d41;">💡 Este es el estado predeterminado de las muestras</p>
                    </div>
                '''
            else:
                record.confirmation_text = ''
    
    @api.model
    def default_get(self, fields_list):
        """Pre-cargar datos si es modo edición"""
        res = super().default_get(fields_list)
        
        # Verificar si es modo edición
        if self.env.context.get('edit_mode'):
            reception_id = self.env.context.get('reception_id')
            if reception_id:
                reception = self.env['lims.sample.reception'].browse(reception_id)
                if reception.exists():
                    # Pre-cargar datos de la recepción existente
                    res.update({
                        'edit_mode': True,
                        'reception_id': reception.id,
                        'reception_state': reception.reception_state,
                        'reception_date': reception.reception_date,
                        'reception_time': reception.reception_time,
                        'reception_notes': reception.reception_notes,
                        'analyst_id': reception.analyst_id.id if reception.analyst_id else False,
                    })
                    
                    # Si está rechazada, cargar motivo de rechazo
                    if reception.reception_state == 'rechazada':
                        res['rejection_reason'] = reception.reception_notes
                    
                    # NUEVO: Pre-cargar las líneas de muestra con el código EXISTENTE
                    if self.env.context.get('default_reception_mode') == 'individual':
                        sample_id = self.env.context.get('default_sample_id')
                        if sample_id:
                            res['sample_lines'] = [(0, 0, {
                                'sample_id': sample_id,
                                'sample_code': reception.sample_code  # Usar código EXISTENTE
                            })]
        
        return res

    @api.onchange('sample_id', 'sample_ids', 'reception_mode')
    def _onchange_samples(self):
        """Crear líneas automáticamente cuando cambian las muestras"""
        # NO hacer nada si estamos en modo edición y ya hay líneas pre-cargadas
        if self.edit_mode and self.sample_lines:
            return
            
        if self.reception_mode == 'individual' and self.sample_id:
            self.sample_lines = [(5, 0, 0)]  # Limpiar líneas existentes
            self.sample_lines = [(0, 0, {'sample_id': self.sample_id.id})]
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

    def _validate_analyst_pin(self):
        """Validar analista y PIN"""
        if not self.analyst_id:
            raise UserError(_('Debe seleccionar el analista responsable.'))
        
        if not self.pin_input:
            raise UserError(_('Debe ingresar su PIN de verificación.'))
        
        if not self.analyst_id.validate_pin(self.pin_input):
            raise UserError(_('PIN incorrecto. Verifique e intente nuevamente.'))
        
        return True

    def action_confirm_reception(self):
        """Confirmar procesamiento de muestras"""
        self.ensure_one()
        
        # Validar analista y PIN PRIMERO
        self._validate_analyst_pin()
        
        # Validar motivo de rechazo
        if self.reception_state == 'rechazada' and not self.rejection_reason:
            raise UserError(_('Debe especificar el motivo de rechazo.'))
        
        if not self.sample_lines:
            raise UserError(_('No hay muestras para procesar.'))
        
        created_receptions = []
        updated_codes = []
        
        for line in self.sample_lines:
            # Solo requerir código si el estado es 'recibida'
            if self.reception_state == 'recibida':
                if not line.sample_code or line.sample_code.strip() == '':
                    # Generar código automáticamente usando el código sugerido
                    line.sample_code = line.suggested_code
            else:
                # Para otros estados, limpiar el código
                line.sample_code = '/'
            
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
                'analyst_id': self.analyst_id.id,  # Guardar analista responsable
            }
            
            # Agregar observaciones según el estado
            if self.reception_state == 'rechazada':
                reception_data['reception_notes'] = self.rejection_reason
            else:
                # Para 'recibida', 'no_recibida' y 'sin_procesar', usar observaciones del wizard o mantener existentes
                reception_data['reception_notes'] = self.reception_notes or ''
            
            if existing_reception:
                # Verificar si el código cambió para mostrar en el mensaje
                old_code = existing_reception.sample_code
                existing_reception.write(reception_data)
                
                if old_code != line.sample_code:
                    updated_codes.append(f'{old_code} → {line.sample_code}')
                else:
                    updated_codes.append(line.sample_code if line.sample_code != '/' else 'Sin código')
                
                created_receptions.append(existing_reception)
            else:
                # Crear nueva recepción
                reception_data['sample_id'] = line.sample_id.id
                new_reception = self.env['lims.sample.reception'].create(reception_data)
                created_receptions.append(new_reception)
                updated_codes.append(f'Nuevo: {line.sample_code if line.sample_code != "/" else "Sin código"}')
        
        # Preparar mensaje de éxito
        if self.reception_state == 'recibida':
            message = f"✅ Se han marcado como RECIBIDAS {len(created_receptions)} muestra(s) exitosamente."
            notification_type = 'success'
        elif self.reception_state == 'rechazada':
            message = f"❌ Se han marcado como RECHAZADAS {len(created_receptions)} muestra(s)."
            notification_type = 'warning'
        elif self.reception_state == 'no_recibida':
            message = f"⚠️ Se han marcado como NO RECIBIDAS {len(created_receptions)} muestra(s)."
            notification_type = 'warning'
        else:  # sin_procesar
            message = f"⚪ Se han marcado como SIN PROCESAR {len(created_receptions)} muestra(s)."
            notification_type = 'success'
        
        # Mostrar códigos procesados solo si hay códigos
        if updated_codes and self.reception_state == 'recibida':
            codes_summary = ', '.join(updated_codes[:3])
            if len(updated_codes) > 3:
                codes_summary += f' y {len(updated_codes) - 3} más...'
            message += f'\n\n📝 Códigos asignados: {codes_summary}'
        
        # Mostrar notificación
        self.env['bus.bus']._sendone(
            self.env.user.partner_id, 
            'simple_notification', 
            {
                'title': f'Procesamiento Completado por {self.analyst_id.full_name}',
                'message': message,
                'type': notification_type
            }
        )
        
        return {'type': 'ir.actions.act_window_close'}