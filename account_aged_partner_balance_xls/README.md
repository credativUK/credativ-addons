.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Export Aged Partner Balance to Excel
====================================

This module adds the ability to export to an XLS file to the Aged Partner Balance report wizard.

Limitations
===========

The currencies will not be displayed in the XLS report as it would take significant effort to support the multi-currency and display the symbols
The XLWT library does not allow adding a default filter so no autofilter will be created automatically, this can be easily done through your favourite office application.