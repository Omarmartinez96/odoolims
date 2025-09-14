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
    
    finish_datetime = fields.Datetime(
        string='Fecha y Hora de Finalización',
        required=True,
        default=lambda self: self._get_tijuana_now(),
        help='Fecha y hora de finalización del uso'
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
    
    def _get_tijuana_now(self):
        """Obtener hora actual de Tijuana"""
        tijuana_tz = pytz.timezone('America/Tijuana')
        utc_now = pytz.UTC.localize(datetime.utcnow())
        tijuana_now = utc_now.astimezone(tijuana_tz)
        return tijuana_now.replace(tzinfo=None)
    
    @api.depends('usage_log_ids')
    def _compute_samples_info(self):
        for wizard in self:
            if not wizard.usage_log_ids:
                wizard.samples_info = "<p>No hay registros seleccionados</p>"
                continue
            
            html_content = """
            <div style="margin: 10px 0;">
                <h4>🔬 Muestras que se finalizarán:</h4>
                <table class="table table-sm table-striped">
                    <thead>
                        <tr>
                            <th>Equipo</th>
                            <th>Código Muestra</th>
                            <th>Identificación</th>
                            <th>Medio de Cultivo</th>
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
                            <td><strong>{log.equipment_id.name}</strong></td>
                            <td>{sample_code}</td>
                            <td>{sample_id}</td>
                            <td>{media_name}</td>
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
        
        if not self.finish_datetime:
            raise UserError('Debe especificar la fecha y hora de finalización.')
        
        # Finalizar todos los registros
        update_values = {
            'end_datetime': self.finish_datetime,
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
                'title': 'Equipos Finalizados',
                'message': f'✅ Se finalizaron {len(self.usage_log_ids)} registros de uso de equipos.',
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