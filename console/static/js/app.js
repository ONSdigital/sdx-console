$(function () {

    function asyncGet(url) {
        // Return a new promise.
        return new Promise(function (resolve, reject) {
            // Do the usual XHR stuff
            var req = new XMLHttpRequest();
            req.open("GET", url, true);

            req.onload = function () {
                // This is called even on 404 etc
                // so check the status
                if (req.status == 200) {
                    // Resolve the promise with the response text
                    resolve(req.response);
                }
                else {
                    // Otherwise reject with the status text
                    // which will hopefully be a meaningful error
                    reject(Error(req.statusText));
                }
            };

            // Handle network errors
            req.onerror = function () {
                reject(Error("Network Error"));
            };

            // Make the request
            req.send();
        });
    }

    function asyncGetJSON(url) {
        return asyncGet(url).then(JSON.parse);
    }

    function asyncPostJSON(url, json_data) {
        // Return a new promise.
        return new Promise(function (resolve, reject) {
            // Do the usual XHR stuff
            var req = new XMLHttpRequest();
            req.open("POST", url, true);

            req.onload = function () {
                // This is called even on 404 etc
                // so check the status
                if (req.status == 200) {
                    // Resolve the promise with the response text
                    resolve(req.response);
                }
                else {
                    // Otherwise reject with the status text
                    // which will hopefully be a meaningful error
                    reject(Error(req.statusText));
                }
            };

            // Handle network errors
            req.onerror = function () {
                reject(Error("Network Error"));
            };

            req.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

            // Make the request
            req.send(JSON.stringify(json_data));
        });
    }

    function convert_utc_to_local(utc_dt) {
        if (!utc_dt) {
            return "";
        }
        utcDateTime = moment.utc(utc_dt);
        localDateTime = utcDateTime.local();
        return localDateTime.format("Y-m-d H:mm:ss");
    }

    function guid() {
        // http://stackoverflow.com/a/105074
        function s4() {
            return Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
        }

        return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
    }

    function get_survey_data() {
        var data = $("#post-data").val();
        var obj = JSON.parse(data);

        // if no tx_id
        if (!("tx_id" in obj)) {
            // generate uuid
            obj["tx_id"] = guid();
        }

        // if no submitted_at
        if (!("submitted_at" in obj)) {
            // set as current date and time
            obj["submitted_at"] = moment.utc().format("YYYY-MM-DDTHH:mm:ssZ");
        }
        return obj;
    }

    $(".utc_datetime").each(function (index, obj) {
        obj.innerHTML = convert_utc_to_local(obj.innerHTML);
    });

    $("#submit-data").on("click", function (event) {
        event.preventDefault();
        var postData = get_survey_data();
        var quantity = $("#survey-quantity").val();
        $(".alert").hide();
        asyncPostJSON("/submit", {
            "survey": postData,
            "quantity": quantity
        }).then(function (data) {
            $(".alert").removeClass("alert-success alert-danger hidden");
            $(".alert").addClass("alert panel panel--simple panel--success alert-success").text("Posted: " + data);
            $(".alert").show();
        }, function (error) {
            $(".alert").removeClass("alert-success alert-danger hidden");
            $(".alert").addClass("alert panel panel--simple panel--error alert-danger").text("Error during submission");
            $(".alert").show();
            window.alert("Failed submission");
            console.error("Failed!", error);
        });
    });

    $("#validate").on("click", function (event) {
        event.preventDefault();
        var postData = get_survey_data();
        $(".alert").hide();
        asyncPostJSON("/validate", postData).then(function (data) {
            var jsonData = JSON.parse(data);
            if (jsonData.valid === true) {
                $(".alert").removeClass("alert-success alert-danger hidden");
                $(".alert").addClass("alert panel panel--simple panel--success alert-success").text("Validation result: " + data);
                $(".alert").show();
            } else {
                $(".alert").removeClass("alert-success alert-danger hidden");
                $(".alert").addClass("alert panel panel--simple panel--error alert-danger").text("Validation Error. Result: " + data);
                $(".alert").show();
            }
        }, function (error) {
            $(".alert").removeClass("alert-success alert-danger hidden");
            $(".alert").addClass("alert-danger").text("Error during validation submission");
            $(".alert").show();
            window.alert("Failed validation");
            console.error("Failed!", error);
        });
    });

    $("#survey-selector").on("change", function (event) {
        asyncGet("/static/surveys/" + $(event.target).val()).then(function (data) {
            $("#post-data").val(data);
        }, function (error) {
            console.error("Failed!", error);
        });
    });

    $("#empty-ftp").on("click", function (event) {
        $(".alert").hide();
        if (window.confirm("Are you sure you want to clear the FTP?")) {
            asyncGetJSON("/clear").then(function (data) {
                for (var i in dataTypes) {
                    var dataType = dataTypes[i];
                    $("#" + dataType + "-data tbody").empty();
                }
                $(".alert").removeClass("alert-success alert-danger hidden");
                $(".alert").addClass("alert panel panel--simple panel--success alert-success").text("Cleared " + data.removed + " files from FTP");
                $(".alert").show();
                window.alert("Cleared " + data.removed + " files from FTP");
            }, function (error) {
                $(".alert").removeClass("alert-success alert-danger hidden");
                $(".alert").addClass("alert-danger").text("Error on emptying ftp");
                $(".alert").show();
            });
        }
    });

    var dataTypes = ["pck", "image", "index", "receipt", "json"];

    function refreshFTP() {
        $("#refresh-ftp").show();
        asyncGetJSON("/ftp.json").then(function (ftpData) {

            for (var i in dataTypes) {
                var dataType = dataTypes[i];
                var tableData = ftpData[dataType];

                $("#" + dataType + "-data tbody").empty();

                $.each(tableData, function (filename, metadata) {
                    var $tableRow = $('<tr id="' + metadata['name'] + '"><td><a href="#">' + metadata['name'] + '</a></td><td>' + metadata['size'] + 'b</td><td>' + metadata['modify'] + '</td></tr>');

                    var onClickType = dataType;

                    $tableRow.on("click", function (event) {
                        var filename = $(event.target).closest("tr").attr("id");
                        $("#contentModal .modal-title").text(filename);
                        asyncGet("/view/" + onClickType + "/" + filename).then(function (data) {
                            $("#contentModal .modal-body").html(data);
                            $("#contentModal").modal("show");
                        }, function (error) {
                            console.error("FTP failed!", error);
                        });
                    });

                    $("#" + dataType + "-data tbody").append($tableRow);
                });
            }
            $("#refresh-ftp").hide();

            // recurse:
            setTimeout(refreshFTP, 5000);

        }, function (error) {
            $("#refresh-ftp").hide();
            console.error("FTP failed!", error);
        });
    }

    // on page load stuff:

    asyncGet("/static/surveys/023.0102.json").then(function (response) {
        $("#post-data").text(response);
    }, function (error) {
        console.error("Failed loading survey 023.0102!", error);
    });

    asyncGetJSON("/surveys").then(function (surveys) {
        for (var i = 0; i < surveys.length; i++) {
            $("#survey-selector")
                .append($("<option>", {value: surveys[i]})
                    .text(surveys[i]));
        }
    }, function (error) {
        console.error("Failed loading surveys!", error);
    });

    // kick off the ftp polling:
    refreshFTP();

});


    function checkAll(ele) {
        var checkboxes = document.getElementsByTagName('input');
        if (ele.checked) {
            for (var i = 0; i < checkboxes.length; i++) {
                if (checkboxes[i].type == 'checkbox') {
                    checkboxes[i].checked = true;
                }
            }
        } else {
            for (var i = 0; i < checkboxes.length; i++) {
                console.log(i)
                if (checkboxes[i].type == 'checkbox') {
                    checkboxes[i].checked = false;
                }
            }
        }
    }