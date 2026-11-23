import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        UPDATE ir_ui_view
           SET active = FALSE
         WHERE model = 'res.partner'
           AND active = TRUE
           AND arch_db::text LIKE '%custom_child_ids%'
        RETURNING id, name
    """)
    deactivated = cr.fetchall()
    if deactivated:
        _logger.info(
            "Deactivated obsolete res.partner views referencing missing field 'custom_child_ids': %s",
            deactivated,
        )

