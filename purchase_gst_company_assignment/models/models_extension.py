# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this purchase order company ownership was reassigned via GST company reassignment action.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this purchase order line company ownership was reassigned via GST company reassignment action.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this picking company ownership was reassigned via GST company reassignment action.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)


class StockMove(models.Model):
    _inherit = "stock.move"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this stock move company ownership was reassigned via GST company reassignment action.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this stock move line company ownership was reassigned via GST company reassignment action.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)


class AccountMove(models.Model):
    _inherit = "account.move"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this bill/journal entry company ownership was reassigned via GST company reassignment action.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)

    @api.depends("move_type", "line_ids.amount_residual")
    def _compute_payments_widget_reconciled_info(self):
        super()._compute_payments_widget_reconciled_info()
        for move in self:
            if move.invoice_payments_widget and isinstance(move.invoice_payments_widget, dict):
                content = move.invoice_payments_widget.get("content") or []
                for line in content:
                    counterpart_move = False
                    if line.get("move_id"):
                        counterpart_move = self.env["account.move"].browse(line["move_id"])

                    target_company = False
                    if counterpart_move and counterpart_move.company_id:
                        target_company = counterpart_move.company_id
                    elif move.company_id:
                        target_company = move.company_id

                    if target_company:
                        line["company_name"] = target_company.display_name or target_company.name


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this journal item/bill line company ownership was reassigned via GST company reassignment action.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this payment company ownership was reassigned via GST company reassignment action.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        return super()._check_company(fnames=fnames)


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this reconciliation record was updated via GST company reassignment action.",
    )


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this bank statement line was reassigned via GST company reassignment action.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        if hasattr(super(), "_check_company"):
            return super()._check_company(fnames=fnames)


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    is_company_transferred = fields.Boolean(
        string="Is Company Transferred",
        default=False,
        copy=False,
        index=True,
        help="Indicates whether this bank statement was reassigned via GST company reassignment action.",
    )

    def _check_company(self, fnames=None):
        if self.env.context.get("skip_check_company"):
            return
        if hasattr(super(), "_check_company"):
            return super()._check_company(fnames=fnames)
