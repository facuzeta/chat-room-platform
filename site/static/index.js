function allow_refresh_or_exit() {
    console.log('allow_refresh_or_exit')
    window.onbeforeunload = null;
    $('body').css('overscroll-behavior-y', 'auto')
}
function prevent_refresh_or_exit() {
    console.log('prevent_refresh_or_exit')
    window.onbeforeunload = function () { return true; }
    $('body').css('overscroll-behavior-y', 'contain')

}


function polling() {
    var jqxhr = $.get('get_state', function (data) {
        //console.log(data);
        router(data);
    });

    if ((current_stage != null) && (current_stage.includes('s2_'))) {
        // me fijo que el chatSocket este ok por si se cae.
        if ((chatSocket == null) || (chatSocket.readyState == WebSocket.CLOSED)) {
            // se cayo, trato de reconectar
            if (chatSocket == null) console.log('En polling, chatSocket == null');
            else console.log('En polling, chatSocket.readyState: ', chatSocket.readyState);
            create_chat_and_connect();
        }
    }


    setTimeout(polling, POLLINF_FREQ_IN_MS);
}


function router(data) {
    var stage_name = data.stage_name;
    var stage_name_clean = data.stage_name_clean;

    $('#stage_name').html(stage_name_clean)

    if (stage_name) {
        // state change?
        if (current_stage != stage_name) {
            console.log(current_stage + '->' + stage_name, data, current_timer_interval)
            current_stage = stage_name;

            // reset timer (obj and html) and timout html
            time_clean()

            // set new clock
            if (data.timeout) {
                var timeout_obj = new Date(data.timeout)
                set_timeout_clock(timeout_obj);
            }
            if (data.question_order) {
                question_order = data.question_order;
                question_order_s2 = data.question_order_s2;
            }
            if (data.group_name) {
                group_name = data.group_name;
            }

            if (data.experiment_input_type){
                experiment_input_type = data.experiment_input_type;
            }

            if (data.experiment_has_instructions_s2){
                experiment_has_instructions_s2 = data.experiment_has_instructions_s2;
                experiment_instructions_s2_content = data.experiment_instructions_s2_content;
            }

            if (stage_name == 's1') {
                prevent_refresh_or_exit();
                create_chat_and_connect();
            }

            check_and_submit_not_sent_answer(stage_name);

            render_next_step(stage_name);
        }
    }
}

function modal_show_wait() {
    console.log('modal_show_wait', new Date());
    $('#modal_submit_answers').modal({ backdrop: 'static', keyboard: false });
    return new Promise(function(resolve, reject){
        $('#modal_submit_answers').on('shown.bs.modal', function (event) {
            console.log('modal_show_wait resolve!', new Date());

            resolve()
          })
    })
}

async function modal_hide_wait(div_name) {
    console.log('modal_hide_wait',div_name, new Date());
    if ($('#'+div_name).data('bs.modal')?._isShown){

        $('#'+div_name).modal('hide');
        return new Promise(function(resolve, reject){

            $('#'+div_name).on('shown.bs.modal', function (event) {
                resolve()
              })
        })
    
    }else{
        return new Promise(function(resolve, reject){resolve()})
    }
}

function check_and_submit_not_sent_answer(stage_name) {
    console.log('check_and_submit_not_sent_answer')
    // check if s1 or s3 have rechead timeout
    // and the answers did not have send them yet
    if (stage_name.includes('s2')) {
        if (!has_sent_s1) submit_answers('s1');
    }

    if (stage_name == 'thanks') {
        if (!has_sent_s3) submit_answers('s3');
    }
}

// esta funcion tiene manejar la actualziacion del timer
function set_timeout_clock(timeout_obj) {
    console.log('set_timeout_clock', timeout_obj)
    current_timer_interval = setInterval(timer_update, 1000)
    // $("#current_timeout").html(timeout_obj.toLocaleString());
    current_timeout = timeout_obj;
}

