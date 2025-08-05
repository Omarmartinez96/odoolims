from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsReportSelectionWizardV2(models.TransientModel):
    _name = 'lims.report.selection.wizard.v2'
    _description = 'Wizard de Selección de Reportes v2'

    analysis_ids = fields.Many2many(
        'lims.analysis.v2',
        string='Análisis Seleccionados',
        readonly=True
    )
    
    analysis_count = fields.Integer(
        string='Cantidad de Análisis',
        readonly=True
    )
    
    report_category = fields.Selection([
        ('bioburden', '🦠 Bioburden / Biocarga'),
        ('viable_particles', '🔬 Partículas Viables'),
        ('endotoxin', '🧪 Endotoxinas'),
        ('general_ilac', '🏆 General con Sellos ILAC'),
        ('general_no_ilac', '📄 General sin Sellos ILAC'),
    ], string='Categoría de Reporte', required=True)
    
    report_language = fields.Selection([
        ('es', '🇪🇸 Español'),
        ('en', '🇺🇸 English'),
    ], string='Idioma', default='es', required=True)
    
    report_status = fields.Selection([
        ('preliminary', '📋 Preliminar'),
        ('final', '📄 Final'),
        ('signing', '✍️ Para Firma Manual'),
    ], string='Tipo de Reporte', default='final', required=True)

    def action_generate_report(self):
        """Generar el reporte seleccionado"""
        if not self.analysis_ids:
            raise UserError('No hay análisis seleccionados.')
        
        return self.env['lims.analysis.v2'].generate_custom_report(
            self.analysis_ids.ids, 
            {
                'report_type': self.report_category,
                'language': self.report_language,
                'status': self.report_status
            }
        )
    
    @api.model
    def default_get(self, fields_list):
        """Establecer análisis desde contexto"""
        defaults = super().default_get(fields_list)
        
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            analyses = self.env['lims.analysis.v2'].browse(active_ids)
            defaults.update({
                'analysis_ids': [(6, 0, active_ids)],
                'analysis_count': len(analyses)
            })
        
        return defaults