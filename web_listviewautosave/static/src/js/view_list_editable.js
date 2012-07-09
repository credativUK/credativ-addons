openerp.web_listviewautosave = function(openerp) {
var QWeb = openerp.web.qweb,
      _t = openerp.web._t;
openerp.web.ListView.List.include({
        edit_record: function (record_id) {
            if (this.edition) {
                if (this.edition) {
                return this.save_row();
            	}
            } else {
                this.render_row_as_form(
                    this.$current.find('[data-id=' + record_id + ']'));
                $(this).trigger(
                    'edit',
                    [record_id, this.dataset]);
            }
        },
        new_record: function () {
            if (this.edition) {
                var self = this, done = $.Deferred();
                return this.edition_form
                    .do_save(null, this.options.editable === 'top')
                    .pipe(function (result) {
                        if (result.created && !self.edition_id) {
                            self.records.add({id: result.result},
                                {at: self.options.editable === 'top' ? 0 : null});
                            self.edition_id = result.result;
                        }
                        var edited_record = self.records.get(self.edition_id);

                        return $.when(
                            self.handle_onwrite(self.edition_id),
                            self.cancel_pending_edition().then(function () {
                                $(self).trigger('saved', [self.dataset]);
                            })).pipe(function () {
                                self.dataset.index = null;
                                self.render_row_as_form();
                            }, null);
                    }, null);
            } else {
                this.dataset.index = null;
                this.render_row_as_form();
            }
        }
    });
};
