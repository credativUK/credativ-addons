openerp.save_on_blur_chrome = $(window).blur(function (event) {
    var obj = $(document.activeElement);
    $('a:first').focus();
    $(obj).focus();
});
