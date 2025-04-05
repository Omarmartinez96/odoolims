#lims_custody_chain.py 
from odoo import models, fields

class LimsCustodyChain(models.Model):
    _name = 'lims.custody_chain'
    _description = 'Cadena de Custodia'
    _rec_name = 'custody_chain_code'

    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = args

        if name:
            # Buscar por código de cadena y plan de muestreo directamente
            domain = ['|', ('custody_chain_code', operator, name), ('sampling_plan', operator, name)]

            # Buscar muestras relacionadas con varios criterios
            sample_domain = [
                '|', '|', '|', '|', '|',
                ('sample_identifier', operator, name),
                ('sample_description', operator, name),
                ('sample_type_id.name', operator, name),
                ('instrument_used', operator, name),
                ('sampling_technician', operator, name),
            ]

            sample_matches = self.env['lims.sample'].search(sample_domain)
            if sample_matches:
                domain = ['|'] + domain + [('sample_ids', 'in', sample_matches.ids)]

        return self.search(domain, limit=limit).name_get()

    custody_chain_code = fields.Char(
        string="Código de Cadena de Custodia", 
        #required=True, 
        copy=False
    )
    cliente_id = fields.Many2one(
        'res.partner', 
        string="Cliente", 
        #required=True, 
        domain=[('is_lims_customer', '=', True)]
    )
    sucursal_id = fields.Many2one(
        'lims.branch', 
        string="Sucursal", 
        #required=True, 
        domain="[('customer_id', '=', cliente_id)]"
    )
    departamento_id = fields.Many2one(
        'lims.department', 
        string="Departamento", 
        domain="[('branch_id', '=', sucursal_id)]"
    )
    date_created = fields.Datetime(
        string="Fecha de Creación", 
        default=fields.Datetime.now
    )
    sample_ids = fields.One2many(
        'lims.sample', 
        'custody_chain_id', 
        string='Muestra'
    )
    chain_of_custody_state = fields.Selection(
        [('draft', 'Borrador'), ('in_progress', 'En Proceso'), ('done', 'Finalizado')], 
        string="Estado de CdC",
        default='draft', 
        #required=True
    )
    quotation_id = fields.Many2one(
        'sale.order',
        string ="Referencia de cotización"
    )
    sampling_plan = fields.Text(
        string="Plan de muestreo"
    )
    collected_by = fields.Char(
        string="Recolectado por"
    )
    collection_datetime = fields.Datetime(
        string="Fecha y Hora de Recolección"
    )
    sampling_observations = fields.Text(
        string="Observaciones de Muestreo"
    )
    internal_notes = fields.Text(
        string="Observaciones internas"
    )
