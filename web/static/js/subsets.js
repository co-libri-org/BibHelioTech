function enable(elmt){
    elmt.removeClass('disabled').addClass('enabled');
}
function disable(elmt){
    elmt.removeClass('enabled').addClass('disabled');
}
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

function toggleSubsetDisplay(subset_name, taskStatus, subsetStatus, message, alt_message, statusClass="") {

    const subsetTr = $(`#${subset_name}`);
    const showLink = subsetTr.find(".show-subset");
    const unzipBtn = subsetTr.find(".unzip-subset");
    const statusMsg = subsetTr.find(".zip-status");
    const statusSpinner = subsetTr.find(".status-spin");

    disable(showLink)
    disable(unzipBtn)

    statusMsg.text(message).attr("title", alt_message).addClass(statusClass);
    if ( taskStatus == "error" ){
            disable(showLink);
            disable(unzipBtn);
    } else if ( taskStatus == "unknown" ){
        if ( subsetStatus == "extracted"){
            enable(showLink);
            disable(unzipBtn);
        } else if ( subsetStatus == "zipped") {
            enable(unzipBtn);
            disable(showLink);
        }

    }
    else if  (1 === 1) {
        console.log("else if")
    }
    else {
        console.log("else ")
    }

}


function updateSubsetStatus(subsetName){
   // now dynamically build the flask url
   const url = urlSubsetStatusTemplate.replace("__subset_name__", subsetName);

   $.ajax({
            url: url,
            method: 'GET',
        })
   .done((res) => {
        const taskStatus = res.data.task_status;
        const subsetStatus = res.data.subset_status;
        const subsetMessage = res.data.message;
        const altMessage = res.data.alt_message;


        if (taskStatus == "started") {
            // update and wait for task to finish
            setTimeout(function() {
                updateSubsetStatus(subsetName);
            }, 500);
        } else if (taskStatus == "queued") {
            // update and wait for task to be executed
            setTimeout(function() {
                updateSubsetStatus(subsetName);
            }, 1000);
        }

       toggleSubsetDisplay(subsetName, taskStatus, subsetStatus, subsetMessage, altMessage)

   })
   .fail((err) => {
        res = err.responseJSON
        console.error("Got 503 from route:", res);
        const subsetMessage = res.data.message;
        const altMessage = res.data.alt_message;
        toggleSubsetDisplay(subsetName, "error", "", subsetMessage, altMessage, "error")
   });
}

function setUnzipBtnOnClick(){
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

