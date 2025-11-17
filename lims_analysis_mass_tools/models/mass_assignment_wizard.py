from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsMassAssignmentWizardV2(models.TransientModel):
    _name = 'lims.mass.assignment.wizard.v2'
    _description = 'Wizard de Asignación Masiva v2'

    parameter_analysis_ids = fields.Many2many(
        'lims.parameter.analysis.v2',
        string='Parámetros Seleccionados',
        readonly=True
    )
    
    parameters_count = fields.Integer(
        string='Cantidad de Parámetros',
        compute='_compute_parameters_count'
    )
    
    assignment_type = fields.Selection([
        ('analyst', '👤 Asignar Analista Responsable'),
        ('dates', '📅 Asignar Fechas de Procesamiento'),
        ('media', '🧪 Asignar Medios de Cultivo'),
        ('equipment', '🔧 Asignar Equipos'),
        ('status', '📊 Cambiar Estados'),
        ('environment', '🏭 Asignar Ambientes de Procesamiento'),
    ], string='Tipo de Asignación', required=True)

    parameters_summary = fields.Text(
        string='Resumen de Parámetros Seleccionados',
        compute='_compute_parameters_summary',
        readonly=True
    )

    parameters_by_type_info = fields.Text(
        string='Distribución por Tipo',
        compute='_compute_parameters_by_type',
        readonly=True
    )

    parameters_by_status_info = fields.Text(
        string='Distribución por Estado',
        compute='_compute_parameters_by_status',
        readonly=True
    )

    @api.depends('parameter_analysis_ids')
    def _compute_parameters_summary(self):
        for record in self:
            if not record.parameter_analysis_ids:
                record.parameters_summary = "No hay parámetros seleccionados"
                continue
            
            info_lines = []
            for param in record.parameter_analysis_ids:
                # Información básica del parámetro
                analyst_info = param.analyst_id.full_name if param.analyst_id else "Sin analista"
                status_info = dict(param._fields['analysis_status_checkbox'].selection)[param.analysis_status_checkbox]
                result_info = param.result_value if param.result_value else "Sin resultado"
                
                info_lines.append(f"• {param.name} ({param.microorganism or 'Sin microorganismo'})")
                info_lines.append(f"  └ Analista: {analyst_info} | Estado: {status_info}")
                info_lines.append(f"  └ Resultado: {result_info}")
                info_lines.append("")  # Línea en blanco para separar
            
            record.parameters_summary = "\n".join(info_lines)

    @api.depends('parameter_analysis_ids')
    def _compute_parameters_by_type(self):
        for record in self:
            if not record.parameter_analysis_ids:
                record.parameters_by_type_info = "No hay parámetros para analizar"
                continue
            
            type_distribution = {}
            category_distribution = {}
            
            for param in record.parameter_analysis_ids:
                # Por tipo de resultado
                result_type = "Cualitativo" if param.result_type == 'qualitative' else "Cuantitativo"
                type_distribution[result_type] = type_distribution.get(result_type, 0) + 1
                
                # Por categoría
                category_map = {
                    'physical': 'Físico',
                    'chemical': 'Químico', 
                    'microbiological': 'Microbiológico',
                    'other': 'Otro'
                }
                category = category_map.get(param.category, 'Sin categoría')
                category_distribution[category] = category_distribution.get(category, 0) + 1
            
            info_lines = ["TIPOS DE RESULTADO:"]
            for result_type, count in type_distribution.items():
                info_lines.append(f"• {result_type}: {count} parámetros")
            
            info_lines.append("\nCATEGORÍAS:")
            for category, count in category_distribution.items():
                info_lines.append(f"• {category}: {count} parámetros")
            
            record.parameters_by_type_info = "\n".join(info_lines)

    @api.depends('parameter_analysis_ids')
    def _compute_parameters_by_status(self):
        for record in self:
            if not record.parameter_analysis_ids:
                record.parameters_by_status_info = "No hay parámetros para analizar"
                continue
            
            status_distribution = {}
            report_distribution = {}
            analyst_distribution = {}
            
            for param in record.parameter_analysis_ids:
                # Por estado de análisis
                status = dict(param._fields['analysis_status_checkbox'].selection)[param.analysis_status_checkbox]
                status_distribution[status] = status_distribution.get(status, 0) + 1
                
                # Por estado de reporte
                report = dict(param._fields['report_status'].selection)[param.report_status]
                report_distribution[report] = report_distribution.get(report, 0) + 1
                
                # Por analista
                analyst = param.analyst_id.full_name if param.analyst_id else "Sin asignar"
                analyst_distribution[analyst] = analyst_distribution.get(analyst, 0) + 1
            
            info_lines = ["ESTADOS DE ANÁLISIS:"]
            for status, count in status_distribution.items():
                info_lines.append(f"• {status}: {count} parámetros")
            
            info_lines.append("\nESTADOS DE REPORTE:")
            for report, count in report_distribution.items():
                info_lines.append(f"• {report}: {count} parámetros")
            
            info_lines.append("\nANALISTAS ASIGNADOS:")
            for analyst, count in analyst_distribution.items():
                info_lines.append(f"• {analyst}: {count} parámetros")
            
            record.parameters_by_status_info = "\n".join(info_lines)

    @api.depends('parameter_analysis_ids')
    def _compute_parameters_count(self):
        for record in self:
            record.parameters_count = len(record.parameter_analysis_ids)

    def action_open_specific_wizard(self):
        """Abrir el wizard específico según el tipo seleccionado"""
        if not self.parameter_analysis_ids:
            raise UserError('No hay parámetros seleccionados.')
        
        wizard_mapping = {
            'analyst': 'lims.mass.analyst.wizard.v2',
            'dates': 'lims.mass.dates.wizard.v2', 
            'media': 'lims.mass.media.wizard.v2',
            'equipment': 'lims.mass.equipment.wizard.v2',
            'status': 'lims.mass.status.wizard.v2',
            'environment': 'lims.mass.environment.wizard.v2',
        }
        
        wizard_model = wizard_mapping.get(self.assignment_type)
        wizard_name = dict(self._fields["assignment_type"].selection)[self.assignment_type]
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Asignación Masiva - {wizard_name}',
            'res_model': wizard_model,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parameter_analysis_ids': [(6, 0, self.parameter_analysis_ids.ids)]
            }
        }
    
    @api.model
    def default_get(self, fields_list):
        """Establecer parámetros desde contexto"""
        defaults = super().default_get(fields_list)
        
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            defaults['parameter_analysis_ids'] = [(6, 0, active_ids)]
        
        return defaults