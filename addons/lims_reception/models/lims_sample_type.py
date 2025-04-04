#lims_sample_type.py 

from odoo import models, fields

class LimsSampleType(models.Model): 
    _name = 'lims.sample.type'
    _description = 'Tipo de muestra'
    _order = 'name'

    name = fields.Char(
        string='Tipo de muestra',
        #required=True,
        translate=True
    )
    description = fields.Text(
        string='Descripción (opcional)'
    )