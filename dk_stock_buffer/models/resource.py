from odoo import fields, models, api


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    number_of_days = fields.Integer(
        string='Number of days',
        compute='_compute_number_of_days',
        store=True,
    )

    @api.depends('attendance_ids', 'attendance_ids.week_type', )
    def _compute_number_of_days(self):
        for rec in self:
            attendances = rec._get_global_attendances()
            if rec.two_weeks_calendar:
                number_of_days = len(set(attendances.filtered(lambda cal: cal.week_type == '1').mapped('dayofweek')))
                number_of_days += len(set(attendances.filtered(lambda cal: cal.week_type == '0').mapped('dayofweek')))
            else:
                number_of_days = len(set(attendances.mapped('dayofweek')))

            rec.number_of_days = number_of_days


