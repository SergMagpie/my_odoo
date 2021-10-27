from odoo import models, api, _
from odoo.exceptions import AccessError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def search(self, args, **kwargs):
        result = super(ProjectTask, self).search(args, **kwargs)
        if result and self.user_has_groups('limited_task_performer.group_limited_task_performer'):
            result = result.filtered(
                lambda
                    x: self.env.user.partner_id.id in x.message_follower_ids.partner_id.ids)
        return result

    def read(self, fields=None, context=None, load="_classic_read"):
        actions = super(ProjectTask, self).read(fields=fields, load=load)
        if self.user_has_groups(
                'limited_task_performer.group_limited_task_performer'
        ) and self.env.user.partner_id.id not in self.message_follower_ids.partner_id.ids:
            raise AccessError(_('You are not subscribed to this task!'))
        return actions

    @api.model
    def search_panel_select_range(self, args, **kwargs):
        if self.user_has_groups('limited_task_performer.group_limited_task_performer'):
            search_domain = kwargs['search_domain']
            search_domain.append(['id', 'in', self.search([]).filtered(
                lambda
                    x: self.env.user.partner_id.id in x.message_follower_ids.partner_id.ids).ids])
            kwargs['search_domain'] = search_domain
        result = super(ProjectTask, self).search_panel_select_range(args, **kwargs)
        return result
