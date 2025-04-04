#lims_container_type.py 

from odoo import models, fields

class LimsContainerType(models.Model):
    _name = 'lims.container.type'
    _description = 'Tipo de recipiente'
    _order = 'name'

    name = fields.Char(
        string='Nombre del recipiente',
        #required=True, 
        translate=True
    )
    description = fields.Text(
        string='Descripción (opcional)'
    )