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
        readonly=True,
        help='Lista de muestras que se finalizarán'
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
    
    def _combine_date_time_to_utc(self, date_field, time_field):
        """Combinar fecha y hora de Tijuana y convertir a UTC para almacenamiento"""
        if not date_field:
            return False
        
        if not time_field:
            time_field = '12:00'
        
        try:
            import pytz
            
            # Parsear tiempo HH:MM
            time_parts = time_field.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            # Crear datetime naive en tiempo local (Tijuana)
            local_datetime = datetime.combine(
                date_field,
                datetime.min.time().replace(hour=hour, minute=minute)
            )
            
            # Localizar en zona de Tijuana
            tijuana_tz = pytz.timezone('America/Tijuana')
            tijuana_datetime = tijuana_tz.localize(local_datetime)
            
            # Convertir a UTC para almacenamiento en Odoo
            utc_datetime = tijuana_datetime.astimezone(pytz.UTC)
            
            # Retornar sin timezone info (Odoo lo maneja internamente)
            return utc_datetime.replace(tzinfo=None)
            
        except Exception as e:
            # Fallback: usar datetime naive (puede causar inconsistencias)
            return datetime.combine(date_field, datetime.min.time().replace(hour=hour, minute=minute))
    
    def action_finish_usage(self):
        """Finalizar el uso de los equipos y sincronizar con medios originales"""
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
        
        # Combinar fecha y hora EN TIMEZONE DE TIJUANA
        finish_datetime_utc = self._combine_date_time_to_utc(self.finish_date, self.finish_time)
        
        # Finalizar registros en bitácora
        update_values = {
            'end_datetime': finish_datetime_utc,
        }
        
        self.usage_log_ids.write(update_values)
        
        # SINCRONIZAR CON MEDIOS ORIGINALES EN LIMS_ANALYSIS_V2
        updated_media_count = 0
        for log in self.usage_log_ids:
            if log.related_media_id and log.usage_type == 'incubation':
                # Actualizar el medio original con la fecha/hora real de finalización
                log.related_media_id.write({
                    'incubation_end_date_real': self.finish_date,
                    'incubation_end_time_real': self.finish_time
                })
                updated_media_count += 1
        
        message = f'✅ Se finalizaron {len(self.usage_log_ids)} incubaciones correctamente.'
        if updated_media_count > 0:
            message += f'\n📋 Se actualizaron {updated_media_count} medios en análisis.'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Incubaciones Finalizadas',
                'message': message,
                'type': 'success',
            }
        }
    
    @api.model
    def default_get(self, fields_list):
        """Establecer registros desde contexto y calcular info de muestras"""
        defaults = super().default_get(fields_list)
        
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            # Filtrar solo registros que pueden finalizarse
            logs_to_finish = self.env['lims.equipment.usage.log'].browse(active_ids).filtered(
                lambda l: l.is_active_use or l.status_display == '🔴 Vencido'
            )
            defaults['usage_log_ids'] = [(6, 0, logs_to_finish.ids)]
            
            # CALCULAR INFO DE MUESTRAS INMEDIATAMENTE
            if logs_to_finish:
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
                                <th>Fin Previsto</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                
                for log in logs_to_finish:
                    sample_code = log.sample_code or 'Sin código'
                    sample_id = 'Sin identificación'
                    if log.related_analysis_id and log.related_analysis_id.sample_identifier:
                        sample_id = log.related_analysis_id.sample_identifier
                    
                    media_name = log.media_culture_name or 'Sin medio'
                    
                    # CAMBIO: Mostrar fin previsto en formato dd/mmm/yyyy
                    if log.planned_end_datetime:
                        try:
                            # Convertir de UTC a Tijuana para mostrar
                            tijuana_tz = pytz.timezone('America/Tijuana')
                            planned_utc = pytz.UTC.localize(log.planned_end_datetime)
                            planned_tijuana = planned_utc.astimezone(tijuana_tz)
                            planned_date = planned_tijuana.strftime('%d/%b/%Y %H:%M')
                        except:
                            planned_date = log.planned_end_datetime.strftime('%d/%b/%Y %H:%M')
                    else:
                        planned_date = 'Sin fecha límite'
                    
                    html_content += f"""
                            <tr>
                                <td><strong>{sample_code}</strong></td>
                                <td>{sample_id}</td>
                                <td>{media_name}</td>
                                <td>{log.equipment_id.name}</td>
                                <td>{planned_date}</td>
                            </tr>
                    """
                
                html_content += """
                        </tbody>
                    </table>
                </div>
                """
                
                defaults['samples_info'] = html_content
            else:
                defaults['samples_info'] = "<p>No hay registros que se puedan finalizar</p>"
        
        return defaults