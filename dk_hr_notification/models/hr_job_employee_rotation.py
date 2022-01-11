# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class HrJobEmployeeRotation(models.Model):
    _name = 'hr.job.employee.rotation'
    _inherit = ['hr.job.employee.rotation', 'send.notification.mail']



    @api.model
    def create(self, vals):
        rec = super(HrJobEmployeeRotation, self).create(vals)

        template_values = {
            'name': rec.employee_id.name or '',
            'job_title': rec.job_id.name or '',
            'department_name': rec.department_id.name or '',
        }
        rec.send_notification_mail(
            template_name='rotation_request_is_open',
            email_from=[rec.request_initiator_id.work_email],
            email_to=[rec.employee_id.work_email],
            template_values=template_values)
        return rec


    def write(self, values):
        if not values.get('recruiter_id', False):
            return super(HrJobEmployeeRotation, self).write(values)

        elif not self.recruiter_id:
            result = super(HrJobEmployeeRotation, self).write(values)
            for rec in self:
                template_values = {
                    'user_name': self.recruiter_id.display_name or '',
                }
                recipients = [
                    rec.request_initiator_id.work_email,
                    self.recruiter_id.email,
                ]
                rec.send_notification_mail(
                    template_name='rotation_recruiter_has_been_appointed',
                    email_to=recipients,
                    template_values=template_values)

        elif values.get('recruiter_id', False) != self.recruiter_id.id:
            first_manager_mail = self.recruiter_id.email
            result = super(HrJobEmployeeRotation, self).write(values)
            for rec in self:
                template_values = {
                    'user_name': self.recruiter_id.display_name or '',
                    'action_date': fields.Date.today()
                }
                recipients = [
                    rec.request_initiator_id.work_email,
                    self.recruiter_id.email,
                    first_manager_mail,
                ]
                rec.send_notification_mail(
                    template_name='rotation_hr_manager_changed',
                    email_to=recipients,
                    template_values=template_values)
        else:
            result = super(HrJobEmployeeRotation, self).write(values)
        return result


    def set_rejected(self):
        if not self.rejection_reason:
            raise UserError(_('You must determine the reason for the refusal'))
        else:
            super(HrJobEmployeeRotation, self).set_rejected()
            recipients = [
                self.request_initiator_id.work_email,
                self.employee_id.work_email,
                self.parent_id.work_email,
                self.parent_id.parent_id.work_email,
            ]
            template_values = {
                'name': self.employee_id.name or '',
                'rejection_reason': self.rejection_reason,
            }
            self.send_notification_mail(
                template_name='rotation_request_denied',
                email_to=recipients,
                template_values=template_values)

    def set_closed(self):
        if not self.reason_for_closing:
            raise UserError(_('You must determine the reason for closing'))
        else:
            super(HrJobEmployeeRotation, self).set_closed()
            if self.reason_for_closing == 'refused':
                recipients = [
                    self.request_initiator_id.work_email,
                    self.employee_id.work_email,
                    self.parent_id.work_email,
                    self.parent_id.parent_id.work_email,
                ]
                template_values = {
                    'name': self.employee_id.name or '',
                }
                self.send_notification_mail(
                    template_name='rotation_is_closed_refused',
                    email_to=recipients,
                    template_values=template_values)
            elif self.reason_for_closing == 'head_refused':
                if self.rotation_kind != 'company':
                    raise UserError(_('Rotation is not initiated by the company'))
                recipients = [
                    self.request_initiator_id.work_email,
                    self.employee_id.work_email,
                    self.parent_id.work_email,
                    self.parent_id.parent_id.work_email,
                ]
                template_values = {
                    'name': self.employee_id.name or '',
                }
                self.send_notification_mail(
                    template_name='rotation_is_closed_head_refused',
                    email_to=recipients,
                    template_values=template_values)
            elif self.reason_for_closing == 'reserve':
                recipients = [
                    self.request_initiator_id.work_email,
                    self.employee_id.work_email,
                    self.parent_id.work_email,
                    self.parent_id.parent_id.work_email,
                ]
                template_values = {
                    'name': self.employee_id.name or '',
                }
                self.send_notification_mail(
                    template_name='rotation_is_closed_reserve',
                    email_to=recipients,
                    template_values=template_values)
            elif self.reason_for_closing == 'rotation':
                recipients = [
                    self.request_initiator_id.work_email,
                    self.employee_id.work_email,
                    self.parent_id.work_email,
                    self.parent_id.parent_id.work_email,
                ]
                template_values = {
                    'name': self.employee_id.name or '',
                }
                self.send_notification_mail(
                    template_name='rotation_is_closed_rotation',
                    email_to=recipients,
                    template_values=template_values)
            elif self.reason_for_closing == 'transferred':
                recipients = [
                    self.request_initiator_id.work_email,
                    self.request_initiator_id.parent_id.work_email,
                    self.employee_id.work_email,
                    self.parent_id.work_email,
                    self.parent_id.parent_id.work_email,
                    self.desired_department_id.manager_id.work_email,
                ]
                template_values = {
                    'name': self.employee_id.name or '',
                    'desired_job': self.desired_job_id.name or '',
                    'desired_department': self.desired_department_id.name or '',
                }
                self.send_notification_mail(
                    template_name='rotation_is_closed_transferred',
                    email_to=recipients,
                    template_values=template_values)

    def set_approval(self):
        rec = super(HrJobEmployeeRotation, self).set_approval()
        recipients = [
            self.request_initiator_id.work_email,
            self.request_initiator_id.parent_id.work_email,
            self.employee_id.work_email,
            self.parent_id.work_email,
            self.parent_id.parent_id.work_email,
            self.desired_department_id.manager_id.work_email,
        ]
        template_values = {
            'name': self.employee_id.name or '',
            'desired_job': self.desired_job_id.name or '',
            'desired_department': self.desired_department_id.name or '',
        }
        self.send_notification_mail(
            template_name='rotation_is_approval',
            email_to=recipients,
            template_values=template_values)
        return rec

