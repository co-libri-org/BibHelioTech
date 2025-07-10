function updateExtractedTr(istex_struct){
    alert(JSON.stringify(istex_struct));
}
function setAddBtnOnClick(){
    $('.add-extracted').click(function(){
        const subset_name = $(this).data("subset_name")
        const istex_id = $(this).data("istex_id")
        $.ajax({
            url: urlAddExtracted,
            method: "POST",
            data: JSON.stringify({ subset_name: subset_name, istex_id: istex_id, exec_type: "mocked" }),
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
    });
}
