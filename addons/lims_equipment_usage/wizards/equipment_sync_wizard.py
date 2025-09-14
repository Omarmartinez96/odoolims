from odoo import models, fields, api
from odoo.exceptions import UserError

class LimsEquipmentSyncWizard(models.TransientModel):
    _name = 'lims.equipment.sync.wizard'
    _description = 'Wizard para Sincronizar Equipos'

    equipment_ids = fields.Many2many(
        'lims.lab.equipment',
        string='Equipos a Sincronizar',
        readonly=True
    )
    
    equipment_count = fields.Integer(
        string='Cantidad de Equipos',
        compute='_compute_equipment_count'
    )
    
    sync_incubation = fields.Boolean(
        string='Sincronizar Incubaciones',
        default=True,
        help='Incluir equipos de incubación'
    )
    
    sync_processing = fields.Boolean(
        string='Sincronizar Procesamiento',
        default=True,
        help='Incluir equipos de ambiente (BSC, Flujo Laminar, etc.)'
    )
    
    sync_other_equipment = fields.Boolean(
        string='Sincronizar Otros Equipos',
        default=True,
        help='Incluir equipos adicionales (balanzas, etc.)'
    )
    
    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        for wizard in self:
            wizard.equipment_count = len(wizard.equipment_ids)
    
    def action_sync_equipment(self):
        """Ejecutar sincronización"""
        if not self.equipment_ids:
            raise UserError('No hay equipos seleccionados.')
        
        total_created = 0
        total_updated = 0
        total_skipped = 0
        
        for equipment in self.equipment_ids:
            result = equipment.action_sync_equipment_historical_usage()
            # Extraer números del mensaje si es posible
            # Por ahora solo contar equipos procesados
            total_created += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sincronización Completada',
                'message': f'✅ Se procesaron {len(self.equipment_ids)} equipos correctamente.',
                'type': 'success',
            }
        }
    
    @api.model
    def default_get(self, fields_list):
        """Establecer equipos desde contexto"""
        defaults = super().default_get(fields_list)
        
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            defaults['equipment_ids'] = [(6, 0, active_ids)]
        
        return defaults