# basic_models.py
from odoo import models, fields

class LimsSampleType(models.Model):
    _name = 'lims.sample.type'
    _description = 'Tipo de muestra'
    _order = 'name'
    
    name = fields.Char(
        string='Tipo de muestra',
        required=True,
        translate=True
    )
    description = fields.Text(
        string='Descripción (opcional)'
    )
    active = fields.Boolean(
        string='Activo', 
        default=True
    )

class LimsContainerType(models.Model):
    _name = 'lims.container.type'
    _description = 'Tipo de recipiente'
    _order = 'name'
    
    name = fields.Char(
        string='Nombre del recipiente',
        required=True,
        translate=True
    )
    description = fields.Text(
        string='Descripción (opcional)'
    )
    capacity = fields.Char(
        string='Capacidad', 
        help='Ej: 500mL, 1L'
    )
    material = fields.Selection([
        ('plastic', 'Plástico'),
        ('glass', 'Vidrio'),
        ('metal', 'Metal'),
        ('other', 'Otro')
    ], string='Material')
    active = fields.Boolean(
        string='Activo', 
        default=True
    )

# NOTA: Los modelos lims.branch, lims.department, lims.contact 
# ya existen en el módulo 'lims_customer', no los creamos aquí