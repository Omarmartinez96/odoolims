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
        string='Iniciales de quien recibió',
        required=True,
        size=5,
        help='Máximo 5 caracteres'
    )
    
    reception_notes = fields.Text(
        string='Observaciones de la Muestra'
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
    
    def action_confirm_reception(self):
        """Confirmar recepción de muestras"""
        self.ensure_one()
        
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
            
            if existing_reception:
                # Actualizar existente
                existing_reception.write({
                    'reception_state': 'recibida',
                    'reception_date': self.reception_date,
                    'reception_time': self.reception_time,
                    'received_by_initials': self.received_by_initials,
                    'reception_notes': self.reception_notes,
                })
                created_receptions.append(existing_reception)
            else:
                # Crear nueva recepción
                new_reception = self.env['lims.sample.reception'].create({
                    'sample_id': sample.id,
                    'reception_state': 'recibida',
                    'reception_date': self.reception_date,
                    'reception_time': self.reception_time,
                    'received_by_initials': self.received_by_initials,
                    'reception_notes': self.reception_notes,
                })
                created_receptions.append(new_reception)
        
        # Mensaje de éxito
        message = f"Se han marcado como recibidas {len(created_receptions)} muestra(s) exitosamente."
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('¡Recepción Exitosa!'),
                'message': _(message),
                'type': 'success',
            }
        }