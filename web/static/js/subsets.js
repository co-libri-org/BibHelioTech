function failedToStatus(err, statusElmtId, message) {
    err_status = err.responseJSON.status;
    err_message = err.responseJSON.data.message;
    alt_message = err.responseJSON.data.alt_message;
    $(statusElmtId).removeClass("finished started failed queued undefined");
    $(statusElmtId).addClass(err_status);
    $(statusElmtId).html(err_message);
    $(statusElmtId).attr("title", alt_message);
    console.error(message)
    console.error(err)
}

function toggleSubsetDisplay(subset_name, state){

    const subsetBtnElmtId = '#show-' + subset_name;
    const unzipBtnElmtId = '#unzip-' + subset_name;
    const statusElmtId = '#zip-status-' + subset_name;
    const spinnerElmtId = '#spinner-' + subset_name;

    if (state  == 'extracted'){
        $(subsetBtnElmtId).removeClass('disabled')
    }
    else if (state == 'zipped' ) {
        $(unzipBtnElmtId).removeClass('disabled')
    }
    else if (state == 'running' ) {
        // show spinner while running task
        $(spinnerElmtId).removeClass('d-none').addClass('d-inline-block')
    }
    else if (state == 'reset' ) {
        // Disable all
        $(subsetBtnElmtId).addClass('disabled')
        $(unzipBtnElmtId).addClass('disabled')
        $(spinnerElmtId).removeClass('d-inline-block').addClass('d-none')
    }
    //if
}
// url_for template for dynamically use before subset_name is known
const urlSubsetStatusTemplate = "{{ url_for('main.api_subset_status', subset_name='__subset_name__') }}";

function updateSubsetStatus(subset_name){
    console.log("Updating status for "+subset_name);
   // now dynamically build the flask url
   const url = urlSubsetStatusTemplate.replace("__subset_name__", subset_name);
   const statusElmtId = '#zip-status-' + subset_name;

   toggleSubsetDisplay(subset_name, 'reset');

   $.ajax({
            url: url,
            method: 'GET',
        })
   .done((res) => {
        const taskStatus = res.data.task_status;
        const taskProgress = res.data.task_progress;


        if (taskStatus == "started") {
            $(statusElmtId).html(taskProgress).attr("title", res.data.alt_message);
            toggleSubsetDisplay(subset_name, 'running');
            setTimeout(function() {
                updateSubsetStatus(subset_name);
            }, 500);
        } else if (taskStatus == "queued") {
            toggleSubsetDisplay(subset_name, 'reset');
            $(statusElmtId).html(taskStatus)
                               .attr("title", res.data.alt_message);
            // wait for queued to be executed
            setTimeout(function() {
                updateSubsetStatus(subset_name);
            }, 1000);
        } else if (taskStatus == "finished") {
            // update display
            toggleSubsetDisplay(subset_name, 'extracted');
            $(statusElmtId).html("Finished")
                               .attr("title", res.data.alt_message);
        } else {
            $(statusElmtId).html(res.data.message)
                               .attr("title", res.data.alt_message);
        }
   })
   .fail((err) => {
        failedToStatus(err, statusElmtId, "FAILED Update Unzip Status");
   });
}

function setUnzipBtnOnCLick(){
    $('.unzip-subset').click(function(){
        const subset_name = $(this).data("subset_name")
        const total_files = $(this).data("total_files")
        $.ajax({
            url: "{{url_for('main.api_subset_unzip')}}",
            method: "POST",
            data: JSON.stringify({ subset_name: subset_name, total_files: total_files}),
            contentType: 'application/json; charset=utf-8'
        })
        .done((res) => {
            updateSubsetStatus(subset_name);
        })
        .fail((err) => {
            const statusElmtId = '#zip-status-' + subset_name;
            failedToStatus(err, statusElmtId, "FAILED Unzip Subset");
            console.error(err);
        });
    });
}

function updateAllStatuses() {
    $('.zip-status').each(function(index) {
        const subset_name = $(this).data("subset_name")
        updateSubsetStatus(subset_name);
    });
}

