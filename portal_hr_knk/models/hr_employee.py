# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, _
from odoo.exceptions import MissingError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def create_emp_user(self):
        # if not self.env['ir.mail_server'].search([]):
        #     raise MissingError(
        #         _("Please create atleast one Outgoing Mail Servers."))
        if not self.work_email:
            raise MissingError(
                _("Please add work email for employee to create portal user."))
        values = {
            'name': self.name,
            'login': self.work_email,
            'email': self.work_email,
        }
        user = self.env['res.users']._create_user_from_template(values)
        user.action_reset_password()
        self.user_id = user
