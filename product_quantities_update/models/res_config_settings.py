from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = ['res.config.settings']

    rkbbearings_end_point_url = fields.Char(
        string='End point URL',
    )  # https://crm.rkbbearings.com/webservice.php
    rkbbearings_user = fields.Char(
        string='User',
    )  # UserWeb
    rkbbearings_user_key = fields.Char(
        string='User key',
    )  # ypOvZ8sqSqMGt9JQ

    planned_date_switzerland = fields.Many2one(
        comodel_name='rkb.planed.date',
        string='Planned date Switzerland',
    )
    planned_date_italy = fields.Many2one(
        comodel_name='rkb.planed.date',
        string='Planned date Italy',
    )
    planned_date_romania = fields.Many2one(
        comodel_name='rkb.planed.date',
        string='Planned date Romania',
    )

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        Param = self.env['ir.config_parameter'].sudo()
        Param.set_param("product_quantities_update.rkbbearings_end_point_url", self.rkbbearings_end_point_url)
        Param.set_param("product_quantities_update.rkbbearings_user", self.rkbbearings_user)
        Param.set_param("product_quantities_update.rkbbearings_user_key", self.rkbbearings_user_key)

        Param.set_param("product_quantities_update.planned_date_switzerland", self.planned_date_switzerland.id)
        Param.set_param("product_quantities_update.planned_date_italy", self.planned_date_italy.id)
        Param.set_param("product_quantities_update.planned_date_romania", self.planned_date_romania.id)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(rkbbearings_end_point_url=params.get_param('product_quantities_update.rkbbearings_end_point_url',
                                                              default='https://crm.rkbbearings.com/webservice.php'))
        res.update(rkbbearings_user=params.get_param('product_quantities_update.rkbbearings_user'))
        res.update(rkbbearings_user_key=params.get_param('product_quantities_update.rkbbearings_user_key'))

        res.update(
            planned_date_switzerland=int(params.get_param('product_quantities_update.planned_date_switzerland')) or False,
            planned_date_italy=int(params.get_param('product_quantities_update.planned_date_italy')) or False,
            planned_date_romania=int(params.get_param('product_quantities_update.planned_date_romania')) or False,
        )
        return res
