# -*- coding: utf-8 -*-
from odoo import fields, models, api


class HrJobEmployeeRotation(models.Model):
    _name = 'hr.job.employee.rotation'
    _description = 'hr_job_employee_rotation'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin', 'utm.mixin']

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True)

    job_id = fields.Many2one(
        comodel_name='hr.job',
        string='Position',
        required=True)

    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        required=True)

    parent_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Manager',
        required=True)

    experience_all = fields.Integer(
        string='Experience all',
    )

    experience_previous_jobs = fields.Integer(
        string='Experience in previous jobs',
    )

    desired_job_id = fields.Many2one(
        comodel_name='hr.job',
        string='Desired rotation position',
        required=True)

    desired_department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Desired department',
        required=True)

    date_completion = fields.Date(
        string='Date completion',
        default=fields.Date.context_today
    )

    request_initiator = fields.Many2one(
        comodel_name='hr.employee',
        string='Request initiator',
    )

    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),
                   ('new', 'New'),
                   ('pending', 'Pending'),
                   ('approval', 'Approval'),
                   ('closed', 'Closed'),
                   ],
        default='draft',
        tracking=True, )

    def set_draft(self):
        self.write({'state': 'draft'})

    def set_new(self):
        self.write({'state': 'new'})

    def set_pending(self):
        self.write({'state': 'pending'})

    def set_approval(self):
        self.write({'state': 'approval'})

    def set_closed(self):
        self.write({'state': 'closed'})

    def name_get(self):
        results = []
        for rec in self:
            results.append((rec.id, rec.job_id.name))
        return results

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.job_id = self.employee_id.job_id.id
        self.department_id = self.employee_id.department_id.id
        self.parent_id = self.employee_id.parent_id.id
