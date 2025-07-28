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
    
    
    # CAMPOS EXISTENTES DE ANÁLISIS
    analysis_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('in_progress', 'En Proceso'),
        ('completed', 'Completado'),
        ('reviewed', 'Revisado'),
        ('approved', 'Aprobado')
    ], string='Estado del Análisis', default='pending')
    
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
    @api.depends('cfu_count', 'cfu_dilution')
    def _compute_cfu_result(self):
        """Calcular resultado de UFC automáticamente considerando dilución"""
        for record in self:
            if not record.cfu_count:
                record.cfu_result = False
                continue
                
            count = record.cfu_count
            dilution_factors = {
                'direct': 1,
                '10_1': 10,
                '10_2': 100,
                '10_3': 1000,
                '10_4': 10000,
                '10_5': 100000,
                '10_6': 1000000
            }
            
            factor = dilution_factors.get(record.cfu_dilution, 1)
            final_count = count * factor
            
            # Formatear según el rango
            if final_count == 0:
                record.cfu_result = "No detectado"
            elif final_count < 10:
                record.cfu_result = f"< 1.0 x 10¹ UFC/g"
            elif final_count > 300000:
                record.cfu_result = f"> 3.0 x 10⁵ UFC/g"
            else:
                # Convertir a notación científica
                if final_count >= 1000:
                    exp = len(str(int(final_count))) - 1
                    base = final_count / (10 ** exp)
                    record.cfu_result = f"{base:.1f} x 10{chr(8304 + exp)} UFC/g"
                else:
                    record.cfu_result = f"{final_count} UFC/g"
    
    @api.depends('category', 'microorganism', 'name')
    def _compute_result_type_suggestion(self):
        """Sugerir tipo de resultado según el parámetro"""
        for record in self:
            if not record.category:
                record.result_type_suggestion = False
                continue
                
            suggestions = []
            
            if record.category == 'microbiological':
                micro_name = (record.microorganism or record.name or '').lower()
                
                if any(x in micro_name for x in ['coliform', 'aerob', 'mesofil', 'levadura', 'moho']):
                    suggestions.append("🔢 <b>Recuento:</b> Contar colonias en placa, seleccionar dilución")
                    suggestions.append("📝 El resultado se calculará automáticamente")
                elif any(x in micro_name for x in ['salmonella', 'listeria', 'e.coli o157', 'campylobacter']):
                    suggestions.append("✅ <b>Cualitativo:</b> Detectado/No Detectado o Presencia/Ausencia")
                else:
                    suggestions.append("🧪 <b>Microbiológico:</b> Usar resultado cualitativo o recuento según corresponda")
                    
            elif record.category == 'chemical':
                suggestions.append("🔬 <b>Químico:</b> Ingresar valor numérico + unidad")
                suggestions.append("📊 Ej: 7.2 (valor) + pH (unidad) = '7.2 pH'")
                
            elif record.category == 'physical':
                suggestions.append("⚗️ <b>Físico:</b> Ingresar medición + unidad")
                suggestions.append("🌡️ Ej: 25 (valor) + °C (unidad) = '25°C'")
            
            if suggestions:
                record.result_type_suggestion = "<br/>".join(suggestions)
            else:
                record.result_type_suggestion = "💡 <b>Resultado principal:</b> Ingresar el resultado final del análisis"
    
    @api.onchange('result_numeric', 'result_unit')
    def _onchange_numeric_result(self):
        """Auto-completar resultado principal cuando se llena numérico + unidad"""
        if self.result_numeric and self.result_unit:
            # Formatear número según el tipo
            if self.result_unit.lower() in ['ph', 'unidades de ph']:
                self.result_value = f"{self.result_numeric:.1f} {self.result_unit}"
            elif self.category == 'chemical':
                self.result_value = f"{self.result_numeric} {self.result_unit}"
            else:
                self.result_value = f"{self.result_numeric}{self.result_unit}"
    
    @api.onchange('result_qualitative')
    def _onchange_qualitative_result(self):
        """Auto-completar resultado principal con resultado cualitativo"""
        if self.result_qualitative:
            qualitative_map = {
                'detected': 'Detectado',
                'not_detected': 'No Detectado',
                'positive': 'Positivo',
                'negative': 'Negativo',
                'presence': 'Presencia',
                'absence': 'Ausencia',
                'growth': 'Crecimiento',
                'no_growth': 'Sin Crecimiento',
                'confirmed': 'Confirmado',
                'not_confirmed': 'No Confirmado'
            }
            self.result_value = qualitative_map.get(self.result_qualitative, self.result_qualitative)
    
    @api.onchange('cfu_result')
    def _onchange_cfu_result(self):
        """Auto-completar resultado principal con resultado de UFC"""
        if self.cfu_result and self.category == 'microbiological':
            self.result_value = self.cfu_result
    
    @api.onchange('below_detection_limit', 'above_quantification_limit')
    def _onchange_limits(self):
        """Auto-completar resultado cuando está fuera de límites"""
        if self.below_detection_limit:
            limit = getattr(self.parameter_id, 'detection_limit', None) or '0.01'
            unit = self.result_unit or getattr(self.parameter_id, 'unit', '') or ''
            self.result_value = f"< {limit} {unit}".strip()
        elif self.above_quantification_limit:
            limit = getattr(self.parameter_id, 'quantification_limit', None) or '100'
            unit = self.result_unit or getattr(self.parameter_id, 'unit', '') or ''
            self.result_value = f"> {limit} {unit}".strip()