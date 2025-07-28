from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class LimsLabEquipment(models.Model):
    _name = 'lims.lab.equipment'
    _description = 'Equipos de Laboratorio'
    _rec_name = 'name'
    _order = 'equipment_type, name'

    name = fields.Char(
        string='Nombre del Equipo',
        required=True,
        help='Nombre o identificador del equipo'
    )
    
    equipment_code = fields.Char(
        string='Código del Equipo',
        help='Código interno del equipo'
    )
    
    equipment_type = fields.Selection([
        ('campana_flujo', 'Campana de Flujo Laminar'),
        ('campana_bioseguridad', 'Campana de Bioseguridad'),
        ('incubadora', 'Incubadora'),
        ('autoclave', 'Autoclave'),
        ('balanza', 'Balanza'),
        ('microscopio', 'Microscopio'),
        ('centrifuga', 'Centrífuga'),
        ('estufa', 'Estufa'),
        ('refrigerador', 'Refrigerador'),
        ('congelador', 'Congelador'),
        ('otro', 'Otro')
    ], string='Tipo de Equipo', required=True)
    
    brand = fields.Char(
        string='Marca'
    )
    
    model = fields.Char(
        string='Modelo'
    )
    
    serial_number = fields.Char(
        string='Número de Serie'
    )
    
    location = fields.Char(
        string='Ubicación',
        help='Ubicación física del equipo en el laboratorio'
    )
    
    is_active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    calibration_date = fields.Date(
        string='Fecha de Calibración'
    )
    
    next_calibration_date = fields.Date(
        string='Próxima Calibración'
    )
    
    maintenance_notes = fields.Text(
        string='Notas de Mantenimiento'
    )
    
    def name_get(self):
        """Mostrar nombre completo del equipo"""
        result = []
        for record in self:
            name = record.name
            if record.equipment_code:
                name = f"[{record.equipment_code}] {name}"
            if record.location:
                name += f" - {record.location}"
            result.append((record.id, name))
        return result