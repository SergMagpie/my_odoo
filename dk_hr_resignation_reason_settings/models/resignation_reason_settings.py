from odoo import api, fields, models, _

# Must be the same as in the model 'hr.resignation' !
RESIGNATION_TYPE = [('resigned', 'Normal Resignation'),
                    ('fired', 'Fired by the company')]


class ResignationReasonSettings(models.Model):
    _name = 'resignation.reason.settings'
    _description = "DK hr resignation reason settings"

    name = fields.Char(
        string='Resignation reason',
        required=True,
    )

    resignation_ids = fields.One2many(
        comodel_name='hr.resignation',
        inverse_name='resignation_reason',
    )

    resignation_type = fields.Selection(
        selection=RESIGNATION_TYPE,
        help="Select the type of resignation: normal "
             "resignation or fired by the company",
        required=True,
    )
