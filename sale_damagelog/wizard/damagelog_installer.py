from osv import fields, osv

class damagelog_migrate_config(osv.osv_memory):
    _name = 'damagelog.migrate.config'
    _inherit = 'res.config'

    _columns = {
        'note': fields.text('Description'),
    }
    
    _defaults = {
         'note': """Migrating the check box values to a default selection "Category".
For example, if one Damage Log record has the "Transport" check box selected, when updating the module with the selection box, it would choose "Transport" option from the selection.
Similarly for "Product Quality" check box selected, it would choose "Post-delivery / Quality issue" from the selection. """
    }
    
    def execute(self, cr, uid, ids, context=None):
        if context is None:
             context = {}
             
        obj_damagelog = self.pool.get('sale.damagelog')
        damagelog_ids = obj_damagelog.search(cr, uid, [])
        if damagelog_ids:
            for damagelog in obj_damagelog.browse(cr, uid, damagelog_ids):
                if damagelog.flag_transport:
                    obj_damagelog.write(cr, uid, [damagelog.id], {'category': 'transport'})
                if damagelog.flag_product_quality:
                    obj_damagelog.write(cr, uid, [damagelog.id], {'category': 'pd_quality'})
                
        return {
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'sale.damagelog',
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'nodestroy':False,
                }

damagelog_migrate_config()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: