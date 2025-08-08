from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class LimsParameterAnalysisPortalExtension(models.Model):
    _inherit = 'lims.parameter.analysis.v2'

    # ===============================================
    # === CAMPOS BÁSICOS PARA ASIGNACIÓN ===
    # ===============================================
    analyst_assigned_id = fields.Many2one(
        'res.users',
        string='Analista Asignado',
        help='Analista portal asignado para procesar este parámetro'
    )
    
    assignment_date = fields.Datetime(
        string='Fecha de Asignación',
        help='Cuándo se asignó este parámetro al analista'
    )
    
    # ===============================================
    # === CAMPOS BÁSICOS DE ESTADO ===
    # ===============================================
    portal_status = fields.Selection([
        ('not_assigned', 'Sin Asignar'),
        ('assigned', 'Asignado'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado')
    ], string='Estado Portal', default='not_assigned')
    
    portal_priority = fields.Selection([
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], string='Prioridad', default='normal')
    
    portal_notes = fields.Text(
        string='Notas del Portal',
        help='Notas adicionales del analista'
    )

    # ===============================================
    # === MÉTODOS BÁSICOS ===
    # ===============================================
    
    def assign_to_analyst(self, analyst_id, priority='normal'):
        """Asignar parámetro a un analista - VERSIÓN BÁSICA"""
        analyst = self.env['res.users'].browse(analyst_id)
        
        if not analyst.has_group('lims_portal_analyst.group_portal_analyst'):
            raise UserError('El usuario seleccionado no es un analista portal válido.')
        
        self.write({
            'analyst_assigned_id': analyst_id,
            'assignment_date': fields.Datetime.now(),
            'portal_status': 'assigned',
            'portal_priority': priority
        })
        
        _logger.info(f"Parámetro {self.name} asignado a {analyst.name}")
        return True

    @api.model 
    def get_analyst_parameters(self, analyst_id=None, status_filter=None):
        """Obtener parámetros de un analista - VERSIÓN BÁSICA"""
        if not analyst_id:
            analyst_id = self.env.user.id
        
        domain = [('analyst_assigned_id', '=', analyst_id)]
        
        if status_filter:
            domain.append(('portal_status', '=', status_filter))
        
        return self.search(domain, order='portal_priority desc, assignment_date asc')

    def mark_completed(self):
        """Marcar como completado - VERSIÓN BÁSICA"""
        if not self.result_value:
            raise UserError('Debes ingresar un resultado antes de completar.')
        
        self.write({
            'portal_status': 'completed',
            'analysis_status_checkbox': 'finalizado'
        })
        
        return True