//Code started by Michael Ortega for the LIG
//December 06th, 2016


var select_op_divs      = []
var select_op_selected  = []
var nb_cols_in_displayed_table = 4

//This function ask about all the operators, and then update the "operators selection" modal
function select_op_open_modal() {
    
    //cleaning
    $('#select_op_tags_select').empty();
    $('#select_op_names_select').empty();
    document.getElementById('select_op_panel_title').value = '';
    
    //Before opening the modal, we have to ask about the existing operators, and then make the tags list
    ws_request('list_operators_classes', [], {}, function (result) {
        var tags_list = [];
        var sostl = document.getElementById('select_op_tags_select');
        var sosnl = document.getElementById('select_op_names_select');
        
        var div = document.getElementById('select_op_panel');
        while(div.firstChild){
            div.removeChild(div.firstChild);
        }
        
        global_ops_cl = JSON.parse(JSON.stringify(result));
        global_ops_cl.forEach( function (op) {
            op['tags'].forEach( function (tag) {
                if (tags_list.indexOf(tag) == -1) {
                        tags_list.push(tag);
                        var option = document.createElement("option");
                        option.text = tag;
                        sostl.add(option);
                }
            });
            var option = document.createElement("option");
            option.text = op['name'];
            option.value = op['id'];
            option.setAttribute("data-subtext", op['daemon']);
            sosnl.add(option);
        });
            
        $('#select_op_tags_select').selectpicker('refresh');
        $('#select_op_names_select').selectpicker('refresh');
        current_modal_id = 'modal_op_selector';
        $('#modal_op_selector').modal();
    });
}


function select_op_make_table(nb_cols, ids, divs) {
    
    //table creation
    var tbl = document.createElement('table');
    var tbdy = document.createElement('tbody');
    var nb_rows = Math.ceil(ids.length/nb_cols);
    
    tbl.style.width = '100%';
    
    var index = 0;
    for (var i=0; i< nb_rows; i++) {
        var tr = document.createElement('tr');
        for (var j=0; j<nb_cols; j++) {
            if (ids[index] != null) {
                var td = document.createElement('td');
                td.setAttribute('align', 'center');
                td.style.width = '20px';
                td.appendChild(divs[index]);
                tr.appendChild(td);
                index = index + 1;
            }
        }
        tbdy.appendChild(tr);
    }
    tbl.appendChild(tbdy);
    return tbl;
}


function select_op_on_change(from) {
    //'from' is in ['tags, 'names'], not used for now ....
    
    var ops_to = document.getElementById("select_op_tags_select").options;
    var ops_no = document.getElementById("select_op_names_select").options;
    
    //cleaning
    var pdiv = document.getElementById('select_op_panel');
    select_op_selected = []
    select_op_divs = []
    
    //tags
    for (var o=0; o<ops_to.length; o++) {
        if (ops_to[o].selected) {
            global_ops_cl.forEach( function (op) {
                if (op['tags'].indexOf(ops_to[o].text) >= 0 && select_op_selected.indexOf(op['id']) == -1) {
                    select_op_divs.push(select_op_new_operator(parseInt(op['id']), true));
                    select_op_selected.push(parseInt(op['id']));
                }
            });
        }
    }
    
    //names
    for (var o=0; o<ops_no.length; o++) {
        if (ops_no[o].selected && select_op_selected.indexOf(parseInt(ops_no[o].value)) == -1) {
            select_op_divs.push(select_op_new_operator(parseInt(ops_no[o].value), true));
            select_op_selected.push(parseInt(ops_no[o].value));
        }
    }
    
    //Cleaning
    while(pdiv.firstChild){
        pdiv.removeChild(pdiv.firstChild);
    }
    pdiv.appendChild(select_op_make_table(nb_cols_in_displayed_table, select_op_selected, select_op_divs));
}


