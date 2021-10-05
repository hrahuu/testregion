# © 2016 Serpent Consulting Services Pvt. Ltd. (support@serpentcs.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo import api, fields, models, _


class MassObject(models.Model):
    _name = "mass.object"
    _description = "Mass Editing Object"

    name = fields.Char('Name', required=True, index=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True, ondelete="cascade",
                               help="Model is used for Selecting Fields. "
                                    "This is editable until Sidebar menu "
                                    "is not created.")
    field_ids = fields.Many2many('ir.model.fields', 'mass_field_rel',
                                 'mass_id', 'field_id', 'Fields')
    ref_ir_act_window_id = fields.Many2one('ir.actions.act_window',
                                           'Sidebar Action',
                                           readonly=True,
                                           help="Sidebar action to make this "
                                                "template available on "
                                                "records of the related "
                                                "document model.")
    model_list = fields.Char('Model List')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', _('Name must be unique!')),
    ]

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.field_ids = [(6, 0, [])]
        model_list = []
        if self.model_id:
            model_obj = self.env['ir.model']
            model_list = [self.model_id.id]
            active_model_obj = self.env[self.model_id.model]
            if active_model_obj._inherits:
                model_names = active_model_obj._inherits.keys()
                inherits_model_list = model_obj.search([('model',
                                                         'in',
                                                         list(model_names))])
                model_list.extend((inherits_model_list and
                                   inherits_model_list.ids or []))
        self.model_list = model_list

    def create_action(self):
        self.ensure_one()
        vals = {}
        action_obj = self.env['ir.actions.act_window']
        button_name = _('Mass Editing (%s)') % self.name
        vals['ref_ir_act_window_id'] = action_obj.create({
            'name': button_name,
            'type': 'ir.actions.act_window',
            'res_model': 'mass.editing.wizard',
            'context': "{'mass_editing_object' : %d}" % (self.id),
            'view_mode': 'form',
            'view_id': self.env.ref('mass_editing.view_mass_object_form').id,
            'target': 'new',
            'binding_model_id': self.model_id.id,
        }).id
        self.write(vals)
        return True

    def unlink_action(self):
        for mass in self:
            try:
                if mass.ref_ir_act_window_id:
                    mass.ref_ir_act_window_id.unlink()
            except:
                raise UserError(_("Deletion of the action record failed."))
        return True

    def unlink(self):
        self.unlink_action()
        return super(MassObject, self).unlink()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update({'name': _("%s (copy)" % self.name), 'field_ids': []})
        return super(MassObject, self).copy(default)
