# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2012 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
from osv import osv, fields#, except_osv
from openerp import pooler, tools
from openerp.tools.translate import _

import logging

#from base_external_referentials.decorator import only_for_referential
#from base_external_referentials.external_osv import ExternalSession
from base_external_referentials import external_osv

import os
import re
import time
import socket
import datetime
import ftplib
import tempfile
import csv

_logger = logging.getLogger(__name__)

def encode_vals(d, encoding, errors='replace'):
    res = {}
    for k, v in d.items():
        if isinstance(v, unicode):
            res[k] = v.encode(encoding, errors)
        elif isinstance(v, str):
            res[k] = unicode(v.decode(encoding)).encode(encoding, errors)
        else:
            res[k] = v
    return res

class ExternalReferentialError(Exception):
    def __init__(self, message, model_name=None, res_ids=None):
        super(Exception, self).__init__(message)
        self.model_name = model_name
        self.res_ids = res_ids

class Connection(object):
    '''
    Connection implements import and export of CSV data over FTP.

    Synopnsis, import:

    >>> conn = Connection('username', 'password', 'host', 0, cr, uid)
    >>> conn.init_import(remote_csv_fn='OUT/data.csv', oe_model_name='foo.bar', external_key_name='id', column_headers=['id', 'name', 'other'])
    >>> conn.call('list')
    [{'id': '1', 'name': 'Foo', 'other': 'something'}, {'id': '2', 'name': 'Bar', 'other': 'something'}]
    >>> conn.call('get', id=1)
    [{'id': '1', 'name': 'Foo', 'other': 'Bar'}]
    >>> conn.call('get', other='something')
    [{'id': '1', 'name': 'Foo', 'other': 'something'}, {'id': '2', 'name': 'Bar', 'other': 'something'}]
    >>> conn.finalize_import()

    Synopsis, sync:

    >>> conn = Connection('username', 'password', 'host', 0, cr, uid)
    >>> conn.init_sync(import_csv_fn='OUT/data.csv', export_csv_fn='IN/data.csv', oe_model_name='foo.bar', external_key_name='id', column_headers=['id', 'name', 'other'], required_fields=['id', 'name'])
    >>> conn.call('update', records=[(1, {'id': '1', 'name': 'Baz'}), (2, {'id': '2', 'other': 'something else'})])
    >>> conn.call('create', records=[(3, {'id': '3', 'name': 'Bam'}), (5, {'id': '5', 'name': 'Bat'})])
    >>> conn.finalize_export()
    '''

    def __init__(self, username, password, host, referential_id, cr, uid, port=21, timeout=5, out_encoding='utf-8', csv_writer_opts={}, debug=False, logger=False, reporter=None):
        '''
        The constructor sets up the FTP connection.

        @username (str): FTP username
        @password (str): FTP password
        @host (str): FTP host name
        @referential_id (int): the ID of the external referential which is using this FTP connection
        @cr (Cursor): database cursor
        @uid (int): OpenERP user ID
        @port (int): FTP port
        @timeout (int): FTP connection timeout
        @debug (bool): True if debugging messages should be issued
        @logger (Logger): a Logger object to log to
        @reporter (external_report_lines): an external_report_lines to which some errors will be reported

        Class properties created in this constructor include:

          - _import_cache which is a list of 2-tuples each comprising
            a record number from the CSV file, and a dict of the
            record

          - _export_cache which is a list of 3-tuples each comprising
            a string which may be 'update', 'create', or 'delete', the
            res_id of the original resource, and a dict of the altered
            record
        '''
        assert(isinstance(port, int))
        assert(isinstance(timeout, int))

        self.username = username
        self.password = password
        self.host = host
        self.referential_id = referential_id
        self.cr = cr
        self.uid = uid
        self.port = port
        self.timeout = timeout
        self._oe_model_name = 'external.referential'
        self.debug = debug
        self._out_encoding = out_encoding
        self.logger = logger or _logger
        self.reporter = reporter

        class CustomWriterDialect(csv.Dialect):
            delimiter = csv_writer_opts.get('delimier',',')
            quotechar = csv_writer_opts.get('quotechar','"')
            doublequote = csv_writer_opts.get('doublequote',True)
            skipinitialspace = csv_writer_opts.get('skipinitialspace',False)
            lineterminator = csv_writer_opts.get('lineterminator','\r\n')
            quoting = csv_writer_opts.get('quoting',csv.QUOTE_NONE)
        self._csv_writer_dialect = CustomWriterDialect()
        self._csv_writer_field_proc = csv_writer_opts.get('fieldproc',lambda f: f)

        self._import_ready = False
        self._export_ready = False
        self._sync_ready = False
        self._import_cache = {}
        self._export_cache = {}

        self._dispatch_table = {
            'list': self._list,
            'get': self._get,
            'update': self._update,
            'create': self._create,
            'delete': self._delete
            }

        self._connect()

    def __del__(self):
        self._disconnect()

    def _connect(self, attempts=3, wait_time=3):
        '''
        Connect to the FTP server.

        @attempts (int) number of attempts that should be made to connect
        @wait_time (int) time in seconds to wait between attempts
        '''
        if self.debug:
            self.logger.info('Attempting FTP connection to %s:%d' % (self.host, self.port))

        error_list = []
        for attempt in range(1, attempts+1):
            try:
                self._ftp_client = ftplib.FTP()
                self._ftp_client.connect(self.host, self.port, timeout=self.timeout)
                self._ftp_client.login(user=self.username, passwd=self.password)
                if self.debug:
                    self.logger.info('FTP connection to %s:%d success: "%s"' % (self.host, self.port, self._ftp_client.getwelcome()))
                return True
            except (socket.error, IOError), X:
                except_msg = 'Attempt %d: Could not establish FTP connection to %s:%d: [Errno %d] %s' % (attempt, self.host, self.port, X.errno, X.strerror)
                error_list.append(except_msg)
                self.logger.error(except_msg)
                time.sleep(wait_time)

            except ftplib.all_errors, X:
                except_msg = 'Attempt %d: Could not establish FTP connection to %s:%d: %s' % (attempt, self.host, self.port, X.message)
                error_list.append(except_msg)
                self.logger.error(except_msg)
                time.sleep(wait_time)
 
        err_msg = '\n'.join(error_list)
        self.reporter.log_system_fail(self.cr, self.uid, self._oe_model_name, 'connect', self.referential_id, exc=None, msg=err_msg)
        raise osv.except_osv(_('Connection Error'), _(err_msg))

    def _disconnect(self):
        try:
            if self.debug:
                self.logger.debug('Disconnecting from FTP %s:%d' % (self.host, self.port))
            self._ftp_client.quit()
        except ftplib.all_errors, X:
            if self.debug:
                self.logger.warn('Disconnect from FTP %s:%d failed: %s' % (self.host, self.port, X.message))

    def init_import(self, remote_csv_fn, oe_model_name, external_key_name, column_headers, context=None):
        if not context:
            context = {}

        try:
            self._oe_model_name = oe_model_name
            # make a temporary file to store the CSV
            (self._import_tmp_fd, self._import_tmp_fn) = tempfile.mkstemp(prefix='oe_')

            # retrieve the CSV
            self._import_tmp = open(self._import_tmp_fn, 'wb')
            if self.debug:
                self.logger.debug('CSV import: About to call FTP command: RETR %s' % (remote_csv_fn,))
            self._ftp_client.retrbinary('RETR %s' % (remote_csv_fn,), self._import_tmp.write)

            self._import_tmp.close()
            os.close(self._import_tmp_fd)

            if self.debug:
                self.logger.debug('CSV import: Retrieved %d bytes from %s (remote) into %s (local)' % (os.path.getsize(self._import_tmp_fn), remote_csv_fn, self._import_tmp.name))

            # find the external key name column
            self._id_col_name = external_key_name
            self._column_headers = column_headers
            self._id_col = self._column_headers.index(self._id_col_name)

            self._import_cache = {}
            self._import_ready = True
        except IOError, X:
            msg = 'CSV import: Could not retrieve %s (remote) into %s (local): [Errno %d] %s' %\
                (remote_csv_fn, self._import_tmp.name, X.errno, X.strerror)
            self.logger.error(msg)
            if self.reporter:
                self.reporter.log_system_fail(self.cr, self.uid, self._oe_model_name, 'connect', self.referential_id, exc=X, msg=msg)
            self._clean_up_import()
            self._import_ready = False
        except ftplib.all_errors, X:
            msg = 'CSV import: Could not retrieve %s (remote) into %s (local): %s' %\
                (remote_csv_fn, self._import_tmp.name, X.message)
            self.logger.error(msg)
            if self.reporter:
                self.reporter.log_system_fail(self.cr, self.uid, self._oe_model_name, 'connect', self.referential_id, exc=X, msg=msg)
            self._clean_up_import()
            self._import_ready = False
    
    def find_importables(self, dirs, matching=None, context=None):
        if not context:
            context = {}

        matching = matching or re.compile('.*')
        res = []
        for d in dirs:
            try:
                self._ftp_client.cwd(d)
                res.extend(map(lambda f: d + '/' + f, filter(lambda f: matching.search(f), self._ftp_client.nlst())))
            except ftplib.error_perm, X:
                if str(X) == "550 No files found":
                    # if a directory is empty it doesn't matter
                    continue
                else:
                    msg = 'CSV import: Could not retrieve list of importables from %s matching "%s": %s' %\
                        (d, matching.pattern, X.message)
                    self.logger.error(msg)
                    if self.reporter:
                        self.reporter.log_system_fail(self.cr, self.uid, self._oe_model_name, 'import', self.referential_id, exc=X, msg=msg)
        return res

    def _clean_up_import(self):
        try:
            self._import_cache = {}
            if self._import_tmp:
                if self.debug:
                    self.logger.debug('CSV import: Removing temporary local import file %s' % (self._import_tmp_fn,))
                self._import_tmp.close()
                try:
                    # init_import will have closed the file descriptor
                    # unless an error occurred during retrieval
                    os.close(self._import_tmp_fd)
                except (OSError, IOError):
                    pass
                os.remove(self._import_tmp_fn)
                return True
            else:
                return False
        except IOError, X:
            msg = 'Error removing temporary local import file %s: [Errno %d] %s' %\
                (self._import_tmp_fn, X.errno, X.strerror)
            self.logger.error(msg)
            if self.reporter:
                self.reporter.log_system_fail(self.cr, self.uid, self._oe_model_name, 'import', self.referential_id, exc=X, msg=msg)

    def _check_import_ready(self):
        if not self._import_ready:
            raise ExternalReferentialError('External referential CRUD call made while import data was not available.')
        return True

    def _import_records_iter(self):
        try:
            with open(self._import_tmp_fn, 'rU') as f:
                csv_in = csv.DictReader(f, fieldnames=self._column_headers, restkey='__extra__', restval='__missing__')
                for row in csv_in:
                    if '__extra__' in row or any([v == '__missing__' for v in row.values()]):
                        print row
                        raise csv.Error('Fields in row do not match column headers')
                    yield (csv_in.line_num, row)
        except csv.Error, X:
            msg = 'CSV import: error reading import CSV at line %d: %s' %\
                (csv_in.line_num, X.message)
            self.logger.error(msg)
            if self.reporter:
                self.reporter.log_system_fail(self.cr, self.uid, self._oe_model_name, 'import', self.referential_id, exc=X, msg=msg)
            self._clean_up_import()
            self._import_ready = False
        
    def finalize_import(self, context=None):
        if not context:
            context = {}

        self._clean_up_import()
        self._import_ready = False

    def init_export(self, remote_csv_fn, oe_model_name, external_key_name, column_headers, required_fields, context=None):
        if not context:
            context = {}

        try:
            self._oe_model_name = oe_model_name
            self._export_remote_fn = remote_csv_fn
            (self._export_tmp_fd, self._export_tmp_fn) = tempfile.mkstemp(prefix='oe_')

            if self.debug:
                self.logger.debug('CSV export: Created local CSV cache file %s' % (self._export_tmp_fn,))

            self._id_col_name = external_key_name
            self._column_headers = column_headers
            #self._id_col = self._column_headers.index(self._id_col_name)
            #if self._id_col_name not in required_fields:
            #    required_fields.append(self._id_col_name)
            self._required_fields = required_fields

            self._export_cache = {}
            self._export_ready = True
        except IOError, X:
            msg = 'CSV export: Could not create local CSV cache file %s: [Errno %d] %s' %\
                (self._export_tmp.name, X.errno, X.strerror)
            if self.reporter:
                self.reporter.log_system_fail(self.cr, self.uid, self._oe_model_name, 'export', self.referential_id, exc=X, msg=msg)
            self.logger.error(msg)
            self._clean_up_export()
            self._export_ready = False
        
    def _check_export_ready(self):
        if not self._export_ready:
            raise ExternalReferentialError('External referential CRUD call made before export initialised.')
        return True

    def finalize_export(self, context=None):
        if not context:
            context = {}

        self._check_export_ready()
        try:
            self._export_ready = False
            self._write_export_cache()
            if self.debug:
                self.logger.debug('CSV export: About to execute FTP command: STOR %s; sending %s' % (self._export_remote_fn, self._export_tmp_fn))
            self._ftp_client.storbinary('STOR %s' % (self._export_remote_fn,), open(self._export_tmp_fn, 'rU'))
            self._clean_up_export()
        except IOError, X:
            msg = 'CSV export: Could not send %s (local) to %s (remote): [Errno %d] %s' %\
                (self._export_tmp_fn, self._export_remote_fn, X.errno, X.strerror)
            self.logger.error(msg)
            if self.reporter:
                self.reporter.log_system_fail(self.cr, self.uid, self._oe_model_name, 'export', self.referential_id, exc=X, msg=msg)
            self._clean_up_export()
            raise X
        except ftplib.all_errors, X:
            msg = 'CSV export: Could not send %s (local) to %s (remote): %s' %\
                (self._export_tmp_fn, self._export_remote_fn, X.message)
            self.logger.error(msg)
            if self.reporter:
                self.reporter.log_system_fail(self.cr, self.uid, self._oe_model_name, 'export', self.referential_id, exc=X, msg=msg)
            self._clean_up_export()
            self._export_ready = False
            raise X

    def _write_export_cache(self):
        try:
            with open(self._export_tmp_fn, 'wb') as f:
                csv_out = csv.DictWriter(f, fieldnames=self._column_headers, dialect=self._csv_writer_dialect)
                # TODO Should we send just the altered records? Or all
                # the data we imported with alterations? Let's assume
                # it's everything with alterations for now

                ids = sorted(list(set(self._import_cache.keys() + self._export_cache.keys())))

                for id in ids:
                    try:
                        if id in self._export_cache:
                            op, res_id, rec = self._export_cache[id]
                            if op == 'update' or op == 'create':
                                rec = dict([(k, self._csv_writer_field_proc(v)) for k, v in rec.items() if k in self._column_headers])
                                csv_out.writerow(encode_vals(rec, self._out_encoding))
                            elif op == 'delete':
                                # TODO What to do with deleted records?
                                pass
                        elif id in self._import_cache:
                            rec = self._import_cache[id][1]
                            rec = dict([(k, self._csv_writer_field_proc(v)) for k, v in rec.items() if k in self._column_headers])
                            csv_out.writerow(encode_vals(rec, self._out_encoding))
                    except csv.Error, X:
                        self.logger.error('CSV export: CSV writing error: %s' % (X.message,))
                        raise X
                    except ValueError, X:
                        self.logger.error('CSV export: Attempted to write incorrect record: %s' % (X.message,))
                        raise X

                if self.debug:
                    self.logger.debug('CSV export: wrote %d records to local CSV file %s' % (len(ids), self._export_tmp_fn))
        except IOError, X:
            msg = 'CSV export: Could not write to local CSV file %s: [Errno %d] %s' %\
                (self._export_tmp_fn, self._export_remote_fn, X.errno, X.strerror)
            self.logger.error(msg)
            if self.reporter:
                self.reporter.log_system_fail(self.cr, self.uid, self._oe_model_name, 'export', self.referential_id, exc=X, msg=msg)
            self._clean_up_export()
            raise X

    def _clean_up_export(self):
        try:
            self._export_cache = {}
            if self.debug:
                self.logger.debug('CSV export: Removing temporary local export file %s' % (self._export_tmp_fn,))
            try:
                os.close(self._export_tmp_fd)
            except (OSError, IOError):
                pass
            os.remove(self._export_tmp_fn)
            return True
        except IOError, X:
            msg = 'Error removing temporary local export file %s: [Errno %d] %s' %\
                (self._export_tmp_fn, X.errno, X.strerror)
            self.logger.error(msg)
            if self.reporter:
                self.reporter.log_system_fail(self.cr, self.uid, self._oe_model_name, 'export', self.referential_id, exc=X, msg=msg)
            raise X

    def init_sync(self, import_csv_fn, export_csv_fn, oe_model_name, external_key_name, column_headers, required_fields, context=None):
        if not context:
            context = {}

        self.init_import(import_csv_fn, oe_model_name, external_key_name, column_headers)
        self._cache_import()
        self.init_export(export_csv_fn, oe_model_name, external_key_name, column_headers, required_fields)

        self.sync_ready = True

    def _read_import_ids(self):
        self._check_import_ready()
        for rec_num, row in self._import_records_iter():
            if row[self._id_col_name] not in self._import_cache:
                self._import_cache[row[self._id_col_name]] = (rec_num, None)
            else:
                self._import_cache[row[self._id_col_name]] = (rec_num, self._import_cache[row[self._id_col_name]][1])

    def _cache_import(self):
        self._check_import_ready()
        for rec_num, row in self._import_records_iter():
            self._import_cache[row[self._id_col_name]] = (rec_num, row)

    def call(self, method, **kw_args):
        applicable_method = self._dispatch_table.get(method, None)
        if applicable_method:
            return applicable_method(**kw_args)
        else:
            raise NotImplementedError('External referential for CSV over FTP has no implementation for method: %s' % (method,))

    def _list(self):
        self._check_import_ready()

        # FIXME Should this method include the contents of the
        # _export_cache?
        result = [row for rec_num, row in self._import_records_iter()]

        if self.debug:
            self.logger.debug('CSV import: "list" method returning %d records' % (len(result),))

        return result

    def _get(self, **search_fields):
        assert(len(search_fields) >= 1)
        assert(set(search_fields.keys()) <= set(self._column_headers))
        self._check_import_ready()

        # if the export cache or import cache contains a record for
        # the give ID, return that record
        if self._id_col_name in search_fields:
            if search_fields[self._id_col_name] in self._export_cache:
                return [self._export_cache[search_fields[self._id_col_name]][2]]
            if search_fields[self._id_col_name] in self._import_cache:
                return [self._import_cache[search_fields[self._id_col_name]][1]]

        # otherwise find the records in the local CSV file
        result = [row for rec_num, row in self._import_records_iter()
                  if search_fields == dict([(fn, row[fn]) for fn in search_fields.keys()])]

        # check for duplicate IDs
        if self._id_col_name in search_fields and len(result) > 1:
            self.logger.warn('CSV import: "get" method found %d records matching ID value %s' % (len(result), search_fields[self._id_col_name]))
            # in this case, don't cache
            return result

        # cache the retrieved records
        if self._id_col_name in search_fields:
            for row in result:
                # Stored cached records without the line number
                self._import_cache[row[self._id_col_name]] = (None, row)
                if self.debug:
                    self.logger.debug('CSV import: caching imported record ID %s' % (row[self._id_col_name],))

        return result

    def _update(self, records):
        self._check_export_ready()
        self._check_import_ready()

        if isinstance(records, dict):
            records = [records]

        # FIXME This method can't be used to change the ID value of
        # records
        for res_id, rec in records:
            if self._id_col_name not in rec:
                self.logger.error('CSV export: Cannot update record with no given ID: %s' % (rec,))
                continue
            if self._get(**{self._id_col_name: rec[self._id_col_name]}):
                cpy = self._import_cache[rec[self._id_col_name]][1]
                cpy.update(rec)
                self._export_cache[rec[self._id_col_name]] = ('update', res_id, cpy)
                if self.debug:
                    self.logger.debug('CSV export: updating record with %s=%s' % (self._id_col_name, rec[self._id_col_name]))

        # generate a list of res_ids which will *not* be updated
        failed = list(set([res_id for res_id, r in records]) - set([res_id for op, res_id, rec in self._export_cache.values()]))
        if failed:
            raise ExternalReferentialError('Method "update" failed for IDs: %s' % (failed,), self._oe_model_name, failed)

    def _create(self, records):
        self._check_export_ready()

        if isinstance(records, dict):
            records = [records]

        for res_id, rec in records:
            if not self._id_col_name in rec:
                self.logger.error('CSV export: Will not create record with missing key field: %s' % (rec,))
                continue

            # do not replace existing records
            if rec[self._id_col_name] in self._import_cache:
                self.logger.error('CSV export: Will not replace existing record: %s = %s' % (self._id_col_name, rec[self._id_col_name]))
                continue
                
            # ensure the new record has all the required fields
            if set(self._required_fields).difference(set(rec.keys())):
                self.logger.error('CSV export: Will not create record with missing required fields: %s; %s' %
                                  (', '.join(list(set(self._required_fields) - set(rec.keys()))), rec))
                continue

            # ensure that the new record has values for all fields
            rec.update(dict([(fn, '') for fn in self._column_headers if fn not in rec.keys()]))

            # add the new record to the export cache
            self._export_cache[rec[self._id_col_name]] = ('create', res_id, rec)
            if self.debug:
                self.logger.debug('CSV export: creating record with %s=%s' % (self._id_col_name, rec[self._id_col_name]))

        # generate a list of res_ids which will *not* be exported
        failed = list(set([res_id for res_id, r in records]) - set([res_id for op, res_id, rec in self._export_cache.values()]))
        if failed:
            raise ExternalReferentialError('Method "create" failed for IDs: %s' % (failed,), self._oe_model_name, failed)

    def _delete(self, ids):
        # FIXME How will delete actually work? Do we need to have
        # import_ready?
        self._check_export_ready()
        self._check_import_ready()

        if not isinstance(ids, list):
            ids = [ids]

        failed = []
        for id in ids:
            if self._get(**{self._id_col_name: id}):
                # FIXME What is the res_id?
                self._export_cache[id] = ('delete', None, self._import_cache[id][1])
                if self.debug:
                    self.logger.debug('CSV export: deleting record with %s=%s' % (self._id_col_name, id))
            else:
                self.logger.error('CSV export: Cannot delete record, unknown %s value "%s"' % (self._id_col_name, id))
                failed.append(id)

        # FIXME failed should contain res_ids; it currently returns external keys
        if failed:
            raise ExternalReferentialError('Method "delete" failed for IDs: %s' % (failed,), self._oe_model_name, failed)

