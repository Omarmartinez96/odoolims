from odoo import models, fields, api

class LimsContact(models.Model):
    _name = 'lims.contact'
    _description = 'Contactos'

    name = fields.Char(string="Nombre del Contacto", required=True)
    email = fields.Char(string="Correo Electrónico")
    phone = fields.Char(string="Teléfono")

    department_id = fields.Many2one(
        'lims.department',
        string="Departamento",
        required=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string="Contacto (Odoo)",
        help="Se utiliza para funciones nativas como correos."
    )

    job_title = fields.Char(string="Puesto", help="Cargo o puesto del contacto en la empresa")

    @api.model_create_multi
    def create(self, vals_list):
        contacts = super().create(vals_list)

        return contacts
