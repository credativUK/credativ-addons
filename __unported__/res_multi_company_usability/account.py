# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2014 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv

class AccountAccount(osv.osv):
    _inherit = 'account.account'

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code', 'company_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' ' + name
            name = "%s (%s)" % (record['name'], record['company_id'][1])
            res.append((record['id'], name))
        return res

class AccountJournal(osv.osv):
    _inherit = 'account.journal'

    def name_get(self, cr, user, ids, context=None):
        """
        Returns a list of tupples containing id, name.
        result format: {[(id, name), (id, name), ...]}

        @param cr: A database cursor
        @param user: ID of the user currently logged in
        @param ids: list of ids for which name should be read
        @param context: context arguments, like lang, time zone

        @return: Returns a list of tupples containing id, name
        """
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = self.browse(cr, user, ids, context=context)
        res = []
        for rs in result:
            if rs.currency:
                currency = rs.currency
            else:
                currency = rs.company_id.currency_id
            name = "%s (%s) (%s)" % (rs.name, currency.name, rs.company_id.name)
            res += [(rs.id, name)]
        return res

class AccountFiscalyear(osv.osv):
    _inherit = "account.fiscalyear"

    def name_get(self, cr, user, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, user, ids, ['name', 'company_id'], context=context)
        res = []
        for record in reads:
            name = "%s (%s)" % (record['name'], record['company_id'][1])
            res.append((record['id'], name))
        return res

class AccountPeriod(osv.osv):
    _inherit = "account.period"

    def name_get(self, cr, user, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, user, ids, ['name', 'company_id'], context=context)
        res = []
        for record in reads:
            name = "%s (%s)" % (record['name'], record['company_id'][1])
            res.append((record['id'], name))
        return res

class AccountJournalPeriod(osv.osv):
    _inherit = "account.journal.period"

    def name_get(self, cr, user, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, user, ids, ['name', 'company_id'], context=context)
        res = []
        for record in reads:
            name = "%s (%s)" % (record['name'], record['company_id'][1])
            res.append((record['id'], name))
        return res

class AccountTaxCode(osv.osv):
    _inherit = 'account.tax.code'

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','code','company_id'], context)
        return [(x['id'], "%s (%s)" % ((x['code'] and (x['code'] + ' - ') or '') + x['name'], x['company_id'][1])) \
                for x in reads]

class AccountTax(osv.osv):
    _inherit = 'account.tax'

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for record in self.read(cr, uid, ids, ['description','name','company_id'], context=context):
            name = record['description'] and record['description'] or record['name']
            name = "%s (%s)" % (name, record['company_id'][1])
            res.append((record['id'],name ))
        return res

class AccountFiscalPosition(osv.osv):
    _inherit = 'account.fiscal.position'

    def name_get(self, cr, user, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, user, ids, ['name', 'company_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['company_id']:
                name = "%s (%s)" % (name, record['company_id'][1])
            res.append((record['id'], name))
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
