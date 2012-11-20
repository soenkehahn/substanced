$(document).ready(
    // set up pjax tabs
    // XXX does this really need to be in a document ready event handler?
    function () {

        var pjax_sel = '#inner-content';

        $(document).pjax(
            '.js-pjax',
            {container:pjax_sel, 
             timeout:0}
        )
            .on('pjax:beforeSend', function () {
                console.log('starting PJAX');
//                $('#inner-content').fadeTo('fast', 0.1);
            })
            .on('pjax:success', function (data) {
//                $('#inner-content').fadeTo('fast', 1);
                return false;
            })
            .on('pjax:error', function (jqxhr, status, error) {
                console.log('pjax server error');
                console.log(error);
            });
        
    }

);

$('.tabtarget').click(
    // manage active tab when it's clicked
    function () {
        $('.tabtarget').removeClass('active');
        $(this).attr({'class':'tabtarget active'});
        return true;
    }
);

    
