from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError

class LimsAnalysis(models.Model):
    _name = 'lims.analysis'
    _description = 'Análisis de Muestra'
    _inherit = ['mail.thread', 'mail.activity.mixin']
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
    
    # Información heredada de la muestra (para facilidad)
    sample_identifier = fields.Char(
        string='Identificación de Muestra',
        related='sample_id.sample_identifier',
        readonly=True,
        store=True
    )
    custody_chain_id = fields.Many2one(
        'lims.custody_chain',
        string='Cadena de Custodia',
        related='sample_id.custody_chain_id',
        readonly=True,
        store=True
    )
    cliente_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='sample_id.cliente_id',
        readonly=True,
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
    ], string='Estado', default='draft', tracking=True)
    
    # Lote de análisis (opcional, para agrupar análisis)
    batch_id = fields.Many2one(
        'lims.analysis.batch',
        string='Lote de Análisis'
    )
    
    # Resultados de parámetros
    parameter_result_ids = fields.One2many(
        'lims.parameter.result',
        'analysis_id',
        string='Resultados de Parámetros'
    )
    
    # Observaciones
    analysis_notes = fields.Text(
        string='Observaciones del Análisis'
    )
    internal_notes = fields.Text(
        string='Notas Internas'
    )
    
    # Campos computados
    progress_percentage = fields.Float(
        string='Progreso (%)',
        compute='_compute_progress',
        store=True
    )
    total_parameters = fields.Integer(
        string='Total Parámetros',
        compute='_compute_progress',
        store=True
    )
    completed_parameters = fields.Integer(
        string='Parámetros Completados',
        compute='_compute_progress',
        store=True
    )
    
    @api.depends('parameter_result_ids', 'parameter_result_ids.result_state')
    def _compute_progress(self):
        for analysis in self:
            total = len(analysis.parameter_result_ids)
            completed = len(analysis.parameter_result_ids.filtered(
                lambda r: r.result_state == 'completed'
            ))
            
            analysis.total_parameters = total
            analysis.completed_parameters = completed
            analysis.progress_percentage = (completed / total * 100) if total > 0 else 0
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generar código de análisis y crear resultados de parámetros"""
        for vals in vals_list:
            # Generar código
            if vals.get('analysis_code', '/') == '/':
                year = str(datetime.today().year)
                sequence = self.env['ir.sequence'].next_by_code('lims.analysis') or '001'
                vals['analysis_code'] = f'AN{year}{sequence.zfill(4)}'
        
        analyses = super().create(vals_list)
        
        # Auto-crear resultados desde los parámetros de la muestra
        for analysis in analyses:
            analysis._create_parameter_results()
        
        return analyses
    
    def _create_parameter_results(self):
        """Crear resultados automáticamente desde los parámetros de la muestra"""
        for parameter in self.sample_id.parameter_ids:
            self.env['lims.parameter.result'].create({
                'analysis_id': self.id,
                'parameter_id': parameter.id,
                'result_state': 'pending'
            })
    
    def action_start_analysis(self):
        """Iniciar análisis"""
        self.analysis_state = 'in_progress'
        self.analysis_start_date = fields.Date.context_today(self)
    
    def action_complete_analysis(self):
        """Completar análisis"""
        if all(result.result_state == 'completed' for result in self.parameter_result_ids):
            self.analysis_state = 'completed'
            self.analysis_end_date = fields.Date.context_today(self)
        else:
            raise UserError('No se pueden completar análisis con parámetros pendientes.')
    
    def action_validate_analysis(self):
        """Validar análisis (solo supervisor)"""
        self.analysis_state = 'validated'