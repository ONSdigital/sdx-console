function genList(page, noPages) {
    if (page > 0 && page < noPages) {
        var list = document.getElementById("paglist");
        var entry = document.createElement("li");
        var a = document.createElement("a");
        var linkpage = page.toString();
        var id = ("page" + linkpage);
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
        a.setAttribute("href", "/store/" + pageString + "?" + paramsString);
    }
}
