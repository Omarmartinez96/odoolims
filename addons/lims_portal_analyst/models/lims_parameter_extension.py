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
    
    @api.model 
    def get_all_lab_parameters(self, filters=None):
        """Obtener TODOS los parámetros del laboratorio con filtros"""
        domain = []
        
        if filters:
            # Filtro por estado
            if filters.get('status_filter'):
                if filters['status_filter'] == 'available':
                    domain.append(('analyst_assigned_id', '=', False))
                elif filters['status_filter'] == 'my_assigned':
                    domain.append(('analyst_assigned_id', '=', self.env.user.id))
                elif filters['status_filter'] in ['sin_procesar', 'en_proceso', 'finalizado']:
                    domain.append(('analysis_status_checkbox', '=', filters['status_filter']))
            
            # Filtro por cliente
            if filters.get('customer_id'):
                domain.append(('analysis_id.customer_id', '=', int(filters['customer_id'])))
            
            # Filtro por categoría
            if filters.get('category'):
                domain.append(('category', '=', filters['category']))
            
            # Filtro por tipo de resultado
            if filters.get('result_type'):
                domain.append(('result_type', '=', filters['result_type']))
            
            # Filtro por búsqueda de texto
            if filters.get('search'):
                search = filters['search']
                domain.append(['|', '|', '|', 
                            ('name', 'ilike', search),
                            ('microorganism', 'ilike', search),
                            ('analysis_id.sample_code', 'ilike', search),
                            ('analysis_id.customer_id.name', 'ilike', search)])
        
        return self.search(domain, order='analysis_start_date desc, id desc')

    def take_parameter(self):
        """Tomar/asignar parámetro al analista actual"""
        if self.analyst_assigned_id:
            raise UserError(f'Este parámetro ya está asignado a {self.analyst_assigned_id.name}.')
        
        self.write({
            'analyst_assigned_id': self.env.user.id,
            'assignment_date': fields.Datetime.now(),
            'portal_status': 'assigned',
            'portal_priority': 'normal'
        })
        
        _logger.info(f"Parámetro {self.name} tomado por {self.env.user.name}")
        return True

    def release_parameter(self):
        """Liberar parámetro (solo si es el analista asignado)"""
        if self.analyst_assigned_id.id != self.env.user.id:
            raise UserError('Solo puedes liberar parámetros asignados a ti.')
        
        self.write({
            'analyst_assigned_id': False,
            'assignment_date': False,
            'portal_status': 'not_assigned',
            'portal_notes': False
        })
        
        _logger.info(f"Parámetro {self.name} liberado por {self.env.user.name}")
        return True

    @api.model
    def get_lab_statistics(self):
        """Obtener estadísticas globales del laboratorio"""
        all_params = self.search([])
        
        return {
            'total_parameters': len(all_params),
            'available_parameters': len(all_params.filtered(lambda p: not p.analyst_assigned_id)),
            'assigned_parameters': len(all_params.filtered(lambda p: p.analyst_assigned_id)),
            'my_parameters': len(all_params.filtered(lambda p: p.analyst_assigned_id.id == self.env.user.id)),
            'completed_today': len(all_params.filtered(lambda p: 
                p.analysis_status_checkbox == 'finalizado' and 
                p.write_date.date() == fields.Date.context_today(self) if p.write_date else False
            )),
            'pending_urgent': len(all_params.filtered(lambda p: 
                p.portal_priority == 'urgent' and 
                p.analysis_status_checkbox != 'finalizado'
            ))
        }