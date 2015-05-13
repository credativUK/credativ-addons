/*---------------------------------------------------------
 * OpenERP web_linkedin (module)
 *---------------------------------------------------------*/

openerp.web_progressbar_custom = function(instance) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

    instance.web_progressbar_custom.FieldProgressBarCustom = instance.web.form.AbstractField.extend({
        template: 'FieldProgressBar',
        render_value: function() {
            var values, start, end, value;
            value = 0.0;
            if (typeof this.get('value') == "string") {
                values = this.get('value').split("/");
                if (values.length == 2) {
                    start = parseFloat(values[0].replace(/^\s+|\s+$/g, ''));
                    end = parseFloat(values[1].replace(/^\s+|\s+$/g, ''));
                    if (start / end != NaN) value = start / end;
                }
            }
            this.$el.progressbar({
                value: value * 100,
                disabled: this.get("effective_readonly")
            });
            this.$('span').html(this.get('value'));
        }
    });

    instance.web.form.widgets.add('progressbar_custom', 'instance.web_progressbar_custom.FieldProgressBarCustom');

    instance.web_progressbar_custom.ListFieldProgressBarCustom = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            var values, start, end, value;
            value = 0.0;
            if (typeof row_data[this.id].value == "string") {
                values = row_data[this.id].value.split("/");
                if (values.length == 2) {
                    start = parseFloat(values[0].replace(/^\s+|\s+$/g, ''));
                    end = parseFloat(values[1].replace(/^\s+|\s+$/g, ''));
                    if (start / end != NaN) value = start / end;
                }
            }
            return _.template(
                '<span><%-text%> <progress value="<%-value%>" max="100" style="width: 50%;"></progress></span>', {
                    value: _.str.sprintf("%.0f", value * 100),
                    text: row_data[this.id].value
                });
        }
    });

    instance.web.list.columns.add('field.progressbar_custom', 'instance.web_progressbar_custom.ListFieldProgressBarCustom');
};
// vim:et fdc=0 fdl=0:
