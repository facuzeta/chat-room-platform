
function send_external_rater_value(erv_id) {

    data = {
        erv_id: erv_id,
        value_fermi: $("#value__" + erv_id + "__fermi").val(),
        value_number: $("#value__" + erv_id + "__number").val(),
    }

    $.post('/external_raters/save_rate/'+HASH+"/"+erv_id+"/"+data.value_fermi+'/'+data.value_number,{}).done(function(msg){  })
    .fail(function(xhr, status, error) {
        // error handling
        alert("There was a problem saving the results", error)
    });

    console.log(data)


    // Hide the current prompt.
    $("#chat__"+erv_id).hide()

    // Show the next prompt.
    var actual_chat_index = $(".rater_valuation").index($("#chat__"+erv_id))

    if (actual_chat_index < $(".rater_valuation").length -1){
        
        var next_erv_id = $($(".rater_valuation")[actual_chat_index+1])[0].id.split("__")[1]

        console.log("next_erv_id=",next_erv_id)

        // Show it.
        $("#chat__"+next_erv_id).show()

        // Focus the first input.
        $("#value__"+next_erv_id+"__fermi").focus()


    }else{
        location.reload()
    }

    
}
