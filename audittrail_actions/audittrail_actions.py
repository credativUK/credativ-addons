# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2009 credativ Ltd (<http://credativ.co.uk>).
#    All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
from audittrail import audittrail

class audittrail_rule(osv.osv):
    _inherit = "audittrail.rule"
    _columns = {
        "server_action": fields.many2one("ir.actions.server", "Server Action", domain="[('model_id','=',object_id)]"),
    }
audittrail_rule()

class audittrail_objects_proxy2(audittrail.audittrail_objects_proxy):
    """ Uses Object proxy for auditing changes on object of subscribed Rules"""
    
    def process_data(self, cr, uid, pool, res_ids, model, method, old_values={}, new_values={}, field_list=[]):
        """
        This function processes and iterates recursively to log the difference between the old
        data (i.e before the method was executed) and the new data and creates audittrail log
        accordingly.

        :param cr: the current row, from the database cursor,
        :param uid: the current user’s ID,
        :param pool: current db's pooler object.
        :param res_ids: Id's of resource to be logged/compared.
        :param model: model object which values are being changed
        :param method: method to log: create, read, unlink, write, actions, workflow actions
        :param old_values: dict of values read before execution of the method
        :param new_values: dict of values read after execution of the method
        :param field_list: optional argument containing the list of fields to log. Currently only
            used when performing a read, it could be usefull later on if we want to log the write
            on specific fields only.
        :return: True
        """
        # loop on all the given ids
        for res_id in res_ids:
            # compare old and new values and get audittrail log lines accordingly
            lines = self.prepare_audittrail_log_line(cr, uid, pool, model, res_id, method, old_values, new_values, field_list)

            # if at least one modification has been found
            for model_id, resource_id in lines:
                vals = {
                    'method': method,
                    'object_id': model_id,
                    'user_id': uid,
                    'res_id': resource_id,
                }
                if (model_id, resource_id) not in old_values and method not in ('copy', 'read'):
                    # the resource was not existing so we are forcing the method to 'create'
                    # (because it could also come with the value 'write' if we are creating
                    #  new record through a one2many field)
                    vals.update({'method': 'create'})
                if (model_id, resource_id) not in new_values and method not in ('copy', 'read'):
                    # the resource is not existing anymore so we are forcing the method to 'unlink'
                    # (because it could also come with the value 'write' if we are deleting the
                    #  record through a one2many field)
                    vals.update({'method': 'unlink'})
                # create the audittrail log in super admin mode, only if a change has been detected
                if lines[(model_id, resource_id)]:
                    log_id = pool.get('audittrail.log').create(cr, 1, vals)
                    model = pool.get('ir.model').browse(cr, uid, model_id)
                    self.create_log_line(cr, 1, log_id, model, lines[(model_id, resource_id)])
                    
                    context = {
                        'method' : vals['method'],
                        'object' : pool.get(model.model).browse(cr, uid, resource_id),
                        'user': pool.get('res.users').browse(cr, uid, uid).name,
                        'resource_read': old_values and old_values.values()[0]['text'] or new_values.values()[0]['text'],
                        'lines': lines[(model_id, resource_id)],
                    }
                    audit_rule = pool.get('audittrail.rule').search(cr, uid, [('object_id', '=', model_id), ('server_action', '!=', False)])
                    if audit_rule:
                        server_action = pool.get('audittrail.rule').browse(cr, uid, audit_rule[0]).server_action
                        context.update({'active_model': server_action.model_id.id, 'active_id': server_action.id, 'active_ids': [server_action.id]})
                        pool.get('ir.actions.server').run(cr, uid, [server_action.id], context)
        return True
    
audittrail_objects_proxy2()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: