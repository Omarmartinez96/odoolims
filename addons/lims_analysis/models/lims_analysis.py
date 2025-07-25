from odoo import models, fields, api
from datetime import datetime

class LimsAnalysis(models.Model):
    _name = 'lims.analysis'
    _description = 'Análisis de Muestra'
    _rec_name = 'analysis_code'
    _order = 'create_date desc'

    # Código de análisis auto-generado
    analysis_code = fields.Char(
        string='Código de Análisis',
        default='/',
        copy=False,
        readonly=True
    )
    
    # Relación con la muestra
    sample_id = fields.Many2one(
        'lims.sample',
        string='Muestra',
        required=True,
        ondelete='cascade'
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