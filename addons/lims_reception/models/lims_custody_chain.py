#lims_custody_chain.py 
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LimsCustodyChain(models.Model):
    _name = 'lims.custody_chain'
    _description = 'Cadena de Custodia'
    _rec_name = 'custody_chain_code'

    contact_id = fields.Many2one('res.partner',
        string='Contacto'
    )
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

    def send_email_comprobante(self):
        for record in self:
            if record.chain_of_custody_state != 'done':
                raise UserError(_('La cadena de custodia debe estar finalizada para enviar el comprobante.'))

            #Usar el contacto si existe, sino el cliente
            email = record.contact_id.email or record.cliente_id.email
            if not email:
                raise UserError(_('No se encontró un correo electrónico válido en el contacto o cliente'))

            #Busca la plantilla de correo
            template = self.env.ref('lims_custody_chain.email_template_comprobante', 
            raise_if_not_found=False
            )
            if not template: 
                raise UserError(_('No se encontró la plantilla de correo electrónico.'))

            #Reemplazar dinámicamente el destinatario si es necesario
            mail_values = {'email_to': email}
            template.send_mail(record.id, 
            force_send=True,
            email_values=mail_values
            )