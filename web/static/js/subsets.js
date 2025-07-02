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

function toggleSubsetDisplay(subset_name, taskStatus, subsetStatus, message, alt_message){

    const subsetTr = $(`#${subset_name}`);
    const showLink = subsetTr.find(".show-subset");
    const unzipBtn = subsetTr.find(".unzip-subset");
    const statusMsg = subsetTr.find(".zip-status");
    const statusSpinner = subsetTr.find(".status-spin");

    showLink.addClass("disabled");
    unzipBtn.addClass("disabled");
    statusMsg.text(taskStatus+" World");

    if (taskStatus === "CnxError") {
        if (subsetStatus === "extracted") {
            enable(showLink);
            disable(unzipBtn);
            statusMsg.text("Extracted");
        } else {
            disable(showLink);
            disable(unzipBtn);
            statusMsg.text("Err Cnx");
        }
    } else if (taskStatus === "NoJob") {
        if (subsetStatus === "extracted") {
            enable(showLink);
            disable(unzipBtn);
            statusMsg.text("Extracted");
        } else {
            disable(showLink);
            enable(unzipBtn);
            statusMsg.text("Zipped");
        }
    } else if (taskStatus === "queued") {
        statusMsg.text("queued since ...");
    } else if (taskStatus === "started") {
        statusMsg.text("running since ...");
    } else if (taskStatus === "finished" || taskStatus === "other") {
        if (subsetStatus === "extracted") {
            enable(showLink);
            disable(unzipBtn);
            statusMsg.text("Extracted");
        } else {
            disable(showLink);
            enable(unzipBtn);
            statusMsg.text("Zipped");
        }
    } else {
        console.log("taskStatus: "+taskStatus);
        console.log("subsetStatus: "+subsetStatus);
    }
}


function updateSubsetStatus(subsetName){
    console.log("Updating status for "+subsetName);
   // now dynamically build the flask url
   const url = urlSubsetStatusTemplate.replace("__subset_name__", subsetName);

   $.ajax({
            url: url,
            method: 'GET',
        })
   .done((res) => {
        const subsetStatus = res.data.subset_status;
        const taskStatus = res.data.task_status;
        const taskProgress = res.data.task_progress;
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

        let normalizedStatus = taskStatus;
        if (res.status === "error" && altMessage.includes("Redis")) {
            normalizedStatus = "CnxError";
        } else if (res.status === "failed" && altMessage.includes("No task id")) {
            normalizedStatus = "NoJob";
        }

       toggleSubsetDisplay(subsetName, normalizedStatus, subsetStatus, subsetMessage, altMessage)

   })
   .fail((err) => {
        console.error("Error", err);
        // TODO: call fallback
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

