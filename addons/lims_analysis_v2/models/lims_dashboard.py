from odoo import models, fields, api

class LimsDashboard(models.Model):
    _name = 'lims.dashboard'
    _description = 'Dashboard de Análisis LIMS'
    _auto = False  # No crear tabla, es un modelo virtual
    
    # ===============================================
    # === MÉTRICAS PRINCIPALES ===
    # ===============================================
    total_samples = fields.Integer(
        string='Total de Muestras',
        compute='_compute_metrics'
    )
    
    samples_all_ready = fields.Integer(
        string='Muestras con Todos los Parámetros Listos',
        compute='_compute_metrics'
    )
    
    samples_in_process = fields.Integer(
        string='Muestras con Parámetros en Proceso',
        compute='_compute_metrics'
    )
    
    samples_completed = fields.Integer(
        string='Muestras con Parámetros Completados',
        compute='_compute_metrics'
    )
    
    samples_reported = fields.Integer(
        string='Muestras Marcadas como Reportadas',
        compute='_compute_metrics'
    )
    
    samples_signed = fields.Integer(
        string='Muestras Firmadas',
        compute='_compute_metrics'
    )
    
    # Métricas adicionales útiles
    samples_pending = fields.Integer(
        string='Muestras Pendientes',
        compute='_compute_metrics'
    )
    
    samples_this_week = fields.Integer(
        string='Muestras Esta Semana',
        compute='_compute_metrics'
    )
    
    samples_today = fields.Integer(
        string='Muestras Hoy',
        compute='_compute_metrics'
    )
    
    @api.depends('create_date')
    def _compute_metrics(self):
        """Calcular todas las métricas del dashboard"""
        Analysis = self.env['lims.analysis.v2']
        
        for record in self:
            # Total de muestras
            all_samples = Analysis.search([])
            record.total_samples = len(all_samples)
            
            # Muestras con TODOS los parámetros listos
            record.samples_all_ready = Analysis.search_count([
                ('all_parameters_ready', '=', True)
            ])
            
            # Muestras con parámetros en proceso (al menos uno en proceso)
            samples_in_process = Analysis.search([])
            in_process_count = 0
            for sample in samples_in_process:
                if any(p.analysis_status_checkbox == 'en_proceso' 
                      for p in sample.parameter_analysis_ids):
                    in_process_count += 1
            record.samples_in_process = in_process_count
            
            # Muestras con parámetros completados (al menos uno completado)
            completed_count = 0
            for sample in all_samples:
                if any(p.analysis_status_checkbox == 'finalizado' 
                      for p in sample.parameter_analysis_ids):
                    completed_count += 1
            record.samples_completed = completed_count
            
            # Muestras reportadas
            record.samples_reported = Analysis.search_count([
                ('report_sent_to_client', '=', True)
            ])
            
            # Muestras firmadas
            record.samples_signed = Analysis.search_count([
                ('signature_state', '=', 'signed')
            ])
            
            # Muestras pendientes (sin ningún parámetro procesado)
            pending_count = 0
            for sample in all_samples:
                if all(p.analysis_status_checkbox == 'sin_procesar' 
                      for p in sample.parameter_analysis_ids):
                    pending_count += 1
            record.samples_pending = pending_count
            
            # Muestras de esta semana
            from datetime import datetime, timedelta
            today = fields.Date.context_today(self)
            week_start = today - timedelta(days=today.weekday())
            record.samples_this_week = Analysis.search_count([
                ('reception_date', '>=', week_start)
            ])
            
            # Muestras de hoy
            record.samples_today = Analysis.search_count([
                ('reception_date', '=', today)
            ])
    
    # ===============================================
    # === ACCIONES DE NAVEGACIÓN ===
    # ===============================================
    def action_view_all_samples(self):
        """Ver todas las muestras"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Todas las Muestras',
            'res_model': 'lims.analysis.v2',
            'view_mode': 'list,form',
            'target': 'current',
            'context': {'group_by': 'custody_chain_id'}
        }
    
    def action_view_samples_ready(self):
        """Ver muestras con todos los parámetros listos"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Muestras con Parámetros Listos',
            'res_model': 'lims.analysis.v2',
            'view_mode': 'list,form',
            'domain': [('all_parameters_ready', '=', True)],
            'target': 'current',
            'context': {'group_by': 'custody_chain_id'}
        }
    
    def action_view_samples_in_process(self):
        """Ver muestras en proceso"""
        # Obtener IDs de muestras en proceso
        Analysis = self.env['lims.analysis.v2']
        samples = Analysis.search([])
        in_process_ids = []
        for sample in samples:
            if any(p.analysis_status_checkbox == 'en_proceso' 
                  for p in sample.parameter_analysis_ids):
                in_process_ids.append(sample.id)
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Muestras en Proceso',
            'res_model': 'lims.analysis.v2',
            'view_mode': 'list,form',
            'domain': [('id', 'in', in_process_ids)],
            'target': 'current',
            'context': {'group_by': 'custody_chain_id'}
        }
    
    def action_view_samples_reported(self):
        """Ver muestras reportadas"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Muestras Reportadas',
            'res_model': 'lims.analysis.v2',
            'view_mode': 'list,form',
            'domain': [('report_sent_to_client', '=', True)],
            'target': 'current',
            'context': {'group_by': 'custody_chain_id'}
        }
    
    @api.model
    def get_dashboard_data(self):
        """Método para obtener datos del dashboard vía RPC"""
        dashboard = self.create({})
        return {
            'total_samples': dashboard.total_samples,
            'samples_all_ready': dashboard.samples_all_ready,
            'samples_in_process': dashboard.samples_in_process,
            'samples_completed': dashboard.samples_completed,
            'samples_reported': dashboard.samples_reported,
            'samples_signed': dashboard.samples_signed,
            'samples_pending': dashboard.samples_pending,
            'samples_this_week': dashboard.samples_this_week,
            'samples_today': dashboard.samples_today,
        }