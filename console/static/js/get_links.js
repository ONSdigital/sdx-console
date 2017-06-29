function genList(i, no_pages) {
    if (i > 0 && i < no_pages) {
        var list = document.getElementById('paglist');
        var entry = document.createElement('li');
        var a = document.createElement('a');
        var page = i.toString();
        var id = ("page" + page);
        a.setAttribute("id", id);
        a.appendChild(document.createTextNode(page));
        entry.appendChild(a);
        list.appendChild(entry);
    }
}

function getLinks(page) {
    if (page > 0) {
        let params = (new URL(document.location)).searchParams;
        var paramsString = params.toString();
        var pageString = page.toString();
        var id = ("page" + pageString);
        var a = document.getElementById(id);
        a.href = ("/store/" + pageString + "?" + paramsString);
    }
}
