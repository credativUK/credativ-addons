import wizard
import pooler
import netsvc

stock_move_form = "" 

stock_move_fields = {
    'stock_move_id' : {'string':'Stock Move', 'type':'many2one','relation':'stock.move', 'required':True}
}

def _create_damage_log(self, cr, uid, data, context=None):
    pool = pooler.get_pool(cr.dbname)
    mod_obj = pool.get('ir.model.data')
    act_obj = pool.get('ir.actions.act_window')
    damagelog_obj = pool.get('sale.damagelog')
    move = pool.get('stock.move').read(cr, uid, data['form']['stock_move_id'], ['product_qty'], context=context)
    damagelog_id = damagelog_obj.create(cr,uid,{'stock_move_id':data['form']['stock_move_id'],'product_qty':move['product_qty']},context=context)
    return {
            'name': 'Damage Log',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'sale.damagelog',
            'view_id': False,
            'res_id': damagelog_id,
            'type': 'ir.actions.act_window',
            }

 
     

class create_damagelog_from_outgoing(wizard.interface):
    
    def execute_cr(self, cr, uid, data, state='init', context=None):
        self.states[state]['result']['arch'] = """<?xml version="1.0"?>
                                                <form string="Create Damage Log">
                                                    <separator colspan="4" string="Select a stock move for the damagelog" />
                                                    <field name="stock_move_id" domain="[('picking_id','=',""" + str(context.get('active_id',False)) + """)]"/>
                                                </form>
                                                """
        return super(create_damagelog_from_outgoing, self).execute_cr(cr, uid, data, state=state, context=context)
     
    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : stock_move_form,
                    'fields' : stock_move_fields,
                    'state' : [('end', 'Cancel'),('create', 'Create DamageLog') ]}
        },
        'create' : {
            'actions' : [],
            'result' : {'type' : 'action',
                    'action' : _create_damage_log,
                    'state' : 'end'}
        },
    }
    
create_damagelog_from_outgoing("outgoing_create_damagelog")
