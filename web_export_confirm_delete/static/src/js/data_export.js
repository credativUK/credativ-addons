openerp.web_export_confirm_delete = function(instance) {
var QWeb = instance.web.qweb,
      _t = instance.web._t;
instance.web.DataExport = instance.web.DataExport.extend({
    show_exports_list: function() {
        var self = this;
        if (self.$el.find('#saved_export_list').is(':hidden')) {
            self.$el.find('#ExistsExportList').show();
            return $.when();
        }
        return this._super().done(function (export_list) {
            if (!export_list.length) {
                return;
            }
            self.$el.find('#delete_export_list_confirm').click(function() {
                var select_exp = self.$el.find('#saved_export_list option:selected');
                if (select_exp.val()) {
                    if (!confirm(_.str.sprintf(_t("Do you really want to delete the export list?")))) {
                        return;
                    }
                    self.exports.unlink([parseInt(select_exp.val(), 10)]);
                    select_exp.remove();
                    self.$el.find("#fields_list option").remove();
                    if (self.$el.find('#saved_export_list option').length <= 1) {
                        self.$el.find('#ExistsExportList').hide();
                    }
                }
            });
        });
    }
});

};