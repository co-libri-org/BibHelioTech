//
// BHT tasks display
//

// Change the catalog status depending on request response
//
function toggleWrapper(res, action) {
    const catElmtId = '#cat-link-' + res.data.paper_id;
    const statusElmtId = '#paper-status-' + res.data.paper_id;

    cat_element = $(catElmtId);
    status_element = $(statusElmtId)

    if ( cat_element.length > 0 ) {
        // element catalog exists in DOM
        toggleCatalog(res, action, catElmtId);
    } else if ( status_element.length > 0 ){
        // element paper-status exists in DOM
        togglePaperStatus(res, action, statusElmtId)
    } else {
        // none of the previous
        alert("None");
        return
    }
}

function togglePaperStatus(res, action, statusElmtId){
    if  ( ["finished", "failed"].includes(res.data.task_status) ){
        html_content = "Version <b>"+res.data.ppl_ver+"</b> "+res.data.task_status+" at "+res.data.task_stopped;
    }
    else if ( res.data.task_status == 'started') {
        html_content = "Version <b>"+res.data.ppl_ver+"</b> "+"running since "+res.data.task_started;
    }
    $(statusElmtId).html( html_content);
}

function toggleCatalog(res, action, catElmtId) {
    if (action == "enable") {
        $(catElmtId).contents()[0].data = res.data.ppl_ver;
        $(catElmtId).removeAttr('disabled');
        if (res.data.cat_is_processed === false) {
            $(catElmtId).find('span').removeClass('invisible').addClass('visible');
        }
    } else if (action == "disable") {
        $(catElmtId).contents()[0].data = '___';
        $(catElmtId).attr('disabled', 'disabled');
        $(catElmtId).find('span').removeClass('visible').addClass('invisible');
    }
}

// Update the status element from error returned from server (503)
//
function failedToStatus(err, statusElmtId) {
    err_status = err.responseJSON.status;
    err_message = err.responseJSON.data.message;
    alt_message = err.responseJSON.data.alt_message;
    paper_id = err.responseJSON.data.paper_id;
    $(statusElmtId).removeClass("finished started failed queued undefined");
    $(statusElmtId).addClass(err_status);
    $(statusElmtId).html(err_message);
    $(statusElmtId).attr("title", alt_message);
}

// Update the status element by request on paper's id
//
function setStatus(paper_id) {
    // Build dom elements' ids to grab
    const spinnerElmtId = '#spinner-' + paper_id
    const statusElmtId = '#bht-status-' + paper_id
    $.ajax({
            url: `/bht_status/${paper_id}`,
            method: 'GET',
        })
        .done((res) => {
            const taskStatus = res.data.task_status;

            // Update css class
            $(statusElmtId).removeClass("finished started failed queued undefined");
            $(statusElmtId).addClass(taskStatus);

            // Disable spinner if active
            $(spinnerElmtId).removeClass('d-inline-block')
            $(spinnerElmtId).addClass('d-none')

            // Update status text content from request response
            $(statusElmtId).html(res.data.message)
            $(statusElmtId).attr('title', res.data.alt_message)

            // Update display depending on status
            if (taskStatus === 'started') {
                // show spinner while running task
                $(spinnerElmtId).removeClass('d-none')
                $(spinnerElmtId).addClass('d-inline-block')
                // update task elapsed each 1s
                setTimeout(function() {
                    setStatus(res.data.paper_id);
                }, 1000);
            }
            else if (taskStatus === 'queued') {
                // wait for queued to be executed
                setTimeout(function() {
                    setStatus(res.data.paper_id);
                }, 1000);
            }
            else if (taskStatus === 'finished') {
                // update catalog availability when task finished, then quit
                toggleWrapper(res, "enable");
                return false;
            }
            else if (taskStatus === 'failed') {
                // disable catalog access when task failed, then quit
                toggleWrapper(res, "disable");
                return false;
            }
            else {
                console.log(res);
            }
        })
        .fail((err) => {
            // Show there was an error returned by /bht_status/p_id
            failedToStatus(err, statusElmtId);
        });
}

// Update status for all papers
//
function updateAllStatuses() {
    $('.bht-status').each(function(index) {
        const paperId = $(this).attr('id').substring(11);
        setStatus(paperId);
    });
}

// Run a task by paper's id at run-btn click
//
function setBhtRunOnClick() {
    $('.run-bht').on('click', function() {
        let paper_id = $(this).data('paper_id');
        const statusElmtId = '#bht-status-' + paper_id;
        $(statusElmtId).fadeOut(200).fadeIn(200);
        $.ajax({
                url: '/bht_run',
                data: {
                    paper_id: paper_id,
                    file_type: $(this).data('file_type')
                },
                method: 'POST'
            })
            .done((res) => {
                toggleWrapper(res, "disable");
                if (res.status === "success") {
                    setStatus(res.data.paper_id);
                } else {
                    alert("Error: " + res.data.message);
                }
            })
            .fail((err) => {
                // Show there was an error returned by /bht-run
                failedToStatus(err, statusElmtId);
            });
    });
}