# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _inherit = ['hr.resignation', 'send.notification.mail']

    cancel_resignation_reason = fields.Selection(
        selection=[('remains', 'The employee remains to work in the company.'),
                   ('fired', 'The employee is fired, all subtasks for dismissal are fulfilled.')],
        string='Cancel resignation reason',
    )

    @api.model
    def create(self, vals):
        rec = super(HrResignation, self).create(vals)

        template_values = {
            'name': rec.employee_id.name or '',
            'job_title': rec.hr_job_id.name or '',
            'department_name': rec.department_id.name or '',
            'resignation_type': rec.resignation_type or '',
        }
        rec.send_notification_mail(
            template_name='resignation_request_is_open',
            email_from=[rec.employee_id.parent_id.work_email],
            email_to=[rec.employee_id.parent_id.parent_id.work_email],
            template_values=template_values)
        return rec

    def write(self, values):
        if not values.get('responsible_manager_id', False):
            return super(HrResignation, self).write(values)

        elif not self.responsible_manager_id:
            result = super(HrResignation, self).write(values)
            for rec in self:
                template_values = {
                    'user_name': self.responsible_manager_id.display_name or '',
                }
                recipients = [
                    rec.employee_id.parent_id.work_email,
                    self.responsible_manager_id.email,
                ]
                rec.send_notification_mail(
                    template_name='resignation_recruiter_has_been_appointed',
                    email_to=recipients,
                    template_values=template_values)

        elif values.get('responsible_manager_id', False) != self.responsible_manager_id.id:
            first_manager_mail = self.responsible_manager_id.email
            result = super(HrResignation, self).write(values)
            for rec in self:
                template_values = {
                    'user_name': self.responsible_manager_id.display_name or '',
                    'action_date': fields.Date.today()
                }
                recipients = [
                    rec.employee_id.parent_id.work_email,
                    self.responsible_manager_id.email,
                    first_manager_mail,
                ]
                rec.send_notification_mail(
                    template_name='resignation_hr_manager_changed',
                    email_to=recipients,
                    template_values=template_values)
        else:
            result = super(HrResignation, self).write(values)
        return result

    def cancel_resignation(self):
        if not self.cancel_resignation_reason:
            raise UserError(_('You must determine the reason for cancel'))
        else:
            super(HrResignation, self).cancel_resignation()
            if self.cancel_resignation_reason == 'remains':
                recipients = [
                    self.employee_id.parent_id.work_email,
                    self.employee_id.parent_id.parent_id.work_email,
                ]
                template_values = {
                    'name': self.employee_id.name or '',
                }
                self.send_notification_mail(
                    template_name='resignation_is_cancel_remains',
                    email_to=recipients,
                    template_values=template_values)
            elif self.cancel_resignation_reason == 'fired':
                recipients = [
                    self.employee_id.parent_id.work_email,
                    self.employee_id.parent_id.parent_id.work_email,
                ]
                template_values = {
                    'name': self.employee_id.name or '',
                }
                self.send_notification_mail(
                    template_name='resignation_is_cancel_fired',
                    email_to=recipients,
                    template_values=template_values)
