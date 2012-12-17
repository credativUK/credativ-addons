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
import time
import socket
import datetime
import ftplib
import tempfile
import csv

_logger = logging.getLogger(__name__)

class ExternalReferentialError(Exception):
    pass

class Connection(object):
    '''
    Connection implements import and export of CSV data over FTP.

    Synopnsis, import:

    >>> conn = Connection('username', 'password', 'host')
    >>> conn.init_import(remote_csv_fn='OUT/data.csv', external_key_name='id', column_headers=['id', 'name', 'other'])
    >>> conn.call('list')
    [{'id': '1', 'name': 'Foo', 'other': 'something'}, {'id': '2', 'name': 'Bar', 'other': 'something'}]
    >>> conn.call('get', id=1)
    [{'id': '1', 'name': 'Foo', 'other': 'Bar'}]
    >>> conn.call('get', other='something')
    [{'id': '1', 'name': 'Foo', 'other': 'something'}, {'id': '2', 'name': 'Bar', 'other': 'something'}]
    >>> conn.finalize_import()

    Synopsis, sync:

    >>> conn = Connection('username', 'password', 'host')
    >>> conn.init_sync(import_csv_fn='OUT/data.csv', export_csv_fn='IN/data.csv', external_key_name='id', column_headers=['id', 'name', 'other'], required_fields=['id', 'name'])
    >>> conn.call('update', [{'id': '1', 'name': 'Baz'}, {'id': '2', 'other': 'something else'}])
    >>> conn.call('create', [{'id': '3', 'name': 'Bam'}, {'id': '5', 'name': 'Bat'}])
    >>> conn.finalize_export()
    '''

    def __init__(self, username, password, host, port=21, timeout=5, debug=False, logger=False):
        '''
        The constructor sets up the FTP connection.

        @username (str): FTP username
        @password (str): FTP password
        @host (str): FTP host name
        @port (int): FTP port
        @timeout (int): FTP connection timeout
        @debug (bool): True if debugging messages should be issued
        @logger (Logger): a Logger object to log to

        Class properties created in this constructor include:

          - _import_cache which is a list of 2-tuples each comprising
            a record number from the CSV file, and a dict of the
            record

          - _export_cache which is a list of 2-tuples each comprising
            a string which may be 'update', 'create', or 'delete', and
            a dict of the altered record
        '''
        assert(isinstance(port, int))
        assert(isinstance(timeout, int))

        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.timeout = timeout
        self.debug = debug
        self.logger = logger or _logger

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
 
        #raise except_osv(_('Connection Error'), _('\n'.join(error_list)))
        # TODO Issue error email; can we do this by raising an
        # exception?

    def _disconnect(self):
        try:
            if self.debug:
                self.logger.debug('Disconnecting from FTP %s:%d' % (self.host, self.port))
            self._ftp_client.quit()
        except ftplib.all_errors, X:
            if self.debug:
                self.logger.warn('Disconnect from FTP %s:%d failed: %s' % (self.host, self.port, X.message))

    def init_import(self, remote_csv_fn, external_key_name, column_headers):
        try:
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
            # TODO Report error
            self.logger.error('CSV import: Could not retrieve %s (remote) into %s (local): [Errno %d] %s' % (remote_csv_fn, self._import_tmp.name, X.errno, X.strerror))
            self._clean_up_import()
            self._import_ready = False
        except ftplib.all_errors, X:
            # TODO Report error
            self.logger.error('CSV import: Could not retrieve %s (remote) into %s (local): %s' % (remote_csv_fn, self._import_tmp.name, X.message))
            self._clean_up_import()
            self._import_ready = False
    
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
            self.logger.error('Error removing temporary local import file %s: [Errno %d] %s' % (self._import_tmp_fn, X.errno, X.strerror))
            # TODO Report error

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
            self.logger.error('CSV import: error reading import CSV at line %d: %s' % (csv_in.line_num, X.message))
            self._clean_up_import()
            self._import_ready = False
            # TODO Report error
        
    def finalize_import(self):
        self._clean_up_import()
        self._import_ready = False

    def init_export(self, remote_csv_fn, external_key_name, column_headers, required_fields):
        try:
            self._export_remote_fn = remote_csv_fn
            (self._export_tmp_fd, self._export_tmp_fn) = tempfile.mkstemp(prefix='oe_')

            if self.debug:
                self.logger.debug('CSV export: Created local CSV cache file %s' % (self._export_tmp_fn,))

            self._id_col_name = external_key_name
            self._column_headers = column_headers
            self._id_col = self._column_headers.index(self._id_col_name)
            if self._id_col_name not in required_fields:
                required_fields.append(self._id_col_name)
            self._required_fields = required_fields

            self._export_cache = {}
            self._export_ready = True
        except IOError, X:
            # TODO Report error
            self.logger.error('CSV export: Could not create local CSV cache file %s: [Errno %d] %s' % (self._export_tmp.name, X.errno, X.strerror))
            self._clean_up_export()
            self._export_ready = False
        
    def _check_export_ready(self):
        if not self._export_ready:
            raise ExternalReferentialError('External referential CRUD call made before export initialised.')
        return True

    def finalize_export(self):
        self._check_export_ready()
        try:
            self._export_ready = False
            self._write_export_cache()
            if self.debug:
                self.logger.debug('CSV export: About to execute FTP command: STOR %s; sending %s' % (self._export_remote_fn, self._export_tmp_fn))
            self._ftp_client.storbinary('STOR %s' % (self._export_remote_fn,), open(self._export_tmp_fn, 'rU'))
            self._clean_up_export()
        except IOError, X:
            # TODO Report error
            self.logger.error('CSV export: Could not send %s (local) to %s (remote): [Errno %d] %s' % (self._export_tmp_fn, self._export_remote_fn, X.errno, X.strerror))
            self._clean_up_export()
        except ftplib.all_errors, X:
            # TODO Report error
            self.logger.error('CSV export: Could not send %s (local) to %s (remote): %s' % (self._export_tmp_fn, self._export_remote_fn, X.message))
            self._clean_up_export()
            self._export_ready = False

    def _write_export_cache(self):
        try:
            with open(self._export_tmp_fn, 'wb') as f:
                csv_out = csv.DictWriter(f, fieldnames=self._column_headers, quoting=csv.QUOTE_ALL)
                # TODO Should we send just the altered records? Or all
                # the data we imported with alterations? Let's assume
                # it's everything with alterations for now

                ids = sorted(list(set(self._import_cache.keys() + self._export_cache.keys())))

                try:
                    for id in ids:
                        if id in self._export_cache:
                            op, rec = self._export_cache[id]
                            if op == 'update' or op == 'create':
                                csv_out.writerow(self._export_cache[id][1])
                            elif op == 'delete':
                                # TODO What to do with deleted records?
                                pass
                        elif id in self._import_cache:
                            csv_out.writerow(self._import_cache[id][1])
                except csv.Error, X:
                    self.logger.error('CSV export: CSV writing error at line %d: %s' % (csv_out.line_num, X.message))
                    # TODO Report error
                except ValueError, X:
                    self.logger.error('CSV export: Attempted to write incorrect record at line %d: %s' % (csv_out.line_num, X.message))
                    # TODO Report error

                if self.debug:
                    self.logger.debug('CSV export: wrote %d records to local CSV file %s' % (len(ids), self._export_tmp_fn))
        except IOError, X:
            # TODO Report error
            self.logger.error('CSV export: Could not write to local CSV file %s: [Errno %d] %s' % (self._export_tmp_fn, self._export_remote_fn, X.errno, X.strerror))
            self._clean_up_export()

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
            self.logger.error('Error removing temporary local export file %s: [Errno %d] %s' % (self._export_tmp_fn, X.errno, X.strerror))
            # TODO Report error

    def init_sync(self, import_csv_fn, export_csv_fn, external_key_name, column_headers, required_fields):
        self.init_import(import_csv_fn, external_key_name, column_headers)
        self._cache_import()
        self.init_export(export_csv_fn, external_key_name, column_headers, required_fields)

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
            for cache in [self._export_cache, self._import_cache]:
                rec_no, record = cache.get(search_fields[self._id_col_name], (None, None))
                if record:
                    return [record]

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
        for rec in records:
            if self._id_col_name not in rec:
                self.logger.error('CSV export: Cannot update record with no given ID: %s' % (rec,))
                continue
            if self._get(**{self._id_col_name: rec[self._id_col_name]}):
                cpy = self._import_cache[rec[self._id_col_name]][1]
                cpy.update(rec)
                print 'Updating %s with %s to make %s' % (self._import_cache[rec[self._id_col_name]][1], rec, cpy)
                self._export_cache[rec[self._id_col_name]] = ('update', cpy)
                if self.debug:
                    self.logger.debug('CSV export: updating record with %s=%s' % (self._id_col_name, rec[self._id_col_name]))

    def _create(self, records):
        self._check_export_ready()
        self._check_import_ready()

        if isinstance(records, dict):
            records = [records]

        for rec in records:
            # do not replace existing records
            if rec[self._id_col_name] in self._import_cache:
                self.logger.error('CSV export: Will not replace existing record: %s = %s' % (self._id_col_name, rec[self._id_col_name]))
                continue
                
            # ensure the new record has all the required fields
            if not(set(rec.keys()) <= set(self._required_fields)):
                self.logger.error('CSV export: Will not create record with missing required fields: %s; %s' %
                                  (', '.join(list(set(self._required_fields) - set(rec.keys()))), rec))
                continue

            # ensure that the new record has values for all fields
            rec.update(dict([(fn, '') for fn in self._column_headers if fn not in rec.keys()]))

            # add the new record to the export cache
            self._export_cache[rec[self._id_col_name]] = ('create', rec)
            if self.debug:
                self.logger.debug('CSV export: creating record with %s=%s' % (self._id_col_name, rec[self._id_col_name]))

    def _delete(self, ids):
        self._check_export_ready()
        self._check_import_ready()

        if not isinstance(ids, list):
            ids = [ids]

        for id in ids:
            if self._get(**{self._id_col_name: id}):
                self._export_cache[id] = ('delete', self._import_cache[id][1])
                if self.debug:
                    self.logger.debug('CSV export: deleting record with %s=%s' % (self._id_col_name, id))
            else:
                self.logger.error('CSV export: Cannot delete record, unknown %s value "%s"' % (self._id_col_name, id))
