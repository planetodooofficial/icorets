# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class JournalCompanyReassignmentLog(models.Model):
    _name = "journal.company.reassignment.log"
    _description = "Journal Entry Company Reassignment Audit Log"
    _order = "execution_date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    execution_date = fields.Datetime(
        string="Execution Date",
        default=fields.Datetime.now,
        readonly=True,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Executed By",
        default=lambda self: self.env.user,
        readonly=True,
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        readonly=True,
        index=True,
    )
    source_company_id = fields.Many2one(
        "res.company",
        string="Source Company",
        readonly=True,
    )
    target_company_id = fields.Many2one(
        "res.company",
        string="Target / Assigned Company",
        readonly=True,
    )
    action_type = fields.Selection(
        [
            ("manual", "Manual / Batch Reassignment"),
            ("picking_match", "Stock Picking String Match"),
            ("bill_match", "Bill / Invoice / Note Match"),
        ],
        string="Reassignment Method",
        readonly=True,
    )
    records_updated = fields.Integer(
        string="Total Records Updated",
        readonly=True,
    )
    status = fields.Selection(
        [
            ("success", "Success"),
            ("nothing_to_update", "Nothing to Update"),
            ("failed", "Failed / Error"),
        ],
        string="Status",
        default="success",
        readonly=True,
        index=True,
    )
    summary = fields.Text(
        string="Execution Summary & Breakdown",
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == _("New"):
                vals["name"] = f"JRN-LOG/{fields.Datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return super().create(vals_list)