function select_op_new_operator(cl_id, removable) {
    var cl = class_from_id(cl_id);
    var ndiv = document.createElement('div');
    var s = '';
    if (removable) {
        ndiv.id = "select_op_selected_"+cl.id+'rem';
        s = '   <table> \
                        <tr> \
                            <td align="center">'+cl.svg+ ' \
                            <td valign="top"> <span class="glyphicon glyphicon-remove" onclick="select_op_delete_op(\''+cl.id+'\');" style="cursor: pointer;"/> \
                        <tr>';
    }
    else {
        ndiv.id = "select_op_selected_"+cl.id+"_static";
        ndiv.setAttribute('draggable', 'true');
        ndiv.style.zIndex = '2';
        ndiv.classList.add("sakura_static_operator");
        s = '   <table> \
                        <tr> \
                            <td align="center">'+cl.svg+ ' \
                        <tr>';
    }
    
    var l = cl.name.length;
    var fname = cl.name;
    if (l > 7) {
        fname = cl.name.substring(0,7)+'.';
    }
    
    s += '<td align="center"> <font size="1">'+fname+'</font>';
    s += '</table>';
    ndiv.innerHTML = s;
    return (ndiv);
}


function select_op_delete_op(id) {
    
    var index = select_op_selected.indexOf(parseInt(id));
    
    select_op_selected.splice(index, 1);
    select_op_divs.splice(index, 1);
    
    var pdiv = document.getElementById('select_op_panel');
    //Cleaning
    while(pdiv.firstChild){
        pdiv.removeChild(pdiv.firstChild);
    }
    pdiv.appendChild(select_op_make_table(nb_cols_in_displayed_table, select_op_selected, select_op_divs));
}


function select_op_add_panel() {
    
    var title = document.getElementById('select_op_panel_title').value;
    
    //Here we manage a panel title by default
    if (title == '') { 
        title  = "Panel 0";
        var cpt = 0;
        global_op_panels.forEach( function (p) {
            console.log(p);
            if (p['title'] == title) {
                 cpt += 1;
            }
        title = "Panel "+cpt;
        });
    }
    
    var divs = []
    select_op_selected.forEach( function(item) {
        divs.push(select_op_new_operator(item, false));
    });
    
    var tbl = select_op_make_table(3, select_op_selected, divs);
    var tmp_el = document.createElement("div");
    tmp_el.appendChild(tbl);
    
    var acc_id = global_op_panels.length;
    global_op_panels.forEach( function (op) {
        if (op['id'] == acc_id)
            acc_id ++;
    });
    
    acc_id = "accordion_"+acc_id
    
    select_op_create_accordion(title, acc_id, tmp_el.innerHTML);
    
    //update global variable
    global_op_panels.push({'id': acc_id, 'title': title, 'selected_ops': select_op_selected, gui: {'opened': true}});
    current_modal_id = null;
    $('#modal_op_selector').modal('hide');
    
   //Send the the current global var to the hub
   save_project()
}


function change_chevron(a, panel_id) {
    
    var panel = panel_from_id(panel_id);
    var span_class = a.find('span').attr('class');
    
    if (span_class == "glyphicon glyphicon-chevron-up") {
        a.find('span').removeClass('glyphicon glyphicon-chevron-up').addClass('glyphicon glyphicon-chevron-down');
        panel.gui.opened = false;
    }
    else {
        a.find('span').removeClass('glyphicon glyphicon-chevron-down').addClass('glyphicon glyphicon-chevron-up');
        panel.gui.opened = true;
    }
    
    save_project();
}


function select_op_create_accordion(title, id, ops) {
    
    var title_escaped = title.replace(' ', '_');
    var wrapper= document.createElement('div');
    load_from_template(
                    wrapper,
                    "panel.html",
                    {'id': id, 'title': title, 'title_escaped': title_escaped},
                    function () {
                        var modal = wrapper.firstChild;
                        $(modal).find("#panel_"+id+"_body").html(ops);
                        var acc_div = document.getElementById('op_left_accordion');
                        var butt = document.getElementById('select_op_add_button');
                        
                        acc_div.insertBefore(wrapper.firstChild, butt);
                    });
}


function change_panel_title(id) {
    console.log($("#"+id));
    $("#"+id).attr('contentEditable', true);

/*}).blur(
    function() {
        $(this).attr('contentEditable', false);
    };
*/
}


function select_op_delete_accordion(id) {
    var acc = document.getElementById(id);
    document.getElementById('op_left_accordion').removeChild(acc);
    
    var index = panel_index_from_id(acc.id);
    global_op_panels.splice(index,1);
    
    save_project();
}


function panel_from_id(id) {
    return global_op_panels.find( function (e) {
        return e['id'] === id;
    });
}

function panel_index_from_id(id) {
    for (var i=0; i< global_op_panels.length; i++)
        if (global_op_panels[i]['id'] == id)
            return i;
    return -1
}