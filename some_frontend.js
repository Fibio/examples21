$(document).ready(function() {

    initFieldDatePicker('[name="appointment_date', {
        startDay: getToday(),
    });

    $('#id_total_test_time').change(function() {
        // Calculate vo2max
        var totalTime = $(this).val()
        if (totalTime.length && totalTime != 0) {
            totalTime = parseFloat(totalTime);
            var vo2Max;
            if (pGender == 1) {
                vo2Max = Math.round(4.38 * totalTime - 3.90);
            } else {
                vo2Max = Math.round(14.8 - (1.379 * totalTime) + (0.451 * Math.pow(totalTime, 2)) - (0.012 * Math.pow(totalTime, 3)));
            }
            $('#id_vo2').val(vo2Max);
        } else {
            if (totalTime == 0) {
                $('#id_vo2').val(0);
            }
        }
    });

    $('.weight-test input').change(function() {
        // Calculate RPM
        var thisID = $(this).attr('id');
        var baseID = thisID.substring(0, thisID.lastIndexOf('-'));
        var weightVal = $('#' + baseID + '-weight').val();
        var repsVal = $('#' + baseID + '-reps').val();
        if (weightVal.length != 0 && repsVal.length != 0) {
            var rpm = Math.round(parseFloat(weightVal) + (parseFloat(weightVal) * (parseFloat(repsVal) - 1) * 0.029), 1)
            $('#' + baseID + '-rpm').val(rpm);
        }
    });

    $('.custom-control-input.complete').change(function() {
        var inputParent = $(this).parents('.set-reason ');
        if(this.checked) {
            inputParent.next('.reason').removeClass('d-none');
            inputParent.siblings('.measures').addClass('d-none');
        } else {
            inputParent.next('.reason').addClass('d-none');
            inputParent.siblings('.measures').removeClass('d-none');
        }
    });
});
