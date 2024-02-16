# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import base64
from datetime import datetime
from dateutil import relativedelta

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    batch_name = fields.Char(string="Batch name", related="payslip_run_id.name", store=True)