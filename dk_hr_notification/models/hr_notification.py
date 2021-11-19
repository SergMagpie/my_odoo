from string import Template

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrNotification(models.Model):
    _name = 'hr.notification'

    name = fields.Char(
        string='Name notification',
        translate=True
    )

    template_name = fields.Char(
        string='Internal name',
        required=True,
        index=True,
    )

    notification = fields.Text(
        string='Notification'
    )

    sender = fields.Many2many(
        comodel_name='hr.employee',
        relation='hr_notification_sender_rel',
        string='Notification sender',
    )

    recipient = fields.Many2many(
        comodel_name='hr.employee',
        relation='hr_notification_recipient_rel',
        string='Notification recipient',
    )


class SendNotificationMail(models.AbstractModel):
    _name = 'send.notification.mail'
    _description = 'Send Notification Mail'

    def send_notification_mail(self, template_name, template_values, email_from=[], email_to=[]):
        notification = self.env['hr.notification'].search([('template_name', '=', template_name)], limit=1)
        if not notification:
            raise ValidationError(_("The template is missing or damaged."))
        template_id = self.env['mail.template'].search([('name', '=', template_name)], limit=1)
        if not template_id:
            template = self.env['mail.template']
            template_data = {
                'name': template_name,
                'model_id': self.env['ir.model']._get(self._name).id,
            }
            template_id = template.create(template_data)

        # prepare body
        prepare_body = Template(notification.notification)
        try:
            body = prepare_body.substitute(template_values)
        except KeyError:
            raise ValidationError(_("The template is missing or damaged (KeyError)."))

        template_id['subject'] = notification.name

        email_from.extend(notification.sender.mapped('work_email'))
        senders = ','.join(map(str, filter(lambda x: x, email_from)))
        template_id['email_from'] = senders

        email_to.extend(notification.recipient.mapped('work_email'))
        recipients = ','.join(map(str, filter(lambda x: x, email_to)))
        template_id['email_to'] = recipients

        template_id['body_html'] = body

        if not template_id['mail_server_id']:
            template_id['mail_server_id'] = template_id.mail_server_id.search([], order='sequence', limit=1).id

        template_id['auto_delete'] = False

        template_id.send_mail(self.id, force_send=True, raise_exception=True)
