$(document).ready(function () {

    var pjax_sel = '#inner-content';
    $(document).pjax(
        '.js-pjax',
        {fragment:pjax_sel, container:pjax_sel, timeout:0}
    )
        .on('pjax:beforeSend', function () {
            console.log('starting PJAX');
//            $('#main').fadeTo('fast', 0.3);
        })
        .on('pjax:success', function (data) {
//            $('#main').fadeTo('fast', 1);
            return false;
        })
        .on('pjax:error', function (jqxhr, status, error) {
            console.log(error);
            console.log('pjax server error');
        });

});


