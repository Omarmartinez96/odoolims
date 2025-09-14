from odoo import models, fields, api
from odoo.exceptions import UserError
import pytz
from datetime import datetime

class LimsEquipmentFinishWizard(models.TransientModel):
    _name = 'lims.equipment.finish.wizard'
    _description = 'Wizard para Finalizar Uso de Equipos'

    usage_log_ids = fields.Many2many(
        'lims.equipment.usage.log',
        string='Registros a Finalizar',
        readonly=True
    )
    
    finish_date = fields.Date(
        string='Fecha de Finalización',
        required=True,
        default=fields.Date.context_today,
        help='Fecha de finalización del uso'
    )
    
    finish_time = fields.Char(
        string='Hora de Finalización',
        required=True,
        default=lambda self: self._get_tijuana_time(),
        help='Hora de finalización en formato HH:MM'
    )
    
    samples_info = fields.Html(
        string='Muestras a Finalizar',
        compute='_compute_samples_info',
        help='Lista de muestras que se finalizarán'
    )
    
    notes = fields.Text(
        string='Observaciones',
        help='Observaciones adicionales sobre la finalización'
    )
    
    def _get_tijuana_time(self):
        """Obtener hora actual de Tijuana en formato HH:MM"""
        try:
            tijuana_tz = pytz.timezone('America/Tijuana')
            utc_now = pytz.UTC.localize(datetime.utcnow())
            tijuana_now = utc_now.astimezone(tijuana_tz)
            return tijuana_now.strftime('%H:%M')
        except:
            # Fallback si hay problemas con timezone
            return datetime.now().strftime('%H:%M')
    
    def _combine_date_time(self, date_field, time_field):
        """Combinar fecha y hora en datetime"""
        if not date_field:
            return False
        
        if not time_field:
            time_field = '12:00'
        
        try:
            # Parsear tiempo HH:MM
            time_parts = time_field.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            # Combinar fecha y hora
            combined = datetime.combine(
                date_field,
                datetime.min.time().replace(hour=hour, minute=minute)
            )
            
            return combined
        except:
            # Si hay error, usar mediodía como default
            return datetime.combine(date_field, datetime.min.time().replace(hour=12))
    
    @api.depends('usage_log_ids')
    def _compute_samples_info(self):
        for wizard in self:
            if not wizard.usage_log_ids:
                wizard.samples_info = "<p>No hay registros seleccionados</p>"
                continue
            
            html_content = """
            <div style="margin: 10px 0;">
                <h4>🔬 Estas a punto de finalizar la incubación de las siguientes muestras:</h4>
                <table class="table table-sm table-striped">
                    <thead>
                        <tr>
                            <th>Código Muestra</th>
                            <th>Identificación</th>
                            <th>Medio de Cultivo</th>
                            <th>Equipo</th>
                            <th>Inicio</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for log in wizard.usage_log_ids:
                sample_code = log.sample_code or 'Sin código'
                sample_id = 'Sin identificación'
                if log.related_analysis_id and log.related_analysis_id.sample_identifier:
                    sample_id = log.related_analysis_id.sample_identifier
                
                media_name = log.media_culture_name or 'Sin medio'
                start_date = log.start_datetime.strftime('%d/%m/%Y %H:%M') if log.start_datetime else 'Sin fecha'
                
                html_content += f"""
                        <tr>
                            <td><strong>{sample_code}</strong></td>
                            <td>{sample_id}</td>
                            <td>{media_name}</td>
                            <td>{log.equipment_id.name}</td>
                            <td>{start_date}</td>
                        </tr>
                """
            
            html_content += """
                    </tbody>
                </table>
            </div>
            """
            
            wizard.samples_info = html_content
    
    def action_finish_usage(self):
        """Finalizar el uso de los equipos"""
        if not self.usage_log_ids:
            raise UserError('No hay registros para finalizar.')
        
        if not self.finish_date or not self.finish_time:
            raise UserError('Debe especificar la fecha y hora de finalización.')
        
        # Validar formato de hora
        try:
            time_parts = self.finish_time.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except:
            raise UserError('El formato de hora debe ser HH:MM (ejemplo: 14:30)')
        
        # Combinar fecha y hora
        finish_datetime = self._combine_date_time(self.finish_date, self.finish_time)
        
        # Finalizar todos los registros
        update_values = {
            'end_datetime': finish_datetime,
        }
        
        if self.notes:
            for log in self.usage_log_ids:
                current_notes = log.usage_notes or ''
                new_notes = f"{current_notes}\nFinalizado: {self.notes}" if current_notes else f"Finalizado: {self.notes}"
                log.usage_notes = new_notes
        
        self.usage_log_ids.write(update_values)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Incubaciones Finalizadas',
                'message': f'✅ Se finalizaron {len(self.usage_log_ids)} incubaciones correctamente.',
                'type': 'success',
            }
        }
    
    @api.model
    def default_get(self, fields_list):
        """Establecer registros desde contexto"""
        defaults = super().default_get(fields_list)
        
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            # Filtrar solo registros que pueden finalizarse
            logs_to_finish = self.env['lims.equipment.usage.log'].browse(active_ids).filtered(
                lambda l: l.is_active_use or l.status_display == '🔴 Vencido'
            )
            defaults['usage_log_ids'] = [(6, 0, logs_to_finish.ids)]
        
        return defaults