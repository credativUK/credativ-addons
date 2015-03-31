Procurement Sale Allocation Scheduler Module
++++++++++++++++++++++++++++++++++++++++++++

The module allows procurements to be switched between the Make To Stock (MTS) and Make To Order (MTO) workflow automatically by the procurement scheduler.


1 Overview
**********

=====================
Procurement Scheduler
=====================

The procurement scheduler is responsible for attempting to complete procurements by making stock available by allocating to available stock, or creating Purchase Orders (PO) to order new stock.


2 User Guide
************

============
User Actions
============

POs can have procurements automatically allocated to them by the procurement scheduler if they have free space and are allowing allocations

A new flag on the PO can set if a PO allows automatic allocations or not

============
Instructions
============

The procurement scheduler will run as a scheduled job as standard, this can be configured by the administrator or run automatically when needed with the mrp_jit module

By setting the flag 'Auto Allocate Procurements' on a PO (default True) the procurement scheduler will attempt to allocate procurements in exception to it


3 Technical Guide
*****************

============
Installation
============

Install the module procurement_sale_allocation_scheduler

All POs will be set to allow automatic allocations by default, for existing POs which should not allow automatic allocations set the field 'procurements_auto_allocate' to false

========
Removing
========

Uninnstall the module procurement_sale_allocation_scheduler

The column 'procurements_auto_allocate' can be safely dropped from the 'purchase.order' table if required.

=======
Testing
=======

1) MTS to MTO automatically

   a) Create and confirm a new PO with MTS product A with quantity 10, with Auto Allocate Procurements set to true

   b) Create and confirm a new SO with MTS product A with quantity 4

   c) Verify the procurement for the SO is MTS and in exception

   d) Run the procurement scheduler

   e) Verify the procurement is linked to the PO and the PO has two lines of 4 and 6, the first allocated to the procurement

   f) Fully receive the PO

   g) Verify the stock for the SO is now available


5 Troubleshooting
*****************

1) A procurement is MTS and in exception but is not being allocated to a PO automatically

   a) Please confirm that there is a PO which has an unallocated PO line for the same product, for at least the same quantity, is going to the same warehouse and location, and is set to allow automatic allocations

2) I have unlinked a procurement to a PO to allow another procurement to be linked to that PO, however the allocation keeps being reset

   a) This would indicate a race condition in the scheduler where it is trying to repeatedly link the first procurement, which has a higher priority, rather than the second to the PO. To get around this the PO can temporarily be set to not allow automatic allocations until both procurements have been updated.
