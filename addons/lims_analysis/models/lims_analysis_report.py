from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class LimsAnalysisReport(models.Model):
    _name = 'lims.analysis.report'
    _description = 'Reporte de Resultados de Análisis'
    _rec_name = 'report_code'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    customer_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='custody_chain_id.cliente_id',
        readonly=True,
        store=True
    )
    
    # AGREGAR AQUÍ:
    reception_date = fields.Date(
        string='Fecha de Recepción',
        compute='_compute_reception_date',
        store=True,
        help='Fecha de recepción más temprana de las muestras'
    )

    # Código automático del reporte
    report_code = fields.Char(
        string='Código de Reporte',
        copy=False,
        default='/',
        readonly=True
    )
    
    # Relación con cadena de custodia
    custody_chain_id = fields.Many2one(
        'lims.custody_chain',
        string='Cadena de Custodia',
        required=True,
        readonly=True
    )
    
    # Campos relacionados para información rápida
    custody_chain_code = fields.Char(
        string='Código de Cadena',
        related='custody_chain_id.custody_chain_code',
        readonly=True,
        store=True
    )
    
    customer_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='custody_chain_id.cliente_id',
        readonly=True,
        store=True
    )
    
    # Análisis incluidos
    analysis_ids = fields.Many2many(
        'lims.analysis',
        string='Análisis Incluidos',
        required=True
    )
    
    # Tipo de reporte
    report_type = fields.Selection([
        ('preliminary', 'Preliminar'),
        ('final', 'Final')
    ], string='Tipo de Reporte', required=True)
    
    # Estado del reporte
    report_state = fields.Selection([
        ('draft', 'Borrador'),
        ('ready', 'Listo para Autorización'),
        ('authorized', 'Autorizado por Calidad'),
        ('sent', 'Enviado')
    ], string='Estado', default='draft', tracking=True)
    
    # Fechas
    report_date = fields.Date(
        string='Fecha de Reporte',
        default=fields.Date.context_today
    )

# AUTORIZACIÓN DE CALIDAD
    quality_signature = fields.Binary(
        string='Firma de Autorización de Calidad',
        help='Firma del personal de calidad que autoriza la emisión de resultados'
    )
    quality_signature_date = fields.Datetime(
        string='Fecha de Autorización'
    )
    quality_signature_name = fields.Char(
        string='Responsable de Calidad'
    )
    quality_signature_position = fields.Char(
        string='Cargo del Responsable'
    )
    is_authorized = fields.Boolean(
        string='Autorizado por Calidad',
        compute='_compute_is_authorized',
        store=True
    )
    
    # Estadísticas del reporte
    total_samples = fields.Integer(
        string='Total de Muestras',
        compute='_compute_report_stats',
        store=True
    )
    total_parameters = fields.Integer(
        string='Total de Parámetros',
        compute='_compute_report_stats', 
        store=True
    )
    completed_parameters = fields.Integer(
        string='Parámetros Completados',
        compute='_compute_report_stats',
        store=True
    )
    
    # Notas
    quality_notes = fields.Text(
        string='Notas de Calidad',
        help='Observaciones del personal de calidad'
    )

# MÉTODOS COMPUTADOS
    @api.depends('quality_signature')
    def _compute_is_authorized(self):
        for record in self:
            record.is_authorized = bool(record.quality_signature)
    
    @api.depends('analysis_ids.parameter_analysis_ids')
    def _compute_report_stats(self):
        for record in self:
            samples = record.analysis_ids.mapped('sample_reception_id.sample_id')
            all_params = record.analysis_ids.mapped('parameter_analysis_ids')
            ready_params = all_params.filtered(lambda p: p.report_status == 'ready')
            
            record.total_samples = len(samples)
            record.total_parameters = len(all_params)
            record.completed_parameters = len(ready_params)

