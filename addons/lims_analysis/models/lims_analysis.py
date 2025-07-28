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

    # Campo relacionado para mostrar el código de muestra
    sample_code = fields.Char(
        string='Código de Muestra',
        related='sample_reception_id.sample_code',
        readonly=True,
        store=True
    )

    # Campos relacionados para información adicional
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
    
    # 🆕 RELACIÓN CON PARÁMETROS DE ANÁLISIS
    parameter_analysis_ids = fields.One2many(
        'lims.parameter.analysis',
        'analysis_id',
        string='Parámetros de Análisis'
    )
    
    @api.depends('sample_reception_id')
    def _compute_display_name(self):
        """Calcular nombre del análisis"""
        for analysis in self:
            if analysis.sample_code:
                analysis.display_name = f"Análisis - {analysis.sample_code}"
            else:
                analysis.display_name = "Análisis"
    
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

    @api.model_create_multi
    def create(self, vals_list):
            """Override create para copiar parámetros desde la muestra"""
            records = super().create(vals_list)
            
            for record in records:
                # Obtener parámetros de la muestra a través de la recepción
                if record.sample_reception_id and record.sample_reception_id.sample_id:
                    sample = record.sample_reception_id.sample_id
                    sample_parameters = sample.parameter_ids
                    
                    print(f"DEBUG: Muestra encontrada: {sample.sample_identifier}")
                    print(f"DEBUG: Parámetros encontrados: {len(sample_parameters)}")
                    
                    # Crear parámetros de análisis para cada parámetro de la muestra
                    for param in sample_parameters:
                        print(f"DEBUG: Creando parámetro de análisis para: {param.name}")
                        
                        self.env['lims.parameter.analysis'].create({
                            'analysis_id': record.id,
                            'parameter_id': param.id,
                            'name': param.name or 'Sin nombre',
                            'method': param.method or '',
                            'microorganism': param.microorganism or '',
                            'unit': param.unit or '',
                            'category': param.category or 'other',
                            'sequence': param.id,  # Usar el ID como secuencia temporal
                        })
                        
                else:
                    print(f"DEBUG: No se encontró muestra para el análisis {record.id}")
                    print(f"DEBUG: sample_reception_id: {record.sample_reception_id}")
                    if record.sample_reception_id:
                        print(f"DEBUG: sample_id: {record.sample_reception_id.sample_id}")
            
            return records


# 🆕 NUEVO MODELO PARA PARÁMETROS DE ANÁLISIS
class LimsParameterAnalysis(models.Model):
    _name = 'lims.parameter.analysis'
    _description = 'Parámetros de Análisis con Resultados'
    _rec_name = 'name'
    _order = 'sequence, name'

    # Relación con el análisis padre
    analysis_id = fields.Many2one(
        'lims.analysis',
        string='Análisis',
        required=True,
        ondelete='cascade'
    )
    
    # Información del parámetro (copiada desde el parámetro original)
    parameter_id = fields.Many2one(
        'lims.sample.parameter',
        string='Parámetro Original',
        readonly=True
    )
    
    name = fields.Char(
        string='Nombre del Parámetro',
        required=True
    )
    method = fields.Char(
        string='Método'
    )
    microorganism = fields.Char(
        string='Microorganismo/Analito'
    )
    unit = fields.Char(
        string='Unidad'
    )
    category = fields.Selection([
        ('physical', 'Físico'),
        ('chemical', 'Químico'),
        ('microbiological', 'Microbiológico'),
        ('other', 'Otro')
    ], string='Categoría')
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    # 🆕 CAMPOS PARA RESULTADOS Y ANÁLISIS
    analysis_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('reviewed', 'Revisado'),
        ('approved', 'Aprobado')
    ], string='Estado del Análisis', default='pending')
    
    result_value = fields.Char(
        string='Resultado',
        help='Resultado obtenido del análisis'
    )
    
    result_numeric = fields.Float(
        string='Resultado Numérico',
        help='Para resultados que requieren cálculos'
    )
    
    result_qualitative = fields.Selection([
        ('positive', 'Positivo'),
        ('negative', 'Negativo'),
        ('presence', 'Presencia'),
        ('absence', 'Ausencia'),
        ('growth', 'Crecimiento'),
        ('no_growth', 'Sin Crecimiento')
    ], string='Resultado Cualitativo')
    
    analysis_date = fields.Date(
        string='Fecha de Análisis'
    )
    
    analyst_notes = fields.Text(
        string='Observaciones del Analista',
        help='Notas técnicas sobre el análisis realizado'
    )
    
    internal_notes = fields.Text(
        string='Notas Internas',
        help='Notas internas del laboratorio'
    )
    
    # Método utilizado específico para este análisis
    specific_method = fields.Text(
        string='Procedimiento Específico',
        help='Detalles específicos del método utilizado'
    )
    
    # Control de calidad específico
    qc_passed = fields.Boolean(
        string='Control de Calidad Aprobado',
        default=False
    )
    
    qc_notes = fields.Text(
        string='Notas de Control de Calidad'
    )


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
    
