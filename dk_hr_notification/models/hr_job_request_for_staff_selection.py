# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class HrJobRequestForStaffSelection(models.Model):
    _name = 'hr.job.request.for.staff.selection'
    _inherit = ['hr.job.request.for.staff.selection', 'send.notification.mail']

    rejection_reason = fields.Char(string='Rejection reason')

    reason_for_closing = fields.Selection([
        ('canceled', 'The customer canceled the vacancy'),
        ('filled', 'The vacancy is filled'),
    ], string='Reason for closing', default=False
    )

    applicant = fields.Many2one(
        comodel_name='hr.applicant',
        string='Applicant',
    )

    date_of_employment = fields.Date(
        string='Date of employment',
    )

    @api.model
    def create(self, vals):
        rec = super(HrJobRequestForStaffSelection, self).create(vals)

        template_values = {
            'first_name': rec.request_initiator.firstname or '',
            'last_name': rec.request_initiator.lastname or '',
            'job_title': rec.request_initiator.job_title or '',
            'display_name': rec.job_id.display_name or '',
            'vacancies_count': rec.vacancies_count or 0,
        }
        rec.send_notification_mail(
            template_name='selection_request_is_open',
            email_from=[rec.request_initiator.work_email],
            template_values=template_values)
        return rec

    def set_rejected(self):
        if not self.rejection_reason:
            raise UserError(_('You must determine the reason for the refusal'))
        else:
            super(HrJobRequestForStaffSelection, self).set_rejected()

            template_values = {
                'display_name': self.job_id.display_name or '',
                'vacancies_count': self.vacancies_count or 0,
                'rejection_reason': self.rejection_reason,
            }
            self.send_notification_mail(
                template_name='selection_request_denied',
                email_to=[self.request_initiator.work_email],
                template_values=template_values)

    def set_closed(self):
        if not self.reason_for_closing:
            raise UserError(_('You must determine the reason for closing'))
        else:
            super(HrJobRequestForStaffSelection, self).set_closed()
            if self.reason_for_closing == 'canceled':
                template_values = {
                    'display_name': self.job_id.display_name or '',
                }
                self.send_notification_mail(
                    template_name='vacancy_is_removed',
                    email_to=[self.request_initiator.work_email],
                    template_values=template_values)
            elif self.reason_for_closing == 'filled':
                template_values = {
                    'display_name': self.job_id.display_name or '',
                    'applicant': self.applicant.display_name or '',
                    'date_of_employment': self.date_of_employment or '',
                }
                recipients = [
                    self.request_initiator.work_email,
                    self.request_initiator.parent_id.work_email,
                ]
                self.send_notification_mail(
                    template_name='job_offer_is_signed',
                    email_to=recipients,
                    template_values=template_values)
