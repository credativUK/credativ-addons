from openerp import netsvc
from osv import osv

class purchase_order(osv.osv):

    _name    = 'purchase.order'
    _inherit = 'purchase.order'



    # Create invoices for pickings whose ids are specified in context.
    # journal_id, group and invoice date can be specified using wiz_defs.
    def _create_invoice(self, cr, uid, ids, wiz_defs, context=None):
        if context is None:
            context = {}

        picking_pool = self.pool.get('stock.picking')
        context.update({'date_inv' : wiz_defs.get('invoice_date', False)})
        active_ids = context.get('active_ids', [])
        active_picking = picking_pool.browse(cr, uid, context.get('active_id',False), context=context)
        inv_type = picking_pool._get_invoice_type(active_picking)
        context.update({'inv_type' : inv_type})
        if isinstance(wiz_defs['journal_id'], tuple):
            wiz_defs['journal_id'] = wiz_defs['journal_id'][0]
        res = picking_pool.action_invoice_create(cr, uid, active_ids,
                                                 journal_id = wiz_defs['journal_id'],
                                                 group = wiz_defs.get('group', False),
                                                 type = inv_type,
                                                 context=context)
        return res



    # Called on a purchase_order when the corresponding incoming picking is received.
    # Extend the existing code to automate incoive creation / validation at this point.
    def picking_done(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        ret = super(purchase_order, self).picking_done(cr, uid, ids, context=context)
        wf_service = netsvc.LocalService('workflow')
        wiz_obj = self.pool.get('stock.invoice.onshipping')
        pick_obj = self.pool.get('stock.picking')
        for id in ids:
            pick_ids = pick_obj.search(cr, uid, [('purchase_id','=',id)], context=context)

            # Identify pickings associated with this PO which require invoicing.
            pick_data = pick_obj.read(cr, uid, pick_ids, ['invoice_state'], context=context)
            pick_ids_2bi = [pd['id'] for pd in pick_data if pd['invoice_state'] == '2binvoiced']

            if pick_ids_2bi:

                # Call to default_get (and view_init by extension)
                # requires information passed in through context.
                context.update({ 'active_id'    : pick_ids_2bi[0],
                                 'active_ids'   : pick_ids_2bi[:],
                                 'active_model' : 'stock.picking',
                               })

                # Get and use the values that the wizard would have used by default,
                # and create the invoice(s).
                wiz_fields = ['journal_id','group','invoice_date']
                wiz_defs = wiz_obj.default_get(cr, uid, wiz_fields, context=context)
                inv_res = self._create_invoice(cr, uid, ids, wiz_defs, context=context)
                p2bi = pick_ids_2bi
                inv_ids = [inv_res.get(p2bi[i], False) for i in range(len(p2bi))]
                inv_ids = [iid for iid in inv_ids if iid]

                # Send the signal to validate each newly-created invoice.
                for inv_id in inv_ids:
                    wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cr)

        return ret



purchase_order()
