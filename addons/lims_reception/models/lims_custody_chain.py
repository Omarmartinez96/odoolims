from odoo import models, fields, api

class LimsCustodyChain(models.Model):
    _name = 'lims.custody_chain'
    _description = 'Cadena de Custodia'
    _rec_name = 'custody_chain_code'

    custody_chain_code = fields.Char(
        string="Código de Cadena de Custodia",
        required=True,
        copy=False,
    )

    cliente_id = fields.Many2one(
        'res.partner', 
        string="Cliente", 
        required=True,
        domain=[('is_lims_customer', '=', True)]
    )


    sucursal_id = fields.Many2one(
        'lims.branch',  # Corregido: antes era 'res.sucursal'
        string="Sucursal",
        required=True,
        domain="[('customer_id', '=', cliente_id)]",
        help="Sucursal asociada al cliente seleccionado."
    )

    departamento_id = fields.Many2one(
        'lims.department',  # Corregido: antes era 'res.departamento'
        string="Departamento",
        domain="[('branch_id', '=', sucursal_id)]",
        help="Departamento asociado a la sucursal seleccionada."
    )

    date_created = fields.Datetime(
        string="Fecha de Creación",
        default=fields.Datetime.now,
    )

    state = fields.Selection(
        [('draft', 'Borrador'),
         ('in_progress', 'En Proceso'),
         ('done', 'Finalizado')],
        string="Estado",
        default='draft',
        required=True,
        help="Estado de la cadena de custodia."
    )

    sample_ids = fields.One2many(
        'lims.sample',
        'custody_chain_id',
        string="Muestras Asociadas",
        help="Lista de muestras asociadas a esta cadena de custodia."
    )
