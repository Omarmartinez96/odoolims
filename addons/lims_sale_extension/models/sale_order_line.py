# -*- coding: utf-8 -*-
from odoo import api, models

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        # Llamamos al comportamiento base para que ponga precio, impuestos, etc.
        super(SaleOrderLine, self)._onchange_product_id()
        # Si hay producto, armamos el name completo
        if self.product_id:
            # Nombre del producto
            name = self.product_id.display_name
            # Descripción de venta (puede tener varias líneas)
            desc = self.product_id.description_sale or ''
            # Concatenamos nombre + salto de línea + descripción
            self.name = name + (('\n' + desc) if desc else '')
