# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    reassignment_log_count = fields.Integer(
        string="Reassignment Logs",
        compute="_compute_reassignment_log_count",
    )
    reassignment_log_ids = fields.One2many(
        "journal.company.reassignment.log",
        "journal_id",
        string="Company Reassignment Logs",
        readonly=True,
    )

    def _compute_reassignment_log_count(self):
        for journal in self:
            journal.reassignment_log_count = self.env["journal.company.reassignment.log"].search_count([
                ("journal_id", "=", journal.id),
            ])

    def action_view_reassignment_logs(self):
        """View all company reassignment audit logs for this journal."""
        self.ensure_one()
        return {
            "name": _("Reassignment Logs: %s", self.name),
            "type": "ir.actions.act_window",
            "res_model": "journal.company.reassignment.log",
            "view_mode": "list,form",
            "domain": [("journal_id", "=", self.id)],
            "context": {"default_journal_id": self.id},
        }

    def action_open_company_reassign_wizard(self):
        """Open Button 1 Wizard: Manual company-to-company reassign for this journal."""
        self.ensure_one()
        return {
            "name": _("Reassign Journal Entries to Branch Company"),
            "type": "ir.actions.act_window",
            "res_model": "journal.company.reassign.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_journal_id": self.id,
                "default_source_company_id": self.company_id.id,
            },
        }

    def action_open_picking_match_wizard(self):
        """Open Button 2 Wizard: Reassign by stock picking string match for this journal."""
        self.ensure_one()
        return {
            "name": _("Reassign Journal Entries by Stock Picking Match"),
            "type": "ir.actions.act_window",
            "res_model": "journal.picking.match.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_journal_id": self.id,
                "default_source_company_id": self.company_id.id,
            },
        }