function timer_update() {
    var timeleft = current_timeout - new Date();
    var minutes = Math.floor((timeleft % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = ('00' + Math.floor((timeleft % (1000 * 60)) / 1000).toString()).slice(-2);

    if (timeleft < 0) $(".current_timer").html('');
    else $(".current_timer").html(minutes + ':' + seconds);
}

function time_clean() {
    clearInterval(current_timer_interval);
    current_timer_interval = null;
    $(".current_timer").html('');
    $("#current_timeout").html('');
}


function render_next_step_s1_and_s3(stage_name) {
    // reset time variables
    reset_time_variables();

    // change style clock
    render_header_style(stage_name)

    // show next step
    $("#step_" + stage_name).show()

    var counter = 0;
    question_order.forEach(function (r) {

        var input_id = stage_name + '_input_' + r.question_id;
        var slider_id = stage_name + '_slider_' + r.question_id;

        var initial_value = '';
        if ((stage_name == 's3') && (answer_dic_s1[r.question_id] != null)) {
            initial_value = answer_dic_s1[r.question_id].input_value;
        }

        var stage_number = '1';
        if (stage_name == 's3') stage_number = '3';

        var initial_value_confidence = 3;
        if ((stage_name == 's3') && (answer_dic_s1[r.question_id] != null)) {
            initial_value_confidence = answer_dic_s1[r.question_id].confidence;
        }

        var consensus_value = null;
        if ((stage_name == 's3') && (consensus_dic_s2[r.question_id] != null)) {
            consensus_value = consensus_dic_s2[r.question_id];
        }


        var button_next_message = CMS__next;
        if (counter == question_order.length - 1) button_next_message = CMS__end;

        var display_item = 'none';
        if (counter == 0) display_item = '';

        if (experiment_input_type == 'VALUE_AND_CONFIDENCE') {

            var question = `
            <form action="javascript:next_question(${counter},'${stage_name}')">
                <div id='${stage_name}_question_item_${r.question_id}' style="display:${display_item}" class='${stage_name}_questions_item s1_and_s3_questions_item'>
                    <div style="">
                        <div style='width:100%'>
                        <b>${CMS__stage} ${stage_number}</b> > ${CMS__question} ${counter + 1} / ${question_order.length}
                        </div>
                        <div>

                            <label class='question_green'>${r.text} </label>

                            <div class='question_input_number_class'>
                                <input id="${input_id}"  class='custom-select question_input_number_class_input' value='' type="number" required
                                oninput='javascript:update_change_for_timestamp_value()'
                                placeholder='${CMS__s1_s3_complete_your_answer_placerholder}'>
                            </div>
                            <hr>
                            <input id="${stage_name}_question_id_${r.question_id}"  value='${r.question_id}' type="hidden">

                            <div class='question_confidence_all'>
                                <div class='question_input_confidence_class'>
                                    ${CMS__question_input_confidence_class__text}
                                </div>

                                <div>

                                <div class='row-cuadrado'>
                                    <label class="cuadrado"  for="${slider_id}__label_exslider__0" id='${slider_id}__0'>
                                        <input class="cuadrado-checkbox" type="radio" onchange='javascript:update_change_for_timestamp_slider("${slider_id}__0")'
                                        name="${slider_id}" id="${slider_id}__label_exslider__0" value="1" required> ${CMS__slider_confidence_0}
                                    </label>

                                    <label class="cuadrado"  for="${slider_id}__label_exslider__1"  id='${slider_id}__1'>
                                        <input class="cuadrado-checkbox" type="radio" onchange='javascript:update_change_for_timestamp_slider("${slider_id}__1")'
                                        name="${slider_id}" id="${slider_id}__label_exslider__1" value="2" required> ${CMS__slider_confidence_1}
                                    </label>

                                    <label class="cuadrado"  for="${slider_id}__label_exslider__2"  id='${slider_id}__2'>
                                        <input class="cuadrado-checkbox" type="radio" onchange='javascript:update_change_for_timestamp_slider("${slider_id}__2")'
                                        name="${slider_id}" id="${slider_id}__label_exslider__2" value="3" required> ${CMS__slider_confidence_2}
                                    </label>

                                    <label class="cuadrado"  for="${slider_id}__label_exslider__3"  id='${slider_id}__3'>
                                        <input class="cuadrado-checkbox" type="radio" onchange='javascript:update_change_for_timestamp_slider("${slider_id}__3")'
                                        name="${slider_id}" id="${slider_id}__label_exslider__3" value="4" required> ${CMS__slider_confidence_3}
                                    </label>

                                    <label class="cuadrado"  for="${slider_id}__label_exslider__4"  id='${slider_id}__4'>
                                        <input class="cuadrado-checkbox" type="radio" onchange='javascript:update_change_for_timestamp_slider("${slider_id}__4")'
                                        name="${slider_id}" id="${slider_id}__label_exslider__4" value="5" required> ${CMS__slider_confidence_4}
                                    </label>
                                </div>
                            </div>
                        </div>
                        <input type='submit' class="btn btn-green btn-block" value='${button_next_message}'
                        style="margin: auto;margin-bottom: 10px;margin-top: 60px;"/>

                    </div>
                </div>
            </form>
            `;
       }

       if (experiment_input_type == 'SLIDER_AGREEMENT') {

        var question = `
        <form action="javascript:next_question_for_moral(${counter},'${stage_name}','${input_id}')">
            <div id='${stage_name}_question_item_${r.question_id}' style="display:${display_item}" class='${stage_name}_questions_item s1_and_s3_questions_item'>
                <div style="">
                    <div style='width:100%'>
                    <b>${CMS__stage} ${stage_number}</b> > ${CMS__question} ${counter + 1} / ${question_order.length}
                    </div>
                    <div>

                        <label class='question_green'>${r.text} </label>
                        
                        <br>
                        <label class='question_input_confidence_class'>${CMS__after_statement_moral} </label>

                        
                        <div class='question_input_number_class'>
                         <div id='${input_id}_alert_move_slider' style='display:none; color:#6abc3a'>${CMS__please_move_slider}</div>
                         <label id="${input_id}_value" class='slider_value'></label>

                          <input type="range" min="0" max="10" step="1" 
                          value="5" id="${input_id}" 
                          class="question_input_number_class_input slider_agreement_transparente"  
                          onchange="javascript:update_change_for_timestamp_value();slider_agreement_do_visible('${input_id}')">
                          <span style='float:left'>Nada</span>
                          <span style='float:right'>Mucho</span>
                          <br>
                          <br>

                        </div>
                        <hr>
                        <input id="${stage_name}_question_id_${r.question_id}"  value='${r.question_id}' type="hidden">

                        <div class='question_confidence_all'>
                            <div class='question_input_confidence_class'>
                                ${CMS__question_input_confidence_class__text}
                            </div>

                            <div>

                            <div class='row-cuadrado'>
                                <label class="cuadrado"  for="${slider_id}__label_exslider__0" id='${slider_id}__0'>
                                    <input class="cuadrado-checkbox" type="radio" onchange='javascript:update_change_for_timestamp_slider("${slider_id}__0")'
                                    name="${slider_id}" id="${slider_id}__label_exslider__0" value="1" required> ${CMS__slider_confidence_0}
                                </label>

                                <label class="cuadrado"  for="${slider_id}__label_exslider__1"  id='${slider_id}__1'>
                                    <input class="cuadrado-checkbox" type="radio" onchange='javascript:update_change_for_timestamp_slider("${slider_id}__1")'
                                    name="${slider_id}" id="${slider_id}__label_exslider__1" value="2" required> ${CMS__slider_confidence_1}
                                </label>

                                <label class="cuadrado"  for="${slider_id}__label_exslider__2"  id='${slider_id}__2'>
                                    <input class="cuadrado-checkbox" type="radio" onchange='javascript:update_change_for_timestamp_slider("${slider_id}__2")'
                                    name="${slider_id}" id="${slider_id}__label_exslider__2" value="3" required> ${CMS__slider_confidence_2}
                                </label>

                                <label class="cuadrado"  for="${slider_id}__label_exslider__3"  id='${slider_id}__3'>
                                    <input class="cuadrado-checkbox" type="radio" onchange='javascript:update_change_for_timestamp_slider("${slider_id}__3")'
                                    name="${slider_id}" id="${slider_id}__label_exslider__3" value="4" required> ${CMS__slider_confidence_3}
                                </label>

                                <label class="cuadrado"  for="${slider_id}__label_exslider__4"  id='${slider_id}__4'>
                                    <input class="cuadrado-checkbox" type="radio" onchange='javascript:update_change_for_timestamp_slider("${slider_id}__4")'
                                    name="${slider_id}" id="${slider_id}__label_exslider__4" value="5" required> ${CMS__slider_confidence_4}
                                </label>
                            </div>
                        </div>
                    </div>
                    <input type='submit' class="btn btn-green btn-block" value='${button_next_message}'
                    style="margin: auto;margin-bottom: 10px;margin-top: 60px;"/>

                </div>
            </div>
        </form>
        `;
   }

        $("#" + stage_name + "_questions").append(question);
        counter += 1;
    });

    question_order.forEach(function (r) {
        var slider_id = stage_name + '_slider_' + r.question_id;
        $("#" + slider_id).slider({ 'setValue': '3' });
    })

    if (stage_name == 's3') s3_render_s1_values_new_format(0);
}

function update_change_for_timestamp_value() {
    last_time_value_chage = new Date();
    console.log('update_change_for_timestamp_value', last_time_value_chage);
}

function update_change_for_timestamp_slider(id) {
    $('.cuadrado').removeClass('cuadrado-verde');
    $('#' + id).addClass('cuadrado-verde');
    last_time_slider_change = new Date();
    console.log('update_change_for_timestamp_slider', last_time_slider_change, id);
}

function render_next_step_s2(stage_name) {
    $("#step_s2").show()
    $(".step_s2").show()
    reset_consensus_inputs();

    // get the index of the question (s2_i)
    var i = stage_name[3] - 1;

    // load trigger and change clock style
    var trigger = question_order_s2[i].text;
    $("#stage_s2__trigger").html(trigger);
    $("#div_s2_question").show();
    render_header_style(stage_name)
    console.log(trigger);

    // read preivuosly answers
    var question_id = question_order_s2[i].question_id;
    var value = '';
    var confidence = '';
    if (answer_dic_s1[question_id] != null && answer_dic_s1[question_id].input_value != null) {
        value = answer_dic_s1[question_id].input_value;
        confidence = answer_dic_s1[question_id].confidence;
    }

    console.log(trigger, value, confidence);
    console.log(answer_dic_s1[question_id])

    $("#stage_s2__answered_value").html(value);
    if (experiment_input_type == 'SLIDER_AGREEMENT') {
        $("#stage_s2__answered_value_slash_total").show();

    }

    
    $("#stage_s2__answered_confidence").html(confidence);
    $("#stage_s2__number_question_of").html(i + 1);
    $("#step_s2_controlls").show()

    add_trigger_to_chat(trigger);

    // Si estoy en s2_1 y tengo definido un primer lo muestro
    if (stage_name == 's2_1' && experiment_has_instructions_s2 ){
        show_instructions_s2()
    }


}

function show_instructions_s2(){
    // // add_trigger_to_chat
    // var div = `<div class="trigger_in_chat">
    // <label class="trigger_in_chat_trigger">${experiment_instructions_s2_content}</label>
    // </div>`;
    // $('#chat-log').append(div);
    // var chat = $('#chat-log');
    // if (chat.length) chat.scrollTop(chat[0].scrollHeight - chat.height());

    // $("#inputs-box").hide()

    console.log('show_instructions_s2', new Date())
    $('#modal_instructions_s2_body').html(experiment_instructions_s2_content);
    $('#modal_instructions_s2').modal({
        keyboard: false
      })


    setTimeout(function(){
        console.log('show_instructions_s2_timeout', new Date())
        modal_hide_wait("modal_instructions_s2");
    }, MODAL_PRIMER_S2_TIMEOUT)
}

function render_header_style(stage) {
    if (stage.includes('s2')) {
        $("#header-clock_and_question").show()
        $("#header-onlyclock").hide()
    } else {
        $("#header-clock_and_question").hide()
        $("#header-onlyclock").show()
    }
}

function div_new_question(trigger) {
    div = '<br><br><div style="color:black"><b>';
    div += trigger;
    div += '</b></div>';
    return div
}

function reset_time_variables() {
    last_time_slider_change = null;
    last_time_value_chage = null;
}


// $('#myModal').on('hidden.bs.modal', function (event) {
//     // do something...
//   })

async function render_next_step(stage_name) {


    console.log('render_next_step', stage_name)
    // hide waiting modals
    $(".step").hide();

    if (stage_name == 'ws1') $("#step_" + stage_name).show()


    if ((stage_name == 's1') || (stage_name == 's3')) {
        $("#status").show()
        $("#step_s2_controlls").hide()
        $("#step_s3_controlls").show()

        render_next_step_s1_and_s3(stage_name)
    }

    if (stage_name.includes('s2_')) {
        modal_hide_wait("modal_submit_answers");
        s2_question_timestamp_start = new Date();
        $("#status").show()
        // saco modals por las dudas de nuevo
        // modal_hide_wait();
        render_next_step_s2(stage_name);
        // pongo esto aca nuevamente para evitar una rice condition con los modals
        setTimeout(function() {modal_hide_wait("modal_submit_answers")}, 2000);
    }

    if (stage_name == 'thanks') {
        go_to_thanks();
    }


}

function go_to_thanks() {
    allow_refresh_or_exit();
    window.location.replace("/thanks");

}

function next_question_for_moral(index_current_question, stage_name, slider_id){
    // input_field. setCustomValidity('')
    // if sliders has been moved
    if (slider_has_been_moved(slider_id)){
        next_question(index_current_question, stage_name);
    }else{
        $("#"+slider_id+"_alert_move_slider").show()
        //
        // input_field.setCustomValidity("Por favor definí primero tu respuesta");
        // input_field.reportValidity();
    }
}


async function next_question(index_current_question, stage_name) {
    index_current_question = parseInt(index_current_question);
    $("." + stage_name + "_questions_item").hide()

    // levanto la info y la guardo en las variables answer_dic_s
    var question_id = question_order[index_current_question].question_id;
    var input_value = $("#" + stage_name + "_input_" + question_id).val();
    var question_id_check = $("#" + stage_name + "_question_id_" + question_id).val();
    if (question_id_check != question_id) console.log('Error, esto no deberia pasar')
    var confidence = $('input[name=' + stage_name + '_slider_' + question_id + ']:checked').val()


    if (stage_name == 's1') {
        var r = {
            question_id: question_id, confidence: confidence,
            input_value: input_value, timestamp: new Date(),
            index_current_question: index_current_question,
            last_time_slider_change: last_time_slider_change,
            last_time_value_chage: last_time_value_chage,
        }
        answer_dic_s1[question_id] = r

        // lleno los valore para s3
        $("#s3_input_" + question_id).val(input_value);
        $("#s3_slider_" + question_id).val(confidence);
    }

    if (stage_name == 's3') {
        var r = {
            question_id: question_id, confidence: confidence,
            input_value: input_value, timestamp: new Date(),
            index_current_question: index_current_question,
            last_time_slider_change: last_time_slider_change,
            last_time_value_chage: last_time_value_chage,
        }
        answer_dic_s3[question_id] = r

    }


    if (index_current_question == (question_order.length - 1)) {
        submit_answers(stage_name);
        // oculto todo y muestro modal
        $(".step").hide()
        $("#status").hide()
        $("#step_s3_controlls").hide();

        // show only if I am in s1 (this fix could help avoid rise condition between show and hide modal)
        if (current_stage == 's1') await modal_show_wait();
    } else {
        $("#" + stage_name + "_question_item_" + (question_order[(index_current_question + 1)].question_id)).show()
        // todo no esta andando por ahi es porque no se rendirzo aun?
        $("#" + stage_name + "_input_" + question_order[(index_current_question + 1)].question_id).focus();
        // this fix error in ticks
        $(".sliders").slider('refresh');

        if (stage_name == 's3') {
            s3_render_s1_values_new_format(index_current_question + 1)
        }

    }
}

function s3_render_s1_values_new_format(index) {
    $("#stage_s3__previuosly_consensus_div").hide();

    var next_question_id = question_order[index].question_id;
    if (answer_dic_s1[next_question_id] != null) {
        var current_value = answer_dic_s1[next_question_id].input_value;
        var current_confidence = answer_dic_s1[next_question_id].confidence;

        $("#stage_s3__answered_value").html(current_value);
        $("#stage_s3__answered_confidence").html(current_confidence);
        $("#step_s3_controlls").show();

    }


    var consensus_value = consensus_dic_s2[next_question_id];
    if (consensus_value != null) {
        $("#stage_s3__previuosly_consensus_div").show();
        // $("#stage_s3__consensus_s2").html(consensus_value);
    }


}

function submit_answers(stage_name) {
    console.log('submit_answers', stage_name);
    $("#btn_submit_answers_" + stage_name).hide();


    if (stage_name == 's1') {
        $.post('/answer', { 'answer_dic_s1': JSON.stringify(answer_dic_s1), 'stage_frontend': 's1' });
        console.log('POST s1', answer_dic_s1);
        has_sent_s1 = true;
    }
    if (stage_name == 's3') {
        has_sent_s3 = true;
        $.post('/answer', { 'answer_dic_s3': JSON.stringify(answer_dic_s3), 'stage_frontend': 's3' });
        go_to_thanks();

    }
}


function slider_has_been_moved(div_id){
    var has_moved = $("#"+div_id).hasClass('slider_agreement_visible');
    return has_moved;
}

function submit_consensus() {
    console.log('submit_consensus');
    var value = $("#consensus_value").val();

    if (experiment_input_type == 'SLIDER_AGREEMENT'){
        // if it has not been moved, return
        if (!slider_has_been_moved('consensus_value')) return;
    }

    var i = current_stage[3] - 1;
    var question_id = question_order_s2[i].question_id;

    consensus_dic_s2[question_id] = value;
    data = {
        'consensus_value': value, 'timestamp_consensus': new Date(),
        'timestamp_current_question_discussion_start': s2_question_timestamp_start,
        'question_id': question_id,
    };
    $.post('/answer', { 'answer_dic_s2': JSON.stringify(data), 'stage_frontend': current_stage });

    $('.consensus_ok').hide();
    $("#control_consenso").hide();

    add_consensus_to_chat(value);

    $("#modal_consensus").modal('hide')

}

function reset_consensus_inputs() {
    console.log('reset_consensus_inputs')
    $("#consensus_checkbox").prop('checked', false)

    $("#consensus_value").val('');
    $(".consensus_ok").hide();
    $("#control_consenso").show();
}

function consensus_checkbox_change() {

    $('#modal_consensus').on('hidden.bs.modal', function (e) {
        console.log('se cerro el modal')
        $("#consensus_checkbox").prop('checked',false)
    })
    $('#modal_consensus').on('hide.bs.modal', function (e) {
        console.log('se cerro el modal')
        $("#consensus_checkbox").prop('checked',false)
    })


    console.log('consensus_checkbox_change')

    if ($("#consensus_checkbox").prop('checked')) {
        var content = '';

        if (experiment_input_type == 'VALUE_AND_CONFIDENCE') {

            content = '<label>Valor de la respuesta grupal.</label><input required class="form-control" type="number" placeholder="" id="consensus_value">';
        }
        if (experiment_input_type == 'SLIDER_AGREEMENT') {
            content = `
            <label style='color:black'>La posición grupal con respecto a este frase fue:</label>
            <label id="consensus_value_value" class='slider_value'></label>
            <input type="range" min="0" max="10" step="1" value="" id="consensus_value"
             class="question_input_number_class_input slider_agreement_transparente" 
             onchange="javascript:slider_agreement_do_visible('consensus_value')">
             <span style='color:#6abc3a;float:left'>Nada</span>
             <span style='color:#6abc3a;float:right'>Mucho</span>
             <br>
             <br>             
            `;
        }
        $("#consensus_ok_div_container").html(content);

        $('.consensus_ok').show();
        $('#modal_consensus').modal()
    } else {
        $('.consensus_ok').hide();
        $("#consensus_checkbox").prop('checked',false)
    }
}



// chat
// const roomName = JSON.parse(document.getElementById('room-name').textContent);
function create_chat_and_connect() {
    if (!chatSocket_semaphore) {
        console.log('El semaforo no lo dejo pasar a chatSocket')
        return;
    }

    var ws_protocol = 'ws://'
    if (location.protocol == 'https:') {
        var ws_protocol = 'wss://'
    }

    chatSocket_semaphore = false;
    chatSocket = new WebSocket(
        ws_protocol
        + window.location.host
        + '/ws/chat/'
        + group_name
        + '/'
    );

    console.log('chatSocket.readyState->', chatSocket.readyState)

    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        console.log(data)
        add_to_chat(data.user, data.message, data.color, data.own_msg)
    };

    chatSocket.onclose = function (e) {
        console.error('Chat socket closed unexpectedly');
        create_chat_and_connect();
    };

    document.querySelector('#chat-message-input').focus();
    document.querySelector('#chat-message-input').onkeyup = function (e) {
        if (e.keyCode === 13) {  // enter, return
            document.querySelector('#chat-message-submit').click();
        }
    };

    document.querySelector('#chat-message-submit').onclick = function (e) {
        const messageInputDom = document.querySelector('#chat-message-input');
        const message = messageInputDom.value;
        if (message.length > 0){
            chatSocket.send(JSON.stringify({
                'message': message,
                'stage_name': current_stage,
                'timestamp': new Date(),
            }));    
        }
        messageInputDom.value = '';
    };
    chatSocket_semaphore = true;
}


function add_to_chat(user, message, color, own_msg) {
    if (own_msg) {
        var div = `
                    <div class="chat-box chat-box-right">
                        ${message}
                        <label class="dot" style='vertical-align: middle; background-color:${color};'></label>
                    </div>
                  `;
    } else {
        var div = `
        <div class="chat-box">
            <div style='height:25px; display: flex;justify-content: flex-start;align-content: center;align-items: baseline;'>
                <label class="dot" style='vertical-align: middle; background-color:${color};'></label>
                <label style="color:${color}; font-weight:bold; ">
                ${user}
            </label>
            </div>
            <div style="color:black;margin-top: auto;margin-left: 25px;margin-top: 10px;">${message}</div>
        </div>
    `
    }

    $('#chat-log').append(div);
    var chat = $('#chat-log');
    if (chat.length) chat.scrollTop(chat[0].scrollHeight - chat.height());
}


function add_trigger_to_chat(trigger) {
    var div = `<div class="trigger_in_chat">
                    ${CMS__trigger_to_chat}
                    <label class="trigger_in_chat_trigger">${trigger}</label>
                </div>`;
    $('#chat-log').append(div);
    var chat = $('#chat-log');
    if (chat.length) chat.scrollTop(chat[0].scrollHeight - chat.height());
}


function add_consensus_to_chat(cosensus) {
    var div = `<div class="consensus_in_chat">
                ${CMS__consensus_chat} 
                <label class="consensus_in_chat_value">${cosensus}</label>
            </div>`;
    $('#chat-log').append(div);
    var chat = $('#chat-log');
    if (chat.length) chat.scrollTop(chat[0].scrollHeight - chat.height());
}


function slider_agreement_do_visible(input_id){
    $("#"+input_id).addClass('slider_agreement_visible')
    $("#"+input_id+'_value').html($("#"+input_id).val())


}