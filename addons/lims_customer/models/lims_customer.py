# -*- coding: utf-8 -*-
from odoo import models, fields

class LimsCustomer(models.Model):
    _inherit = 'res.partner'

    is_lims_customer = fields.Boolean(string='Cliente LIMS', default=True)
    client_code = fields.Char(string="Código del Cliente", required=True)

    # Campos adicionales directos de res.partner (para claridad)
    vat = fields.Char(string="RFC / TAX ID")
    street = fields.Char(string="Calle")
    street2 = fields.Char(string="Calle 2")
    city = fields.Char(string="Ciudad")
    state_id = fields.Many2one('res.country.state', string="Estado")
    zip = fields.Char(string="Código Postal")
    country_id = fields.Many2one('res.country', string="País")
    phone = fields.Char(string="Teléfono")
    email = fields.Char(string="Email")
    company_type = fields.Selection(
        [('person', 'Individual'), ('company', 'Compañía')],
        string="Tipo de Compañía",
        default='company'
    )

    fiscal_address = fields.Char(string="Dirección Fiscal")

    branch_ids = fields.One2many(
        'lims.branch',
        'customer_id',
        string="Sucursales"
    )
