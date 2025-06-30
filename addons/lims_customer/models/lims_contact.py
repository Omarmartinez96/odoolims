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

    @api.model
    def create(self, vals):
        contact = super().create(vals)

        if not contact.partner_id and contact.email:
            # Crear automáticamente un res.partner
            partner = contact.env['res.partner'].create({
                'name': contact.name,
                'email': contact.email,
                'phone': contact.phone,
                'type': 'contact',
            })
            contact.partner_id = partner.id

        return contact
