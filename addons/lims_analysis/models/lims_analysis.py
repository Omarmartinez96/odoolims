from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError

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
    
    # Campos calculados desde la muestra
    sample_code = fields.Char(
        string='Código de Muestra',
        compute='_compute_sample_info',
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
        compute='_compute_sample_info',
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
    
    @api.depends('sample_id', 'analyst_id')
    def _compute_sample_info(self):
        """Calcular información de la muestra y nombre del análisis"""
        for analysis in self:
            # Obtener código de recepción
            sample_code = ''
            if analysis.sample_id:
                reception = self.env['lims.sample.reception'].search([
                    ('sample_id', '=', analysis.sample_id.id)
                ], limit=1)
                sample_code = reception.sample_code if reception else 'Sin código'
            
            analysis.sample_code = sample_code
            
            # Crear nombre del análisis
            parts = []
            if sample_code:
                parts.append(sample_code)
            if analysis.sample_id and analysis.sample_id.sample_identifier:
                parts.append(f"({analysis.sample_id.sample_identifier})")
            if analysis.analyst_id:
                parts.append(f"- {analysis.analyst_id.name}")
            
            analysis.display_name = " ".join(parts) if parts else "Análisis"
    
    def action_start_analysis(self):
        """Iniciar análisis"""
        self.analysis_state = 'in_progress'
        self.analysis_start_date = fields.Date.context_today(self)
    
    def action_complete_analysis(self):
        """Completar análisis"""
        self.analysis_state = 'completed'
        self.analysis_end_date = fields.Date.context_today(self)

class LimsSample(models.Model):
    _inherit = 'lims.sample'
    
    def action_create_analysis(self):
        """Crear análisis para esta muestra"""
        # Verificar que esté recibida
        reception = self.env['lims.sample.reception'].search([
            ('sample_id', '=', self.id),
            ('reception_state', '=', 'recibida')
        ], limit=1)
        
        if not reception:
            raise UserError('Solo se pueden crear análisis para muestras recibidas.')
        
        # Crear análisis
        analysis = self.env['lims.analysis'].create({
            'sample_id': self.id,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Análisis de Muestra',
            'res_model': 'lims.analysis',
            'res_id': analysis.id,
            'view_mode': 'form',
            'target': 'current',
        }