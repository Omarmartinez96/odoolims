from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsMassMediaWizardV2(models.TransientModel):
    _name = 'lims.mass.media.wizard.v2'
    _description = 'Asignación Masiva de Medios de Cultivo'

    parameter_analysis_ids = fields.Many2many(
        'lims.parameter.analysis.v2',
        string='Parámetros Seleccionados',
        readonly=True
    )
    
    parameters_count = fields.Integer(
        string='Cantidad de Parámetros',
        compute='_compute_parameters_count'
    )
    
    process_type = fields.Selection([
        ('pre_enrichment', 'Pre-enriquecimiento'),
        ('selective_enrichment', 'Enriquecimiento Selectivo'),
        ('quantitative', 'Cuantitativo'),
        ('qualitative', 'Cualitativo'),
        ('confirmation', 'Confirmación')
    ], string='Tipo de Proceso', required=True)
    
    assignment_method = fields.Selection([
        ('media_set', 'Usar Set de Medios Predefinido'),
        ('individual_media', 'Seleccionar Medios Individuales'),
        ('copy_from_parameter', 'Copiar desde Otro Parámetro')
    ], string='Método de Asignación', required=True)
    
    # Para sets de medios
    media_set_id = fields.Many2one(
        'lims.media.set',
        string='Set de Medios',
        domain="[('process_type', '=', process_type), ('active', '=', True)]"
    )
    
    # Para medios individuales
    selected_media_ids = fields.Many2many(
        'lims.culture.media',
        string='Medios Seleccionados'
    )
    
    media_usage = fields.Selection([
        ('diluyente', 'Diluyente'),
        ('eluyente', 'Eluyente'),
        ('enriquecimiento', 'Enriquecimiento'),
        ('desarrollo_selectivo', 'Desarrollo Selectivo'),
        ('desarrollo_diferencial', 'Desarrollo Diferencial'),
        ('desarrollo_selectivo_diferencial', 'Desarrollo Selectivo y Diferencial'),
        ('pruebas_bioquimicas', 'Pruebas Bioquímicas'),
        ('transporte', 'Transporte'),
        ('mantenimiento', 'Mantenimiento'),
        ('otro', 'Otro')
    ], string='Uso de los Medios')
    
    # Para copiar desde otro parámetro
    source_parameter_id = fields.Many2one(
        'lims.parameter.analysis.v2',
        string='Parámetro Fuente'
    )
    
    # Opciones adicionales
    include_incubation_settings = fields.Boolean(
        string='Incluir Configuración de Incubación',
        default=True
    )
    
    clear_existing_media = fields.Boolean(
        string='Limpiar Medios Existentes del Proceso',
        default=True,
        help='Eliminar medios existentes del mismo tipo de proceso antes de agregar nuevos'
    )

    @api.depends('parameter_analysis_ids')
    def _compute_parameters_count(self):
        for record in self:
            record.parameters_count = len(record.parameter_analysis_ids)

    @api.onchange('assignment_method')
    def _onchange_assignment_method(self):
        """Limpiar campos según método seleccionado"""
        if self.assignment_method != 'media_set':
            self.media_set_id = False
        if self.assignment_method != 'individual_media':
            self.selected_media_ids = [(5, 0, 0)]
            self.media_usage = False
        if self.assignment_method != 'copy_from_parameter':
            self.source_parameter_id = False

    def action_assign_media(self):
        """Asignar medios a todos los parámetros seleccionados"""
        if not self.parameter_analysis_ids:
            raise UserError('No hay parámetros seleccionados.')
        
        total_media_created = 0
        
        for parameter in self.parameter_analysis_ids:
            if self.assignment_method == 'media_set':
                media_count = self._assign_from_media_set(parameter)
            elif self.assignment_method == 'individual_media':
                media_count = self._assign_individual_media(parameter)
            elif self.assignment_method == 'copy_from_parameter':
                media_count = self._copy_from_parameter(parameter)
            
            total_media_created += media_count
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Medios Asignados',
                'message': f'Se crearon {total_media_created} medios para {len(self.parameter_analysis_ids)} parámetros.',
                'type': 'success',
            }
        }
    
    def _assign_from_media_set(self, parameter):
        """Asignar medios desde un set"""
        if not self.media_set_id:
            return 0
        
        # Limpiar medios existentes si está marcado
        if self.clear_existing_media:
            existing_media = parameter.media_ids.filtered(
                lambda m: m.process_type == self.process_type
            )
            existing_media.unlink()
        
        # Crear nuevos medios desde el set
        media_count = 0
        for set_line in self.media_set_id.media_line_ids:
            vals = {
                'parameter_analysis_id': parameter.id,
                'process_type': self.process_type,
                'media_source': 'internal',
                'culture_media_name': set_line.culture_media_id.name,
                'media_usage': set_line.media_usage,
                'preparation_notes': set_line.notes or '',
                'sequence': set_line.sequence,
            }
            
            if self.include_incubation_settings:
                vals['requires_incubation'] = True
                
            self.env['lims.analysis.media.v2'].create(vals)
            media_count += 1
        
        return media_count
    
    def _assign_individual_media(self, parameter):
        """Asignar medios individuales"""
        if not self.selected_media_ids:
            return 0
        
        # Limpiar medios existentes si está marcado
        if self.clear_existing_media:
            existing_media = parameter.media_ids.filtered(
                lambda m: m.process_type == self.process_type
            )
            existing_media.unlink()
        
        # Crear nuevos medios
        media_count = 0
        for sequence, media in enumerate(self.selected_media_ids, 1):
            vals = {
                'parameter_analysis_id': parameter.id,
                'process_type': self.process_type,
                'media_source': 'internal',
                'culture_media_name': media.name,
                'media_usage': self.media_usage or 'otro',
                'sequence': sequence * 10,
            }
            
            if self.include_incubation_settings:
                vals['requires_incubation'] = True
                
            self.env['lims.analysis.media.v2'].create(vals)
            media_count += 1
        
        return media_count
    
    def _copy_from_parameter(self, parameter):
        """Copiar medios desde otro parámetro"""
        if not self.source_parameter_id:
            return 0
        
        source_media = self.source_parameter_id.media_ids.filtered(
            lambda m: m.process_type == self.process_type
        )
        
        if not source_media:
            return 0
        
        # Limpiar medios existentes si está marcado
        if self.clear_existing_media:
            existing_media = parameter.media_ids.filtered(
                lambda m: m.process_type == self.process_type
            )
            existing_media.unlink()
        
        # Copiar medios
        media_count = 0
        for media in source_media:
            vals = media.copy_data()[0]
            vals['parameter_analysis_id'] = parameter.id
            self.env['lims.analysis.media.v2'].create(vals)
            media_count += 1
        
        return media_count