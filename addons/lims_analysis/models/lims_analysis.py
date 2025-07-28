from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class LimsAnalysis(models.Model):
    _name = 'lims.analysis'
    _description = 'Análisis de Muestra'
    _rec_name = 'display_name'
    _order = 'create_date desc'

    # Relación con la recepción de muestra (que tiene el sample_code)
    sample_reception_id = fields.Many2one(
        'lims.sample.reception',
        string='Muestra Recibida',
        required=True,
        ondelete='cascade',
        domain=[('reception_state', '=', 'recibida')]
    )

    # Campos relacionados desde la recepción
    sample_code = fields.Char(
        string='Código de Muestra',
        related='sample_reception_id.sample_code',
        readonly=True,
        store=True
    )

    sample_identifier = fields.Char(
        string='Identificación de Muestra',
        related='sample_reception_id.sample_identifier',
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
    
    @api.depends('sample_reception_id', 'analyst_id')
    def _compute_display_name(self):
        """Calcular nombre del análisis"""
        for analysis in self:
            parts = []
            if analysis.sample_code:
                parts.append(analysis.sample_code)
            if analysis.sample_identifier:
                parts.append(f"({analysis.sample_identifier})")
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

    def action_clean_orphan_records(self):
        """Método temporal para limpiar registros huérfanos"""
        # Buscar análisis con sample_reception_id que no existe
        all_analyses = self.search([])
        orphan_count = 0
        
        for analysis in all_analyses:
            try:
                # Intentar acceder a la recepción
                if analysis.sample_reception_id:
                    reception_exists = analysis.sample_reception_id.exists()
                    if not reception_exists:
                        analysis.unlink()
                        orphan_count += 1
            except:
                # Si hay error, es huérfano
                analysis.unlink()
                orphan_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Limpieza Completada',
                'message': f'Se eliminaron {orphan_count} registros huérfanos',
                'type': 'success',
            }
        }

    @api.model
    def cron_clean_orphan_records(self):
        """Cron job para limpiar registros huérfanos automáticamente"""
        # Limpiar análisis huérfanos
        orphan_analyses = self.search([]).filtered(
            lambda a: not a.sample_reception_id.exists()
        )
        if orphan_analyses:
            _logger.info(f"Limpiando {len(orphan_analyses)} análisis huérfanos")
            orphan_analyses.unlink()
        
        # Limpiar recepciones huérfanas
        orphan_receptions = self.env['lims.sample.reception'].search([]).filtered(
            lambda r: not r.sample_id.exists()
        )
        if orphan_receptions:
            _logger.info(f"Limpiando {len(orphan_receptions)} recepciones huérfanas")
            orphan_receptions.unlink()

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
        
        # Crear análisis usando la recepción
        analysis = self.env['lims.analysis'].create({
            'sample_reception_id': reception.id,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Análisis de Muestra',
            'res_model': 'lims.analysis',
            'res_id': analysis.id,
            'view_mode': 'form',
            'target': 'current',
        }