# 🆕 NUEVO MODELO PARA PARÁMETROS DE ANÁLISIS
class LimsParameterAnalysis(models.Model):
    _name = 'lims.parameter.analysis'
    _description = 'Parámetros de Análisis con Resultados'
    _rec_name = 'name'
    _order = 'sequence, name'

    # Relación con el análisis padre
    analysis_id = fields.Many2one(
        'lims.analysis',
        string='Análisis',
        required=True,
        ondelete='cascade'
    )
    
    # Información del parámetro (copiada desde el parámetro original)
    parameter_id = fields.Many2one(
        'lims.sample.parameter',
        string='Parámetro Original',
        readonly=True
    )
    
    name = fields.Char(
        string='Nombre del Parámetro',
        required=True
    )
    method = fields.Char(
        string='Método'
    )
    microorganism = fields.Char(
        string='Microorganismo/Analito'
    )
    unit = fields.Char(
        string='Unidad'
    )
    category = fields.Selection([
        ('physical', 'Físico'),
        ('chemical', 'Químico'),
        ('microbiological', 'Microbiológico'),
        ('other', 'Otro')
    ], string='Categoría')
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    # 🆕 CAMPOS PARA PROCESAMIENTO DE MUESTRAS
    sample_treatment_type = fields.Selection([
        ('nom_110', 'NOM-110-SSA1-1994: Diluciones'),
        ('iso_11737', 'ISO 11737-1:2018: Determinación de microorganismos en dispositivos médicos'),
        ('method_treatment', 'Tratamiento de acuerdo con el método de ensayo'),
        ('client_requirements', 'Tratamiento de acuerdo con requerimientos del cliente'),
        ('external_methodology', 'Tratamiento de acuerdo con metodología del proveedor externo'),
        ('no_preparation', 'Muestra no requiere preparación adicional')
    ], string='Tipo de Tratamiento de Muestra')
    
    # Campos específicos para diluciones
    requires_dilution = fields.Boolean(
        string='Requiere Diluciones',
        compute='_compute_requires_dilution',
        store=True
    )
    
    dilution_10_1 = fields.Boolean(
        string='10⁻¹',
        help='Dilución 1:10'
    )
    dilution_10_2 = fields.Boolean(
        string='10⁻²',
        help='Dilución 1:100'
    )
    dilution_10_3 = fields.Boolean(
        string='10⁻³',
        help='Dilución 1:1,000'
    )
    dilution_10_4 = fields.Boolean(
        string='10⁻⁴',
        help='Dilución 1:10,000'
    )
    other_dilution = fields.Char(
        string='Otra Dilución',
        help='Especificar otra dilución no listada'
    )
    
    # Notas específicas del tratamiento
    treatment_notes = fields.Text(
        string='Notas del Tratamiento',
        help='Observaciones específicas sobre el tratamiento aplicado'
    )
    
    # 🆕 CAMPOS PARA RESULTADOS Y ANÁLISIS (existentes)
    analysis_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('reviewed', 'Revisado'),
        ('approved', 'Aprobado')
    ], string='Estado del Análisis', default='pending')
    
    result_value = fields.Char(
        string='Resultado',
        help='Resultado obtenido del análisis'
    )
    
    result_numeric = fields.Float(
        string='Resultado Numérico',
        help='Para resultados que requieren cálculos'
    )
    
    result_qualitative = fields.Selection([
        ('positive', 'Positivo'),
        ('negative', 'Negativo'),
        ('presence', 'Presencia'),
        ('absence', 'Ausencia'),
        ('growth', 'Crecimiento'),
        ('no_growth', 'Sin Crecimiento')
    ], string='Resultado Cualitativo')
    
    analysis_date = fields.Date(
        string='Fecha de Análisis'
    )
    
    analyst_notes = fields.Text(
        string='Observaciones del Analista',
        help='Notas técnicas sobre el análisis realizado'
    )
    
    internal_notes = fields.Text(
        string='Notas Internas',
        help='Notas internas del laboratorio'
    )
    
    # Método utilizado específico para este análisis
    specific_method = fields.Text(
        string='Procedimiento Específico',
        help='Detalles específicos del método utilizado'
    )
    
    # Control de calidad específico
    qc_passed = fields.Boolean(
        string='Control de Calidad Aprobado',
        default=False
    )
    
    qc_notes = fields.Text(
        string='Notas de Control de Calidad'
    )
    
    # 🆕 MÉTODOS COMPUTADOS Y ONCHANGE
    @api.depends('sample_treatment_type')
    def _compute_requires_dilution(self):
        """Determinar si el tipo de tratamiento requiere diluciones"""
        for record in self:
            record.requires_dilution = record.sample_treatment_type in ['nom_110', 'iso_11737']
    
    @api.onchange('sample_treatment_type')
    def _onchange_sample_treatment_type(self):
        """Limpiar campos de dilución si no se requieren"""
        if not self.requires_dilution:
            self.dilution_10_1 = False
            self.dilution_10_2 = False
            self.dilution_10_3 = False
            self.dilution_10_4 = False
            self.other_dilution = False