//
// API Calls
//

// Adds paper's catalog to db
// - pushing the catalog id
// - reloading the page
function push_catalog(){
    let paper_id = $(this).data('paper_id')
    $.post({
        url: "/api/push_catalog",
        data: JSON.stringify({ paper_id: paper_id}),
        contentType: 'application/json; charset=utf-8'
    })
    .done((res) => {
        if (res.status == "success"){
            console.log('Catalog added to db for paper id: ', res.data.paper_id);
        } else {
            console.log('Error adding to db for paper id: ', res.data.paper_id);
        }
        location.reload();
    })
    .fail((err) => {
        alert("ERROR when trying to add catalog to db. See logs.");
        console.log(err);
    });
}

