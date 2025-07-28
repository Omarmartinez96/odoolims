from odoo import models, fields, api
from datetime import datetime

class LimsAnalysis(models.Model):
    _name = 'lims.analysis'
    _description = 'Análisis de Muestra'
    _rec_name = 'display_name'
    _order = 'create_date desc'

    # Relación con la muestra
    sample_id = fields.Many2one(
        'lims.sample',
        string='Muestra',
        required=True,
        ondelete='cascade'
    )
    
    sample_code = fields.Char(
        string='Código de Muestra',
        related='sample_id.sample_reception_id.sample_code',
        readonly=True,
        store=True
    )

    sample_identifier = fields.Char(
        string='Identificación de Muestra',
        related='sample_id.sample_identifier',
        readonly=True,
        store=True
    )

    display_name = fields.Char(
        string='Nombre del Análisis',
        compute='_compute_display_name',
        store=True
    )

    # Asignación de analista
    analyst_id = fields.Many2one(
        'res.users',
        string='Analista Asignado',
        required=True,
        default=lambda self: self.env.user
    )
    
    # Fechas
    analysis_start_date = fields.Date(
        string='Fecha de Inicio',
        default=fields.Date.context_today
    )
    analysis_end_date = fields.Date(
        string='Fecha de Finalización'
    )
    
    # Estado del análisis
    analysis_state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('validated', 'Validado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft')
    
    # Observaciones
    analysis_notes = fields.Text(
        string='Observaciones del Análisis'
    )
    internal_notes = fields.Text(
        string='Notas Internas'
    )
    
    def action_start_analysis(self):
        """Iniciar análisis"""
        self.analysis_state = 'in_progress'
        self.analysis_start_date = fields.Date.context_today(self)
    
    def action_complete_analysis(self):
        """Completar análisis"""
        self.analysis_state = 'completed'
        self.analysis_end_date = fields.Date.context_today(self)

@api.depends('sample_code', 'sample_identifier', 'analyst_id')
def _compute_display_name(self):
    for analysis in self:
        parts = []
        if analysis.sample_code:
            parts.append(analysis.sample_code)
        if analysis.sample_identifier:
            parts.append(f"({analysis.sample_identifier})")
        if analysis.analyst_id:
            parts.append(f"- {analysis.analyst_id.name}")
        
        analysis.display_name = " ".join(parts) if parts else "Análisis"