from odoo import models, fields


class Job(models.Model):
    _inherit = "hr.job"

    def write(self, values):
        if not values.get('user_id', False):
            return super(Job, self).write(values)

        elif not self.user_id:
            result = super(Job, self).write(values)
            for job_request in self.env['hr.job.request.for.staff.selection'].search([('job_id', '=', self.id)]):
                template_values = {
                    'user_name': self.user_id.display_name or '',
                }
                recipients = [
                    job_request.request_initiator_id.work_email,
                    self.user_id.email,
                ]
                job_request.send_notification_mail(
                    template_name='responsible_personnel_manager_has_been_appointed',
                    email_to=recipients,
                    template_values=template_values)

        elif values.get('user_id', False) != self.user_id.id:
            first_manager_mail = self.user_id.email
            result = super(Job, self).write(values)
            for job_request in self.env['hr.job.request.for.staff.selection'].search([('job_id', '=', self.id)]):
                template_values = {
                    'user_name': self.user_id.display_name or '',
                    'action_date': fields.Date.today()
                }
                recipients = [
                    job_request.request_initiator_id.work_email,
                    self.user_id.email,
                    first_manager_mail,
                ]
                job_request.send_notification_mail(
                    template_name='responsible_hr_manager_changed',
                    email_to=recipients,
                    template_values=template_values)
        else:
            result = super(Job, self).write(values)
        return result