# CREACIÓN AUTOMÁTICA DE CÓDIGO
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('report_code') or vals.get('report_code') == '/':
                year = str(datetime.today().year)
                prefix = 'RP' if vals.get('report_type') == 'preliminary' else 'RF'
                
                # Buscar reportes del mismo tipo y año
                existing = self.search([
                    ('report_code', 'like', f'{prefix}%/{year}'),
                    ('report_code', '!=', '/')
                ])
                
                def extract_number(code):
                    try:
                        parts = code.split('/')
                        if len(parts) >= 1:
                            number_part = parts[0].replace(prefix, '')
                            return int(number_part)
                        return 0
                    except (ValueError, IndexError):
                        return 0
                
                max_num = max([extract_number(rec.report_code) for rec in existing], default=0)
                next_num = str(max_num + 1).zfill(3)
                vals['report_code'] = f'{prefix}{next_num}/{year}'
        
        return super().create(vals_list)
    
# ACCIONES
    def action_authorize_quality(self):
        """Abrir vista para autorización de calidad"""
        self.ensure_one()
        
        if self.report_state != 'ready':
            raise UserError('El reporte debe estar en estado "Listo" para autorizar.')
        
        return {
            'name': 'Autorización de Calidad',
            'type': 'ir.actions.act_window',
            'res_model': 'lims.analysis.report',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('lims_analysis.view_analysis_report_quality_auth_form').id,
            'target': 'new',
            'context': {'quality_auth_mode': True}
        }
    
    def action_save_quality_authorization(self):
        """Guardar autorización de calidad"""
        self.ensure_one()
        
        if not self.quality_signature:
            raise UserError('Debe proporcionar una firma de autorización.')
        
        if not self.quality_signature_name:
            raise UserError('Debe especificar el nombre del responsable.')
        
        self.write({
            'quality_signature_date': fields.Datetime.now(),
            'report_state': 'authorized'
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Autorización Guardada',
                'message': 'El reporte ha sido autorizado por el personal de calidad.',
                'type': 'success',
            }
        }
    
    def action_generate_pdf(self):
        """Generar PDF del reporte - simplificado"""
        self.ensure_one()
        
        # Marcar parámetros como reportados si no están ya marcados
        params_to_mark = self.analysis_ids.mapped('parameter_analysis_ids').filtered(
            lambda p: p.report_status == 'ready'
        )
        if params_to_mark:
            params_to_mark.write({'report_status': 'reported'})
        
        return self.env.ref('lims_analysis.action_report_analysis_results').report_action(self)
    
    @api.model
    def create_preliminary_report_for_chain(self, custody_chain_id):
        """Crear reporte preliminar para una cadena de custodia"""
        chain = self.env['lims.custody_chain'].browse(custody_chain_id)
        
        # Buscar análisis con parámetros listos
        analyses = self.env['lims.analysis'].search([
            ('sample_reception_id.sample_id.custody_chain_id', '=', custody_chain_id),
            ('has_ready_parameters', '=', True)
        ])
        
        if not analyses:
            raise UserError('No hay análisis con parámetros listos para esta cadena de custodia.')
        
        report = self.create({
            'custody_chain_id': custody_chain_id,
            'analysis_ids': [(6, 0, analyses.ids)],
            'report_type': 'preliminary',
            'report_state': 'ready'
        })
        
        return report
    
    @api.model
    def create_final_report_for_chain(self, custody_chain_id):
        """Crear reporte final para una cadena de custodia"""
        chain = self.env['lims.custody_chain'].browse(custody_chain_id)
        
        # Buscar análisis completamente terminados
        analyses = self.env['lims.analysis'].search([
            ('sample_reception_id.sample_id.custody_chain_id', '=', custody_chain_id),
            ('all_parameters_ready', '=', True)
        ])
        
        if not analyses:
            raise UserError('No hay análisis completamente terminados para esta cadena de custodia.')
        
        report = self.create({
            'custody_chain_id': custody_chain_id,
            'analysis_ids': [(6, 0, analyses.ids)],
            'report_type': 'final',
            'report_state': 'ready'
        })
        
        return report
    
    @api.depends('analysis_ids.sample_reception_id.reception_date')
    def _compute_reception_date(self):
        """Calcular fecha de recepción desde las muestras recibidas"""
        for report in self:
            reception_dates = report.analysis_ids.mapped('sample_reception_id.reception_date')
            valid_dates = [date for date in reception_dates if date]
            
            if valid_dates:
                report.reception_date = min(valid_dates)
            else:
                report.reception_date = False