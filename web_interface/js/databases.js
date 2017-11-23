//Code started by Michael Ortega for the LIG
//August, 21st, 2017


function fill_dbms() {
    //first we ask the hub the dbms
    sakura.common.ws_request('list_datastores', [], {}, function (result) {
        console.log(result);
        $('#database_dbms_input').empty();
            result.forEach( function(sgbd) {
            if (sgbd['online'])
                $('#database_dbms_input').append('<option value="'+sgbd['datastore_id']+'">datastore_id: '+sgbd['datastore_id']+" / daemon_id: "+sgbd['daemon_id']+'</option>');
        });
    });
}


function new_database() {
    var name = $('#database_name_input').val();
    
    if ((name.replace(/ /g,"")).length == 0) {
        alert("Empty name!! We cannot create data without a name.");
        return ;
    }
    
    var short_d     = $('#database_shortdescription_input').val();
    //var tags      = $('#dataset_tags_input').val();
    var dbms_id     = $('#database_dbms_input').val();
    var public_val  = $('#database_public_input')[0].checked;
    
    sakura.common.ws_request('new_database', [parseInt(dbms_id), name], {'short_desc': short_d}, function(result) {
        if (result < 0) {
            alert("Something Wrong with the values ! Please check and submit again.");
        }
        else {
            $('#createDataBaseModal').modal('hide');
        }
    });
}
