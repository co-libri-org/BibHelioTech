function updateExtractedTr(istex_struct){
    // build the paper-show url
    const paper_show_url = urlPaperShowTemplate.replace("__paper_id__", istex_struct.paper_id);

    // get <tr> by id==istex_id
    const $tr = $('#'+istex_struct.istex_id);
    if ($tr.length === 0){
        console.error("TR not found for istex_id:", istex_struct.istex_id);
        return;
    }

    // change class "to_add" in "added" or "mocked" by istex_struct.status
    $tr.removeClass("to_add").addClass(istex_struct.status);

    // insert <a class="btn"> in first <th>  with inner_text=istex_struct.paper_id and href="#"
    $firstTh = $tr.find('th.td_num');
    $firstTh.html(`<a class="btn btn-warning" href="${paper_show_url}" title="Show paper #${istex_struct.paper_id}">${istex_struct.paper_id}</a>`);

    // in last <td> remove <button> replace with text "added"
    const $lastTd = $tr.find('td').last();
    $lastTd.empty().text(istex_struct.status);

    // move the page to that <tr>
    //$('html, body').animate({
    //    scrollTop: $tr.offset().top - 100 // offset for visibility
    //}, 500);
}

// Add extracted calls api/add_extracted
function handleAddExtracted(subset_name, istex_id){
    $.ajax({
        url: urlAddExtracted,
        method: "POST",
        data: JSON.stringify({ subset_name: subset_name, istex_id: istex_id, exec_type: "db" }),
        contentType: 'application/json; charset=utf-8'
    })
    .done((res) => {
        updateExtractedTr(res.data.istex_struct);
    })
    .fail((err) => {
        //const statusElmtId = '#zip-status-' + subset_name;
        //failedToStatus(err, statusElmtId, "FAILED Unzip Subset");
        console.error(err);
    });
}

// for each button.add-extracted,
// set the on-click event callback
function setAddBtnOnClick(){
    $('.add-extracted').click(function(){
        const subset_name = $(this).data("subset_name");
        const istex_id = $(this).data("istex_id");
        handleAddExtracted(subset_name, istex_id);
    });
}

// Filtering enables Add All button
$('#filter-not_in_db').click(function () {
    const $filterBtn = $(this);
    const $addAllBtn = $('#add-not_in_db')
    const isFiltering = $filterBtn.text().trim() === "Filter db";
    if ( isFiltering ){
        $('tr.in_db').hide();
        $addAllBtn.prop("disabled", false);
        $filterBtn.text("Unfilter");
    } else {
        $('tr.in_db').show();
        $addAllBtn.prop("disabled", true);
        $filterBtn.text("Filter db");
    }

});

// when add-all-btn is clicked,
// call the same callback for each button.add-extracted
$('#add-not_in_db').click(function () {
    $('.add-extracted').each(function () {
        const subset_name = $(this).data("subset_name");
        const istex_id = $(this).data("istex_id");
        handleAddExtracted(subset_name, istex_id);
    });
});
